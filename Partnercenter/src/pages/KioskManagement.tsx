import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useKiosk } from '../context/KioskContext';
import { Monitor, Plus, Calendar, Loader2, CheckCircle2, ArrowRightCircle } from 'lucide-react';

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

interface StoreItem {
  id: string;
  name: string;
  owner_name?: string | null;
}

export default function KioskManagement() {
  const { token, user } = useAuth();
  const { currentKioskId, setCurrentKioskId } = useKiosk();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [kiosks, setKiosks] = useState<KioskItem[]>([]);
  const ownerFilter = searchParams.get('ownerName');
  const [stores, setStores] = useState<StoreItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // 등록 모달 상태
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newKioskName, setNewKioskName] = useState('');
  const [newKioskModel, setNewKioskModel] = useState('');
  const [newKioskType, setNewKioskType] = useState('Store');
  const [newKioskStoreId, setNewKioskStoreId] = useState('');
  const [newKioskStatus, setNewKioskStatus] = useState('WAITING');
  const [isCreating, setIsCreating] = useState(false);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      // 1. 키오스크 목록 가져오기
      const kiosksRes = await fetch('/kiosks/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (kiosksRes.status === 403) {
        throw new Error('키오스크 관리 권한이 없습니다 (403).');
      }
      if (!kiosksRes.ok) throw new Error('키오스크 목록을 불러오지 못했습니다.');
      const kiosksData = await kiosksRes.json();
      setKiosks(kiosksData);

      // 2. 사업자 확인 완료 매장 목록 가져오기 (기기 등록용 dropdown 소스)
      const storesRes = await fetch('/kiosks/active-stores', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (storesRes.ok) {
        const storesData = await storesRes.json();
        setStores(storesData);
        if (storesData.length > 0) {
          setNewKioskStoreId(storesData[0].id);
        }
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  // 키오스크 가동상태 토글
  const handleToggleKioskStatus = async (e: React.MouseEvent, kioskId: string, currentStatus: string) => {
    e.stopPropagation();
    const nextStatus = currentStatus === 'OPERATING' ? 'WAITING' : 'OPERATING';
    try {
      const res = await fetch(`/kiosks/${kioskId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: nextStatus })
      });
      if (!res.ok) throw new Error('키오스크 상태 수정에 실패했습니다.');
      
      setKiosks(kiosks.map(k => k.id === kioskId ? { ...k, status: nextStatus } : k));
    } catch (err: any) {
      alert(err.message);
    }
  };

  // 키오스크 기기 추가 처리
  const handleCreateKiosk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKioskStoreId) {
      alert('등록할 매장을 선택해 주세요.');
      return;
    }
    setIsCreating(true);
    try {
      const res = await fetch('/kiosks/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newKioskName,
          model_name: newKioskModel,
          type: newKioskType,
          status: newKioskStatus,
          user_id: newKioskStoreId
        })
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || '키오스크 등록에 실패했습니다.');
      }
      
      setIsModalOpen(false);
      setNewKioskName('');
      setNewKioskModel('');
      setNewKioskType('Store');
      setNewKioskStatus('WAITING');
      fetchData(); // 리스트 리프레시
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteKioskDirect = async (e: React.MouseEvent, kioskId: string) => {
    e.stopPropagation();
    if (!window.confirm('정말로 이 키오스크 기기를 삭제하시겠습니까? 기기에 등록된 상품 매핑 정보가 모두 소멸됩니다.')) return;
    try {
      const res = await fetch(`/kiosks/${kioskId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('기기 삭제에 실패했습니다.');
      
      alert('키오스크가 성공적으로 삭제되었습니다.');
      if (currentKioskId === kioskId) {
        setCurrentKioskId('');
        localStorage.removeItem('currentKioskId');
        localStorage.removeItem('currentKioskName');
      }
      fetchData(); // Refresh list
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleSwitchKiosk = (kioskId: string) => {
    setCurrentKioskId(kioskId);
    window.location.href = '/';
  };

  const ownerStoreIds = ownerFilter
    ? stores.filter(s => s.owner_name === ownerFilter).map(s => s.id)
    : [];

  const filteredKiosks = ownerFilter
    ? kiosks.filter(k => ownerStoreIds.includes(k.user_id))
    : kiosks;

  if (isLoading) {
    return (
      <div className="flex-grow p-8 flex justify-center items-center h-full">
        <Loader2 className="animate-spin text-[#7C3AED]" size={48} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-grow p-8 flex flex-col justify-center items-center h-full">
        <div className="bg-red-50 text-red-700 px-6 py-4 rounded-2xl shadow-sm text-center max-w-md">
          <h3 className="text-xl font-bold mb-2">접근 권한 제한</h3>
          <p className="text-sm font-medium">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-1">키오스크 기기 관리</h1>
          <p className="text-gray-500 text-base">각 가맹점 매장의 키오스크 기기를 추가하고 상태를 조회합니다.</p>
        </div>
        {(stores.length > 0 || user?.role === 'DEV' || user?.role === 'HEAD') && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center space-x-2 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold px-5 py-3 rounded-xl transition-all shadow-sm cursor-pointer"
          >
            <Plus size={20} />
            <span>신규 기기 등록</span>
          </button>
        )}
      </div>

      {ownerFilter && (
        <div className="bg-[#7C3AED]/5 text-[#7C3AED] px-5 py-3 rounded-2xl flex justify-between items-center text-sm font-semibold border border-[#7C3AED]/10 animate-fade-in">
          <span>🎯 점주 [{ownerFilter}] 사장님의 키오스크 목록만 필터링되어 보여집니다.</span>
          <button 
            onClick={() => setSearchParams({})} 
            className="bg-white hover:bg-gray-50 border border-gray-200 text-gray-700 px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition-colors"
          >
            필터 해제
          </button>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-100">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100 text-gray-600 font-semibold text-sm">
                <th className="px-6 py-4 text-center">선택</th>
                <th className="px-6 py-4">기기 ID (고유코드)</th>
                <th className="px-6 py-4">매장명</th>
                <th className="px-6 py-4">키오스크명</th>
                <th className="px-6 py-4">모델명</th>
                <th className="px-6 py-4">구분</th>
                <th className="px-6 py-4">가동 상태</th>
                <th className="px-6 py-4">결제 상태</th>
                <th className="px-6 py-4">다음 결제 예정일</th>
                {(user?.role === 'DEV' || user?.role === 'HEAD') && <th className="px-6 py-4 text-center">작업</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700">
              {filteredKiosks.length === 0 ? (
                <tr>
                  <td colSpan={(user?.role === 'DEV' || user?.role === 'HEAD') ? 10 : 9} className="text-center py-12 text-gray-400 font-medium">
                    {ownerFilter ? `[${ownerFilter}] 사장님의 등록된 키오스크 기기가 없습니다.` : '등록된 키오스크 기기가 없습니다.'}
                  </td>
                </tr>
              ) : (
                filteredKiosks.map((kiosk) => (
                  <tr 
                    key={kiosk.id} 
                    className="hover:bg-gray-50/50 transition-colors"
                  >
                    <td className="px-6 py-4 text-center">
                      {kiosk.id === currentKioskId ? (
                        <div className="inline-flex items-center space-x-1.5 bg-green-50 text-green-700 px-3 py-1.5 rounded-full text-xs font-bold border border-green-100">
                          <CheckCircle2 size={14} className="text-green-500" />
                          <span>현재 키오스크</span>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleSwitchKiosk(kiosk.id)}
                          className="inline-flex items-center space-x-1.5 bg-gray-50 hover:bg-[#7C3AED]/10 text-gray-700 hover:text-[#7C3AED] px-3 py-1.5 rounded-full text-xs font-bold border border-gray-200 hover:border-[#7C3AED]/30 transition-all cursor-pointer"
                        >
                          <ArrowRightCircle size={14} />
                          <span>관리 가기</span>
                        </button>
                      )}
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-[#7C3AED]">
                      <button 
                        onClick={() => navigate(`/kiosks/${kiosk.id}`)}
                        className="hover:underline cursor-pointer text-left"
                      >
                        {kiosk.code}
                      </button>
                    </td>
                    <td className="px-6 py-4 font-semibold text-gray-900">
                      <button
                        onClick={() => handleSwitchKiosk(kiosk.id)}
                        className="hover:underline hover:text-[#7C3AED] cursor-pointer text-left font-bold"
                      >
                        {kiosk.store_name || '-'}
                      </button>
                    </td>
                    <td className="px-6 py-4 font-medium text-gray-800">{kiosk.name}</td>
                    <td className="px-6 py-4 text-gray-500">{kiosk.model_name || '-'}</td>
                    <td className="px-6 py-4 text-sm font-semibold">
                      <span className={`px-3 py-1 rounded-full text-xs ${
                        kiosk.type === 'Restaurant' 
                          ? 'bg-orange-50 text-orange-600' 
                          : 'bg-blue-50 text-blue-600'
                      }`}>
                        {kiosk.type === 'Restaurant' ? '외식형' : '판매형'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={(e) => handleToggleKioskStatus(e, kiosk.id, kiosk.status)}
                        className="flex items-center space-x-1.5 hover:bg-gray-100 px-3 py-1.5 rounded-full transition-colors cursor-pointer"
                        title="기기 가동상태 전환"
                      >
                        <span className={`w-2.5 h-2.5 rounded-full ${
                          kiosk.status === 'OPERATING' ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'
                        }`} />
                        <span className={`text-xs font-bold ${
                          kiosk.status === 'OPERATING' ? 'text-green-600' : 'text-yellow-600'
                        }`}>
                          {kiosk.status === 'OPERATING' ? '가동 중' : '대기 중'}
                        </span>
                      </button>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        kiosk.payment_status === 'NORMAL' 
                          ? 'bg-blue-50 text-blue-600' 
                          : 'bg-red-50 text-red-600'
                      }`}>
                        {kiosk.payment_status === 'NORMAL' ? '정상' : '체납(UNPAID)'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      <div className="flex items-center space-x-1">
                        <Calendar size={14} className="text-gray-400" />
                        <span>{kiosk.next_payment_date ? new Date(kiosk.next_payment_date).toLocaleDateString() : '-'}</span>
                      </div>
                    </td>
                    {(user?.role === 'DEV' || user?.role === 'HEAD') && (
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={(e) => handleDeleteKioskDirect(e, kiosk.id)}
                          className="bg-red-50 hover:bg-red-100 text-red-600 px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer"
                        >
                          삭제
                        </button>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 등록 모달 */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-8 shadow-xl space-y-6">
            <div>
              <h3 className="text-2xl font-bold text-gray-900">신규 키오스크 기기 등록</h3>
              <p className="text-gray-500 text-sm mt-1">소속 매장을 지정하고 새 키오스크 기기 사양을 등록합니다.</p>
            </div>
            
            <form onSubmit={handleCreateKiosk} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">소속 매장</label>
                <select
                  value={newKioskStoreId}
                  onChange={(e) => setNewKioskStoreId(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none bg-white font-medium text-gray-800"
                  required
                >
                  {stores.length === 0 ? (
                    <option value="">(등록된 가용 점주가 없습니다)</option>
                  ) : (
                    stores.map(store => (
                      <option key={store.id} value={store.id}>{store.name}</option>
                    ))
                  )}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">기기명</label>
                <input
                  type="text"
                  value={newKioskName}
                  onChange={(e) => setNewKioskName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  placeholder="예: 1호기 입구측"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">모델명</label>
                <input
                  type="text"
                  value={newKioskModel}
                  onChange={(e) => setNewKioskModel(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  placeholder="예: Samsung KM24A-21"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">유형</label>
                  <select
                    value={newKioskType}
                    onChange={(e) => setNewKioskType(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none bg-white"
                  >
                    <option value="Store">일반 판매형(Store)</option>
                    <option value="Restaurant">외식 푸드코트형(Restaurant)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">기본 가동상태</label>
                  <select
                    value={newKioskStatus}
                    onChange={(e) => setNewKioskStatus(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none bg-white"
                  >
                    <option value="WAITING">대기 중(WAITING)</option>
                    <option value="OPERATING">가동 중(OPERATING)</option>
                  </select>
                </div>
              </div>

              <div className="flex space-x-3 pt-4 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-3 rounded-xl transition-colors cursor-pointer text-center"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={isCreating}
                  className="flex-1 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3 rounded-xl transition-colors flex justify-center items-center cursor-pointer"
                >
                  {isCreating ? <Loader2 className="animate-spin" size={20} /> : '등록하기'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
