import React, { useState } from 'react';
import { Upload, Card, Typography, App } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import { BatchUploadScheduler } from '../utils/BatchUploadScheduler';

const { Dragger } = Upload;

interface UploadZoneProps {
    onUploadSuccess?: () => void;
}

import { useTranslation } from 'react-i18next';

export const UploadZone: React.FC<UploadZoneProps> = ({ onUploadSuccess }) => {
    const { message } = App.useApp();
    const [fileList, setFileList] = useState<UploadFile[]>([]);
    const { t } = useTranslation();


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
                    {t('upload.dragText')}
                </p>
                <p className="ant-upload-hint text-gray-500 mt-2 text-base">
                    {t('upload.hint')}
                </p>
            </Dragger>
        </Card>
    );
};


