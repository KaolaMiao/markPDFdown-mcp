import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UploadZone } from '../UploadZone';
import { ApiClient } from '../../services/api';

vi.mock('../../services/api', () => ({
    ApiClient: {
        uploadFile: vi.fn(),
    },
}));

describe('UploadZone', () => {
    const onUploadSuccess = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders upload area', () => {
        render(<UploadZone onUploadSuccess={onUploadSuccess} />);
        expect(screen.getByText(/Click or drag file to this area to upload/i)).toBeInTheDocument();
    });

    it('calls ApiClient.uploadFile when file is selected', async () => {
        (ApiClient.uploadFile as any).mockResolvedValue({ task_id: '123' });

        const { container } = render(<UploadZone onUploadSuccess={onUploadSuccess} />);

        // AntD Dragger input is type=file
        // eslint-disable-next-line testing-library/no-container, testing-library/no-node-access
        const input = container.querySelector('input[type="file"]');

        const file = new File(['hello'], 'hello.pdf', { type: 'application/pdf' });
        if (input) {
            fireEvent.change(input, { target: { files: [file] } });
        }

        await waitFor(() => {
            expect(ApiClient.uploadFile).toHaveBeenCalledWith(file);
        });
        expect(onUploadSuccess).toHaveBeenCalled();
    });
});
