export interface Task {
  id: string;
  task_id?: string;
  file_name?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at?: string;
  result?: string;
  error?: string;
  total_pages?: number;
}

export interface Settings {
  provider: string;
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
      let errorText = response.statusText;
      try {
        const errJson = await response.json();
        errorText = errJson.detail || errJson.message || errorText;
      } catch {
        // ignore
      }
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }
    if (response.status === 204) return {} as T;
    return response.json();
  }


  static async uploadFile(file: File): Promise<Task> {
    const formData = new FormData();
    formData.append('file', file);
    return this.request('/upload', {
      method: 'POST',
      body: formData,
    });
  }

  static async uploadFiles(files: File[]): Promise<Task[]> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    return this.request('/upload/batch', {
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

  static async deleteTask(taskId: string): Promise<void> {
    return this.request(`/tasks/${taskId}`, {
      method: 'DELETE',
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

  static getPageImageUrl(taskId: string, pageNum: number): string {
    return `${this.baseUrl}/tasks/${taskId}/pages/${pageNum}`;
  }

  static async getPageContent(taskId: string, pageNum: number): Promise<{
    page: number;
    status: string;
    content?: string;
    total_pages?: number;
    message?: string;
  }> {
    return this.request(`/tasks/${taskId}/pages/${pageNum}/content`);
  }

  static async regeneratePage(taskId: string, pageNum: number): Promise<{
    message: string;
    task_id: string;
    page_num: number;
    status: string;
  }> {
    return this.request(`/tasks/${taskId}/pages/${pageNum}/regenerate`, {
      method: 'POST',
    });
  }
}
