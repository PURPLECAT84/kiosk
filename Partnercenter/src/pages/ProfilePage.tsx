import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Phone, Lock, KeyRound, Mail, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function ProfilePage() {
  const { user, token } = useAuth();
  
  // 프로필 폼 상태
  const [name, setName] = useState(user?.name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [profileMsg, setProfileMsg] = useState({ text: '', type: '' });

  // 비밀번호 폼 상태
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newPasswordCheck, setNewPasswordCheck] = useState('');
  const [passwordMsg, setPasswordMsg] = useState({ text: '', type: '' });

  if (!user) return null;

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMsg({ text: '저장 중...', type: 'info' });
    try {
      const res = await fetch('/users/me', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name, phone })
      });
      if (!res.ok) throw new Error('프로필 수정에 실패했습니다.');
      
      setProfileMsg({ text: '개인정보가 성공적으로 수정되었습니다.', type: 'success' });
      setTimeout(() => setProfileMsg({ text: '', type: '' }), 3000);
    } catch (err: any) {
      setProfileMsg({ text: err.message, type: 'error' });
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 비밀번호 정규식 검사 (8자리 이상, 영문, 숫자, 특수문자 포함)
    const passwordRegex = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[^a-zA-Z0-9\s]).{8,}$/;
    if (!passwordRegex.test(newPassword)) {
      setPasswordMsg({ text: '비밀번호는 특수문자, 영문, 숫자를 조합하여 입력해주세요.', type: 'error' });
      return;
    }

    // 백엔드 요청 전 프론트엔드에서 1차 검증
    if (newPassword !== newPasswordCheck) {
      setPasswordMsg({ text: '새 비밀번호가 일치하지 않습니다.', type: 'error' });
      return;
    }

    setPasswordMsg({ text: '저장 중...', type: 'info' });
    try {
      const res = await fetch('/users/me/password', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          current_password: currentPassword, 
          new_password: newPassword, 
          new_password_check: newPasswordCheck 
        })
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '비밀번호 변경에 실패했습니다.');
      
      setPasswordMsg({ text: '비밀번호가 성공적으로 변경되었습니다.', type: 'success' });
      setCurrentPassword('');
      setNewPassword('');
      setNewPasswordCheck('');
      setTimeout(() => setPasswordMsg({ text: '', type: '' }), 3000);
    } catch (err: any) {
      setPasswordMsg({ text: err.message, type: 'error' });
    }
  };

  // 로그인 상태 뱃지 렌더러
  const renderProviderBadge = () => {
    const provider = user.login_provider || 'email';
    
    if (provider === 'kakao') {
      return (
        <div className="flex items-center space-x-2 bg-[#FEE500] text-[#000000] px-4 py-2 rounded-xl font-bold w-fit">
          <span>💬 카카오 계정으로 연동됨</span>
        </div>
      );
    } else if (provider === 'google') {
      return (
        <div className="flex items-center space-x-2 bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-xl font-bold w-fit shadow-sm">
          <span>🌐 구글 계정으로 연동됨</span>
        </div>
      );
    } else {
      return (
        <div className="flex items-center space-x-2 bg-gray-100 text-gray-700 px-4 py-2 rounded-xl font-bold w-fit">
          <Mail size={18} />
          <span>📧 일반 이메일 가입 계정</span>
        </div>
      );
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8 pb-20">
      {/* 상태 정보 카드 */}
      <div className="bg-white rounded-2xl shadow-sm p-8">
        <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
          <CheckCircle2 className="mr-2 text-[#7C3AED]" /> 현재 로그인 정보
        </h3>
        <div className="space-y-4">
          <div>
            <span className="text-sm text-gray-500 font-medium block mb-1">로그인된 이메일</span>
            <span className="text-xl font-bold text-gray-900">{user.email}</span>
          </div>
          <div>
            <span className="text-sm text-gray-500 font-medium block mb-2">접속 상태 (Provider)</span>
            {renderProviderBadge()}
          </div>
        </div>
      </div>

      {/* 개인정보 수정 카드 */}
      <div className="bg-white rounded-2xl shadow-sm p-8">
        <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
          <User className="mr-2 text-[#7C3AED]" /> 개인정보 수정
        </h3>
        <form onSubmit={handleProfileSubmit} className="space-y-6 max-w-lg">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">이름</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full pl-10 pr-4 py-3 text-base border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">전화번호</label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full pl-10 pr-4 py-3 text-base border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
              />
            </div>
          </div>
          
          {profileMsg.text && (
            <p className={`text-sm ${profileMsg.type === 'error' ? 'text-red-500' : profileMsg.type === 'success' ? 'text-green-500' : 'text-blue-500'}`}>
              {profileMsg.text}
            </p>
          )}

          <button
            type="submit"
            className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3 rounded-xl transition-colors"
          >
            정보 수정하기
          </button>
        </form>
      </div>

      {/* 비밀번호 변경 카드 (소셜 계정일 경우 숨김 처리 - 옵션 A 적용) */}
      {user.login_provider === 'email' || !user.login_provider ? (
        <div className="bg-white rounded-2xl shadow-sm p-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
            <Lock className="mr-2 text-[#7C3AED]" /> 비밀번호 변경
          </h3>
          <form onSubmit={handlePasswordSubmit} className="space-y-6 max-w-lg">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">현재 비밀번호</label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 text-base border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">새 비밀번호</label>
              <div className="relative">
                <ShieldAlert className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 text-base border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  placeholder="영문, 숫자, 특수문자 포함 8자 이상"
                  required
                  minLength={8}
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">새 비밀번호 확인</label>
              <div className="relative">
                <ShieldAlert className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="password"
                  value={newPasswordCheck}
                  onChange={(e) => setNewPasswordCheck(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 text-base border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  placeholder="새 비밀번호를 한 번 더 입력해주세요"
                  required
                  minLength={8}
                />
              </div>
            </div>

            {passwordMsg.text && (
              <p className={`text-sm ${passwordMsg.type === 'error' ? 'text-red-500' : passwordMsg.type === 'success' ? 'text-green-500' : 'text-blue-500'}`}>
                {passwordMsg.text}
              </p>
            )}

            <button
              type="submit"
              className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3 rounded-xl transition-colors"
            >
              비밀번호 변경하기
            </button>
          </form>
        </div>
      ) : (
        <div className="bg-gray-50 border border-gray-200 rounded-2xl shadow-sm p-8 text-center">
          <ShieldAlert className="mx-auto text-gray-400 mb-4" size={48} />
          <h3 className="text-xl font-bold text-gray-900 mb-2">비밀번호 변경 불가</h3>
          <p className="text-gray-500">
            소셜 연동 계정({user.login_provider === 'kakao' ? '카카오' : '구글'})으로 로그인하셨습니다.<br />
            비밀번호 관리는 해당 소셜 서비스에서 진행해 주세요.
          </p>
        </div>
      )}
    </div>
  );
}
