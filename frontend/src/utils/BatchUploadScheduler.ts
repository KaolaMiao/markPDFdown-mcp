import { ApiClient } from '../services/api';
import i18n from '../i18n';

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
            // Single file mode
            const item = currentQueue[0];
            try {
                await ApiClient.uploadFile(item.file);
                this.messageApi?.success(i18n.t('upload.success', { fileName: item.file.name }));
                item.onSuccess?.('ok');
                if (this.globalOnSuccess) this.globalOnSuccess('ok');
                if (this.parentOnUploadSuccess) this.parentOnUploadSuccess();
            } catch (error) {
                this.messageApi?.error(i18n.t('upload.fail', { error }));
                item.onError?.(error as Error);
            }
        } else {
            // Batch mode
            const files = currentQueue.map(item => item.file);
            try {
                await ApiClient.uploadFiles(files);
                this.messageApi?.success(i18n.t('upload.batchSuccess', { count: files.length }));

                // Notify all items of success
                currentQueue.forEach(item => {
                    item.onSuccess?.('ok');
                });

                if (this.globalOnSuccess) this.globalOnSuccess('ok');
                if (this.parentOnUploadSuccess) this.parentOnUploadSuccess();
            } catch (error) {
                this.messageApi?.error(i18n.t('upload.batchFail', { error }));
                // Notify all items of failure
                currentQueue.forEach(item => {
                    item.onError?.(error as Error);
                });
            }
        }
    }
}

