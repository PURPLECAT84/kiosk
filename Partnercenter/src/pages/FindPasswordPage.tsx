import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { KeyRound, Mail, User, Phone, ShieldAlert, Copy, CheckCircle2 } from 'lucide-react';

export default function FindPasswordPage() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [result, setResult] = useState<{ temp_password: string; message: string } | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setResult(null);
    setIsLoading(true);

    try {
      const res = await fetch('/users/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, phone }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '비밀번호 재설정에 실패했습니다.');

      setResult(data);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(result.temp_password);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="min-h-screen bg-[#F9FAFB] flex flex-col justify-center items-center p-4">
      <div className="bg-white rounded-2xl shadow-sm p-8 w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-[#7C3AED] text-white p-3 rounded-full mb-4">
            <KeyRound size={32} />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">비밀번호 찾기</h1>
          <p className="text-lg text-gray-500 mt-2 text-center">
            가입한 이메일, 이름, 전화번호를 모두 입력해주세요
          </p>
        </div>

        {result ? (
          // ✅ 임시 비밀번호 발급 결과 화면
          <div className="text-center space-y-6">
            <div className="flex justify-center">
              <CheckCircle2 size={64} className="text-green-500" />
            </div>
            <div className="bg-amber-50 border border-amber-300 rounded-2xl p-6 space-y-4">
              <p className="text-gray-700 font-medium text-lg">임시 비밀번호가 발급되었습니다</p>
              <div className="bg-white border-2 border-amber-300 rounded-xl px-6 py-4 flex items-center justify-between">
                <span className="text-2xl font-bold tracking-widest text-gray-900 font-mono">
                  {result.temp_password}
                </span>
                <button
                  onClick={handleCopy}
                  className="ml-4 p-2 text-gray-500 hover:text-[#7C3AED] transition-colors"
                  title="복사하기"
                >
                  {copied ? <CheckCircle2 size={24} className="text-green-500" /> : <Copy size={24} />}
                </button>
              </div>
              <div className="flex items-start space-x-2 text-sm text-amber-700 bg-amber-100 rounded-xl p-3 text-left">
                <ShieldAlert size={18} className="flex-shrink-0 mt-0.5" />
                <p>{result.message}</p>
              </div>
            </div>
            <Link
              to="/login"
              className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white text-lg font-bold py-4 rounded-xl transition-colors text-center block"
            >
              로그인하러 가기
            </Link>
          </div>
        ) : (
          // 📝 입력 폼
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-lg font-medium text-gray-700 mb-2">이메일 (아이디)</label>
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
              {isLoading ? '확인 중...' : '임시 비밀번호 발급받기'}
            </button>

            <div className="flex justify-between text-lg text-gray-500">
              <Link to="/login" className="hover:text-[#7C3AED]">로그인</Link>
              <Link to="/find-id" className="hover:text-[#7C3AED]">아이디 찾기</Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
