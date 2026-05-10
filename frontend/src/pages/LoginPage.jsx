import {useState} from 'react';
import LoginForm from '../components/LoginForm';
import RegisterForm from '../components/RegisterForm';

export default function LoginPage({onLogin}) {
  const [mode, setMode] = useState('login');

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Archive Explorer</h1>
        {mode === 'login' ? (
          <LoginForm onLogin={onLogin} />
        ) : (
          <RegisterForm onRegister={onLogin} />
        )}
        <p className="toggle">
          {mode === 'login' ? (
            <>
              {"Don't have an account? "}
              <button className="link" onClick={() => setMode('register')}>
                Register
              </button>
            </>
          ) : (
            <>
              {"Already have an account? "}
              <button className="link" onClick={() => setMode('login')}>
                Log In
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
