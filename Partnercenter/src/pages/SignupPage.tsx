import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { UserPlus, Mail, KeyRound, User, Phone } from 'lucide-react';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const navigate = useNavigate();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    const payload = {
      email,
      password,
      name,
      phone
    };

    try {
      const res = await fetch('/users/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || '회원가입 중 오류가 발생했습니다.');
      }

      setSuccessMsg('회원가입이 완료되었습니다! 로그인 페이지로 이동합니다.');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-[#F9FAFB] flex flex-col justify-center items-center p-4">
      <div className="bg-white rounded-2xl shadow-sm p-8 w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-[#7C3AED] text-white p-3 rounded-full mb-4">
            <UserPlus size={32} />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">회원가입</h1>
          <p className="text-lg text-gray-500 mt-2">MOKI 파트너가 되어보세요</p>
        </div>

        {successMsg ? (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4">
            <span className="block sm:inline text-lg">{successMsg}</span>
          </div>
        ) : (
          <form onSubmit={handleSignup} className="space-y-6">
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
                  placeholder="비밀번호 8자리 이상"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-lg font-medium text-gray-700 mb-2">이름 (대표자명)</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={24} />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  placeholder="홍길동"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-lg font-medium text-gray-700 mb-2">전화번호</label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={24} />
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  placeholder="010-0000-0000"
                  required
                />
              </div>
            </div>
            
            {errorMsg && <p className="text-red-500 text-lg">{errorMsg}</p>}

            <button
              type="submit"
              className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white text-lg font-bold py-4 rounded-xl transition-colors"
            >
              회원가입 완료
            </button>
          </form>
        )}

        <p className="mt-8 text-center text-lg text-gray-600">
          이미 계정이 있으신가요?{' '}
          <Link to="/login" className="text-[#7C3AED] hover:underline font-medium">
            로그인하기
          </Link>
        </p>
      </div>
    </div>
  );
}
