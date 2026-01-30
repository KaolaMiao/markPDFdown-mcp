import React, { useState } from 'react';
import { Layout, Button, Typography, Space, Drawer } from 'antd';
import { SettingOutlined, GithubOutlined } from '@ant-design/icons';
import { SettingsForm } from '../components/SettingsForm';
import { UploadZone } from '../components/UploadZone';
import { TaskTable } from '../components/TaskTable';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { useTranslation } from 'react-i18next';

const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;

export const Dashboard: React.FC = () => {
    const [settingsVisible, setSettingsVisible] = useState(false);
    const { t } = useTranslation();

    return (
        <Layout className="min-h-screen bg-gray-100">
            <Header className="bg-white border-b border-gray-200 px-8 flex justify-between items-center sticky top-0 z-10">
                <div className="flex items-center gap-3">
                    {/* Use emoji or icon if Logo not available, but user has P1.png in root, maybe copy it later. */}
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">M</div>
                    <Title level={4} style={{ margin: 0 }}>{t('app.title')}</Title>
                </div>
                <Space>
                    <LanguageSwitcher />
                    <Button
                        icon={<SettingOutlined />}
                        onClick={() => setSettingsVisible(true)}
                    >
                        {t('app.settings')}
                    </Button>
                    <Button
                        type="text"
                        icon={<GithubOutlined />}
                        href="https://github.com/MarkPDFdown"
                        target="_blank"
                    />
                </Space>
            </Header>

            <Content className="p-8 w-full flex justify-center">
                <div className="w-full max-w-6xl space-y-8">
                    <section className="text-center mb-8">
                        <Title level={2} style={{ marginBottom: '0.5rem' }}>{t('app.description')}</Title>
                        <Text type="secondary" className="text-lg">
                            {t('app.instruction')}
                        </Text>
                    </section>


                    {/* Upload Zone - Full width in container */}
                    <div className="w-full">
                        <UploadZone onUploadSuccess={() => { /* TaskTable polls automatically */ }} />
                    </div>

                    <TaskTable />
                </div>

            </Content>


            <Footer className="text-center text-gray-400">
                {t('app.footer', { year: new Date().getFullYear() })}
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
