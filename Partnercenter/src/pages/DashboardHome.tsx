import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useKiosk } from '../context/KioskContext';
import { Monitor, LayoutDashboard, Loader2, ArrowRight, RefreshCw, CreditCard, Receipt, TrendingUp, BarChart3 } from 'lucide-react';
import SettlementCalendar from '../components/SettlementCalendar';

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

export default function DashboardHome() {
  const { token, user } = useAuth();
  const { currentKioskId, currentKioskName } = useKiosk();
  const navigate = useNavigate();
  const [kiosks, setKiosks] = useState<KioskItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // 실시간 기기 매출 통계 상태
  const [summary, setSummary] = useState({ today_sales: 0, today_orders: 0, monthly_sales: 0 });
  const [bestSellers, setBestSellers] = useState<{ product_name: string; total_sold: number }[]>([]);
  const [salesTrend, setSalesTrend] = useState<{ date: string; sales: number; refunds: number; net_sales: number }[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<{ method: string; name: string; count: number; amount: number }[]>([]);
  const [hourlyStats, setHourlyStats] = useState<{ hour: string; sales: number; orders: number }[]>([]);
  const [isLoadingStats, setIsLoadingStats] = useState(false);

  const fetchKiosks = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/kiosks/my', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error('키오스크 정보를 불러오는데 실패했습니다.');
      const data = await res.json();
      setKiosks(data);
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
      
      const [summaryRes, bestRes, trendRes, methodsRes, hourlyRes] = await Promise.all([
        fetch('/dashboard/summary', { headers }),
        fetch('/dashboard/best-sellers', { headers }),
        fetch('/dashboard/stats/sales-trend', { headers }),
        fetch('/dashboard/stats/payment-methods', { headers }),
        fetch('/dashboard/stats/hourly', { headers })
      ]);
      
      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        setSummary(summaryData);
      }
      if (bestRes.ok) {
        const bestData = await bestRes.json();
        setBestSellers(bestData);
      }
      if (trendRes.ok) {
        setSalesTrend(await trendRes.json());
      }
      if (methodsRes.ok) {
        setPaymentMethods(await methodsRes.json());
      }
      if (hourlyRes.ok) {
        setHourlyStats(await hourlyRes.json());
      }
    } catch (err) {
      console.error('Failed to fetch dashboard statistics:', err);
    } finally {
      setIsLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchKiosks();
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

  const totalKiosks = kiosks.length;
  const activeKiosks = kiosks.filter(k => k.status === 'OPERATING').length;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 pb-20">
      <div>
        <h1 className="text-3xl font-extrabold text-gray-900 flex items-center gap-2">
          <LayoutDashboard className="text-[#7C3AED]" size={32} />
          {user?.name} 님, 환영합니다!
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          MOKI 키오스크 시스템 통합 대시보드 홈입니다.
        </p>
      </div>

      {/* 요약 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-4 bg-blue-50 text-blue-600 rounded-2xl">
            <Monitor size={28} />
          </div>
          <div>
            <p className="text-gray-400 text-sm font-semibold">등록 키오스크</p>
            <p className="text-2xl font-extrabold text-gray-900">{totalKiosks} 대</p>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-4 bg-green-50 text-green-600 rounded-2xl">
            <RefreshCw size={28} />
          </div>
          <div>
            <p className="text-gray-400 text-sm font-semibold">운영 중 기기</p>
            <p className="text-2xl font-extrabold text-gray-900">{activeKiosks} 대</p>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-4 bg-purple-50 text-[#7C3AED] rounded-2xl">
            <LayoutDashboard size={28} />
          </div>
          <div>
            <p className="text-gray-400 text-sm font-semibold">시스템 권한</p>
            <p className="text-lg font-extrabold text-gray-900">{user?.role} 계정</p>
          </div>
        </div>
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

          {/* 🔥 [신규 추가] 세부 매출 통계 차트 그리드 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 1. 최근 7일 매출 추이 (꺾은선 SVG 차트) */}
            <div className="lg:col-span-2 bg-white rounded-3xl p-6 shadow-sm border border-gray-100 space-y-4">
              <span className="text-gray-900 text-base font-bold block border-b border-gray-100 pb-2">
                최근 7일 매출 추이 (순매출 기준)
              </span>
              {salesTrend.length === 0 ? (
                <div className="text-center py-12 text-gray-400 text-sm font-medium">데이터가 없습니다.</div>
              ) : (() => {
                const width = 600;
                const height = 200;
                const padding = 40;
                const chartWidth = width - padding * 2;
                const chartHeight = height - padding * 2;
                
                const maxVal = Math.max(...salesTrend.map(d => d.net_sales), 10000);
                const points = salesTrend.map((d, i) => {
                  const x = padding + (i * chartWidth) / (salesTrend.length - 1);
                  const y = height - padding - (d.net_sales / maxVal) * chartHeight;
                  return { x, y, label: d.date, value: d.net_sales };
                });

                const pathD = points.length > 0 
                  ? `M ${points[0].x} ${points[0].y} ` + points.slice(1).map(p => `L ${p.x} ${p.y}`).join(' ')
                  : '';
                  
                const areaD = points.length > 0
                  ? `${pathD} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`
                  : '';

                return (
                  <div className="relative group/chart">
                    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
                      <defs>
                        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#7C3AED" stopOpacity="0.25" />
                          <stop offset="100%" stopColor="#7C3AED" stopOpacity="0.0" />
                        </linearGradient>
                      </defs>
                      
                      {/* 가로 보조선 */}
                      {[0, 0.25, 0.5, 0.75, 1].map((ratio, idx) => {
                        const y = padding + chartHeight * ratio;
                        const labelVal = Math.round(maxVal * (1 - ratio));
                        return (
                          <g key={idx}>
                            <line x1={padding} y1={y} x2={width - padding} y2={y} stroke="#F3F4F6" strokeWidth="1" strokeDasharray="4 4" />
                            <text x={padding - 8} y={y + 4} textAnchor="end" className="text-[10px] font-semibold fill-gray-400 font-mono">
                              ₩{labelVal >= 10000 ? `${(labelVal / 10000).toFixed(0)}만` : labelVal}
                            </text>
                          </g>
                        );
                      })}

                      {/* 영역 색상 채우기 */}
                      {areaD && <path d={areaD} fill="url(#areaGrad)" className="transition-all duration-500" />}

                      {/* 꺾은선 그리기 */}
                      {pathD && <path d={pathD} fill="none" stroke="#7C3AED" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" className="transition-all duration-500" />}

                      {/* 데이터 노드 원과 툴팁 호버 영역 */}
                      {points.map((p, idx) => (
                        <g key={idx} className="group/node cursor-pointer">
                          <circle cx={p.x} cy={p.y} r="5" fill="#7C3AED" stroke="#FFFFFF" strokeWidth="2.5" className="transition-all group-hover/node:r-7 shadow-sm" />
                          {/* 호버 시 값 노출 텍스트 */}
                          <text x={p.x} y={p.y - 12} textAnchor="middle" className="text-[10px] font-extrabold fill-[#7C3AED] opacity-0 group-hover/node:opacity-100 transition-opacity bg-white px-1 py-0.5 rounded shadow-sm">
                            ₩{p.value.toLocaleString()}
                          </text>
                          {/* 하단 날짜 라벨 */}
                          <text x={p.x} y={height - 12} textAnchor="middle" className="text-[10px] font-bold fill-gray-500">
                            {p.label}
                          </text>
                        </g>
                      ))}
                    </svg>
                  </div>
                );
              })()}
            </div>

            {/* 2. 오늘 결제 수단별 비중 (도넛 SVG 차트) */}
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 space-y-4 flex flex-col justify-between">
              <div>
                <span className="text-gray-900 text-base font-bold block border-b border-gray-100 pb-2">
                  오늘의 결제 수단 비중
                </span>
                {paymentMethods.length === 0 ? (
                  <div className="text-center py-12 text-gray-400 text-sm font-medium">결제 데이터가 없습니다.</div>
                ) : (() => {
                  const size = 160;
                  const strokeWidth = 22;
                  const radius = (size - strokeWidth) / 2;
                  const circumference = 2 * Math.PI * radius;
                  const total = paymentMethods.reduce((acc, c) => acc + c.amount, 0) || 1;
                  
                  const colors = ["#7C3AED", "#10B981", "#3B82F6", "#F59E0B", "#EF4444"];
                  
                  let accumulatedPercent = 0;
                  const segments = paymentMethods.map((m, idx) => {
                    const percent = m.amount / total;
                    const strokeDasharray = `${percent * circumference} ${circumference}`;
                    const strokeDashoffset = -accumulatedPercent * circumference;
                    accumulatedPercent += percent;
                    return {
                      ...m,
                      strokeDasharray,
                      strokeDashoffset,
                      percent: (percent * 100).toFixed(1),
                      color: colors[idx % colors.length]
                    };
                  });

                  return (
                    <div className="flex items-center justify-between gap-4 py-4">
                      {/* SVG 도넛 */}
                      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="transform -rotate-90">
                        {segments.map((seg, idx) => (
                          <circle
                            key={idx}
                            cx={size / 2}
                            cy={size / 2}
                            r={radius}
                            fill="transparent"
                            stroke={seg.color}
                            strokeWidth={strokeWidth}
                            strokeDasharray={seg.strokeDasharray}
                            strokeDashoffset={seg.strokeDashoffset}
                            className="transition-all duration-500 hover:scale-102 transform origin-center cursor-pointer"
                          />
                        ))}
                        {/* 도넛 가운데 정보 */}
                        <circle cx={size / 2} cy={size / 2} r={radius - strokeWidth / 2} fill="#FFFFFF" />
                      </svg>

                      {/* 범례 */}
                      <div className="flex-1 space-y-2 max-w-[120px]">
                        {segments.map((seg, idx) => (
                          <div key={idx} className="flex items-center justify-between text-[11px] font-semibold text-gray-700">
                            <div className="flex items-center gap-1.5 min-w-0 pr-1">
                              <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: seg.color }} />
                              <span className="truncate">{seg.name}</span>
                            </div>
                            <span className="font-bold text-gray-900">{seg.percent}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })()}
              </div>
              <div className="text-[10px] text-gray-400 text-center font-medium border-t border-gray-50 pt-2">
                오늘 완료된 정상 결제 금액 기준 점유율
              </div>
            </div>

            {/* 3. 오늘 시간대별 매출 추이 (막대 SVG 차트) - 전체 폭 확장 배치 */}
            <div className="lg:col-span-3 bg-white rounded-3xl p-6 shadow-sm border border-gray-100 space-y-4">
              <span className="text-gray-900 text-base font-bold block border-b border-gray-100 pb-2">
                오늘 시간대별 매출 추이 (09시 ~ 22시)
              </span>
              {hourlyStats.length === 0 ? (
                <div className="text-center py-12 text-gray-400 text-sm font-medium">매출 기록이 없습니다.</div>
              ) : (() => {
                const width = 800;
                const height = 180;
                const paddingLeft = 50;
                const paddingRight = 20;
                const paddingTop = 20;
                const paddingBottom = 30;
                
                const chartWidth = width - paddingLeft - paddingRight;
                const chartHeight = height - paddingTop - paddingBottom;
                
                const maxVal = Math.max(...hourlyStats.map(h => h.sales), 50000);
                const barWidth = (chartWidth / hourlyStats.length) * 0.55;
                const gap = (chartWidth / hourlyStats.length) * 0.45;

                return (
                  <div className="relative overflow-x-auto">
                    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto min-w-[600px] overflow-visible">
                      <defs>
                        <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#7C3AED" />
                          <stop offset="100%" stopColor="#C084FC" />
                        </linearGradient>
                      </defs>

                      {/* 가로 보조선 */}
                      {[0, 0.5, 1].map((ratio, idx) => {
                        const y = paddingTop + chartHeight * ratio;
                        const labelVal = Math.round(maxVal * (1 - ratio));
                        return (
                          <g key={idx}>
                            <line x1={paddingLeft} y1={y} x2={width - paddingRight} y2={y} stroke="#F9FAFB" strokeWidth="1.5" />
                            <text x={paddingLeft - 10} y={y + 4} textAnchor="end" className="text-[10px] font-semibold fill-gray-400 font-mono">
                              ₩{labelVal >= 10000 ? `${(labelVal / 10000).toFixed(0)}만` : labelVal}
                            </text>
                          </g>
                        );
                      })}

                      {/* 막대 그리기 */}
                      {hourlyStats.map((h, idx) => {
                        const barHeight = (h.sales / maxVal) * chartHeight;
                        const x = paddingLeft + idx * (barWidth + gap) + gap / 2;
                        const y = height - paddingBottom - barHeight;

                        return (
                          <g key={idx} className="group/bar cursor-pointer">
                            <rect
                              x={x}
                              y={y}
                              width={barWidth}
                              height={Math.max(barHeight, 3)} // 최소 높이 3px 부여
                              rx="4"
                              fill="url(#barGrad)"
                              className="transition-all duration-300 hover:opacity-85"
                            />
                            {/* 막대 상단 금액 레이블 (오늘 매출이 있을 때만) */}
                            {h.sales > 0 && (
                              <text x={x + barWidth / 2} y={y - 6} textAnchor="middle" className="text-[9px] font-extrabold fill-[#7C3AED] opacity-0 group-hover/bar:opacity-100 transition-opacity">
                                ₩{(h.sales / 1000).toFixed(0)}K
                              </text>
                            )}
                            {/* 하단 시간 레이블 */}
                            <text x={x + barWidth / 2} y={height - 10} textAnchor="middle" className="text-[10px] font-bold fill-gray-500">
                              {h.hour}
                            </text>
                          </g>
                        );
                      })}
                    </svg>
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      )}

      {/* 월간 정산 달력 섹션 */}
      {user?.role !== 'STAFF' && (
        <SettlementCalendar />
      )}

      {/* 내 키오스크 목록 섹션 */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-xl font-bold text-gray-900 flex items-center">
              <Monitor className="mr-2 text-[#7C3AED]" size={24} /> 
              {'내가 관리하는 키오스크 기기 목록'}
            </h3>
            <p className="text-gray-500 text-xs mt-1">기기를 클릭하면 해당 키오스크가 활성화되고 대시보드가 새로고침됩니다.</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-2xl text-sm font-semibold">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {kiosks.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-400 font-medium">
              등록된 키오스크 기기가 없습니다.
            </div>
          ) : (
            kiosks.map((kiosk) => (
              <div 
                key={kiosk.id} 
                onClick={() => {
                  localStorage.setItem('currentKioskId', kiosk.id);
                  localStorage.setItem('currentKioskName', kiosk.name);
                  window.location.reload();
                }}
                className={`bg-gray-50 hover:bg-purple-50/30 border rounded-3xl p-6 transition-all duration-200 cursor-pointer flex flex-col justify-between group ${
                  kiosk.id === currentKioskId ? 'border-[#7C3AED] bg-purple-50/10' : 'border-gray-100 hover:border-[#7C3AED]/30'
                }`}
              >
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="bg-[#7C3AED]/10 text-[#7C3AED] px-3 py-1 rounded-full text-xs font-bold font-mono">
                      {kiosk.code}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      kiosk.status === 'OPERATING' ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'
                    }`}>
                      {kiosk.status === 'OPERATING' ? '가동 중' : '대기 중'}
                    </span>
                  </div>
                  <h4 className="text-lg font-extrabold text-gray-900 group-hover:text-[#7C3AED] transition-colors">{kiosk.name}</h4>
                  <p className="text-gray-500 text-xs line-clamp-1">가맹 매장명: <span className="font-semibold text-gray-700">{kiosk.store_name || '미지정 매장'}</span></p>
                </div>
                <div className="mt-6 pt-4 border-t border-gray-100/60 flex justify-between items-center">
                  <div className="text-xs text-gray-600 font-semibold">
                    구분: <span className="text-gray-950 font-bold">{kiosk.type === 'Restaurant' ? '외식형' : '판매형'}</span>
                  </div>
                  <span className="text-xs text-[#7C3AED] font-bold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                    활성화 및 스위칭 <ArrowRight size={14} />
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
