import React, { useState } from 'react';
import { Upload, Card, Typography, App } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { ApiClient } from '../services/api';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';

const { Dragger } = Upload;

interface UploadZoneProps {
    onUploadSuccess?: () => void;
}

// --- Batch Scheduler Class Definition ---
class BatchUploadScheduler {
    private queue: {
        file: File;
        onSuccess?: (body: unknown) => void;
        onError?: (error: Error) => void
    }[] = [];
    private timer: NodeJS.Timeout | null = null;
    private readonly DELAY_MS = 100; // Wait 100ms to collect files

    constructor(
        private globalOnSuccess?: (msg: string) => void,
        private parentOnUploadSuccess?: () => void,
        private messageApi?: {
            success: (content: string) => void;
            error: (content: string) => void
        }
    ) { }

    add(file: File, onSuccess?: (body: unknown) => void, onError?: (error: Error) => void) {
        this.queue.push({ file, onSuccess, onError });
        this.scheduleFlush();
    }

    private scheduleFlush() {
        if (this.timer) clearTimeout(this.timer);
        this.timer = setTimeout(() => this.flush(), this.DELAY_MS);
    }

    private async flush() {
        const currentQueue = [...this.queue];
        this.queue = []; // Clear queue immediately
        this.timer = null;

        if (currentQueue.length === 0) return;

        if (currentQueue.length === 1) {
            // Single file mode - use legacy endpoint
            const item = currentQueue[0];
            try {
                await ApiClient.uploadFile(item.file);
                this.messageApi?.success(`${item.file.name} uploaded successfully`);
                item.onSuccess?.('ok');
                if (this.globalOnSuccess) this.globalOnSuccess('ok');
                if (this.parentOnUploadSuccess) this.parentOnUploadSuccess();
            } catch (error) {
                this.messageApi?.error(`Upload failed: ${error}`);
                item.onError?.(error as Error);
            }
        } else {
            // Batch mode - use new endpoint
            const files = currentQueue.map(item => item.file);
            try {
                const tasks = await ApiClient.uploadFiles(files);
                this.messageApi?.success(`${files.length} files uploaded successfully`);

                // Notify all items of success
                currentQueue.forEach(item => {
                    item.onSuccess?.('ok');
                });

                if (this.globalOnSuccess) this.globalOnSuccess('ok');
                if (this.parentOnUploadSuccess) this.parentOnUploadSuccess();
            } catch (error) {
                this.messageApi?.error(`Batch upload failed: ${error}`);
                // Notify all items of failure
                currentQueue.forEach(item => {
                    item.onError?.(error as Error);
                });
            }
        }
    }
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onUploadSuccess }) => {
    const { message } = App.useApp();
    const [fileList, setFileList] = useState<UploadFile[]>([]);


    // Batch Upload Scheduler Logic
    const [uploadQueue] = useState(() => new BatchUploadScheduler(
        undefined, // No internal onSuccess needed locally, we rely on Dragger's state management
        onUploadSuccess,
        message
    ));

    const customRequest: UploadProps['customRequest'] = async (options) => {
        const { onSuccess: reqSuccess, onError: reqError, file } = options;
        // Register file to scheduler
        uploadQueue.add(file as File, reqSuccess, reqError);
    };




    const props: UploadProps = {
        name: 'file',
        multiple: true,
        fileList,
        customRequest,
        onChange(info) {
            setFileList(info.fileList);
        },
        onDrop(e) {
            console.log('Dropped files', e.dataTransfer.files);
        },
    };

    return (
        <Card className="w-full shadow-lg rounded-xl overflow-hidden border-0">
            <Dragger
                {...props}
                className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 transition-colors py-8"
                style={{ background: '#f9fafb' }} // Explicit background
            >
                <p className="ant-upload-drag-icon text-5xl text-blue-500 mb-4 transition-transform hover:scale-110 duration-300">
                    <InboxOutlined />
                </p>
                <p className="ant-upload-text text-xl font-medium text-gray-700">
                    Click or drag file to this area to upload
                </p>
                <p className="ant-upload-hint text-gray-500 mt-2 text-base">
                    Support for multiple PDF files. Files will be processed in batch.
                </p>
            </Dragger>
        </Card>
    );
};

