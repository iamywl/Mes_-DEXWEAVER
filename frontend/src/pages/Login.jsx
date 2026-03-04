/**
 * Login / Register page.
 */
import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Input, BtnSuccess, FormRow, Select } from '../components/ui';

const Login = () => {
  const {login, register, error, loading, setError} = useAuth();
  const [mode, setMode] = useState('login');

  const handleLogin = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    await login(fd.get('user_id'), fd.get('password'));
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    if (fd.get('password') !== fd.get('password_confirm')) {
      setError('Passwords do not match');
      return;
    }
    const ok = await register({
      user_id: fd.get('user_id'),
      password: fd.get('password'),
      name: fd.get('name'),
      email: fd.get('email'),
      role: fd.get('role'),
    });
    if (ok) setMode('login');
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#020617]">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-black text-blue-500 tracking-tighter italic">DEXWEAVER MES v6.0</h1>
          <p className="text-slate-600 text-xs mt-1">Manufacturing Execution System</p>
        </div>
        <div className="bg-[#1e293b] rounded-2xl border border-slate-700 p-6">
          {/* Tab toggle */}
          <div className="flex mb-6 border-b border-slate-700">
            <button onClick={() => {setMode('login'); setError('');}}
              className={`flex-1 py-2 text-xs font-bold transition-all cursor-pointer ${
                mode === 'login' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-500 hover:text-slate-300'
              }`}>Login</button>
            <button onClick={() => {setMode('register'); setError('');}}
              className={`flex-1 py-2 text-xs font-bold transition-all cursor-pointer ${
                mode === 'register' ? 'text-emerald-400 border-b-2 border-emerald-400' : 'text-slate-500 hover:text-slate-300'
              }`}>Register</button>
          </div>

          {error && (
            <div className={`text-xs p-2 rounded-lg mb-4 ${
              error.includes('successful') || error.includes('승인')
                ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-800'
                : 'bg-red-900/50 text-red-300 border border-red-800'
            }`}>{error}</div>
          )}

          {mode === 'login' && (
            <form onSubmit={handleLogin}>
              <FormRow label="User ID"><Input name="user_id" required className="w-full" placeholder="Enter your ID" autoFocus /></FormRow>
              <FormRow label="Password"><Input name="password" type="password" required className="w-full" placeholder="Enter password" /></FormRow>
              <BtnSuccess type="submit" className="w-full mt-2" disabled={loading}>
                {loading ? 'Logging in...' : 'Login'}
              </BtnSuccess>
            </form>
          )}

          {mode === 'register' && (
            <form onSubmit={handleRegister}>
              <FormRow label="User ID"><Input name="user_id" required className="w-full" placeholder="Choose a user ID" autoFocus /></FormRow>
              <FormRow label="Password"><Input name="password" type="password" required className="w-full" placeholder="Choose a password" /></FormRow>
              <FormRow label="Confirm Password"><Input name="password_confirm" type="password" required className="w-full" placeholder="Confirm password" /></FormRow>
              <FormRow label="Name"><Input name="name" required className="w-full" placeholder="Full name" /></FormRow>
              <FormRow label="Email"><Input name="email" type="email" className="w-full" placeholder="email@example.com" /></FormRow>
              <FormRow label="Role">
                <Select name="role" onChange={() => {}} value="worker"
                  options={[{value:'worker',label:'Worker'},{value:'manager',label:'Manager'},{value:'viewer',label:'Viewer'}]} className="w-full" />
              </FormRow>
              <BtnSuccess type="submit" className="w-full mt-2" disabled={loading}>
                {loading ? 'Registering...' : 'Register'}
              </BtnSuccess>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default Login;
