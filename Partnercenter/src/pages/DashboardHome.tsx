import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useKiosk } from '../context/KioskContext';
import { Store, Monitor, LayoutDashboard, Loader2, ArrowRight, RefreshCw, CreditCard, Receipt, TrendingUp, BarChart3 } from 'lucide-react';

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

export default function DashboardHome() {
  const { token, user } = useAuth();
  const { currentKioskId, currentKioskName } = useKiosk();
  const navigate = useNavigate();
  const [stores, setStores] = useState<StoreItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // 실시간 기기 매출 통계 상태
  const [summary, setSummary] = useState({ today_sales: 0, today_orders: 0, monthly_sales: 0 });
  const [bestSellers, setBestSellers] = useState<{ product_name: string; total_sold: number }[]>([]);
  const [isLoadingStats, setIsLoadingStats] = useState(false);

  const fetchStores = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/store/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error('매장 정보를 불러오는데 실패했습니다.');
      const data = await res.json();
      setStores(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStats = async () => {
    if (user?.role === 'STAFF') return;
    setIsLoadingStats(true);
    try {
      const headers = {
        'Authorization': `Bearer ${token}`,
        ...(currentKioskId ? { 'X-Kiosk-Id': currentKioskId } : {})
      };
      
      const [summaryRes, bestRes] = await Promise.all([
        fetch('/dashboard/summary', { headers }),
        fetch('/dashboard/best-sellers', { headers })
      ]);
      
      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        setSummary(summaryData);
      }
      if (bestRes.ok) {
        const bestData = await bestRes.json();
        setBestSellers(bestData);
      }
    } catch (err) {
      console.error('Failed to fetch dashboard statistics:', err);
    } finally {
      setIsLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchStores();
  }, [token]);

  useEffect(() => {
    fetchStats();
  }, [token, currentKioskId]);

  if (isLoading) {
    return (
      <div className="flex-grow p-8 flex justify-center items-center h-full">
        <Loader2 className="animate-spin text-[#7C3AED]" size={48} />
      </div>
    );
  }

  const isManager = user?.role === 'MANAGER';
  const totalStores = stores.length;
  const totalKiosks = stores.reduce((acc, s) => acc + s.kiosk_count, 0);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 pb-20">
      <div>
        <h1 className="text-3xl font-extrabold text-gray-900 flex items-center gap-2">
          <LayoutDashboard className="text-[#7C3AED]" size={32} />
          {user?.name} 님, 환영합니다!
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          {isManager 
            ? '관리 중인 가맹 매장 현황을 한눈에 파악하세요.' 
            : 'MOKI 키오스크 시스템 통합 대시보드 홈입니다.'}
        </p>
      </div>

      {/* 요약 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-4 bg-purple-50 text-[#7C3AED] rounded-2xl">
            <Store size={28} />
          </div>
          <div>
            <p className="text-gray-400 text-sm font-semibold">관리 매장</p>
            <p className="text-2xl font-extrabold text-gray-900">{totalStores} 개</p>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-4 bg-blue-50 text-blue-600 rounded-2xl">
            <Monitor size={28} />
          </div>
          <div>
            <p className="text-gray-400 text-sm font-semibold">등록 키오스크</p>
            <p className="text-2xl font-extrabold text-gray-900">{totalKiosks} 대</p>
          </div>
        </div>

        {!isManager && (
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center space-x-4">
            <div className="p-4 bg-amber-50 text-amber-600 rounded-2xl">
              <RefreshCw size={28} />
            </div>
            <div>
              <p className="text-gray-400 text-sm font-semibold">시스템 권한</p>
              <p className="text-lg font-extrabold text-gray-900">{user?.role} 계정</p>
            </div>
          </div>
        )}
      </div>

      {/* 실시간 기기별 매출 및 통계 현황 (STAFF 제외) */}
      {user?.role !== 'STAFF' && (
        <div className="space-y-6">
          <div>
            <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <BarChart3 className="text-[#7C3AED]" size={24} />
              <span>실시간 기기별 매출 및 인기 상품</span>
            </h3>
            <p className="text-gray-500 text-xs mt-1">
              현재 선택된 활성 키오스크 [ <span className="text-[#7C3AED] font-bold">{currentKioskName || '기기 미선택'}</span> ] 기준 실시간 매출 통계입니다.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 매출 요약 카드들 */}
            <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between h-40">
                <div className="flex justify-between items-start">
                  <span className="text-gray-400 text-sm font-semibold">오늘의 매출</span>
                  <div className="p-2 bg-purple-50 text-[#7C3AED] rounded-xl">
                    <CreditCard size={20} />
                  </div>
                </div>
                <div>
                  <p className="text-2xl font-extrabold text-gray-900">₩{summary.today_sales.toLocaleString()}</p>
                  <p className="text-xs text-gray-400 mt-1">오늘 결제 완료된 금액</p>
                </div>
              </div>

              <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between h-40">
                <div className="flex justify-between items-start">
                  <span className="text-gray-400 text-sm font-semibold">오늘의 주문 건수</span>
                  <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                    <Receipt size={20} />
                  </div>
                </div>
                <div>
                  <p className="text-2xl font-extrabold text-gray-900">{summary.today_orders} 건</p>
                  <p className="text-xs text-gray-400 mt-1">오늘 발생한 신규 주문</p>
                </div>
              </div>

              <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between h-40">
                <div className="flex justify-between items-start">
                  <span className="text-gray-400 text-sm font-semibold">이달의 누적 매출</span>
                  <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
                    <TrendingUp size={20} />
                  </div>
                </div>
                <div>
                  <p className="text-2xl font-extrabold text-gray-900">₩{summary.monthly_sales.toLocaleString()}</p>
                  <p className="text-xs text-gray-400 mt-1">이번 달 누적 합계</p>
                </div>
              </div>
            </div>

            {/* 인기 상품 Top 5 */}
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 space-y-4">
              <span className="text-gray-900 text-base font-bold block border-b border-gray-100 pb-2">
                인기 상품 Top 5 (오늘)
              </span>
              {bestSellers.length === 0 ? (
                <div className="text-center py-8 text-gray-400 text-sm font-medium">
                  오늘 판매된 상품이 없습니다.
                </div>
              ) : (
                <div className="space-y-3.5">
                  {bestSellers.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center">
                      <div className="flex items-center space-x-2.5 min-w-0 flex-1">
                        <span className="text-xs font-bold text-gray-400 w-4">{idx + 1}</span>
                        <span className="text-sm font-semibold text-gray-700 truncate">{item.product_name}</span>
                      </div>
                      <span className="text-sm font-bold text-gray-900 ml-2">{item.total_sold}개</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 내 매장 목록 섹션 */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-xl font-bold text-gray-900 flex items-center">
              <Store className="mr-2 text-[#7C3AED]" size={24} /> 
              {isManager ? '내가 관리하는 매장 목록' : '전체 가맹 매장 목록'}
            </h3>
            <p className="text-gray-500 text-xs mt-1">아래의 매장을 선택하여 상세 정보 및 키오스크를 관리하세요.</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-2xl text-sm font-semibold">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {stores.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-400 font-medium">
              등록된 매장이 없습니다.
            </div>
          ) : (
            stores.map((store) => (
              <div 
                key={store.id} 
                onClick={() => navigate(`/stores/${store.id}`)}
                className="bg-gray-50 hover:bg-purple-50/30 border border-gray-100 hover:border-[#7C3AED]/30 rounded-3xl p-6 transition-all duration-200 cursor-pointer flex flex-col justify-between group"
              >
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="bg-[#7C3AED]/10 text-[#7C3AED] px-3 py-1 rounded-full text-xs font-bold font-mono">
                      {store.code}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      store.status === 'ACTIVE' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {store.status === 'ACTIVE' ? '영업 중' : '비활성'}
                    </span>
                  </div>
                  <h4 className="text-lg font-extrabold text-gray-900 group-hover:text-[#7C3AED] transition-colors">{store.name}</h4>
                  <p className="text-gray-500 text-xs line-clamp-1">{store.address}</p>
                </div>
                <div className="mt-6 pt-4 border-t border-gray-100/60 flex justify-between items-center">
                  <div className="text-xs text-gray-600 font-semibold">
                    연결된 키오스크: <span className="text-gray-950 font-bold">{store.kiosk_count}대</span>
                  </div>
                  <span className="text-xs text-[#7C3AED] font-bold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                    상세보기 <ArrowRight size={14} />
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
