import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Button,
  Space,
  Pagination,
  Spin,
  Alert,
  Typography,
  Splitter,
  App,
  List,
  Tag,
  Tooltip,
} from 'antd';
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  ReloadOutlined,
  FileTextOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { PDFViewer } from '../components/PDFViewer';
import { MarkdownPreview } from '../components/MarkdownPreview';
import { ApiClient } from '../services/api';
import { useTranslation } from 'react-i18next';

// 定义所有类型内联，避免 TypeScript 编译时的导入问题
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

interface PageInfo {
  page: number;
  status: string;
  content?: string;
  total_pages?: number;
  message?: string;
}

const { Text } = Typography;

/**
 * 双屏预览页面
 *
 * 左侧显示 PDF 页面图片，右侧显示 Markdown 转换结果
 * 支持分页浏览、下载、刷新、任务切换等功能
 */
export const Preview: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const { t } = useTranslation();

  // 状态管理
  const [task, setTask] = useState<Task | null>(null);
  const [allTasks, setAllTasks] = useState<Task[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageContent, setPageContent] = useState<PageInfo | null>(null);
  const [contentLoading, setContentLoading] = useState(false);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [retryCount, setRetryCount] = useState(0);  // 重试计数
  const [regenerating, setRegenerating] = useState(false);  // 重新生成状态
  const MAX_RETRIES = 10;  // 最大重试次数

  // 使用 ref 保存 task 状态，以便在 callback 中访问最新状态而不触发重渲染或依赖更新
  const taskRef = React.useRef<Task | null>(null);
  useEffect(() => {
    taskRef.current = task;
  }, [task]);

  // 加载任务信息
  const fetchTask = useCallback(async () => {
    if (!taskId) return;

    try {
      const result = await ApiClient.getTask(taskId);
      setTask(result);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : t('preview.fetchTaskFail');
      message.error(errorMessage);
      navigate('/');
    }
  }, [taskId, navigate, message, t]);

  // 加载页面内容
  const fetchPageContent = useCallback(
    async (page: number) => {
      if (!taskId) return;

      console.log(`[Preview] Fetching page ${page} content...`);
      setContentLoading(true);

      try {
        const result = await ApiClient.getPageContent(taskId, page);
        console.log(`[Preview] Page ${page} result:`, result);
        setPageContent(result);

        // ✅ 优先检查：如果已经读到 MD 内容，直接停止刷新
        if (result.content && result.content.trim().length > 0) {
          console.log(`[Preview] ✅ Content loaded successfully, stopping refresh`);
          setRetryCount(0);  // 重置重试计数
          return;  // 直接返回，不再触发自动刷新
        }

        // 自动刷新逻辑（带最大重试次数限制）：
        // 1. 任务正在处理中 (status: processing/pending) → 5秒后刷新
        // 2. 任务已完成但内容为空 → 说明正在生成最终文件，3秒后刷新
        const needsRefresh =
          (result.status === 'processing' || result.status === 'pending') &&
          retryCount < MAX_RETRIES;  // 限制最大重试次数

        const needsRetryForCompleted =
          result.status === 'completed' &&
          !result.content &&
          retryCount < MAX_RETRIES;

        if (needsRefresh || needsRetryForCompleted) {
          const delay = result.status === 'completed' ? 3000 : 5000;
          console.log(`[Preview] Scheduling auto-refresh in ${delay}ms (Retry ${retryCount + 1}/${MAX_RETRIES})...`);

          setTimeout(() => {
            // 只有当前页面没变时才刷新
            if (currentPage === page) {
              console.log(`[Preview] Auto-refreshing page ${page}...`);
              setRetryCount(prev => prev + 1);  // 增加重试计数
              fetchPageContent(page);
              fetchTask(); // 同时刷新任务状态
            }
          }, delay);
        } else if (!result.content) {
          // 没有内容且不需要重试（达到最大重试次数）
          console.log(`[Preview] Max retries reached or content not available`);
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : t('preview.fetchContentFail');
        console.error('[Preview] Fetch page content error:', errorMessage);

        // 如果是 404 错误且任务状态是 processing/pending/completed，自动重试（带次数限制）
        const currentTask = taskRef.current;
        const taskStatus = currentTask?.status;

        if (errorMessage.includes('404') &&
          (taskStatus === 'processing' || taskStatus === 'pending' || taskStatus === 'completed') &&
          retryCount < MAX_RETRIES) {
          console.log(`[Preview] Page ${page} not ready (404), auto-retrying in 5 seconds... (Retry ${retryCount + 1}/${MAX_RETRIES})`);

          setTimeout(() => {
            if (currentPage === page) {
              setRetryCount(prev => prev + 1);
              fetchPageContent(page);
              fetchTask();
            }
          }, 5000);
        } else {
          message.error(errorMessage);
          setPageContent(null);
          setRetryCount(0);  // 重置计数
        }
      } finally {
        setContentLoading(false);
      }
    },
    [taskId, fetchTask, message, currentPage, retryCount, t]
  );

  // 加载所有任务列表
  const fetchAllTasks = useCallback(async () => {
    setTasksLoading(true);
    try {
      const data = await ApiClient.getTasks();
      setAllTasks(data.items);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setTasksLoading(false);
    }
  }, []);

  // 初始化加载
  useEffect(() => {
    fetchTask();
    fetchAllTasks();
  }, [fetchTask, fetchAllTasks]);

  // 页码变化时加载内容
  useEffect(() => {
    if (taskId) {
      // console.log(`[Preview] Page changed to ${currentPage}, loading content...`);
      fetchPageContent(currentPage);
    }
  }, [currentPage, taskId, fetchPageContent]);

  // 下载 Markdown
  const handleDownload = async () => {
    if (!taskId) return;

    try {
      const blob = await ApiClient.downloadFile(taskId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `task_${taskId}.md`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success(t('preview.downloadSuccess'));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : t('preview.downloadFail');
      message.error(errorMessage);
    }
  };

  // 刷新页面
  const handleRefresh = () => {
    fetchPageContent(currentPage);
    fetchTask();
  };

  // 重新生成当前页
  const handleRegeneratePage = async () => {
    if (!taskId) return;

    setRegenerating(true);
    const hideLoading = message.loading(t('preview.regenerating', { page: currentPage }), 0);

    try {
      await ApiClient.regeneratePage(taskId, currentPage);

      // 首次快速刷新（2秒后检查单页文件）
      setTimeout(() => {
        fetchPageContent(currentPage);
      }, 2000);

      // 再次刷新（5秒后检查合并文件）
      setTimeout(() => {
        fetchPageContent(currentPage);
        hideLoading();
        message.success(t('preview.regenerateSuccess', { page: currentPage }));
      }, 5000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : t('preview.regenerateFail');
      hideLoading();
      message.error(errorMessage);
    } finally {
      // 延迟重置 loading 状态，给后台足够时间处理
      setTimeout(() => {
        setRegenerating(false);
      }, 6000);
    }
  };

  // 分页处理
  const handlePageChange = (page: number) => {
    console.log(`[Preview] Manual page change to ${page}`);
    setCurrentPage(page);
    setRetryCount(0);  // 重置重试计数
  };

  // 切换任务
  const handleTaskChange = (newTaskId: string) => {
    if (newTaskId === taskId) return;
    console.log(`[Preview] Switching to task ${newTaskId}`);
    setCurrentPage(1); // 重置到第一页
    setPageContent(null);
    setRetryCount(0);  // 重置重试计数
    navigate(`/preview/${newTaskId}`);
  };

  // 初始加载状态
  if (!task) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        <Spin size="large" />
        <Text type="secondary">{t('preview.loadingTask')}</Text>
      </div>
    );
  }

  const totalPages = task.total_pages || 0;

  return (
    <div
      style={{
        height: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        padding: '12px',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0 8px',
        }}
      >
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
            type="default"
          >
            {t('preview.back')}
          </Button>
          <Text strong style={{ fontSize: '16px' }}>
            {task.file_name || `Task ${taskId}`}
          </Text>
          <Tag color={task.status === 'completed' ? 'success' : task.status === 'processing' ? 'processing' : 'default'}>
            {task.status ? t(`task.status.${task.status}`) : task.status}
          </Tag>
          <Text type="secondary">
            ({totalPages} {t('preview.pages')})
          </Text>
        </Space>

        <Space>
          {task.status === 'completed' && (
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleDownload}
            >
              {t('preview.download')}
            </Button>
          )}
          <Tooltip title={t('preview.regenerateTooltip')}>
            <Button
              icon={<SyncOutlined spin={regenerating} />}
              onClick={handleRegeneratePage}
              loading={regenerating}
              disabled={!pageContent?.content}
            >
              {t('preview.regenerate')}
            </Button>
          </Tooltip>
          <Tooltip title={t('preview.refreshTooltip')}>
            <Button
              icon={<ReloadOutlined spin={contentLoading} />}
              onClick={handleRefresh}
            >
              {t('preview.refresh')}
            </Button>
          </Tooltip>
        </Space>
      </div>

      {/* Main Content with Task Sidebar */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          gap: '12px',
          overflow: 'hidden',
        }}
      >
        {/* Left Sidebar - Task List */}
        <div
          style={{
            width: '280px',
            border: '1px solid #d9d9d9',
            borderRadius: '6px',
            backgroundColor: '#fff',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '12px',
              borderBottom: '1px solid #f0f0f0',
              fontWeight: 'bold',
            }}
          >
            {t('preview.tasks')} ({allTasks.length})
          </div>
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
            }}
          >
            <List
              loading={tasksLoading}
              dataSource={allTasks}
              renderItem={(item) => (
                <List.Item
                  key={item.id}
                  style={{
                    cursor: 'pointer',
                    padding: '12px',
                    borderBottom: '1px solid #f0f0f0',
                    backgroundColor: item.id === taskId ? '#e6f7ff' : 'transparent',
                    transition: 'background-color 0.2s',
                  }}
                  onClick={() => handleTaskChange(item.id!)}
                  onMouseEnter={(e) => {
                    if (item.id !== taskId) {
                      e.currentTarget.style.backgroundColor = '#f5f5f5';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (item.id !== taskId) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  <List.Item.Meta
                    avatar={<FileTextOutlined style={{ fontSize: '20px', color: '#1890ff' }} />}
                    title={
                      <Tooltip title={item.file_name}>
                        <div
                          style={{
                            fontWeight: item.id === taskId ? 'bold' : 'normal',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            maxWidth: '150px',
                          }}
                        >
                          {item.file_name || 'Unknown'}
                        </div>
                      </Tooltip>
                    }
                    description={
                      <Space size={4}>
                        <Tag
                          color={
                            item.status === 'completed'
                              ? 'success'
                              : item.status === 'processing'
                                ? 'processing'
                                : item.status === 'failed'
                                  ? 'error'
                                  : 'default'
                          }
                          style={{ margin: 0, fontSize: '11px' }}
                        >
                          {item.status ? t(`task.status.${item.status}`) : item.status}
                        </Tag>
                        {item.total_pages && (
                          <span style={{ fontSize: '11px', color: '#999' }}>
                            {item.total_pages}{t('preview.page')}
                          </span>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </div>
        </div>

        {/* Right - Preview Area */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            overflow: 'hidden',
          }}
        >
          {/* Split View */}
          <div
            style={{
              flex: 1,
              border: '1px solid #d9d9d9',
              borderRadius: '6px',
              overflow: 'hidden',
            }}
          >
            <Splitter
              style={{
                height: '100%',
                width: '100%',
                backgroundColor: '#fff',
              }}
            >
              {/* Left Panel - PDF Image */}
              <Splitter.Panel
                defaultSize="35%"
                min="30%"
                max="70%"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  padding: '12px',
                  backgroundColor: '#f5f5f5',
                }}
              >
                <div
                  style={{
                    flex: 1,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    overflow: 'hidden',
                    borderRadius: '4px',
                    backgroundColor: '#fff',
                  }}
                >
                  <PDFViewer taskId={taskId!} pageNum={currentPage} />
                </div>
              </Splitter.Panel>

              {/* Right Panel - Markdown Content */}
              <Splitter.Panel
                style={{
                  overflow: 'hidden',
                  backgroundColor: '#fffbe6',
                }}
              >
                {contentLoading ? (
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      height: '100%',
                      flexDirection: 'column',
                      gap: '16px',
                    }}
                  >
                    <Spin size="large" />
                    <Text type="secondary">{t('preview.loadingContent')}</Text>
                  </div>
                ) : pageContent?.content ? (
                  <MarkdownPreview content={pageContent.content} />
                ) : (
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      height: '100%',
                      padding: '24px',
                    }}
                  >
                    <Alert
                      message={
                        pageContent?.message ||
                        t('preview.contentNotAvailable')
                      }
                      type="info"
                      showIcon
                    />
                  </div>
                )}
              </Splitter.Panel>
            </Splitter>
          </div>

          {/* Pagination */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              padding: '8px',
              backgroundColor: '#fff',
              borderRadius: '6px',
              border: '1px solid #d9d9d9',
            }}
          >
            <Pagination
              current={currentPage}
              total={totalPages}
              pageSize={1}
              onChange={handlePageChange}
              showSizeChanger={false}
              disabled={totalPages === 0}
              showTitle
              showTotal={(total, range) => t('preview.pagination', { start: range[0], end: range[1], total })}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
