import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowLeft, Trash2, Edit, Monitor, AlertTriangle, Calendar, Loader2 } from 'lucide-react';

interface StoreItem {
  id: string;
  code: string;
  name: string;
  address: string;
  type: string;
  owner_name: string | null;
  status: string;
  created_date: string;
  kiosk_count: number;
}

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

export default function StoreDetail() {
  const { id } = useParams<{ id: string }>();
  const { token, user } = useAuth();
  const navigate = useNavigate();
  
  const [store, setStore] = useState<StoreItem | null>(null);
  const [kiosks, setKiosks] = useState<KioskItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // 권한 체크: 수정/삭제는 DEV, HEAD, MASTER만 가능
  const canManageStore = user?.role === 'DEV' || user?.role === 'HEAD' || user?.role === 'MASTER';

  // 삭제 경고 모달 상태
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // 수정 모달 상태
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editName, setEditName] = useState('');
  const [editAddress, setEditAddress] = useState('');
  const [editOwner, setEditOwner] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchStoreData = async () => {
    setIsLoading(true);
    try {
      // 1. 매장 상세 조회
      const storeRes = await fetch(`/store/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (storeRes.status === 403) {
        throw new Error('이 매장의 상세 정보를 볼 수 있는 권한이 없습니다.');
      }
      if (!storeRes.ok) throw new Error('매장 정보를 불러오지 못했습니다.');
      const storeData = await storeRes.json();
      setStore(storeData);
      setEditName(storeData.name);
      setEditAddress(storeData.address);
      setEditOwner(storeData.owner_name || '');

      // 2. 키오스크 목록 조회 (해당 매장 필터)
      const kiosksRes = await fetch(`/kiosks/?store_id=${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!kiosksRes.ok) throw new Error('키오스크 목록을 불러오지 못했습니다.');
      const kiosksData = await kiosksRes.json();
      setKiosks(kiosksData);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStoreData();
  }, [id, token]);

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

  // 매장 정보 수정
  const handleUpdateStore = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdating(true);
    try {
      const res = await fetch(`/store/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: editName,
          address: editAddress,
          owner_name: editOwner
        })
      });
      if (!res.ok) throw new Error('매장 정보 수정에 실패했습니다.');
      
      setIsEditModalOpen(false);
      fetchStoreData(); // 갱신
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsUpdating(false);
    }
  };

  // 매장 연쇄 삭제 (CASCADE)
  const handleDeleteStore = async () => {
    setIsDeleting(true);
    try {
      const res = await fetch(`/store/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('매장 삭제에 실패했습니다.');
      
      setIsDeleteModalOpen(false);
      navigate('/stores'); // 삭제 후 목록으로 이동
    } catch (err: any) {
      alert(err.message);
    } finally {
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

  if (error || !store) {
    return (
      <div className="flex-grow p-8 flex flex-col justify-center items-center h-full">
        <div className="bg-red-50 text-red-700 px-6 py-4 rounded-2xl shadow-sm text-center">
          <h3 className="text-xl font-bold mb-2">오류 발생</h3>
          <p className="text-sm font-medium">{error || '매장을 찾을 수 없습니다.'}</p>
          <button 
            onClick={() => navigate('/stores')}
            className="mt-4 bg-red-600 hover:bg-red-700 text-white font-semibold px-4 py-2 rounded-xl transition-colors cursor-pointer"
          >
            목록으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 pb-20">
      {/* 뒤로가기 버튼 */}
      <button
        onClick={() => navigate('/stores')}
        className="flex items-center space-x-2 text-gray-600 hover:text-[#7C3AED] font-semibold transition-colors cursor-pointer"
      >
        <ArrowLeft size={20} />
        <span>매장 목록으로</span>
      </button>

      {/* 상단: 매장 기본정보 */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <span className="bg-[#7C3AED]/10 text-[#7C3AED] px-4 py-1.5 rounded-full text-sm font-bold font-mono">
              {store.code}
            </span>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
              store.status === 'ACTIVE' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-500'
            }`}>
              {store.status === 'ACTIVE' ? '운영 중' : '비활성'}
            </span>
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900">{store.name}</h1>
          <p className="text-gray-500 text-base font-medium">{store.address}</p>
          <div className="flex flex-wrap gap-x-6 gap-y-2 pt-2 text-sm text-gray-600 font-semibold">
            <div>점주: <span className="text-gray-950 font-bold">{store.owner_name || '미지정'}</span></div>
            <div>유형: <span className="text-gray-950 font-bold">{store.type === 'Restaurant' ? '외식 푸드코트형' : '일반 판매형'}</span></div>
            <div>등록일: <span className="text-gray-950 font-bold">{new Date(store.created_date).toLocaleDateString()}</span></div>
          </div>
        </div>

        {canManageStore && (
          <div className="flex space-x-3 w-full md:w-auto">
            <button
              onClick={() => setIsEditModalOpen(true)}
              className="flex-1 md:flex-initial flex items-center justify-center space-x-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold px-5 py-3 rounded-xl transition-all cursor-pointer"
            >
              <Edit size={18} />
              <span>수정</span>
            </button>
            <button
              onClick={() => setIsDeleteModalOpen(true)}
              className="flex-1 md:flex-initial flex items-center justify-center space-x-2 bg-red-50 hover:bg-red-100 text-red-600 font-bold px-5 py-3 rounded-xl transition-all cursor-pointer"
            >
              <Trash2 size={18} />
              <span>매장 삭제</span>
            </button>
          </div>
        )}
      </div>

      {/* 하단: 소속 키오스크 목록 */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 space-y-6">
        <div>
          <h3 className="text-2xl font-bold text-gray-900 flex items-center">
            <Monitor className="mr-2.5 text-[#7C3AED]" size={26} /> 등록된 키오스크 기기
          </h3>
          <p className="text-gray-500 text-sm mt-1">이 매장에 등록되어 가동중인 키오스크 목록입니다.</p>
        </div>

        <div className="overflow-hidden border border-gray-100 rounded-2xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100 text-gray-600 font-semibold text-sm">
                <th className="px-6 py-4">기기 ID (고유코드)</th>
                <th className="px-6 py-4">키오스크명</th>
                <th className="px-6 py-4">모델명</th>
                <th className="px-6 py-4">가동 상태</th>
                <th className="px-6 py-4">결제 상태</th>
                <th className="px-6 py-4">다음 결제 예정일</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700">
              {kiosks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-gray-400 font-medium">
                    이 매장에 연결된 키오스크 기기가 없습니다.
                  </td>
                </tr>
              ) : (
                kiosks.map((kiosk) => (
                  <tr key={kiosk.id} className="hover:bg-gray-50 transition-colors cursor-pointer" onClick={() => navigate(`/kiosks/${kiosk.id}`)}>
                    <td className="px-6 py-4 font-mono font-bold text-[#7C3AED]">
                      {kiosk.code}
                    </td>
                    <td className="px-6 py-4 font-semibold text-gray-900">{kiosk.name}</td>
                    <td className="px-6 py-4 text-gray-500">{kiosk.model_name || '-'}</td>
                    <td className="px-6 py-4">
                      <button
                        onClick={(e) => handleToggleKioskStatus(e, kiosk.id, kiosk.status)}
                        className="flex items-center space-x-1.5 hover:bg-gray-200 px-3 py-1.5 rounded-full transition-colors cursor-pointer"
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
                    <td className="px-6 py-4 text-gray-600 flex items-center space-x-1">
                      <Calendar size={14} className="text-gray-400" />
                      <span>{kiosk.next_payment_date ? new Date(kiosk.next_payment_date).toLocaleDateString() : '-'}</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* AlertDialog 모사 매장 삭제 경고 모달 */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8 shadow-xl space-y-6">
            <div className="flex items-center space-x-3 text-red-600">
              <div className="bg-red-50 p-3 rounded-2xl">
                <AlertTriangle size={32} />
              </div>
              <div>
                <h3 className="text-2xl font-bold">경고: 매장 삭제</h3>
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-gray-900 font-bold text-lg">
                정말로 매장 <span className="text-red-600">"{store.name}"</span>을 삭제하시겠습니까?
              </p>
              <div className="bg-red-50 text-red-800 p-4 rounded-2xl text-sm leading-relaxed font-semibold">
                ⚠️ 이 작업은 되돌릴 수 없습니다. 매장을 삭제하면 매장에 등록된 <strong>모든 키오스크 기기, 등록 상품, 카테고리 데이터</strong>가 데이터베이스 레벨에서 즉시 연쇄 삭제(ON DELETE CASCADE)됩니다.
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                disabled={isDeleting}
                onClick={() => setIsDeleteModalOpen(false)}
                className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-3 rounded-xl transition-colors cursor-pointer text-center"
              >
                취소
              </button>
              <button
                disabled={isDeleting}
                onClick={handleDeleteStore}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded-xl transition-colors flex justify-center items-center cursor-pointer"
              >
                {isDeleting ? <Loader2 className="animate-spin" size={20} /> : '매장 삭제 확정'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 수정 모달 */}
      {isEditModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-8 shadow-xl space-y-6">
            <div>
              <h3 className="text-2xl font-bold text-gray-900">매장 정보 수정</h3>
              <p className="text-gray-500 text-sm mt-1">지정된 가맹점 매장 정보를 수정합니다.</p>
            </div>
            
            <form onSubmit={handleUpdateStore} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">매장명</label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">매장 주소</label>
                <input
                  type="text"
                  value={editAddress}
                  onChange={(e) => setEditAddress(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">점주명</label>
                <input
                  type="text"
                  value={editOwner}
                  onChange={(e) => setEditOwner(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  required
                />
              </div>

              <div className="flex space-x-3 pt-4 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-3 rounded-xl transition-colors cursor-pointer text-center"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={isUpdating}
                  className="flex-1 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3 rounded-xl transition-colors flex justify-center items-center cursor-pointer"
                >
                  {isUpdating ? <Loader2 className="animate-spin" size={20} /> : '저장하기'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
