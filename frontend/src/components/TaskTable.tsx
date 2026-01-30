import React, { useEffect, useState } from 'react';
import { Table, Tag, Button, Card, Space, Tooltip } from 'antd';
import { DownloadOutlined, EyeOutlined, ReloadOutlined, DeleteOutlined, FilePdfOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../services/api';
import { TaskProgress } from './TaskProgress';
import { message, Modal } from 'antd';

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

    const handleDelete = (taskId: string) => {
        Modal.confirm({
            title: 'Confirm Delete',
            content: 'Are you sure you want to delete this task? This action cannot be undone.',
            okText: 'Delete',
            okType: 'danger',
            cancelText: 'Cancel',
            onOk: async () => {
                try {
                    await ApiClient.deleteTask(taskId);
                    message.success('Task deleted successfully');
                    fetchTasks(false); // Refresh list
                } catch (error) {
                    message.error('Failed to delete task');
                    console.error(error);
                }
            },
        });
    };

    const columns: ColumnsType<Task> = [
        {
            title: 'File Name',
            dataIndex: 'file_name',
            key: 'file_name',
            width: '30%',
            render: (text) => (
                <Space>
                    <FilePdfOutlined className="text-red-500 text-lg" />
                    <span className="font-medium text-gray-700" title={text}>{text || 'Unknown'}</span>
                </Space>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: '25%',
            render: (status, record) => {
                if (status === 'processing') {
                    return (
                        <TaskProgress
                            taskId={record.id}
                            initialStatus={status}
                            onComplete={() => fetchTasks(false)}
                        />
                    );
                }

                let color = 'default';
                let icon = <ClockCircleOutlined />;
                if (status === 'completed') {
                    color = 'success';
                    icon = <CheckCircleOutlined />;
                } else if (status === 'failed') {
                    color = 'error';
                    icon = <CloseCircleOutlined />;
                } else if (status === 'pending') {
                    color = 'warning';
                    icon = <SyncOutlined spin />;
                }

                return (
                    <Tag color={color} icon={icon} className="px-3 py-1 text-sm rounded-full">
                        {status?.toUpperCase()}
                    </Tag>
                );
            },
        },
        {
            title: 'Created At',
            dataIndex: 'created_at',
            key: 'created_at',
            width: '20%',
            render: (text) => <span className="text-gray-500">{text ? new Date(text).toLocaleString() : '-'}</span>,
        },
        {
            title: 'Action',
            key: 'action',
            align: 'right',
            width: '25%',
            render: (_, record) => (
                <Space size="small">
                    {(record.status === 'completed' || record.status === 'processing') && (
                        <Tooltip title="Preview">
                            <Button
                                type="text"
                                icon={<EyeOutlined className="text-blue-600" />}
                                onClick={() => navigate(`/preview/${record.id}`)}
                            />
                        </Tooltip>
                    )}

                    {record.status === 'completed' && (
                        <Tooltip title="Download Markdown">
                            <Button
                                type="text"
                                icon={<DownloadOutlined className="text-green-600" />}
                                onClick={async () => {
                                    try {
                                        const blob = await ApiClient.downloadFile(record.id || record.task_id || '');
                                        const url = window.URL.createObjectURL(blob);
                                        const link = document.createElement('a');
                                        link.href = url;
                                        const fileName = record.file_name
                                            ? record.file_name.replace(/\.pdf$/i, '.md')
                                            : `${record.id}.md`;
                                        link.download = fileName;
                                        document.body.appendChild(link);
                                        link.click();
                                        document.body.removeChild(link);
                                        window.URL.revokeObjectURL(url);
                                    } catch (error) {
                                        message.error('Download failed');
                                    }
                                }}
                            />
                        </Tooltip>
                    )}

                    <Tooltip title="Delete Task">
                        <Button
                            type="text"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={() => handleDelete(record.id)}
                        />
                    </Tooltip>
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
            className="w-full shadow-lg rounded-xl overflow-hidden border-0"
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
