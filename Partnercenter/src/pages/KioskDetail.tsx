import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowLeft, Trash2, Edit, Calendar, ShieldCheck, Loader2 } from 'lucide-react';

interface KioskItem {
  id: string;
  code: string;
  store_id: string;
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
        // yyyy-MM-dd 포맷팅
        setNextPaymentDate(data.next_payment_date.split('T')[0]);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchKioskData();
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
      
      navigate(`/stores/${kiosk?.store_id}`); // 삭제 성공 시 소속 매장 상세로 귀환
    } catch (err: any) {
      alert(err.message);
      setIsDeleting(false);
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

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8 pb-20">
      {/* 뒤로가기 버튼 */}
      <button
        onClick={() => navigate(`/stores/${kiosk.store_id}`)}
        className="flex items-center space-x-2 text-gray-600 hover:text-[#7C3AED] font-semibold transition-colors cursor-pointer"
      >
        <ArrowLeft size={20} />
        <span>매장 상세 보기로</span>
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
            <p className="text-gray-500 font-medium">소속 매장: <span className="text-[#7C3AED] font-bold">{kiosk.store_name}</span></p>
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
    </div>
  );
}
