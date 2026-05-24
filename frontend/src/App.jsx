import {useState, useEffect} from 'react';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    const onAuthChange = () => setToken(localStorage.getItem('token'));
    window.addEventListener('storage', onAuthChange);
    window.addEventListener('auth-change', onAuthChange);
    return () => {
      window.removeEventListener('storage', onAuthChange);
      window.removeEventListener('auth-change', onAuthChange);
    };
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
