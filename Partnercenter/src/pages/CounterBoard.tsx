import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useKiosk } from '../context/KioskContext';
import { Play, CheckCircle, Clock, RotateCw, AlertTriangle, MonitorOff, ChevronRight, User } from 'lucide-react';

interface OrderItem {
  id: number;
  product_name: string;
  product_price: number;
  quantity: number;
}

interface Order {
  id: number;
  order_no: string | null;
  kiosk_id: string;
  total_amount: number;
  payment_method: string;
  status: string;
  created_date: string;
  items: OrderItem[];
}

export default function CounterBoard() {
  const { token } = useAuth();
  const { currentKioskId, currentKioskName } = useKiosk();
  
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchOrders = async () => {
    if (!currentKioskId) return;
    setIsLoading(true);
    try {
      const res = await fetch(`/order/?kiosk_id=${currentKioskId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Kiosk-Id': currentKioskId
        }
      });
      if (!res.ok) {
        throw new Error('주문 내역을 조회하는데 실패했습니다.');
      }
      const data: Order[] = await res.json();
      setOrders(data);
      setError('');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // 5초 간격 실시간 폴링 동기화
  useEffect(() => {
    fetchOrders();
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchOrders();
    }, 5000);

    return () => clearInterval(interval);
  }, [token, currentKioskId, autoRefresh]);

  const updateOrderStatus = async (orderId: number, nextStatus: string) => {
    try {
      const res = await fetch(`/order/${orderId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: nextStatus })
      });
      if (!res.ok) {
        throw new Error('주문 상태 업데이트에 실패했습니다.');
      }
      // 성공 시 즉시 리스트 갱신
      fetchOrders();
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (!currentKioskId) {
    return (
      <div className="flex-grow p-8 flex flex-col justify-center items-center h-full bg-[#0F172A] text-white">
        <div className="bg-[#1E293B] p-8 rounded-3xl border border-slate-800 text-center max-w-md space-y-6 shadow-2xl">
          <div className="w-16 h-16 bg-[#7C3AED]/20 text-[#7C3AED] rounded-full flex justify-center items-center mx-auto">
            <MonitorOff size={32} />
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-bold">활성 키오스크 미선택</h3>
            <p className="text-sm text-slate-400">
              주방 오더 보드를 사용하려면 왼쪽 하단에서 관리할 키오스크 기기를 먼저 선택해 주세요.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // 주문 상태 분류
  // 'Preparing' -> 준비 중
  // 'Ready' 또는 'Completed' -> 준비 완료
  const preparingOrders = orders.filter(o => o.status === 'Preparing');
  const readyOrders = orders.filter(o => o.status === 'Ready' || o.status === 'Completed').slice(0, 15); // 최근 15개만 표시

  return (
    <div className="flex-grow flex flex-col h-full bg-[#0F172A] text-slate-100 font-sans overflow-hidden">
      
      {/* 주방 상단 헤더 */}
      <header className="bg-[#1E293B]/80 backdrop-blur-md border-b border-slate-800 p-5 flex justify-between items-center z-10">
        <div className="flex items-center space-x-3">
          <div className="bg-[#7C3AED] p-2 rounded-xl text-white font-black text-sm tracking-wider">
            KITCHEN
          </div>
          <div>
            <h1 className="text-lg font-black tracking-tight text-white flex items-center gap-2">
              <span>주방 오더 모니터 보드</span>
              <span className="text-xs font-bold text-slate-400 bg-slate-800 px-2.5 py-0.5 rounded-full border border-slate-700">
                {currentKioskName}
              </span>
            </h1>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl">
            <input 
              type="checkbox" 
              id="auto-refresh"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4 text-[#7C3AED] bg-slate-800 border-slate-700 rounded focus:ring-[#7C3AED]"
            />
            <label htmlFor="auto-refresh" className="text-xs font-bold text-slate-400 select-none cursor-pointer">
              5초 자동 동기화
            </label>
          </div>

          <button 
            onClick={fetchOrders}
            className="p-2 hover:bg-slate-800 active:scale-95 rounded-xl transition-all border border-slate-800 text-slate-400 hover:text-white cursor-pointer"
            title="새로고침"
          >
            <RotateCw size={18} className={isLoading ? "animate-spin" : ""} />
          </button>
        </div>
      </header>

      {error && (
        <div className="bg-red-950/50 border border-red-900 text-red-200 px-6 py-3 text-sm font-semibold flex items-center gap-2">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {/* 메인 2단 보드 그리드 */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 overflow-hidden h-full">
        
        {/* 왼쪽: 준비 중 (Preparing) */}
        <div className="flex flex-col bg-[#1E293B]/40 rounded-3xl border border-slate-800/80 p-5 overflow-hidden h-full">
          <div className="flex justify-between items-center mb-4 pb-3 border-b border-slate-800">
            <h3 className="text-base font-black text-amber-400 flex items-center gap-2">
              <Clock size={18} className="animate-pulse" />
              <span>준비 중 (Preparing)</span>
            </h3>
            <span className="bg-amber-400/10 text-amber-400 text-xs font-extrabold px-3 py-1 rounded-full border border-amber-400/20">
              {preparingOrders.length}건
            </span>
          </div>

          {/* 카드 리스트 */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-1 scrollbar-thin">
            {preparingOrders.length === 0 ? (
              <div className="h-full flex flex-col justify-center items-center text-slate-500 py-12">
                <CheckCircle size={48} className="mb-3 text-slate-700" />
                <p className="text-sm font-bold">대기 중인 주문이 없습니다.</p>
              </div>
            ) : (
              preparingOrders.map((order) => {
                const orderTime = new Date(order.created_date).toLocaleTimeString('ko-KR', {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit'
                });
                return (
                  <div 
                    key={order.id}
                    className="bg-[#1E293B]/80 border border-slate-800 hover:border-amber-500/50 rounded-2xl p-5 shadow-lg flex flex-col justify-between transition-all duration-200 hover:-translate-y-0.5 group"
                  >
                    <div>
                      {/* 주문 헤더 */}
                      <div className="flex justify-between items-start border-b border-slate-800 pb-3 mb-3">
                        <div>
                          <span className="text-xs font-semibold text-slate-500 block">주문 번호</span>
                          <span className="text-lg font-black text-white">{order.order_no || `ID: ${order.id}`}</span>
                        </div>
                        <div className="text-right">
                          <span className="text-xs font-semibold text-slate-500 block">주문 시각</span>
                          <span className="text-xs font-bold text-slate-300">{orderTime}</span>
                        </div>
                      </div>

                      {/* 주문 아이템 */}
                      <div className="space-y-2 mb-4">
                        {order.items.map((item) => (
                          <div key={item.id} className="flex justify-between items-center py-0.5">
                            <span className="text-sm font-bold text-slate-200">{item.product_name}</span>
                            <span className="text-sm font-black text-[#7C3AED] bg-[#7C3AED]/10 px-2 py-0.5 rounded-lg border border-[#7C3AED]/20">
                              {item.quantity}개
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* 완료 동작 버튼 */}
                    <div className="pt-3 border-t border-slate-800 flex justify-between items-center">
                      <span className="text-xs text-slate-500 font-bold">
                        {order.payment_method} · ₩{order.total_amount.toLocaleString()}
                      </span>
                      <button
                        onClick={() => updateOrderStatus(order.id, 'Ready')}
                        className="flex items-center gap-1.5 px-4 py-2 bg-[#7C3AED] hover:bg-[#6D28D9] active:scale-95 text-white text-xs font-black rounded-xl shadow-md transition-all cursor-pointer"
                      >
                        <span>준비 완료</span>
                        <ChevronRight size={14} />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* 오른쪽: 준비 완료 (Ready / Completed) */}
        <div className="flex flex-col bg-[#1E293B]/20 rounded-3xl border border-slate-800/50 p-5 overflow-hidden h-full">
          <div className="flex justify-between items-center mb-4 pb-3 border-b border-slate-800">
            <h3 className="text-base font-black text-emerald-400 flex items-center gap-2">
              <CheckCircle size={18} />
              <span>준비 완료 (Completed)</span>
            </h3>
            <span className="bg-emerald-400/10 text-emerald-400 text-xs font-extrabold px-3 py-1 rounded-full border border-emerald-400/20">
              최근 {readyOrders.length}건
            </span>
          </div>

          {/* 카드 리스트 */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-1 scrollbar-thin">
            {readyOrders.length === 0 ? (
              <div className="h-full flex flex-col justify-center items-center text-slate-600 py-12">
                <p className="text-sm font-bold">최근 완료된 주문이 없습니다.</p>
              </div>
            ) : (
              readyOrders.map((order) => {
                const orderTime = new Date(order.created_date).toLocaleTimeString('ko-KR', {
                  hour: '2-digit',
                  minute: '2-digit'
                });
                return (
                  <div 
                    key={order.id}
                    className="bg-[#1E293B]/30 border border-slate-800/80 opacity-75 hover:opacity-100 rounded-2xl p-4 shadow flex flex-col justify-between transition-all duration-200"
                  >
                    <div className="flex justify-between items-center mb-2">
                      <div>
                        <span className="text-xs font-bold text-slate-500">주문 {order.order_no || order.id}</span>
                      </div>
                      <span className="text-xs text-slate-400">{orderTime}</span>
                    </div>

                    <div className="space-y-1 mb-2">
                      {order.items.map((item) => (
                        <div key={item.id} className="flex justify-between items-center text-xs">
                          <span className="text-slate-300 font-semibold">{item.product_name}</span>
                          <span className="text-slate-400 font-bold">{item.quantity}개</span>
                        </div>
                      ))}
                    </div>

                    <div className="flex justify-between items-center border-t border-slate-800/60 pt-2 text-[10px]">
                      <span className="text-slate-500 font-medium">₩{order.total_amount.toLocaleString()}</span>
                      
                      {/* 상태 변경 롤백 지원 */}
                      <button
                        onClick={() => updateOrderStatus(order.id, 'Preparing')}
                        className="text-slate-400 hover:text-amber-400 transition-colors font-bold cursor-pointer"
                      >
                        준비 중으로 되돌리기
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
