import { ApiClient } from '../services/api';

export class BatchUploadScheduler {
    private queue: {
        file: File;
        onSuccess?: (body: unknown) => void;
        onError?: (error: Error) => void
    }[] = [];
    private timer: NodeJS.Timeout | null = null;
    private readonly DELAY_MS = 100; // Wait 100ms to collect files

    constructor(
        private globalOnSuccess?: (msg: string) => void,
        private parentOnUploadSuccess?: () => void,
        private messageApi?: {
            success: (content: string) => void;
            error: (content: string) => void
        }
    ) { }

    add(file: File, onSuccess?: (body: unknown) => void, onError?: (error: Error) => void) {
        this.queue.push({ file, onSuccess, onError });
        this.scheduleFlush();
    }

    private scheduleFlush() {
        if (this.timer) clearTimeout(this.timer);
        this.timer = setTimeout(() => this.flush(), this.DELAY_MS);
    }

    private async flush() {
        const currentQueue = [...this.queue];
        this.queue = []; // Clear queue immediately
        this.timer = null;

        if (currentQueue.length === 0) return;

        if (currentQueue.length === 1) {
            // Single file mode - use legacy endpoint
            const item = currentQueue[0];
            try {
                await ApiClient.uploadFile(item.file);
                this.messageApi?.success(`${item.file.name} uploaded successfully`);
                item.onSuccess?.('ok');
                if (this.globalOnSuccess) this.globalOnSuccess('ok');
                if (this.parentOnUploadSuccess) this.parentOnUploadSuccess();
            } catch (error) {
                this.messageApi?.error(`Upload failed: ${error}`);
                item.onError?.(error as Error);
            }
        } else {
            // Batch mode - use new endpoint
            const files = currentQueue.map(item => item.file);
            try {
                const tasks = await ApiClient.uploadFiles(files);
                this.messageApi?.success(`${files.length} files uploaded successfully`);

                // Notify all items of success
                currentQueue.forEach(item => {
                    item.onSuccess?.('ok');
                });

                if (this.globalOnSuccess) this.globalOnSuccess('ok');
                if (this.parentOnUploadSuccess) this.parentOnUploadSuccess();
            } catch (error) {
                this.messageApi?.error(`Batch upload failed: ${error}`);
                // Notify all items of failure
                currentQueue.forEach(item => {
                    item.onError?.(error as Error);
                });
            }
        }
    }
}
