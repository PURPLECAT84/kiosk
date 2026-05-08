import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, User, Phone, CheckCircle2 } from 'lucide-react';

export default function FindIdPage() {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [result, setResult] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setResult('');
    setIsLoading(true);

    try {
      const res = await fetch('/users/find-id', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, phone }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '아이디 찾기에 실패했습니다.');

      setResult(data.masked_email);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F9FAFB] flex flex-col justify-center items-center p-4">
      <div className="bg-white rounded-2xl shadow-sm p-8 w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-[#7C3AED] text-white p-3 rounded-full mb-4">
            <Search size={32} />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">아이디 찾기</h1>
          <p className="text-lg text-gray-500 mt-2 text-center">
            가입 시 등록한 이름과 전화번호를 입력해주세요
          </p>
        </div>

        {result ? (
          // ✅ 결과 화면
          <div className="text-center space-y-6">
            <div className="flex justify-center">
              <CheckCircle2 size={64} className="text-[#7C3AED]" />
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-2xl p-6">
              <p className="text-gray-600 text-lg mb-2">회원님의 아이디(이메일)는</p>
              <p className="text-2xl font-bold text-[#7C3AED] tracking-widest">{result}</p>
              <p className="text-sm text-gray-500 mt-2">*보안을 위해 일부만 표시됩니다</p>
            </div>
            <div className="flex flex-col space-y-3">
              <Link
                to="/login"
                className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white text-lg font-bold py-4 rounded-xl transition-colors text-center block"
              >
                로그인하러 가기
              </Link>
              <Link
                to="/find-password"
                className="w-full border border-gray-300 text-gray-700 text-lg font-medium py-4 rounded-xl hover:bg-gray-50 transition-colors text-center block"
              >
                비밀번호 찾기
              </Link>
            </div>
          </div>
        ) : (
          // 📝 입력 폼
          <form onSubmit={handleSubmit} className="space-y-6">
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
              disabled={isLoading}
              className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white text-lg font-bold py-4 rounded-xl transition-colors disabled:opacity-60"
            >
              {isLoading ? '검색 중...' : '아이디 찾기'}
            </button>

            <div className="flex justify-between text-lg text-gray-500">
              <Link to="/login" className="hover:text-[#7C3AED]">로그인</Link>
              <Link to="/find-password" className="hover:text-[#7C3AED]">비밀번호 찾기</Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
