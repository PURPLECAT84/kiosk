import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Loader2, Plus, Trash2, ShieldAlert, Sparkles, Check, X, Layers, CreditCard, Calendar } from 'lucide-react';

interface BillingProduct {
  id: number;
  name: string;
  amount: number;
  billing_type: string;
  period_months: number;
  is_active: boolean;
  created_at: string;
}

export default function BillingProductManagement() {
  const { token, user } = useAuth();
  const [products, setProducts] = useState<BillingProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  // 모달 상태
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // 폼 상태
  const [formData, setFormData] = useState({
    name: '',
    amount: 0,
    billing_type: 'REGULAR',
    period_months: 1
  });

  const fetchProducts = async () => {
    setIsLoading(true);
    setError('');
    try {
      const res = await fetch('/subscribe/products', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error('요금제 상품 목록을 불러오지 못했습니다.');
      const data = await res.json();
      setProducts(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await fetch('/subscribe/products', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || '요금 상품 생성에 실패했습니다.');
      }
      alert('새로운 이용료 요금 상품이 성공적으로 추가되었습니다.');
      setIsModalOpen(false);
      setFormData({ name: '', amount: 0, billing_type: 'REGULAR', period_months: 1 });
      fetchProducts();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleActive = async (id: number, currentActive: boolean) => {
    try {
      const res = await fetch(`/subscribe/products/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ is_active: !currentActive })
      });
      if (!res.ok) throw new Error('상태 변경에 실패했습니다.');
      fetchProducts();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('정말로 이 요금제 상품을 영구 삭제하시겠습니까?\n삭제 시 기존 가입 이력은 보존되나 노출은 중단됩니다.')) return;
    try {
      const res = await fetch(`/subscribe/products/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error('요금제 삭제에 실패했습니다.');
      alert('요금제가 정상적으로 삭제되었습니다.');
      fetchProducts();
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (!['DEV', 'HEAD', 'MASTER'].includes(user?.role || '')) {
    return (
      <div className="p-8 flex flex-col justify-center items-center h-[60vh] text-center space-y-4 font-sans">
        <ShieldAlert size={64} className="text-red-500" />
        <h2 className="text-2xl font-bold text-gray-800">접근 권한 제한</h2>
        <p className="text-gray-500 max-w-md text-sm">이 메뉴는 MOKI 본사 시스템 관리자 전용 메뉴입니다. 일반 사용자 또는 점주는 접근할 수 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 pb-20 font-sans">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 flex items-center gap-2">
            <Layers className="text-[#7C3AED]" size={32} />
            본사 요금제 관리
          </h1>
          <p className="text-gray-500 text-xs mt-1">점주들이 키오스크 활성화를 위해 구독 또는 결제할 요금제 라인업을 구성합니다.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-[#7C3AED] hover:bg-[#6D28D9] text-white px-5 py-3 rounded-2xl text-sm font-bold shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all cursor-pointer"
        >
          <Plus size={18} />
          <span>신규 요금제 추가</span>
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="animate-spin text-[#7C3AED]" size={48} />
        </div>
      ) : error ? (
        <div className="bg-red-50 text-red-700 px-4 py-3 rounded-2xl text-sm font-semibold">
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.length === 0 ? (
            <div className="col-span-full text-center py-20 text-gray-400 font-medium bg-white rounded-3xl border border-gray-100 shadow-sm">
              등록된 이용료 요금 상품이 없습니다. 우측 상단의 추가 버튼을 눌러 첫 요금제를 만들어보세요.
            </div>
          ) : (
            products.map((prod) => (
              <div 
                key={prod.id} 
                className={`bg-white border rounded-3xl p-6 transition-all duration-200 flex flex-col justify-between shadow-sm hover:shadow-md ${
                  prod.is_active ? 'border-gray-150' : 'border-gray-200 bg-gray-50/50 opacity-75'
                }`}
              >
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className={`px-3 py-1 rounded-full text-[10px] font-bold ${
                      prod.billing_type === 'REGULAR' 
                        ? 'bg-purple-100/70 text-[#7C3AED] border border-purple-200/50' 
                        : 'bg-blue-100/70 text-blue-600 border border-blue-200/50'
                    }`}>
                      {prod.billing_type === 'REGULAR' ? '월 정기결제 (구독)' : '단일결제 (1회권)'}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                        prod.is_active ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-500'
                      }`}>
                        {prod.is_active ? '노출 활성' : '숨김 상태'}
                      </span>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xl font-extrabold text-gray-900 line-clamp-1">{prod.name}</h3>
                    <p className="text-xs text-gray-400 mt-1">이용 기간: {prod.period_months}개월</p>
                  </div>

                  <div className="pt-2">
                    <span className="text-2xl font-extrabold text-gray-900">₩{prod.amount.toLocaleString()}</span>
                    <span className="text-xs text-gray-400 font-medium"> / 총액</span>
                  </div>
                </div>

                <div className="mt-8 pt-4 border-t border-gray-100/60 flex justify-between items-center">
                  <button
                    onClick={() => handleToggleActive(prod.id, prod.is_active)}
                    className={`text-xs font-bold px-3.5 py-2 rounded-xl transition-colors cursor-pointer ${
                      prod.is_active 
                        ? 'bg-gray-100 hover:bg-gray-200 text-gray-700' 
                        : 'bg-purple-50 hover:bg-purple-100 text-[#7C3AED]'
                    }`}
                  >
                    {prod.is_active ? '비활성화하기' : '활성화하기'}
                  </button>

                  <button
                    onClick={() => handleDelete(prod.id)}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-xl transition-colors cursor-pointer"
                    title="요금제 영구 삭제"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* 요금제 추가 모달 */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] z-50 flex justify-center items-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl border border-gray-100 space-y-6 animate-scale-up">
            <div className="flex justify-between items-center">
              <h3 className="text-2xl font-extrabold text-gray-900 flex items-center gap-2">
                <Sparkles className="text-[#7C3AED]" size={22} />
                신규 이용료 추가
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="p-1.5 hover:bg-gray-100 rounded-full cursor-pointer">
                <X size={20} className="text-gray-500" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">요금 상품명</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-sm font-semibold"
                  placeholder="예: 3개월 단일권"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">금액 (원)</label>
                <input
                  type="number"
                  value={formData.amount || ''}
                  onChange={(e) => setFormData({ ...formData, amount: parseInt(e.target.value) || 0 })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-sm font-semibold"
                  placeholder="예: 100000"
                  min={0}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">이용 유형</label>
                  <select
                    value={formData.billing_type}
                    onChange={(e) => setFormData({ ...formData, billing_type: e.target.value })}
                    className="w-full px-3 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none bg-white text-sm font-bold"
                  >
                    <option value="REGULAR">정기결제 (구독)</option>
                    <option value="ONETIME">단일결제 (1회권)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">이용 기간 (개월)</label>
                  <input
                    type="number"
                    value={formData.period_months}
                    onChange={(e) => setFormData({ ...formData, period_months: parseInt(e.target.value) || 1 })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-sm font-semibold"
                    min={1}
                    max={36}
                    required
                  />
                </div>
              </div>

              <div className="flex space-x-3 pt-4 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 bg-gray-150 hover:bg-gray-200 text-gray-700 font-bold py-3.5 rounded-xl transition-colors cursor-pointer text-sm text-center"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3.5 rounded-xl transition-colors flex justify-center items-center cursor-pointer text-sm text-center disabled:bg-gray-300"
                >
                  {isSubmitting ? <Loader2 className="animate-spin" size={18} /> : '등록하기'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
