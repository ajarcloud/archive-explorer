import {useState, useEffect} from 'react';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    const onStorage = () => setToken(localStorage.getItem('token'));
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  if (!token) {
    return (
      <LoginPage
        onLogin={(t) => {
          localStorage.setItem('token', t);
          setToken(t);
        }}
      />
    );
  }

  return (
    <DashboardPage
      onLogout={() => {
        localStorage.removeItem('token');
        setToken(null);
      }}
    />
  );
}
