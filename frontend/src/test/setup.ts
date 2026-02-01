import '@testing-library/jest-dom'
import i18n from '../i18n'

// Initialize i18n for tests
i18n.init({
    lng: 'en',
    fallbackLng: 'en',
    resources: {
        en: {
            translation: {
                'settings.title': 'Settings',
                'settings.provider': 'Provider',
                'settings.apiKey': 'API Key',
                'settings.model': 'Model',
                'settings.concurrency': 'Concurrency',
                'settings.save': 'Save Configuration',
                'task.title': 'Tasks',
                'task.refresh': 'Refresh',
                'task.columns.fileName': 'File Name',
                'task.columns.status': 'Status',
                'task.columns.createdAt': 'Created At',
                'task.columns.action': 'Action',
                'task.status.pending': 'Pending',
                'task.status.processing': 'Processing',
                'task.status.completed': 'Completed',
                'task.status.failed': 'Failed',
                'task.action.view': 'View',
                'task.action.download': 'Download',
                'task.action.delete': 'Delete',
                'upload.dragText': 'Click or drag file to this area to upload',
                'upload.hint': 'Support for a single or bulk upload.',
            }
        }
    }
});

Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: any) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => { }, // Deprecated
        removeListener: () => { }, // Deprecated
        addEventListener: () => { },
        removeEventListener: () => { },
        dispatchEvent: () => { },
    }),
});
