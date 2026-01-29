import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypePrism from 'rehype-prism-plus';
import 'prismjs/themes/prism.css';
import '../styles/markdown.css';

interface MarkdownPreviewProps {
  content: string;
}

/**
 * Markdown 预览组件
 *
 * 使用 react-markdown 渲染 Markdown 内容，支持:
 * - GitHub Flavored Markdown (GFM)
 * - 代码高亮 (Prism.js)
 * - 表格、删除线等扩展语法
 */
export const MarkdownPreview: React.FC<MarkdownPreviewProps> = ({ content }) => {
  return (
    <div
      style={{
        padding: '24px',
        height: '100%',
        width: '100%',
        minWidth: 0,
        overflow: 'auto',
        backgroundColor: '#fffbe6',
        boxSizing: 'border-box',
      }}
      className="markdown-preview"
    >
      {content ? (
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[[rehypePrism, { ignoreMissing: true }]]}
        >
          {content}
        </ReactMarkdown>
      ) : (
        <div style={{ textAlign: 'center', color: '#999', marginTop: '100px' }}>
          <p>内容加载中...</p>
        </div>
      )}
    </div>
  );
};
