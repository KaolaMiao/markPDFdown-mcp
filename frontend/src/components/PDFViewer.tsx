import React, { useState } from 'react';
import { Spin, Alert, Image } from 'antd';
import { ApiClient } from '../services/api';

interface PDFViewerProps {
  taskId: string;
  pageNum: number;
  onLoad?: () => void;
  onError?: (error: string) => void;
}

/**
 * PDF 页面图片查看器组件
 *
 * 显示指定页面的渲染图片，支持加载状态和错误处理
 */
export const PDFViewer: React.FC<PDFViewerProps> = ({
  taskId,
  pageNum,
  onLoad,
  onError,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const imageUrl = ApiClient.getPageImageUrl(taskId, pageNum);

  const handleLoad = () => {
    setLoading(false);
    setError(null);
    onLoad?.();
  };

  const handleError = () => {
    setLoading(false);
    const errorMsg = `Failed to load page ${pageNum}`;
    setError(errorMsg);
    onError?.(errorMsg);
  };

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100%',
        width: '100%',
        overflow: 'hidden',
      }}
    >
      {loading && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
          }}
        >
          <Spin size="large" tip={`Loading page ${pageNum}...`} />
        </div>
      )}

      {error && (
        <Alert
          message={error}
          description="Please check if the page conversion is completed"
          type="error"
          showIcon
          style={{ maxWidth: '400px' }}
        />
      )}

      {!error && (
        <Image
          src={imageUrl}
          alt={`Page ${pageNum}`}
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            objectFit: 'contain',
            opacity: loading ? 0 : 1,
            transition: 'opacity 0.3s',
          }}
          onLoad={handleLoad}
          onError={handleError}
          preview={false}
        />
      )}
    </div>
  );
};
