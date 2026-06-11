import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Phone, Lock, KeyRound, Mail, CheckCircle2, ShieldAlert, Briefcase, Trash2, Plus, FileText, Loader2, Upload, X, Clock } from 'lucide-react';

export default function ProfilePage() {
  const { user, token, refreshUser } = useAuth();
  
  // 프로필 폼 상태
  const [name, setName] = useState(user?.name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [profileMsg, setProfileMsg] = useState({ text: '', type: '' });

  // 비밀번호 폼 상태
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newPasswordCheck, setNewPasswordCheck] = useState('');
  const [passwordMsg, setPasswordMsg] = useState({ text: '', type: '' });

  // 사업자 등록 상태
  const [bizNumber, setBizNumber] = useState('');
  const [bizName, setBizName] = useState('');
  const [repName, setRepName] = useState(user?.name || '');
  const [repPhone, setRepPhone] = useState(user?.phone || '');
  const [storeName, setStoreName] = useState('');
  const [docUrl, setDocUrl] = useState('');
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [bizError, setBizError] = useState('');
  const [bizSuccess, setBizSuccess] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  
  // 회원 탈퇴 모달 관련 상태
  const [isDeleteUserOpen, setIsDeleteUserOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const [isDeletingUser, setIsDeletingUser] = useState(false);
  const { logout } = useAuth();

  if (!user) return null;

  const handleDeleteUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setDeleteError('');
    setIsDeletingUser(true);
    try {
      const res = await fetch('/users/me', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ password: deletePassword })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || '회원 탈퇴 처리에 실패했습니다.');
      }
      alert('회원 탈퇴가 완료되었습니다. 그동안 이용해 주셔서 감사합니다.');
      logout();
    } catch (err: any) {
      setDeleteError(err.message);
    } finally {
      setIsDeletingUser(false);
    }
  };

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

  const handleDocUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      setBizError('이미지 파일 크기는 2MB 이하여야 합니다.');
      return;
    }

    setUploadingDoc(true);
    setBizError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/products/image', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '사업자등록증 업로드에 실패했습니다.');
      setDocUrl(data.image_url);
    } catch (err: any) {
      setBizError(err.message);
    } finally {
      setUploadingDoc(false);
    }
  };

  const handleBizSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBizError('');
    setBizSuccess('');

    if (!docUrl) {
      setBizError('사업자등록증 이미지를 업로드해 주세요.');
      return;
    }

    const cleanedStoreName = storeName.replace(/\s+/g, '');
    if (!cleanedStoreName) {
      setBizError('설치매장명은 공백일 수 없습니다.');
      return;
    }

    try {
      const res = await fetch('/users/me/business', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          business_number: bizNumber,
          business_name: bizName,
          representative_name: repName,
          representative_phone: repPhone || null,
          store_name: cleanedStoreName,
          document_url: docUrl
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '사업자 등록에 실패했습니다.');

      setBizSuccess('사업자 정보가 성공적으로 등록되었습니다.');
      setBizNumber('');
      setBizName('');
      setStoreName('');
      setDocUrl('');
      
      await refreshUser();
      setTimeout(() => setBizSuccess(''), 3000);
    } catch (err: any) {
      setBizError(err.message);
    }
  };

  const handleBizDelete = async (bizId: number) => {
    if (!window.confirm('정말 이 사업자 등록 정보를 삭제하시겠습니까? 해당 매장 정보도 함께 제거됩니다.')) return;
    setDeletingId(bizId);
    try {
      const res = await fetch(`/users/me/business/${bizId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || '삭제에 실패했습니다.');
      }
      await refreshUser();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setDeletingId(null);
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

      {/* 🏢 사업자 정보 설정 섹션 (STAFF는 미노출) */}
      {user.role !== 'STAFF' && (
        <div className="bg-white rounded-2xl shadow-sm p-8 space-y-8">
          <div className="flex items-center space-x-2 border-b border-gray-100 pb-4">
            <Briefcase className="text-[#7C3AED]" size={24} />
            <h3 className="text-xl font-bold text-gray-900">사업자 정보 설정</h3>
          </div>

          {/* 등록된 사업자 리스트 */}
          <div className="space-y-4">
            <h4 className="font-bold text-gray-800 text-sm">등록된 사업자 정보</h4>
            {!user.businesses || user.businesses.length === 0 ? (
              <p className="text-gray-400 text-sm py-8 text-center border border-dashed border-gray-200 rounded-xl">
                등록된 사업자 정보가 없습니다. 아래 양식을 작성해 새로 추가해 주세요.
              </p>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {user.businesses.map((biz) => (
                  <div key={biz.id} className="p-5 border border-gray-200 rounded-xl bg-gray-50 flex justify-between items-start shadow-sm">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2 flex-wrap gap-2">
                        <span className="font-bold text-gray-900 text-lg">{biz.business_name}</span>
                        <span className="text-sm text-gray-400">({biz.business_number})</span>
                        {biz.is_verified ? (
                          <span className="bg-green-100 text-green-700 text-xs font-extrabold px-3 py-1 rounded-full flex items-center">
                            <CheckCircle2 size={12} className="mr-1" /> 승인 완료
                          </span>
                        ) : (
                          <span className="bg-yellow-100 text-yellow-700 text-xs font-extrabold px-3 py-1 rounded-full flex items-center">
                            <Clock size={12} className="mr-1" /> 승인 대기중
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>대표자명: <span className="font-semibold text-gray-800">{biz.representative_name}</span> {biz.representative_phone && `| 연락처: ${biz.representative_phone}`}</p>
                        <p>설치 매장: <span className="font-semibold text-[#7C3AED]">{biz.store_name}</span></p>
                      </div>
                      {biz.document_url && (
                        <a
                          href={biz.document_url.startsWith('http') ? biz.document_url : `http://localhost:8000${biz.document_url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-[#7C3AED] hover:text-[#6D28D9] font-bold block mt-2 hover:underline"
                        >
                          사업자등록증 사본 보기
                        </a>
                      )}
                    </div>
                    <button
                      onClick={() => handleBizDelete(biz.id)}
                      disabled={deletingId === biz.id}
                      className="text-red-500 hover:text-red-700 p-2 rounded-lg hover:bg-red-50 transition-colors cursor-pointer"
                    >
                      {deletingId === biz.id ? <Loader2 className="animate-spin" size={18} /> : <Trash2 size={18} />}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 신규 사업자 등록 양식 */}
          <form onSubmit={handleBizSubmit} className="space-y-6 max-w-lg border-t border-gray-100 pt-6">
            <h4 className="font-bold text-gray-800 text-sm flex items-center">
              <Plus size={18} className="mr-1 text-[#7C3AED]" /> 신규 사업자 정보 추가
            </h4>

            {bizError && (
              <div className="bg-red-50 text-red-700 p-4 rounded-xl text-sm font-semibold">
                {bizError}
              </div>
            )}

            {bizSuccess && (
              <div className="bg-green-50 text-green-700 p-4 rounded-xl text-sm font-semibold">
                {bizSuccess}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">사업자 등록번호</label>
                <input
                  type="text"
                  value={bizNumber}
                  onChange={(e) => setBizNumber(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base"
                  placeholder="000-00-00000"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">사업자명</label>
                <input
                  type="text"
                  value={bizName}
                  onChange={(e) => setBizName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base"
                  placeholder="예: 모키반점"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">대표자 이름</label>
                <input
                  type="text"
                  value={repName}
                  onChange={(e) => setRepName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">대표자 전화번호</label>
                <input
                  type="text"
                  value={repPhone}
                  onChange={(e) => setRepPhone(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base"
                  placeholder="선택 사항"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">설치 매장명 (공백 불가)</label>
              <input
                type="text"
                value={storeName}
                onChange={(e) => setStoreName(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base"
                placeholder="예: 모키반점강남점 (공백없이 입력)"
                required
              />
            </div>

            {/* 사업자등록증 이미지 업로드 */}
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">사업자등록증 사본 이미지 (최대 2MB)</label>
              <div className="flex items-center space-x-4">
                <input
                  type="file"
                  onChange={handleDocUpload}
                  accept="image/*"
                  id="biz-doc-upload"
                  className="hidden"
                />
                <label
                  htmlFor="biz-doc-upload"
                  className="bg-gray-50 hover:bg-gray-100 text-gray-700 font-bold px-4 py-4 rounded-xl transition-all text-sm flex flex-col items-center justify-center border-2 border-dashed border-gray-300 w-32 h-32 cursor-pointer"
                >
                  {uploadingDoc ? (
                    <Loader2 className="animate-spin text-[#7C3AED]" size={24} />
                  ) : (
                    <>
                      <Upload size={24} className="text-gray-400 mb-1.5" />
                      <span className="text-xs text-gray-500">이미지 업로드</span>
                    </>
                  )}
                </label>

                {docUrl && (
                  <div className="relative w-32 h-32 rounded-xl overflow-hidden border border-gray-200 group">
                    <img src={docUrl.startsWith('http') ? docUrl : `http://localhost:8000${docUrl}`} alt="Business doc" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-black/40 flex justify-center items-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        type="button"
                        onClick={() => setDocUrl('')}
                        className="bg-white/80 p-1.5 rounded-full hover:bg-white text-gray-900 transition-all cursor-pointer"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={uploadingDoc || deletingId !== null}
              className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3.5 rounded-xl transition-colors flex justify-center items-center cursor-pointer shadow-sm text-base"
            >
              사업자 정보 및 매장 추가
            </button>
          </form>
        </div>
      )}

      {/* ⚠️ 회원 탈퇴 섹션 */}
      <div className="bg-red-50 border border-red-200 rounded-2xl p-8 space-y-4 mt-8">
        <div className="flex items-center space-x-2 text-red-700">
          <ShieldAlert size={24} />
          <h3 className="text-xl font-bold">회원 탈퇴</h3>
        </div>
        <p className="text-sm text-red-850">
          회원 탈퇴를 진행하시면 소유하신 모든 매장 정보 및 키오스크 데이터의 사용이 즉시 중지(비활성화)됩니다.<br />
          신중하게 결정해 주시기 바랍니다.
        </p>
        <button
          onClick={() => {
            setDeletePassword('');
            setDeleteError('');
            setIsDeleteUserOpen(true);
          }}
          className="bg-red-600 hover:bg-red-700 text-white font-bold px-6 py-3 rounded-xl transition-colors cursor-pointer text-sm shadow-sm"
        >
          회원 탈퇴 진행하기
        </button>
      </div>

      {/* 회원 탈퇴 최종 확인 모달 */}
      {isDeleteUserOpen && (
        <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8 shadow-xl space-y-6 relative">
            <button
              onClick={() => setIsDeleteUserOpen(false)}
              className="absolute right-6 top-6 text-gray-400 hover:text-gray-650 cursor-pointer"
            >
              <X size={24} />
            </button>
            
            <div className="text-center pb-2">
              <ShieldAlert className="mx-auto text-red-600 mb-3" size={40} />
              <h3 className="text-2xl font-bold text-gray-900">정말 탈퇴하시겠습니까?</h3>
              <p className="text-xs text-gray-400 mt-1.5">MOKI Partner 계정 탈퇴 확인</p>
            </div>

            {deleteError && (
              <div className="bg-red-50 text-red-700 p-4 rounded-xl text-xs font-semibold">
                {deleteError}
              </div>
            )}

            <form onSubmit={handleDeleteUser} className="space-y-4">
              {user.login_provider === 'email' || !user.login_provider ? (
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-2">보안을 위해 비밀번호를 입력해 주세요.</label>
                  <input
                    type="password"
                    value={deletePassword}
                    onChange={(e) => setDeletePassword(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none text-sm font-semibold"
                    placeholder="비밀번호 입력"
                    required
                  />
                </div>
              ) : (
                <div className="bg-gray-50 border border-gray-200 p-4 rounded-2xl text-xs text-gray-600 space-y-2">
                  <p className="font-bold text-gray-700">💬 소셜 연동 계정 안내</p>
                  <p>소셜 연동 계정({user.login_provider === 'kakao' ? '카카오' : '구글'})은 별도의 비밀번호 확인 없이 탈퇴를 완료할 수 있습니다.</p>
                </div>
              )}

              <div className="flex space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsDeleteUserOpen(false)}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-3.5 rounded-xl text-sm transition-colors cursor-pointer"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={isDeletingUser}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-3.5 rounded-xl text-sm transition-all flex justify-center items-center cursor-pointer shadow-sm"
                >
                  {isDeletingUser ? <Loader2 className="animate-spin" size={18} /> : '탈퇴 완료하기'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
