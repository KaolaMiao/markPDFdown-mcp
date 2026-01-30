import { useState, useEffect, useRef } from 'react';

// 进度事件数据接口
export interface ProgressEventData {
    task_id: string;
    current_page: number;
    total_pages: number;
    progress: number;
    status: string;
    timestamp: number;
}

// Hook 返回值接口
interface UseTaskProgressReturn {
    progress: number;
    currentPage: number;
    totalPages: number;
    status: string;
    isConnected: boolean;
}

/**
 * 自定义 Hook：用于监听任务的 SSE 进度事件
 * @param taskId 任务 ID
 * @param initialStatus 初始状态 (可选)
 */
export function useTaskProgress(taskId: string, initialStatus?: string): UseTaskProgressReturn {
    const [progress, setProgress] = useState<number>(0);
    const [currentPage, setCurrentPage] = useState<number>(0);
    const [totalPages, setTotalPages] = useState<number>(0);
    const [status, setStatus] = useState<string>(initialStatus || 'pending');
    const [isConnected, setIsConnected] = useState<boolean>(false);

    // 使用 ref 来保存 EventSource 实例，防止因闭包问题导致无法正确清理
    const eventSourceRef = useRef<EventSource | null>(null);

    useEffect(() => {
        // 如果没有 taskId 或任务已经完成/失败，则不需要建立连接
        // 注意：如果想要查看历史完成任务的最后进度，可能需要调整逻辑。
        // 这里假设主要是为了监控 "进行中" 的任务。
        if (!taskId || status === 'completed' || status === 'failed') {
            return;
        }

        // 定义连接函数
        const connectSSE = () => {
            // 关闭旧连接
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }

            // 所有的 API 请求都应该基于配置的基础 URL，这里假设后端运行在 8000 端口
            // 在生产环境中，应该从环境变量或配置文件获取
            const API_BASE_URL = 'http://localhost:8000';
            const url = `${API_BASE_URL}/api/v1/events?task_id=${taskId}`;

            console.log(`[SSE] Connecting to ${url}`);
            const eventSource = new EventSource(url);
            eventSourceRef.current = eventSource;

            eventSource.onopen = () => {
                console.log(`[SSE] Cconnection opened for task ${taskId}`);
                setIsConnected(true);
            };

            eventSource.onmessage = (event) => {
                try {
                    // 处理连接消息
                    if (event.data.includes('"client_id":')) {
                        console.log('[SSE] Connected message received');
                        return;
                    }

                    const data: ProgressEventData = JSON.parse(event.data);
                    // console.log('[SSE] Progress update:', data);

                    setProgress(data.progress);
                    setCurrentPage(data.current_page);
                    setTotalPages(data.total_pages);
                    setStatus(data.status);

                    // 如果任务完成或失败，关闭连接
                    if (data.status === 'completed' || data.status === 'failed') {
                        console.log(`[SSE] Task ${taskId} finished with status: ${data.status}, closing connection.`);
                        eventSource.close();
                        setIsConnected(false);
                        eventSourceRef.current = null;
                    }
                } catch (error) {
                    console.error('[SSE] Failed to parse event data:', error);
                }
            };

            eventSource.onerror = (error) => {
                console.error('[SSE] Connection error:', error);
                eventSource.close();
                setIsConnected(false);
                eventSourceRef.current = null;

                // 简单的重连逻辑：如果是处理中，3秒后重试
                if (status === 'processing') {
                    // 暂时不自动重连，避免死循环，让用户手动刷新或依赖轮询兜底
                    // 如果需要自动重连，可以使用 setTimeout 再次调用 connectSSE
                }
            };
        };

        connectSSE();

        // 清理函数
        return () => {
            if (eventSourceRef.current) {
                console.log(`[SSE] Cleaning up connection for task ${taskId}`);
                eventSourceRef.current.close();
                eventSourceRef.current = null;
                setIsConnected(false);
            }
        };
    }, [taskId]); // 移除 status 依赖，防止状态更新导致频繁重连。只在 taskId 变化时重连。
    // 但是我们需要在 status 变为 completed 时停止，这在 onmessage 内部处理了。

    return {
        progress,
        currentPage,
        totalPages,
        status,
        isConnected
    };
}
