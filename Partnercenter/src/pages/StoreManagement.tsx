import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Store, Plus, ToggleLeft, ToggleRight, Loader2 } from 'lucide-react';

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

export default function StoreManagement() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [stores, setStores] = useState<StoreItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // 매장 생성 모달 상태
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newStoreName, setNewStoreName] = useState('');
  const [newStoreAddress, setNewStoreAddress] = useState('');
  const [newStoreType, setNewStoreType] = useState('Store');
  const [newStoreOwner, setNewStoreOwner] = useState(user?.name || '');
  const [isCreating, setIsCreating] = useState(false);

  const fetchStores = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/store/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.status === 403) {
        throw new Error('매장 관리 권한이 없습니다 (403).');
      }
      if (!res.ok) throw new Error('매장 목록을 불러오지 못했습니다.');
      const data = await res.json();
      setStores(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStores();
  }, [token]);

  // 상태 스위칭 (활성 / 비활성)
  const handleToggleStatus = async (id: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    try {
      const res = await fetch(`/store/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: nextStatus })
      });
      if (!res.ok) throw new Error('상태 수정에 실패했습니다.');
      
      // 로컬 상태 즉시 변경
      setStores(stores.map(s => s.id === id ? { ...s, status: nextStatus } : s));
    } catch (err: any) {
      alert(err.message);
    }
  };

  // 매장 생성 처리
  const handleCreateStore = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      const res = await fetch('/store/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newStoreName,
          address: newStoreAddress,
          type: newStoreType,
          owner_name: newStoreOwner
        })
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || '매장 생성에 실패했습니다.');
      }
      
      setIsModalOpen(false);
      setNewStoreName('');
      setNewStoreAddress('');
      setNewStoreType('Store');
      fetchStores(); // 리스트 갱신
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsCreating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 p-8 flex justify-center items-center h-full">
        <Loader2 className="animate-spin text-[#7C3AED]" size={48} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 p-8 flex flex-col justify-center items-center h-full">
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
          <h1 className="text-3xl font-bold text-gray-900 mb-1">매장 관리</h1>
          <p className="text-gray-500 text-base">시스템에 등록된 전체 가맹점 매장을 관리합니다.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center space-x-2 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold px-5 py-3 rounded-xl transition-all shadow-sm cursor-pointer"
        >
          <Plus size={20} />
          <span>신규 매장 등록</span>
        </button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-100">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100 text-gray-600 font-semibold text-sm">
                <th className="px-6 py-4">매장 ID (고유코드)</th>
                <th className="px-6 py-4">매장명</th>
                <th className="px-6 py-4">점주</th>
                <th className="px-6 py-4">구분</th>
                <th className="px-6 py-4">상태 (활성/비활성)</th>
                <th className="px-6 py-4 text-center">등록된 기기 수</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700">
              {stores.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-gray-400 font-medium">
                    등록된 매장이 없습니다.
                  </td>
                </tr>
              ) : (
                stores.map((store) => (
                  <tr key={store.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-mono font-bold text-[#7C3AED]">
                      <button 
                        onClick={() => navigate(`/stores/${store.id}`)}
                        className="hover:underline cursor-pointer"
                      >
                        {store.code}
                      </button>
                    </td>
                    <td className="px-6 py-4 font-semibold text-gray-900">
                      <button 
                        onClick={() => navigate(`/stores/${store.id}`)}
                        className="hover:underline text-left cursor-pointer"
                      >
                        {store.name}
                      </button>
                    </td>
                    <td className="px-6 py-4 text-gray-600">{store.owner_name || '미지정'}</td>
                    <td className="px-6 py-4 text-sm font-semibold">
                      <span className={`px-3 py-1 rounded-full text-xs ${
                        store.type === 'Restaurant' 
                          ? 'bg-orange-50 text-orange-600' 
                          : 'bg-blue-50 text-blue-600'
                      }`}>
                        {store.type === 'Restaurant' ? '외식형(Restaurant)' : '판매형(Store)'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleToggleStatus(store.id, store.status)}
                          className="text-[#7C3AED] hover:text-[#6D28D9] cursor-pointer"
                          title="상태 전환하기"
                        >
                          {store.status === 'ACTIVE' ? (
                            <ToggleRight size={36} className="text-[#7C3AED]" />
                          ) : (
                            <ToggleLeft size={36} className="text-gray-400" />
                          )}
                        </button>
                        <span className={`text-xs font-bold ${
                          store.status === 'ACTIVE' ? 'text-green-600' : 'text-gray-400'
                        }`}>
                          {store.status === 'ACTIVE' ? '활성' : '비활성'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center font-bold text-gray-900">{store.kiosk_count}대</td>
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
              <h3 className="text-2xl font-bold text-gray-900">신규 매장 등록</h3>
              <p className="text-gray-500 text-sm mt-1">새로운 매장 가맹 정보와 점주를 지정하여 등록합니다.</p>
            </div>
            
            <form onSubmit={handleCreateStore} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">매장명</label>
                <input
                  type="text"
                  value={newStoreName}
                  onChange={(e) => setNewStoreName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  placeholder="예: 목동 센트럴점"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">매장 주소</label>
                <input
                  type="text"
                  value={newStoreAddress}
                  onChange={(e) => setNewStoreAddress(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                  placeholder="예: 서울시 양천구 목동동로 100"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">구분</label>
                  <select
                    value={newStoreType}
                    onChange={(e) => setNewStoreType(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none bg-white"
                  >
                    <option value="Store">일반 판매형(Store)</option>
                    <option value="Restaurant">외식 푸드코트형(Restaurant)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">점주명</label>
                  <input
                    type="text"
                    value={newStoreOwner}
                    onChange={(e) => setNewStoreOwner(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none"
                    placeholder="점주명 입력"
                    required
                  />
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
