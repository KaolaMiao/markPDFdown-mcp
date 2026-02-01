import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
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
                { id: '1', file_name: 'test.pdf', status: 'pending', created_at: '2023-01-01' }
            ],
            total: 1
        };

        const mockTasks2 = {
            items: [
                { id: '1', file_name: 'test.pdf', status: 'completed', created_at: '2023-01-01' }
            ],
            total: 1
        };

        (ApiClient.getTasks as any)
            .mockResolvedValueOnce(mockTasks1)
            .mockResolvedValue(mockTasks2);

        render(
            <BrowserRouter>
                <TaskTable pollingInterval={100} />
            </BrowserRouter>
        );

        // Initial load
        await waitFor(() => {
            expect(screen.getByText('test.pdf')).toBeInTheDocument();
            expect(screen.getByText('Pending')).toBeInTheDocument();
        });

        // Wait for update
        await waitFor(() => {
            expect(screen.getByText('Completed')).toBeInTheDocument();
        }, { timeout: 1500 });

        // Check download button exists
        const downloadBtn = screen.getByRole('button', { name: /download/i });
        expect(downloadBtn).toBeInTheDocument();
    });
});
