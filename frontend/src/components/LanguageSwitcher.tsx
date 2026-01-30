import React from 'react';
import { Button, Dropdown } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { MenuProps } from 'antd';

export const LanguageSwitcher: React.FC = () => {
    const { i18n } = useTranslation();

    const currentLanguage = i18n.language.startsWith('zh') ? '中文' : 'English';

    const items: MenuProps['items'] = [
        {
            key: 'en',
            label: 'English',
            onClick: () => i18n.changeLanguage('en'),
        },
        {
            key: 'zh',
            label: '中文',
            onClick: () => i18n.changeLanguage('zh'),
        },
    ];

    return (
        <Dropdown menu={{ items }} placement="bottomRight">
            <Button icon={<GlobalOutlined />}>
                {currentLanguage}
            </Button>
        </Dropdown>
    );
};
