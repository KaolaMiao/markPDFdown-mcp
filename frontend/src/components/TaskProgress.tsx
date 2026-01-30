import React from 'react';
import { Progress, Tag, Typography } from 'antd';
import { SyncOutlined } from '@ant-design/icons';
import { useTaskProgress } from '../services/useTaskProgress';

interface TaskProgressProps {
    taskId: string;
    initialStatus?: string;
    onComplete?: () => void;
}

export const TaskProgress: React.FC<TaskProgressProps> = ({ taskId, initialStatus = 'processing', onComplete }) => {
    const { progress, currentPage, totalPages, status, isConnected } = useTaskProgress(taskId, initialStatus);

    // 如果任务已经完成，或者不是处理中状态，可以在这里处理
    // 但通常这个组件只在 processing 状态下渲染

    // 监听完成状态
    React.useEffect(() => {
        if (status === 'completed' && onComplete) {
            onComplete();
        }
    }, [status, onComplete]);

    // 计算百分比，确保是数字
    const percent = Math.round(progress || 0);

    return (
        <div className="w-full" style={{ minWidth: 150 }}>
            {/* 状态标签 */}
            <div className="flex items-center justify-between mb-1">
                <Tag color="processing" icon={<SyncOutlined spin />}>
                    {status === 'processing' ? '转换中' : status}
                </Tag>
                {isConnected && (
                    <span className="text-xs text-green-500">● 实时连接</span>
                )}
            </div>

            {/* 进度条 */}
            <Progress
                percent={percent}
                size="small"
                status="active"
                strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                }}
            />

            {/* 页码信息 */}
            {totalPages > 0 && (
                <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                    正在处理第 {currentPage} 页 / 共 {totalPages} 页
                </Typography.Text>
            )}
        </div>
    );
};
