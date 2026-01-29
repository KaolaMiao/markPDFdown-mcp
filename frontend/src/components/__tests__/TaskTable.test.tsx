import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { TaskTable } from '../TaskTable';
import { ApiClient } from '../../services/api';

vi.mock('../../services/api', () => ({
    ApiClient: {
        getTasks: vi.fn(),
        getDownloadUrl: vi.fn((id) => `/api/v1/tasks/${id}/download`),
    },
}));

describe('TaskTable', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders tasks and polls for updates', async () => {
        const mockTasks1 = {
            items: [
                { id: '1', task_id: '1', status: 'pending', fileName: 'test.pdf', created_at: '2023-01-01' }
            ],
            total: 1
        };

        const mockTasks2 = {
            items: [
                { id: '1', task_id: '1', status: 'completed', fileName: 'test.pdf', created_at: '2023-01-01' }
            ],
            total: 1
        };

        (ApiClient.getTasks as any)
            .mockResolvedValueOnce(mockTasks1)
            .mockResolvedValue(mockTasks2);

        render(<TaskTable pollingInterval={100} />);

        // Initial load
        await waitFor(() => {
            expect(screen.getByText('test.pdf')).toBeInTheDocument();
            expect(screen.getByText('pending')).toBeInTheDocument();
        });

        // Wait for update
        await waitFor(() => {
            expect(screen.getByText('completed')).toBeInTheDocument();
        }, { timeout: 1500 });

        // Check download link using getByRole
        // AntD Button with href renders an <a> tag
        const link = screen.getByRole('link', { name: /download/i });
        expect(link).toHaveAttribute('href', '/api/v1/tasks/1/download');
    });
});
