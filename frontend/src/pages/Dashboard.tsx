import React, { useState } from 'react';
import { Layout, Button, Drawer, Typography, Space } from 'antd';
import { SettingOutlined, GithubOutlined } from '@ant-design/icons';
import { SettingsForm } from '../components/SettingsForm';
import { UploadZone } from '../components/UploadZone';
import { TaskTable } from '../components/TaskTable';

const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;

export const Dashboard: React.FC = () => {
    const [settingsVisible, setSettingsVisible] = useState(false);

    return (
        <Layout className="min-h-screen bg-gray-100">
            <Header className="bg-white border-b border-gray-200 px-8 flex justify-between items-center sticky top-0 z-10">
                <div className="flex items-center gap-3">
                    {/* Use emoji or icon if Logo not available, but user has P1.png in root, maybe copy it later. */}
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">M</div>
                    <Title level={4} style={{ margin: 0 }}>MarkPDFdown Server</Title>
                </div>
                <Space>
                    <Button
                        icon={<SettingOutlined />}
                        onClick={() => setSettingsVisible(true)}
                    >
                        Settings
                    </Button>
                    <Button
                        type="text"
                        icon={<GithubOutlined />}
                        href="https://github.com/MarkPDFdown"
                        target="_blank"
                    />
                </Space>
            </Header>

            <Content className="p-8 w-full">
                <div className="space-y-8">
                    <section className="text-center mb-12">
                        <Title level={2}>MarkPDFdown 智能转换系统</Title>
                        <Text type="secondary" className="text-lg">
                            使用说明：请上传 PDF 文件，系统将自动调用多模态大模型（支持 GPT-4o, Claude 3.5, Gemini 1.5）进行高精度 Markdown 转换。
                        </Text>
                    </section>

                    <UploadZone onUploadSuccess={() => { /* TaskTable polls automatically */ }} />

                    <TaskTable />
                </div>
            </Content>

            <Footer className="text-center text-gray-400">
                MarkPDFdown Server ©{new Date().getFullYear()} Created by deep-diver
            </Footer>

            <Drawer
                title="Configuration"
                placement="right"
                onClose={() => setSettingsVisible(false)}
                open={settingsVisible}
                size="large"
            >
                <SettingsForm />
            </Drawer>
        </Layout>
    );
};
