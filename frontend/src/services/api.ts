export interface Task {
    id: string; // 后端返回的主键字段
    task_id?: string; // 兼容旧字段
    file_name?: string; // 原始文件名
    status: 'pending' | 'processing' | 'completed' | 'failed';
    created_at?: string;
    result?: string;
    error?: string;
}

export interface Settings {
    provider: string; // 'openai', 'anthropic', etc.
    apiKey: string;
    baseUrl?: string;
    model: string;
    concurrency: number;
}

export class ApiClient {
    static baseUrl = '/api/v1';

    private static async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const response = await fetch(`${this.baseUrl}${endpoint}`, options);
        if (!response.ok) {
            // Try to parse error message
            let errorText = response.statusText;
            try {
                const errJson = await response.json();
                errorText = errJson.detail || errJson.message || errorText;
            } catch (e) {
                // ignore json parse error
            }
            throw new Error(`API Error ${response.status}: ${errorText}`);
        }
        // Return empty if no content
        if (response.status === 204) return {} as T;
        return response.json();
    }

    static async uploadFile(file: File): Promise<{ task_id: string; status: string }> {
        const formData = new FormData();
        formData.append('file', file);

        return this.request('/upload', {
            method: 'POST',
            body: formData,
        });
    }

    static async getTasks(): Promise<{ items: Task[]; total: number }> {
        return this.request('/tasks', {
            method: 'GET',
        });
    }

    static async getTask(taskId: string): Promise<Task> {
        return this.request(`/tasks/${taskId}`, {
            method: 'GET',
        });
    }

    static getDownloadUrl(taskId: string): string {
        return `${this.baseUrl}/tasks/${taskId}/download`;
    }

    static async downloadFile(taskId: string): Promise<Blob> {
        const response = await fetch(this.getDownloadUrl(taskId));
        if (!response.ok) {
            throw new Error(`Download failed: ${response.statusText}`);
        }
        return response.blob();
    }

    static async getSettings(): Promise<Settings> {
        return this.request('/settings', {
            method: 'GET',
        });
    }

    static async updateSettings(settings: Partial<Settings>): Promise<{ success: boolean }> {
        return this.request('/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings),
        });
    }
}
