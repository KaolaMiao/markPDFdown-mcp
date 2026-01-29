"""
SSE事件管理器

用于管理Server-Sent Events (SSE)连接和事件广播。
支持多个客户端同时订阅任务进度更新。
"""

import asyncio
import json
import logging
from typing import Dict, Set
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ProgressEvent:
    """进度事件数据"""
    task_id: str
    current_page: int
    total_pages: int
    progress: float  # 0-100
    status: str  # processing, completed, failed
    timestamp: float

    def to_sse_format(self) -> str:
        """转换为SSE格式"""
        data = json.dumps(asdict(self), ensure_ascii=False)
        return f"data: {data}\n\n"


class SSEManager:
    """
    SSE连接管理器

    管理:
    1. 活跃的SSE连接
    2. 任务订阅关系
    3. 事件广播
    """

    def __init__(self):
        # 每个连接的队列: {queue_id: asyncio.Queue}
        self._client_queues: Dict[str, asyncio.Queue] = {}

        # 任务订阅关系: {task_id: set(queue_id)}
        self._task_subscribers: Dict[str, Set[str]] = {}

        # 客户端任务订阅: {queue_id: set(task_id)}
        self._client_subscriptions: Dict[str, Set[str]] = {}

        # 客户端计数器
        self._client_counter = 0

        self._lock = asyncio.Lock()

    async def subscribe(self, task_id: str) -> tuple[str, asyncio.Queue]:
        """
        订阅任务进度更新

        Args:
            task_id: 任务ID

        Returns:
            (client_id, queue) 客户端ID和事件队列
        """
        async with self._lock:
            # 生成唯一客户端ID
            client_id = f"client_{self._client_counter}"
            self._client_counter += 1

            # 创建客户端队列
            queue: asyncio.Queue = asyncio.Queue(maxsize=100)

            # 注册客户端
            self._client_queues[client_id] = queue
            self._client_subscriptions[client_id] = {task_id}

            # 添加任务订阅
            if task_id not in self._task_subscribers:
                self._task_subscribers[task_id] = set()
            self._task_subscribers[task_id].add(client_id)

            logger.info(f"[SSE] Client {client_id} subscribed to task {task_id}")

            return client_id, queue

    async def unsubscribe(self, client_id: str):
        """
        取消客户端所有订阅

        Args:
            client_id: 客户端ID
        """
        async with self._lock:
            if client_id not in self._client_queues:
                return

            # 获取客户端订阅的任务
            task_ids = self._client_subscriptions.get(client_id, set())

            # 从任务订阅中移除客户端
            for task_id in task_ids:
                if task_id in self._task_subscribers:
                    self._task_subscribers[task_id].discard(client_id)

            # 清理客户端数据
            del self._client_queues[client_id]
            del self._client_subscriptions[client_id]

            logger.info(f"[SSE] Client {client_id} unsubscribed")

    async def broadcast_progress(
        self,
        task_id: str,
        current_page: int,
        total_pages: int,
        progress: float,
        status: str
    ):
        """
        广播进度事件到所有订阅者

        Args:
            task_id: 任务ID
            current_page: 当前页码
            total_pages: 总页数
            progress: 进度百分比 (0-100)
            status: 状态
        """
        async with self._lock:
            if task_id not in self._task_subscribers:
                # 没有订阅者
                return

            # 创建事件
            event = ProgressEvent(
                task_id=task_id,
                current_page=current_page,
                total_pages=total_pages,
                progress=progress,
                status=status,
                timestamp=asyncio.get_event_loop().time()
            )

            # 获取订阅者
            subscribers = self._task_subscribers[task_id].copy()

            # 发送事件到所有订阅者
            for client_id in subscribers:
                if client_id in self._client_queues:
                    queue = self._client_queues[client_id]
                    try:
                        # 非阻塞发送,队列满时丢弃旧事件
                        if queue.full():
                            # 移除最老的事件
                            try:
                                queue.get_nowait()
                            except asyncio.QueueEmpty:
                                pass

                        queue.put_nowait(event.to_sse_format())
                    except asyncio.QueueFull:
                        logger.warning(f"[SSE] Queue full for client {client_id}, event dropped")

    async def event_generator(self, task_id: str):
        """
        生成SSE事件流

        Args:
            task_id: 任务ID

        Yields:
            SSE格式的事件字符串
        """
        client_id, queue = await self.subscribe(task_id)

        try:
            # 发送连接成功消息
            yield f"event: connected\ndata: {{\"client_id\": \"{client_id}\", \"task_id\": \"{task_id}\"}}\n\n"

            # 持续发送事件
            while True:
                try:
                    # 等待事件,设置超时以发送心跳
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    yield ": keep-alive\n\n"
                except GeneratorExit:
                    # 客户端断开连接
                    logger.info(f"[SSE] Client {client_id} disconnected")
                    break
        finally:
            await self.unsubscribe(client_id)

    def get_stats(self) -> dict:
        """获取SSE管理器统计信息"""
        return {
            "total_clients": len(self._client_queues),
            "total_tasks": len(self._task_subscribers),
            "subscriptions": {
                task_id: len(subscribers)
                for task_id, subscribers in self._task_subscribers.items()
            }
        }


# 全局SSE管理器实例
sse_manager = SSEManager()
