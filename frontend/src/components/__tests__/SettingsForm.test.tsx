import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SettingsForm } from '../SettingsForm';
import { ApiClient } from '../../services/api';

// Mock ApiClient
vi.mock('../../services/api', () => ({
    ApiClient: {
        getSettings: vi.fn(),
        updateSettings: vi.fn(),
    },
}));

// Mock App.useApp
vi.mock('antd', async () => {
    const actual = await vi.importActual('antd');
    return {
        ...actual,
        App: {
            useApp: () => ({
                message: {
                    success: vi.fn(),
                    error: vi.fn(),
                    warning: vi.fn(),
                    info: vi.fn(),
                },
            }),
        },
    };
});

describe('SettingsForm', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (ApiClient.getSettings as any).mockResolvedValue({
            provider: 'openai',
            apiKey: 'sk-test',
            model: 'gpt-4o',
            concurrency: 5,
        });
    });

    it('renders form and loads initial settings', async () => {
        render(<SettingsForm />);

        // Check if initial values are loaded
        await waitFor(() => {
            expect(screen.getByDisplayValue('sk-test')).toBeInTheDocument();
        });

        expect(screen.getByLabelText(/Provider/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Model/i)).toBeInTheDocument();
    });

    it('submits settings on finish', async () => {
        (ApiClient.updateSettings as any).mockResolvedValue({ success: true });

        render(<SettingsForm />);

        // Wait for load
        await waitFor(() => screen.getByDisplayValue('sk-test'));

        // Change API Key
        const keyInput = screen.getByDisplayValue('sk-test');
        fireEvent.change(keyInput, { target: { value: 'sk-new-key' } });

        // Submit
        const submitBtn = screen.getByText(/Save Configuration/i);
        fireEvent.click(submitBtn);

        await waitFor(() => {
            expect(ApiClient.updateSettings).toHaveBeenCalledWith(expect.objectContaining({
                apiKey: 'sk-new-key',
            }));
        });
    });
});
