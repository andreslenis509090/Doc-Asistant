import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Lock, Mail, Sparkles, AlertCircle } from 'lucide-react';

export default function LoginModal() {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('andres.rag.dev@gmail.com');
  const [password, setPassword] = useState('Password123!');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, password);
      } else {
        await login(email, password);
      }
    } catch (err) {
      setError(err.message || 'Error en la autenticación');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-xs p-4">
      <div className="w-full max-w-sm bg-[#1e1e1e] border border-[#2f2f2f] rounded-2xl p-6 shadow-2xl text-[#ececec]">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-11 h-11 rounded-full bg-[#10a37f] text-white mb-3 shadow-md">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">Docs Assistant</h2>
          <p className="text-xs text-[#8e8e8e] mt-1">
            {isRegister ? 'Crea una cuenta en Supabase' : 'Inicia sesión para chatear con tus PDFs'}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="block text-xs font-medium text-[#b4b4b4] mb-1">Correo electrónico</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 w-4 h-4 text-[#8e8e8e]" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@correo.com"
                className="w-full bg-[#252525] border border-[#383838] focus:border-[#10a37f] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-[#737373] focus:outline-none transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#b4b4b4] mb-1">Contraseña</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 w-4 h-4 text-[#8e8e8e]" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#252525] border border-[#383838] focus:border-[#10a37f] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-[#737373] focus:outline-none transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 bg-[#10a37f] hover:bg-[#0e8f6f] disabled:opacity-50 text-white font-medium rounded-xl text-xs transition-colors shadow-sm cursor-pointer"
          >
            {loading ? 'Procesando...' : isRegister ? 'Registrarse' : 'Continuar'}
          </button>
        </form>

        <div className="mt-5 text-center">
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError('');
            }}
            className="text-xs text-[#8e8e8e] hover:text-white transition-colors"
          >
            {isRegister ? '¿Ya tienes cuenta? Inicia sesión' : '¿No tienes cuenta? Regístrate'}
          </button>
        </div>
      </div>
    </div>
  );
}
