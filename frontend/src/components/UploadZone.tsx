import React, { useState } from 'react';
import { Upload, message, Card, Typography } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { ApiClient } from '../services/api';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';

const { Dragger } = Upload;

interface UploadZoneProps {
    onUploadSuccess?: () => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onUploadSuccess }) => {
    const [fileList, setFileList] = useState<UploadFile[]>([]);

    const customRequest: UploadProps['customRequest'] = async (options) => {
        const { onSuccess, onError, file } = options;

        try {
            await ApiClient.uploadFile(file as File);
            message.success(`${(file as File).name} uploaded successfully`);
            if (onSuccess) onSuccess('ok');
            if (onUploadSuccess) onUploadSuccess();
            setFileList([]); // Clear file list on success
        } catch (error) {
            message.error(`Upload failed: ${error}`);
            if (onError) onError(error as Error);
        }
    };

    const props: UploadProps = {
        name: 'file',
        multiple: false,
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
        <Card className="max-w-2xl mx-auto mt-8 shadow-md">
            <Dragger {...props} className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 transition-colors">
                <p className="ant-upload-drag-icon text-4xl text-blue-500 mb-4">
                    <InboxOutlined />
                </p>
                <p className="ant-upload-text text-lg font-medium text-gray-700">
                    Click or drag file to this area to upload
                </p>
                <p className="ant-upload-hint text-gray-500 mt-2">
                    Support for PDF files. The file will be processed on the server.
                </p>
            </Dragger>
        </Card>
    );
};
