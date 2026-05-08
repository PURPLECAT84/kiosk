import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogIn, KeyRound, Mail } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    
    // OAuth2PasswordRequestForm expects form data
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
      const res = await fetch('/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });

      if (!res.ok) {
        throw new Error('이메일 또는 비밀번호가 일치하지 않습니다.');
      }

      const data = await res.json();
      login(data.access_token);
      navigate('/');
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-[#F9FAFB] flex flex-col justify-center items-center p-4">
      <div className="bg-white rounded-2xl shadow-sm p-8 w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-[#7C3AED] text-white p-3 rounded-full mb-4">
            <LogIn size={32} />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">MOKI Partner</h1>
          <p className="text-lg text-gray-500 mt-2">파트너센터에 로그인하세요</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-lg font-medium text-gray-700 mb-2">이메일</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={24} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-12 pr-4 py-3 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                placeholder="email@example.com"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-lg font-medium text-gray-700 mb-2">비밀번호</label>
            <div className="relative">
              <KeyRound className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={24} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-12 pr-4 py-3 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                placeholder="비밀번호를 입력하세요"
                required
              />
            </div>
          </div>
          
          {errorMsg && <p className="text-red-500 text-lg">{errorMsg}</p>}

          <button
            type="submit"
            className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white text-lg font-bold py-4 rounded-xl transition-colors"
          >
            이메일로 로그인
          </button>

          {/* 아이디/비밀번호 찾기 */}
          <div className="flex justify-center space-x-4 text-base text-gray-500">
            <Link to="/find-id" className="hover:text-[#7C3AED] transition-colors">아이디 찾기</Link>
            <span className="text-gray-300">|</span>
            <Link to="/find-password" className="hover:text-[#7C3AED] transition-colors">비밀번호 찾기</Link>
          </div>
        </form>

        <div className="mt-8">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500 text-lg">또는 간편 로그인</span>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-4">
            <a
              href="/auth/kakao/login"
              className="flex justify-center items-center py-3 border border-gray-300 rounded-xl hover:bg-yellow-50 transition-colors text-lg font-medium text-gray-700"
            >
              카카오 로그인
            </a>
            <a
              href="/auth/google/login"
              className="flex justify-center items-center py-3 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors text-lg font-medium text-gray-700"
            >
              구글 로그인
            </a>
          </div>
        </div>
        
        <p className="mt-8 text-center text-lg text-gray-600">
          계정이 없으신가요?{' '}
          <Link to="/signup" className="text-[#7C3AED] hover:underline font-medium">
            회원가입
          </Link>
        </p>
      </div>
    </div>
  );
}
