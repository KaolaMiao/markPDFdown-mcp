import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from '../api';

vi.stubGlobal('fetch', vi.fn());

describe('ApiClient', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    const baseUrl = '/api/v1';

    it('uploadFile should post formData to /upload and return task info', async () => {
        const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
        const mockResponse = { task_id: '123', status: 'pending' };

        (fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse,
        });

        const result = await ApiClient.uploadFile(mockFile);

        expect(fetch).toHaveBeenCalledWith(`${baseUrl}/upload`, expect.objectContaining({
            method: 'POST',
            body: expect.any(FormData),
        }));
        expect(result).toEqual(mockResponse);
    });

    it('getTasks should fetch tasks list', async () => {
        const mockTasks = { items: [{ id: '1', status: 'completed' }], total: 1 };
        (fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => mockTasks,
        });

        const result = await ApiClient.getTasks();

        expect(fetch).toHaveBeenCalledWith(`${baseUrl}/tasks`, expect.objectContaining({
            method: 'GET',
        }));
        expect(result).toEqual(mockTasks);
    });

    it('updateSettings should post settings data', async () => {
        const settings = { provider: 'openai', apiKey: 'sk-...' };
        (fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true }),
        });

        await ApiClient.updateSettings(settings);

        expect(fetch).toHaveBeenCalledWith(`${baseUrl}/settings`, expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings),
        }));
    });
});
