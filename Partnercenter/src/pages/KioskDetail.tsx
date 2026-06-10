import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowLeft, Trash2, Edit, Calendar, ShieldCheck, Loader2 } from 'lucide-react';

interface KioskItem {
  id: string;
  code: string;
  user_id: string;
  store_name: string | null;
  name: string;
  model_name: string | null;
  type: string;
  status: string;
  payment_status: string;
  next_payment_date: string | null;
  created_at: string;
}

export default function KioskDetail() {
  const { id } = useParams<{ id: string }>();
  const { token, user } = useAuth();
  const navigate = useNavigate();

  const [kiosk, setKiosk] = useState<KioskItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // 결제정보 수정 입력 폼 상태
  const [paymentStatus, setPaymentStatus] = useState('NORMAL');
  const [nextPaymentDate, setNextPaymentDate] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateMsg, setUpdateMsg] = useState({ text: '', type: '' });

  // 삭제 진행 상태
  const [isDeleting, setIsDeleting] = useState(false);

  // 기기 관리자 목록 관련 상태
  const [admins, setAdmins] = useState<any[]>([]);
  const [isAddAdminModalOpen, setIsAddAdminModalOpen] = useState(false);
  const [addEmail, setAddEmail] = useState('');
  const [addRole, setAddRole] = useState('STAFF');
  const [isAddingAdmin, setIsAddingAdmin] = useState(false);
  const [adminError, setAdminError] = useState('');

  // 권한 검증: DEV 또는 HEAD 권한인지 체크
  const hasBillingEditAuth = user?.role === 'DEV' || user?.role === 'HEAD';

  const fetchKioskData = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`/kiosks/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('키오스크 정보를 불러오지 못했습니다.');
      const data = await res.json();
      setKiosk(data);
      setPaymentStatus(data.payment_status);
      if (data.next_payment_date) {
        setNextPaymentDate(data.next_payment_date.split('T')[0]);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAdmins = async () => {
    try {
      const res = await fetch(`/kiosks/${id}/admins`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAdmins(data);
      }
    } catch (err) {
      console.error('Failed to fetch kiosk admins:', err);
    }
  };

  useEffect(() => {
    fetchKioskData();
    fetchAdmins();
  }, [id, token]);

  // 결제 정보 수정 제출 (PATCH)
  const handleUpdateBilling = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasBillingEditAuth) return;
    setIsUpdating(true);
    setUpdateMsg({ text: '저장 중...', type: 'info' });
    try {
      const formattedDate = nextPaymentDate ? new Date(nextPaymentDate).toISOString() : null;
      const res = await fetch(`/kiosks/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          payment_status: paymentStatus,
          next_payment_date: formattedDate
        })
      });
      if (!res.ok) throw new Error('결제 정보 수정을 실패했습니다.');
      
      setUpdateMsg({ text: '결제 정보가 성공적으로 업데이트되었습니다.', type: 'success' });
      fetchKioskData(); // 최신 데이터로 리프레시
      setTimeout(() => setUpdateMsg({ text: '', type: '' }), 3000);
    } catch (err: any) {
      setUpdateMsg({ text: err.message, type: 'error' });
    } finally {
      setIsUpdating(false);
    }
  };

  // 키오스크 기기 삭제
  const handleDeleteKiosk = async () => {
    if (!window.confirm('정말로 이 키오스크 기기를 삭제하시겠습니까? 기기에 등록된 상품 매핑 정보가 모두 소멸됩니다.')) return;
    setIsDeleting(true);
    try {
      const res = await fetch(`/kiosks/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('기기 삭제에 실패했습니다.');
      
      navigate('/kiosks'); // 삭제 성공 시 키오스크 목록으로 귀환
    } catch (err: any) {
      alert(err.message);
      setIsDeleting(false);
    }
  };

  const handleAddAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAddingAdmin(true);
    setAdminError('');
    try {
      const res = await fetch(`/kiosks/${id}/admins`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ email: addEmail, role: addRole })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '관리자 추가에 실패했습니다.');
      
      setAddEmail('');
      setAddRole('STAFF');
      setIsAddAdminModalOpen(false);
      fetchAdmins();
    } catch (err: any) {
      setAdminError(err.message);
    } finally {
      setIsAddingAdmin(false);
    }
  };

  const handleUpdateAdminRole = async (userId: string, newRole: string) => {
    try {
      const res = await fetch(`/kiosks/${id}/admins/${userId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ role: newRole })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '권한 변경에 실패했습니다.');
      fetchAdmins();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDeleteAdmin = async (userId: string) => {
    if (!window.confirm('정말 이 관리자를 기기 관리자 목록에서 제외하시겠습니까?')) return;
    try {
      const res = await fetch(`/kiosks/${id}/admins/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || '관리자 제외에 실패했습니다.');
      }
      fetchAdmins();
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-grow p-8 flex justify-center items-center h-full">
        <Loader2 className="animate-spin text-[#7C3AED]" size={48} />
      </div>
    );
  }

  if (error || !kiosk) {
    return (
      <div className="flex-grow p-8 flex flex-col justify-center items-center h-full">
        <div className="bg-red-50 text-red-700 px-6 py-4 rounded-2xl shadow-sm text-center">
          <h3 className="text-xl font-bold mb-2">오류 발생</h3>
          <p className="text-sm font-medium">{error || '키오스크 기기를 찾을 수 없습니다.'}</p>
          <button 
            onClick={() => navigate('/kiosks')}
            className="mt-4 bg-red-600 hover:bg-red-700 text-white font-semibold px-4 py-2 rounded-xl transition-colors cursor-pointer"
          >
            기기 목록으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  const roleLevels: Record<string, number> = {
    'DEV': 5,
    'HEAD': 4,
    'MASTER': 3,
    'MANAGER': 2,
    'STAFF': 1
  };

  const getMyRoleOnKiosk = () => {
    if (user?.role === 'DEV') return 'DEV';
    if (user?.role === 'HEAD') return 'HEAD';
    const myRec = admins.find(a => a.user_id === user?.id);
    return myRec ? myRec.role : 'STAFF';
  };

  const myRole = getMyRoleOnKiosk();
  const myLevel = roleLevels[myRole] || 1;

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8 pb-20">
      {/* 뒤로가기 버튼 */}
      <button
        onClick={() => navigate('/kiosks')}
        className="flex items-center space-x-2 text-gray-600 hover:text-[#7C3AED] font-semibold transition-colors cursor-pointer"
      >
        <ArrowLeft size={20} />
        <span>키오스크 목록으로 돌아가기</span>
      </button>

      {/* 기기 정보 요약 카드 */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 space-y-6">
        <div className="flex justify-between items-start">
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <span className="bg-[#7C3AED]/10 text-[#7C3AED] px-4 py-1.5 rounded-full text-sm font-bold font-mono">
                {kiosk.code}
              </span>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                kiosk.status === 'OPERATING' ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'
              }`}>
                {kiosk.status === 'OPERATING' ? '가동 중' : '대기 중'}
              </span>
            </div>
            <h1 className="text-3xl font-extrabold text-gray-900">{kiosk.name}</h1>
            <p className="text-gray-500 font-medium">가맹 매장명: <span className="text-[#7C3AED] font-bold">{kiosk.store_name}</span></p>
          </div>

          <button
            onClick={handleDeleteKiosk}
            disabled={isDeleting}
            className="flex items-center space-x-2 bg-red-50 hover:bg-red-100 text-red-600 font-bold px-4 py-3 rounded-xl transition-all cursor-pointer text-sm"
          >
            <Trash2 size={16} />
            <span>기기 철수 (삭제)</span>
          </button>
        </div>

        <div className="grid grid-cols-2 gap-6 pt-4 border-t border-gray-100 text-sm text-gray-600">
          <div>모델명: <span className="text-gray-950 font-bold ml-1">{kiosk.model_name || '-'}</span></div>
          <div>구분: <span className="text-gray-950 font-bold ml-1">{kiosk.type === 'Restaurant' ? '외식 푸드코트형' : '일반 판매형'}</span></div>
          <div>최초 등록일: <span className="text-gray-950 font-bold ml-1">{new Date(kiosk.created_at).toLocaleDateString()}</span></div>
        </div>
      </div>

      {/* 결제 정보 수정 카드 */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 space-y-6">
        <div>
          <h3 className="text-2xl font-bold text-gray-900 flex items-center">
            <ShieldCheck className="mr-2 text-[#7C3AED]" size={26} /> 기기 라이선스 및 결제 상태 설정
          </h3>
          {!hasBillingEditAuth && (
            <p className="text-red-500 text-sm font-semibold mt-1">
              ⚠️ 해당 정보 변경 권한은 본사(HEAD) 또는 개발자(DEV) 권한 계정으로 로그인한 경우에만 편집할 수 있습니다. (현재 계정 권한: {user?.role})
            </p>
          )}
          {hasBillingEditAuth && (
            <p className="text-gray-500 text-sm mt-1">본사 권한으로 가맹 기기의 결제 체납 처리 및 라이선스 갱신일을 직접 수정할 수 있습니다.</p>
          )}
        </div>

        <form onSubmit={handleUpdateBilling} className="space-y-6 max-w-lg">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">결제 상태</label>
            <select
              value={paymentStatus}
              onChange={(e) => setPaymentStatus(e.target.value)}
              disabled={!hasBillingEditAuth}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none bg-white disabled:bg-gray-50 disabled:text-gray-400 font-semibold"
            >
              <option value="NORMAL">정상 납부 (NORMAL)</option>
              <option value="UNPAID">체납 상태 (UNPAID)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">다음 결제 예정일</label>
            <div className="relative">
              <input
                type="date"
                value={nextPaymentDate}
                onChange={(e) => setNextPaymentDate(e.target.value)}
                disabled={!hasBillingEditAuth}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none disabled:bg-gray-50 disabled:text-gray-400 font-semibold"
              />
            </div>
          </div>

          {updateMsg.text && (
            <p className={`text-sm font-semibold ${
              updateMsg.type === 'error' 
                ? 'text-red-500' 
                : updateMsg.type === 'success' 
                  ? 'text-green-500' 
                  : 'text-blue-500'
            }`}>
              {updateMsg.text}
            </p>
          )}

          {hasBillingEditAuth && (
            <button
              type="submit"
              disabled={isUpdating}
              className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3 rounded-xl transition-all flex justify-center items-center cursor-pointer shadow-sm"
            >
              {isUpdating ? <Loader2 className="animate-spin" size={20} /> : '변경사항 저장하기'}
            </button>
          )}
        </form>
      </div>

      {/* 👥 기기 관리자 리스트 카드 */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 space-y-6">
        <div className="flex justify-between items-center border-b border-gray-100 pb-4">
          <div>
            <h3 className="text-2xl font-bold text-gray-900 flex items-center">
              <ShieldCheck className="mr-2 text-[#7C3AED]" size={26} /> 기기 관리자 설정
            </h3>
            <p className="text-gray-500 text-sm mt-1">이 키오스크를 스위칭하여 상품 관리 및 통계를 모니터링할 수 있는 사용자(직원 등) 목록입니다.</p>
          </div>
          {myLevel > 1 && (
            <button
              onClick={() => setIsAddAdminModalOpen(true)}
              className="bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold px-4 py-2.5 rounded-xl transition-all shadow-sm cursor-pointer text-sm"
            >
              관리자 추가
            </button>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-gray-100 text-gray-500 font-semibold text-sm">
                <th className="py-3 px-4">이름</th>
                <th className="py-3 px-4">이메일</th>
                <th className="py-3 px-4">연락처</th>
                <th className="py-3 px-4">기기 관리 권한</th>
                {myLevel > 1 && <th className="py-3 px-4 text-center">관리</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700">
              {admins.length === 0 ? (
                <tr>
                  <td colSpan={myLevel > 1 ? 5 : 4} className="text-center py-8 text-gray-400 font-medium">
                    등록된 관리자가 없습니다.
                  </td>
                </tr>
              ) : (
                admins.map((admin) => {
                  const targetLevel = roleLevels[admin.role] || 1;
                  const canEdit = myLevel > targetLevel || user?.role === 'DEV';
                  
                  return (
                    <tr key={admin.user_id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="py-4 px-4 font-bold text-gray-900">{admin.name}</td>
                      <td className="py-4 px-4 text-gray-600">{admin.email}</td>
                      <td className="py-4 px-4 text-gray-500">{admin.phone || '-'}</td>
                      <td className="py-4 px-4">
                        {canEdit ? (
                          <select
                            value={admin.role}
                            onChange={(e) => handleUpdateAdminRole(admin.user_id, e.target.value)}
                            className="px-2 py-1 border border-gray-300 bg-white rounded-lg focus:ring-1 focus:ring-[#7C3AED] outline-none text-xs font-semibold text-gray-800"
                          >
                            <option value="STAFF">STAFF (스태프)</option>
                            <option value="MANAGER">MANAGER (매니저)</option>
                            <option value="MASTER">MASTER (점주/마스터)</option>
                            {myLevel >= 4 && <option value="HEAD">HEAD (본사)</option>}
                            {myLevel >= 5 && <option value="DEV">DEV (개발자)</option>}
                          </select>
                        ) : (
                          <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                            admin.role === 'DEV' ? 'bg-purple-100 text-purple-700' :
                            admin.role === 'MASTER' ? 'bg-red-100 text-red-700' :
                            admin.role === 'HEAD' ? 'bg-blue-100 text-blue-700' :
                            admin.role === 'MANAGER' ? 'bg-orange-100 text-orange-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {admin.role}
                          </span>
                        )}
                      </td>
                      {myLevel > 1 && (
                        <td className="py-4 px-4 text-center">
                          {(canEdit || admin.user_id === user?.id) && (
                            <button
                              onClick={() => handleDeleteAdmin(admin.user_id)}
                              className="text-red-500 hover:text-red-700 hover:bg-red-50 px-2.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer"
                            >
                              제외
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ➕ 관리자 추가 모달 */}
      {isAddAdminModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8 shadow-xl space-y-6">
            <div>
              <h3 className="text-2xl font-bold text-gray-900">기기 관리자 추가</h3>
              <p className="text-gray-500 text-sm mt-1">이메일로 등록된 회원을 검색하여 이 기기의 관리 권한을 부여합니다.</p>
            </div>

            {adminError && (
              <div className="bg-red-50 text-red-700 p-4 rounded-xl text-sm font-semibold">
                {adminError}
              </div>
            )}

            <form onSubmit={handleAddAdmin} className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1.5">회원 이메일</label>
                <input
                  type="email"
                  value={addEmail}
                  onChange={(e) => setAddEmail(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base"
                  placeholder="name@example.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1.5">관리 권한 (Role)</label>
                <select
                  value={addRole}
                  onChange={(e) => setAddRole(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 bg-white rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none font-semibold text-gray-800"
                >
                  <option value="STAFF">STAFF (기본 권한: 상품 조회 등)</option>
                  {myLevel >= 2 && <option value="MANAGER">MANAGER (매니저 권한)</option>}
                  {myLevel >= 3 && <option value="MASTER">MASTER (기기 마스터 권한)</option>}
                </select>
              </div>

              <div className="flex space-x-3 pt-4 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setIsAddAdminModalOpen(false)}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-3 rounded-xl transition-colors cursor-pointer text-center"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={isAddingAdmin}
                  className="flex-1 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3 rounded-xl transition-colors flex justify-center items-center cursor-pointer"
                >
                  {isAddingAdmin ? <Loader2 className="animate-spin" size={20} /> : '추가하기'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
