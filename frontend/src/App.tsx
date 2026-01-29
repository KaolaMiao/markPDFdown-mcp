import { ConfigProvider, App as AntApp } from 'antd';
import { Dashboard } from './pages/Dashboard';

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#2563eb', // Blue-600
        },
      }}
    >
      <AntApp>
        <Dashboard />
      </AntApp>
    </ConfigProvider>
  );
}

export default App;

