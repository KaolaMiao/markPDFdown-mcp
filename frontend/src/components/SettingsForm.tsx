import React, { useEffect } from 'react';
import { Form, Input, Select, InputNumber, Button, Card, App } from 'antd';
import { ApiClient } from '../services/api';

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

    useEffect(() => {
        const loadSettings = async () => {
            try {
                const settings = await ApiClient.getSettings();
                form.setFieldsValue(settings);
            } catch (error) {
                console.error(error);
                message.error('Failed to load settings');
            } finally {
                setInitialLoading(false);
            }
        };
        loadSettings();
    }, [form, message]);

    const onFinish = async (values: Settings) => {
        setLoading(true);
        try {
            await ApiClient.updateSettings(values);
            message.success('Settings saved');
        } catch (error) {
            message.error('Failed to save settings');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card title="LLM Configuration" className="max-w-2xl mx-auto mt-8 shadow-md" loading={initialLoading}>
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
                    label="Provider"
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
                    label="API Key"
                    rules={[{ required: true, message: 'API Key is required' }]}
                >
                    <Input.Password placeholder="sk-..." />
                </Form.Item>

                <Form.Item
                    name="baseUrl"
                    label="Base URL (Optional)"
                >
                    <Input placeholder="https://api.openai.com/v1" />
                </Form.Item>

                <Form.Item
                    name="model"
                    label="Model"
                    rules={[{ required: true }]}
                >
                    <Input placeholder="gpt-4o" />
                </Form.Item>

                <Form.Item
                    name="concurrency"
                    label="Concurrency Limit"
                    rules={[{ required: true }]}
                    tooltip="同时处理的页面数量。建议值：2-10（取决于 API 限流），最高可设 50"
                >
                    <InputNumber min={1} max={50} className="w-full" />
                </Form.Item>

                <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading} block>
                        Save Configuration
                    </Button>
                </Form.Item>
            </Form>
        </Card>
    );
};
