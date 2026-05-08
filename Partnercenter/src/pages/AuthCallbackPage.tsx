import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AuthCallbackPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [status, setStatus] = useState('소셜 로그인 처리 중입니다...');
  const isAttempted = React.useRef(false);

  useEffect(() => {
    if (isAttempted.current) return;
    isAttempted.current = true;

    // URL 해시에서 access_token 추출 (Supabase Implicit Flow)
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    const accessToken = hashParams.get('access_token');
    const error = hashParams.get('error');
    const errorDescription = hashParams.get('error_description');

    if (error) {
      setStatus(`로그인 실패: ${errorDescription || error}`);
      setTimeout(() => navigate('/login'), 3000);
      return;
    }

    if (!accessToken) {
      setStatus('유효한 토큰을 찾을 수 없습니다.');
      setTimeout(() => navigate('/login'), 3000);
      return;
    }

    // 백엔드로 토큰 교환 요청
    fetch('/auth/supabase/exchange', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ access_token: accessToken }),
    })
      .then((res) => {
        if (!res.ok) throw new Error('토큰 교환 실패');
        return res.json();
      })
      .then((data) => {
        // 자체 JWT 토큰으로 로그인 처리
        login(data.access_token);
        navigate('/');
      })
      .catch((err) => {
        console.error(err);
        setStatus('인증 처리 중 오류가 발생했습니다.');
        setTimeout(() => navigate('/login'), 3000);
      });
  }, [navigate, login]);

  return (
    <div className="min-h-screen bg-[#F9FAFB] flex justify-center items-center">
      <div className="bg-white p-8 rounded-2xl shadow-sm text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#7C3AED] mx-auto mb-4"></div>
        <p className="text-xl font-medium text-gray-700">{status}</p>
      </div>
    </div>
  );
}
