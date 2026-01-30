import React, { useEffect } from 'react';
import { Form, Input, Select, InputNumber, Button, Card, App } from 'antd';
import { ApiClient } from '../services/api';
import { useTranslation } from 'react-i18next';

// 定义类型内联，避免导入问题
interface Settings {
    provider: string;
    apiKey: string;
    baseUrl?: string;
    model: string;
    concurrency: number;
}

export const SettingsForm: React.FC = () => {
    const { message } = App.useApp();
    const [form] = Form.useForm();
    const [loading, setLoading] = React.useState(false);
    const [initialLoading, setInitialLoading] = React.useState(true);
    const { t } = useTranslation();

    useEffect(() => {
        const loadSettings = async () => {
            try {
                const settings = await ApiClient.getSettings();
                form.setFieldsValue(settings);
            } catch (error) {
                console.error(error);
                message.error(t('settings.loadFail'));
            } finally {
                setInitialLoading(false);
            }
        };
        loadSettings();
    }, [form, message, t]);

    const onFinish = async (values: Settings) => {
        setLoading(true);
        try {
            await ApiClient.updateSettings(values);
            message.success(t('settings.saveSuccess'));
        } catch (error) {
            message.error(t('settings.saveFail'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card title={t('settings.title')} className="max-w-2xl mx-auto mt-8 shadow-md" loading={initialLoading}>
            <Form
                form={form}
                layout="vertical"
                onFinish={onFinish}
                initialValues={{
                    concurrency: 5,
                }}
            >
                <Form.Item
                    name="provider"
                    label={t('settings.provider')}
                    rules={[{ required: true }]}
                >
                    <Select>
                        <Select.Option value="openai">OpenAI</Select.Option>
                        <Select.Option value="anthropic">Anthropic</Select.Option>
                        <Select.Option value="gemini">Gemini</Select.Option>
                        <Select.Option value="ollama">Ollama</Select.Option>
                    </Select>
                </Form.Item>

                <Form.Item
                    name="apiKey"
                    label={t('settings.apiKey')}
                    rules={[{ required: true, message: t('settings.apiKeyRequired') }]}
                >
                    <Input.Password placeholder="sk-..." />
                </Form.Item>

                <Form.Item
                    name="baseUrl"
                    label={t('settings.baseUrl')}
                >
                    <Input placeholder="https://api.openai.com/v1" />
                </Form.Item>

                <Form.Item
                    name="model"
                    label={t('settings.model')}
                    rules={[{ required: true }]}
                >
                    <Input placeholder="gpt-4o" />
                </Form.Item>

                <Form.Item
                    name="concurrency"
                    label={t('settings.concurrency')}
                    rules={[{ required: true }]}
                    tooltip={t('settings.concurrencyTooltip')}
                >
                    <InputNumber min={1} max={50} className="w-full" />
                </Form.Item>

                <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading} block>
                        {t('settings.save')}
                    </Button>
                </Form.Item>
            </Form>
        </Card>
    );
};

