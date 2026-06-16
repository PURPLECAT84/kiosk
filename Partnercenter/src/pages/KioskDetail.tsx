import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowLeft, Trash2, Edit, Calendar, ShieldCheck, Loader2, CreditCard, Sparkles, Check, X, Layers } from 'lucide-react';

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
  billing_key: string | null;
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

  // 정기결제/단일결제 진행 상태 및 상품 선택 상태
  const [isSubscribing, setIsSubscribing] = useState(false);
  const [billingProducts, setBillingProducts] = useState<any[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<number | ''>('');
  const [isOnetimeModalOpen, setIsOnetimeModalOpen] = useState(false);
  const [isVerifyingOnetime, setIsVerifyingOnetime] = useState(false);

  // 가상 결제창 카드 입력 정보 상태
  const [cardNum, setCardNum] = useState('');
  const [cardExpiry, setCardExpiry] = useState('');
  const [cardCvc, setCardCvc] = useState('');

  const fetchBillingProducts = async () => {
    try {
      const res = await fetch('/subscribe/products', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setBillingProducts(data);
        if (data.length > 0) {
          // 기본 선택값 설정 (노출 활성화된 상품 중 첫번째)
          const firstActive = data.find((p: any) => p.is_active);
          if (firstActive) {
            setSelectedProductId(firstActive.id);
          }
        }
      }
    } catch (err) {
      console.error('Failed to fetch billing products:', err);
    }
  };

  const handleRegisterCard = async () => {
    if (!selectedProductId) {
      alert('연동할 요금제 상품을 선택해주세요.');
      return;
    }
    const product = billingProducts.find(p => p.id === selectedProductId);
    if (!product) return;
    if (product.billing_type !== 'REGULAR') {
      alert('정기 구독형 요금 상품이 아닙니다. 단일결제 버튼을 눌러주세요.');
      return;
    }

    setIsSubscribing(true);
    try {
      const res = await fetch('/subscribe/billing-key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          kiosk_id: id,
          customer_uid: `customer_${user?.id}_${id}`,
          billing_product_id: product.id
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || '정기결제 카드 연동에 실패했습니다.');
      }
      alert('사용료 정기 결제 카드가 정상 등록되었으며 기기가 활성화되었습니다!');
      fetchKioskData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsSubscribing(false);
    }
  };

  const handleOnetimePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductId) return;
    const product = billingProducts.find(p => p.id === selectedProductId);
    if (!product) return;

    setIsVerifyingOnetime(true);
    try {
      // 로컬 개발 환경용 랜덤 mock paymentId 생성
      const mockPaymentId = 'pay_one_' + Math.random().toString(36).substring(2, 9) + Math.random().toString(36).substring(2, 9);
      
      const res = await fetch('/subscribe/onetime-verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          kiosk_id: id,
          payment_id: mockPaymentId,
          billing_product_id: product.id
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || '단일결제 승인 검증에 실패했습니다.');
      }
      const resData = await res.json();
      alert(resData.message || '단일결제가 성공적으로 승인 및 검증 완료되었습니다!');
      setIsOnetimeModalOpen(false);
      setCardNum('');
      setCardExpiry('');
      setCardCvc('');
      fetchKioskData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsVerifyingOnetime(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!window.confirm('정기 결제를 해지하시겠습니까? 해지 즉시 기기 가동이 정지됩니다.')) return;
    setIsSubscribing(true);
    try {
      const res = await fetch(`/subscribe/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || '정기결제 해지에 실패했습니다.');
      }
      alert('정기결제가 정상적으로 해지되었습니다.');
      fetchKioskData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsSubscribing(false);
    }
  };

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
    fetchBillingProducts();
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

      {/* 결제 정보 수정 및 기기 정기 구독 카드 */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 space-y-6">
        <div>
          <h3 className="text-2xl font-bold text-gray-900 flex items-center">
            <ShieldCheck className="mr-2 text-[#7C3AED]" size={26} /> {hasBillingEditAuth ? '기기 라이선스 및 결제 상태 설정 (본사 전용)' : '기기 라이선스 및 정기결제 관리'}
          </h3>
          <p className="text-gray-500 text-sm mt-1">
            {hasBillingEditAuth 
              ? '본사 권한으로 가맹 기기의 결제 체납 처리 및 라이선스 갱신일을 직접 수정할 수 있습니다.'
              : '키오스크 서비스 월 가동 사용료 정기 구독 상태를 모니터링하고 카드를 등록/해지합니다.'}
          </p>
        </div>

        {hasBillingEditAuth ? (
          <form onSubmit={handleUpdateBilling} className="space-y-6 max-w-lg">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">결제 상태</label>
              <select
                value={paymentStatus}
                onChange={(e) => setPaymentStatus(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none bg-white font-semibold"
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
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none font-semibold"
                />
              </div>
            </div>

            {updateMsg.text && (
              <p className={`text-sm font-semibold ${
                updateMsg.type === 'error' ? 'text-red-500' : updateMsg.type === 'success' ? 'text-green-500' : 'text-blue-500'
              }`}>
                {updateMsg.text}
              </p>
            )}

            <button
              type="submit"
              disabled={isUpdating}
              className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3 rounded-xl transition-all flex justify-center items-center cursor-pointer shadow-sm"
            >
              {isUpdating ? <Loader2 className="animate-spin" size={20} /> : '변경사항 저장하기'}
            </button>
          </form>
        ) : (
          <div className="space-y-6 max-w-2xl">
            {/* 정기 결제 상태 카드 */}
            {kiosk.billing_key ? (
              <div className="bg-green-50 border border-green-100 rounded-3xl p-6 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-green-800 font-bold text-base flex items-center">
                    <span className="w-2.5 h-2.5 rounded-full bg-green-500 mr-2.5 animate-pulse" />
                    정기결제 구독 활성화됨 (정상)
                  </span>
                  <span className="text-xs text-gray-400 font-mono select-all">{kiosk.billing_key.substring(0, 15)}...</span>
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>정기결제 정보: <span className="font-bold text-gray-900">등록 완료</span></div>
                  <div>다음 결제 예정일: <span className="font-bold text-gray-900">{kiosk.next_payment_date ? new Date(kiosk.next_payment_date).toLocaleDateString() : '-'}</span></div>
                </div>
                <button
                  onClick={handleCancelSubscription}
                  disabled={isSubscribing}
                  className="w-full bg-red-50 hover:bg-red-100/70 border border-red-200/50 text-red-600 font-bold py-3.5 rounded-xl transition-all cursor-pointer text-center text-sm"
                >
                  {isSubscribing ? <Loader2 className="animate-spin" size={20} /> : '정기결제 카드 해지 (기기 정지)'}
                </button>
              </div>
            ) : (
              <div className="bg-red-50 border border-red-100 rounded-3xl p-6 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-red-800 font-bold text-base flex items-center">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500 mr-2.5 animate-pulse" />
                    사용료 결제 대기 / 정지 상태
                  </span>
                  {kiosk.next_payment_date && (
                    <span className="text-xs text-red-600 font-bold">만료일: {new Date(kiosk.next_payment_date).toLocaleDateString()}</span>
                  )}
                </div>
                <p className="text-xs text-red-500 font-medium">
                  현재 카드가 등록되지 않았거나 요금이 미납 상태입니다. 기기 연동 및 상품 동기화를 활성화하려면 아래 요금제 상품 중 하나를 선택하여 결제를 진행해주세요.
                </p>
              </div>
            )}

            {/* 이용 요금제 상품 선택 리스트 */}
            {!kiosk.billing_key && (
              <div className="space-y-4">
                <h4 className="text-sm font-bold text-gray-700 flex items-center gap-1.5">
                  <Layers size={16} className="text-[#7C3AED]" />
                  이용 요금제 상품 선택
                </h4>
                
                {billingProducts.length === 0 ? (
                  <p className="text-xs text-gray-400 py-6 text-center border border-dashed border-gray-200 rounded-2xl">
                    활성화된 본사 요금제 상품이 없습니다. 관리자에게 문의해 주세요.
                  </p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {billingProducts.map((prod) => {
                      if (!prod.is_active) return null;
                      const isSelected = selectedProductId === prod.id;
                      
                      return (
                        <div
                          key={prod.id}
                          onClick={() => setSelectedProductId(prod.id)}
                          className={`p-5 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between space-y-3 relative ${
                            isSelected 
                              ? 'border-[#7C3AED] bg-purple-50/30' 
                              : 'border-gray-200 bg-white hover:border-gray-300'
                          }`}
                        >
                          {isSelected && (
                            <span className="absolute top-4 right-4 bg-[#7C3AED] text-white p-0.5 rounded-full">
                              <Check size={12} />
                            </span>
                          )}
                          <div>
                            <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-bold ${
                              prod.billing_type === 'REGULAR' 
                                ? 'bg-purple-100 text-[#7C3AED]' 
                                : 'bg-blue-100 text-blue-600'
                            }`}>
                              {prod.billing_type === 'REGULAR' ? '정기결제 (구독)' : '단일결제 (1회권)'}
                            </span>
                            <h5 className="font-extrabold text-gray-900 mt-2 text-sm line-clamp-1">{prod.name}</h5>
                            <p className="text-[10px] text-gray-400 mt-0.5">이용 기간: {prod.period_months}개월</p>
                          </div>
                          
                          <div className="text-right">
                            <span className="text-base font-extrabold text-gray-900">₩{prod.amount.toLocaleString()}</span>
                            <span className="text-[10px] text-gray-400 font-medium"> / 총액</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* 선택한 상품에 따른 결제 버튼 */}
                {selectedProductId && (
                  <div className="pt-2">
                    {billingProducts.find(p => p.id === selectedProductId)?.billing_type === 'REGULAR' ? (
                      <button
                        onClick={handleRegisterCard}
                        disabled={isSubscribing}
                        className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3.5 rounded-xl transition-all flex justify-center items-center cursor-pointer shadow-sm text-sm"
                      >
                        {isSubscribing ? <Loader2 className="animate-spin" size={20} /> : '정기결제 카드 등록 및 활성화'}
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          setCardNum('');
                          setCardExpiry('');
                          setCardCvc('');
                          setIsOnetimeModalOpen(true);
                        }}
                        className="w-full bg-[#3B82F6] hover:bg-[#2563EB] text-white font-bold py-3.5 rounded-xl transition-all flex justify-center items-center cursor-pointer shadow-sm text-sm"
                      >
                        <CreditCard size={16} className="mr-2" />
                        단일 결제 진행하기 (1회성)
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
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

      {/* 💳 단일결제 가상 카드 입력 모달 */}
      {isOnetimeModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] z-50 flex justify-center items-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl border border-gray-100 space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-2xl font-extrabold text-gray-900 flex items-center gap-2">
                <Sparkles className="text-[#7C3AED]" size={22} />
                단일결제 진행 (시뮬레이터)
              </h3>
              <button onClick={() => setIsOnetimeModalOpen(false)} className="p-1.5 hover:bg-gray-100 rounded-full cursor-pointer">
                <X size={20} className="text-gray-500" />
              </button>
            </div>

            <div className="bg-purple-50 text-[#7C3AED] p-4 rounded-2xl text-xs font-semibold space-y-1">
              <p>📌 결제 예정 상품: <span className="font-extrabold">{billingProducts.find(p => p.id === selectedProductId)?.name}</span></p>
              <p>💰 결제 금액: <span className="font-extrabold">₩{billingProducts.find(p => p.id === selectedProductId)?.amount.toLocaleString()}</span></p>
            </div>

            <form onSubmit={handleOnetimePayment} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">카드 번호</label>
                <input
                  type="text"
                  value={cardNum}
                  onChange={(e) => setCardNum(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-sm font-semibold"
                  placeholder="xxxx-xxxx-xxxx-xxxx"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">유효기간</label>
                  <input
                    type="text"
                    value={cardExpiry}
                    onChange={(e) => setCardExpiry(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-sm font-semibold"
                    placeholder="MM/YY"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">CVC</label>
                  <input
                    type="password"
                    maxLength={3}
                    value={cardCvc}
                    onChange={(e) => setCardCvc(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-sm font-semibold"
                    placeholder="3자리"
                    required
                  />
                </div>
              </div>

              <div className="flex space-x-3 pt-4 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setIsOnetimeModalOpen(false)}
                  className="flex-1 bg-gray-150 hover:bg-gray-200 text-gray-700 font-bold py-3.5 rounded-xl transition-colors cursor-pointer text-sm text-center"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={isVerifyingOnetime}
                  className="flex-1 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-bold py-3.5 rounded-xl transition-all flex justify-center items-center cursor-pointer shadow-md text-sm"
                >
                  {isVerifyingOnetime ? <Loader2 className="animate-spin" size={18} /> : '결제 승인 요청'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
