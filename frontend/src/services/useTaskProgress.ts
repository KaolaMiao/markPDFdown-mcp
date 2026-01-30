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
    const retryCountRef = useRef<number>(0);
    const statusRef = useRef<string>(status);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // 保持 statusRef 同步，用于在闭包中获取最新状态
    useEffect(() => {
        statusRef.current = status;
    }, [status]);

    useEffect(() => {
        // 如果没有 taskId，则不需要建立连接
        if (!taskId) {
            return;
        }

        // 如果任务已经完成/失败，则不需要建立连接
        // 注意：如果想要查看历史完成任务的最后进度，可能需要调整逻辑。
        // 这里假设主要是为了监控 "进行中" 的任务。
        if (status === 'completed' || status === 'failed') {
            return;
        }

        // 重置重试计数器
        retryCountRef.current = 0;

        // 定义连接函数
        const connectSSE = () => {
            // 关闭旧连接
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }

            // 使用相对路径以支持反向代理（与 ApiClient.baseUrl 保持一致）
            // 在生产环境中，nginx 会将 /api/v1 代理到后端服务
            const url = `/api/v1/events?task_id=${taskId}`;

            console.log(`[SSE] Connecting to ${url}`);
            const eventSource = new EventSource(url);
            eventSourceRef.current = eventSource;

            eventSource.onopen = () => {
                console.log(`[SSE] Connection opened for task ${taskId}`);
                setIsConnected(true);
                // 重置重试计数器
                retryCountRef.current = 0;
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

                // 指数退避重连逻辑：如果仍在处理中，尝试重连
                const currentStatus = statusRef.current;
                if (currentStatus === 'processing' || currentStatus === 'pending') {
                    const retryCount = retryCountRef.current;
                    // 计算退避时间：1s, 2s, 4s, 8s, 最大 30s
                    const delay = Math.min(1000 * Math.pow(2, retryCount), 30000);
                    console.log(`[SSE] Reconnecting in ${delay}ms (attempt ${retryCount + 1})`);

                    // 清除之前的重连定时器
                    if (reconnectTimeoutRef.current) {
                        clearTimeout(reconnectTimeoutRef.current);
                    }

                    reconnectTimeoutRef.current = setTimeout(() => {
                        // 再次检查状态，避免在任务完成后重连
                        if (statusRef.current === 'processing' || statusRef.current === 'pending') {
                            retryCountRef.current = retryCount + 1;
                            reconnectTimeoutRef.current = null;
                            connectSSE();
                        }
                    }, delay);
                }
            };
        };

        connectSSE();

        // 清理函数
        return () => {
            // 清除重连定时器
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
                reconnectTimeoutRef.current = null;
            }

            // 关闭 SSE 连接
            if (eventSourceRef.current) {
                console.log(`[SSE] Cleaning up connection for task ${taskId}`);
                eventSourceRef.current.close();
                eventSourceRef.current = null;
                setIsConnected(false);
            }
        };
    }, [taskId]); // eslint-disable-line react-hooks/exhaustive-deps
    // 移除 status 依赖，防止状态更新导致频繁重连。只在 taskId 变化时重连。
    // status 的变化通过 onmessage 内部处理，并使用 statusRef 获取最新值

    return {
        progress,
        currentPage,
        totalPages,
        status,
        isConnected
    };
}
