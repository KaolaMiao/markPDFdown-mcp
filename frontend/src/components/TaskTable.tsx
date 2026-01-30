import React, { useEffect, useState } from 'react';
import { Table, Tag, Button, Card, Space, Tooltip } from 'antd';
import { DownloadOutlined, EyeOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../services/api';
import { TaskProgress } from './TaskProgress';

// 定义类型内联，避免导入问题
interface Task {
    id: string;
    task_id?: string;
    file_name?: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    created_at?: string;
    result?: string;
    error?: string;
    total_pages?: number;
}

import type { ColumnsType } from 'antd/es/table';

interface TaskTableProps {
    pollingInterval?: number;
}

export const TaskTable: React.FC<TaskTableProps> = ({ pollingInterval = 2000 }) => {
    const navigate = useNavigate();
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);

    const fetchTasks = async (showLoading = false) => {
        if (showLoading) setLoading(true);
        try {
            const data = await ApiClient.getTasks();
            setTasks(data.items);
            setTotal(data.total);
        } catch (error) {
            console.error(error);
        } finally {
            if (showLoading) setLoading(false);
        }
    };

    // Poll logic using adaptive setTimeout
    useEffect(() => {
        let isMounted = true;
        let timeoutId: ReturnType<typeof setTimeout> | undefined;

        const poll = async () => {
            if (!isMounted) return;

            // 1. Fetch tasks
            let hasActiveTasks = false;
            try {
                const data = await ApiClient.getTasks();
                setTasks(data.items);
                setTotal(data.total);

                // Check if any task is still in progress
                hasActiveTasks = data.items.some(t => t.status === 'processing' || t.status === 'pending');
            } catch (error) {
                console.error("Polling error:", error);
            }

            // 2. Schedule next poll based on task status
            // Active: use prop pollingInterval (default 2s), Idle: 15s
            const delay = hasActiveTasks ? pollingInterval : 15000;

            if (isMounted) {
                timeoutId = setTimeout(poll, delay);
            }
        };

        // Initial fetch and start polling
        fetchTasks(true).then(() => {
            timeoutId = setTimeout(poll, pollingInterval);
        });

        return () => {
            isMounted = false;
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, [pollingInterval]);

    // ... (existing imports)

    const columns: ColumnsType<Task> = [
        {
            title: 'ID',
            dataIndex: 'id',
            key: 'id',
            width: 80, // Slightly reduce width
            render: (text) => <span className="text-gray-500 font-mono text-xs">{text ? text.slice(0, 8) + '...' : '-'}</span>,
        },
        // ... (File Name column)
        {
            title: 'File Name',
            dataIndex: 'file_name',
            key: 'file_name',
            width: 200, // Add width constraint
            ellipsis: true, // Enable ellipsis
            render: (text) => <span className="font-medium" title={text}>{text || 'Unknown'}</span>,
        },
        // ... (Created At column)
        {
            title: 'Created At',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 150,
            render: (text) => text ? new Date(text).toLocaleString() : '-',
        },
        {
            title: 'Status / Progress', // Rename column
            dataIndex: 'status',
            key: 'status',
            width: 250, // Increase width for progress bar
            render: (status, record) => {
                if (status === 'processing') {
                    // Use TaskProgress for real-time updates
                    return (
                        <TaskProgress
                            taskId={record.id}
                            initialStatus={status}
                            onComplete={() => fetchTasks(false)} // Refresh list on complete
                        />
                    );
                }

                let color = 'default';
                let icon = null;
                if (status === 'completed') {
                    color = 'success';
                } else if (status === 'failed') {
                    color = 'error';
                } else if (status === 'pending') {
                    color = 'warning';
                }

                return <Tag color={color} icon={icon}>{status?.toUpperCase()}</Tag>;
            },
        },
        {
            title: 'Action',
            key: 'action',
            render: (_, record) => (
                <Space size="middle">
                    {/* 查看按钮 - 已完成或正在处理的任务都可以查看 */}
                    {(record.status === 'completed' || record.status === 'processing') && (
                        <Button
                            type="link"
                            icon={<EyeOutlined />}
                            onClick={() => navigate(`/preview/${record.id}`)}
                        >
                            查看
                        </Button>
                    )}
                    {/* 下载按钮 - 只有已完成的任务可以下载 */}
                    {record.status === 'completed' && (
                        <Button
                            type="link"
                            icon={<DownloadOutlined />}
                            onClick={async () => {
                                try {
                                    // 1. Fetch Blob
                                    const blob = await ApiClient.downloadFile(record.id || record.task_id || '');

                                    // 2. Create Object URL
                                    const url = window.URL.createObjectURL(blob);

                                    // 3. Trigger Download with Correct Filename
                                    const link = document.createElement('a');
                                    link.href = url;

                                    // 优先使用 file_name (.pdf -> .md)，否则使用 id.md
                                    const fileName = record.file_name
                                        ? record.file_name.replace(/\.pdf$/i, '.md')
                                        : `${record.id}.md`;

                                    link.download = fileName;
                                    document.body.appendChild(link);
                                    link.click();

                                    // 4. Cleanup
                                    document.body.removeChild(link);
                                    window.URL.revokeObjectURL(url);
                                } catch (error) {
                                    console.error('Download failed:', error);
                                    // Fallback or alert user
                                    alert('下载失败，请稍后重试');
                                }
                            }}
                        >
                            下载
                        </Button>
                    )}
                </Space>
            ),
        },
    ];

    return (
        <Card
            title={
                <Space>
                    <span>Processing Tasks</span>
                    <Tag color="blue">{total}</Tag>
                </Space>
            }
            extra={
                <Tooltip title="Refresh manually">
                    <Button icon={<ReloadOutlined />} onClick={() => fetchTasks(true)} />
                </Tooltip>
            }
            className="w-full mt-8 shadow-md"
        >
            <Table
                dataSource={tasks}
                columns={columns}
                rowKey="id"
                loading={loading && tasks.length === 0}
                pagination={{ pageSize: 5 }}
            />
        </Card>
    );
};
