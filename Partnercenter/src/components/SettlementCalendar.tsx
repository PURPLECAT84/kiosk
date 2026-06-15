import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useKiosk } from '../context/KioskContext';
import { Calendar, ChevronLeft, ChevronRight, Loader2, DollarSign, RefreshCcw, Download } from 'lucide-react';

interface SettlementData {
  date: string;
  sales: number;
  orders: number;
  refunds: number;
}

export default function SettlementCalendar() {
  const { token } = useAuth();
  const { currentKioskId } = useKiosk();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [settlements, setSettlements] = useState<Record<string, SettlementData>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState('');

  const handleDownloadCsv = async () => {
    setIsDownloading(true);
    try {
      const headers: Record<string, string> = {
        'Authorization': `Bearer ${token}`
      };
      if (currentKioskId) {
        headers['X-Kiosk-Id'] = currentKioskId;
      }
      const res = await fetch(`/dashboard/settlement/download?year=${year}&month=${month}`, {
        headers
      });
      if (!res.ok) {
        throw new Error('정산 파일 다운로드에 실패했습니다.');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `moki_settlement_${year}_${String(month).padStart(2, '0')}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsDownloading(false);
    }
  };

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth() + 1; // 1-indexed

  const fetchSettlement = async () => {
    setIsLoading(true);
    setError('');
    try {
      const headers: Record<string, string> = {
        'Authorization': `Bearer ${token}`
      };
      if (currentKioskId) {
        headers['X-Kiosk-Id'] = currentKioskId;
      }

      const res = await fetch(`/dashboard/settlement?year=${year}&month=${month}`, { headers });
      if (!res.ok) {
        throw new Error('정산 정보를 불러오는데 실패했습니다.');
      }
      const data: SettlementData[] = await res.json();
      
      // 날짜별로 매핑 (date string: YYYY-MM-DD -> SettlementData)
      const mapped: Record<string, SettlementData> = {};
      data.forEach(item => {
        mapped[item.date] = item;
      });
      setSettlements(mapped);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSettlement();
  }, [token, currentKioskId, year, month]);

  // 달력 렌더링을 위한 헬퍼들
  const getDaysInMonth = (y: number, m: number) => new Date(y, m, 0).getDate();
  const getFirstDayOfMonth = (y: number, m: number) => new Date(y, m - 1, 1).getDay();

  const daysInMonth = getDaysInMonth(year, month);
  const firstDayIndex = getFirstDayOfMonth(year, month);

  const prevMonthDays = getDaysInMonth(year, month - 1 === 0 ? 12 : month - 1);

  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, currentDate.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, currentDate.getMonth() + 1, 1));
  };

  const daysArray: { day: number; isCurrentMonth: boolean; dateStr: string }[] = [];

  // 이전 달의 남은 날짜들 채우기
  for (let i = firstDayIndex - 1; i >= 0; i--) {
    const d = prevMonthDays - i;
    const m = month - 1 === 0 ? 12 : month - 1;
    const y = month - 1 === 0 ? year - 1 : year;
    const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    daysArray.push({ day: d, isCurrentMonth: false, dateStr });
  }

  // 이번 달 날짜들 채우기
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    daysArray.push({ day: d, isCurrentMonth: true, dateStr });
  }

  // 다음 달의 날짜들로 그리드 채우기 (총 42칸 기준)
  const remaining = 42 - daysArray.length;
  for (let d = 1; d <= remaining; d++) {
    const m = month + 1 === 13 ? 1 : month + 1;
    const y = month + 1 === 13 ? year + 1 : year;
    const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    daysArray.push({ day: d, isCurrentMonth: false, dateStr });
  }

  // 이번 달 총 집계 계산
  const totalMonthlySales = Object.values(settlements).reduce((acc, curr) => acc + curr.sales, 0);
  const totalMonthlyRefunds = Object.values(settlements).reduce((acc, curr) => acc + curr.refunds, 0);
  const netMonthlySales = totalMonthlySales - totalMonthlyRefunds;

  const weekdays = ['일', '월', '화', '수', '목', '금', '토'];

  return (
    <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 space-y-6">
      {/* 달력 헤더 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-gray-100">
        <div>
          <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Calendar className="text-[#7C3AED]" size={24} />
            <span>월간 정산 달력</span>
          </h3>
          <p className="text-xs text-gray-400 mt-1">일별 매출 합계와 환불액을 월간 캘린더 형식으로 확인합니다.</p>
        </div>

        {/* 월 이동 컨트롤러 및 다운로드 */}
        <div className="flex items-center gap-3 self-center sm:self-auto">
          <div className="flex items-center space-x-3 bg-gray-50 p-1 rounded-2xl border border-gray-100 shadow-sm">
            <button 
              onClick={handlePrevMonth}
              className="p-2 hover:bg-gray-100 rounded-xl transition-colors text-gray-600 cursor-pointer"
            >
              <ChevronLeft size={20} />
            </button>
            <span className="text-base font-extrabold text-gray-800 px-2 min-w-[100px] text-center">
              {year}년 {month}월
            </span>
            <button 
              onClick={handleNextMonth}
              className="p-2 hover:bg-gray-100 rounded-xl transition-colors text-gray-600 cursor-pointer"
            >
              <ChevronRight size={20} />
            </button>
          </div>

          <button
            onClick={handleDownloadCsv}
            disabled={isDownloading}
            className="flex items-center gap-2 bg-[#7C3AED] hover:bg-[#6D28D9] text-white px-4 py-2.5 rounded-2xl text-sm font-bold shadow-sm transition-all cursor-pointer disabled:bg-purple-300 disabled:cursor-not-allowed"
            title="당월 정산 데이터를 엑셀(CSV)로 내려받습니다."
          >
            {isDownloading ? (
              <Loader2 className="animate-spin" size={16} />
            ) : (
              <Download size={16} />
            )}
            <span>엑셀 다운로드</span>
          </button>
        </div>
      </div>

      {/* 월간 합계 집계 보드 (Bento Style) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-purple-50 to-indigo-50 p-4 rounded-2xl border border-purple-100 flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-purple-600 block">당월 총 매출액</span>
            <span className="text-xl font-extrabold text-gray-900 mt-1 block">₩{totalMonthlySales.toLocaleString()}</span>
          </div>
          <div className="p-3 bg-purple-100 text-purple-700 rounded-xl">
            <DollarSign size={20} />
          </div>
        </div>

        <div className="bg-gradient-to-br from-red-50 to-orange-50 p-4 rounded-2xl border border-red-100 flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-red-600 block">당월 총 환불액</span>
            <span className="text-xl font-extrabold text-gray-900 mt-1 block">₩{totalMonthlyRefunds.toLocaleString()}</span>
          </div>
          <div className="p-3 bg-red-100 text-red-700 rounded-xl">
            <RefreshCcw size={20} />
          </div>
        </div>

        <div className="bg-gradient-to-br from-emerald-50 to-teal-50 p-4 rounded-2xl border border-emerald-100 flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-emerald-600 block">당월 순 매출액</span>
            <span className="text-xl font-extrabold text-gray-900 mt-1 block">₩{netMonthlySales.toLocaleString()}</span>
          </div>
          <div className="p-3 bg-emerald-100 text-emerald-700 rounded-xl font-bold text-lg">
            ✓
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 px-4 py-3 rounded-2xl text-sm font-semibold">
          {error}
        </div>
      )}

      {/* 달력 그리드 */}
      <div className="relative">
        {isLoading && (
          <div className="absolute inset-0 bg-white/70 backdrop-blur-[2px] z-10 flex justify-center items-center rounded-2xl">
            <Loader2 className="animate-spin text-[#7C3AED]" size={36} />
          </div>
        )}

        {/* 요일 헤더 */}
        <div className="grid grid-cols-7 gap-2 mb-2 text-center">
          {weekdays.map((day, idx) => (
            <div 
              key={idx} 
              className={`text-xs font-bold py-2 ${
                idx === 0 ? 'text-red-500' : idx === 6 ? 'text-blue-500' : 'text-gray-500'
              }`}
            >
              {day}
            </div>
          ))}
        </div>

        {/* 날짜 셀 그리드 */}
        <div className="grid grid-cols-7 gap-2">
          {daysArray.map((cell, idx) => {
            const data = settlements[cell.dateStr];
            const hasData = !!data;
            const isToday = new Date().toISOString().split('T')[0] === cell.dateStr;

            return (
              <div
                key={idx}
                className={`min-h-[90px] p-2 rounded-2xl border flex flex-col justify-between transition-all duration-200 group relative ${
                  cell.isCurrentMonth
                    ? isToday
                      ? 'bg-purple-50/40 border-[#7C3AED] shadow-sm'
                      : 'bg-gray-50/50 border-gray-100 hover:bg-white hover:border-gray-300 hover:shadow-md hover:-translate-y-0.5'
                    : 'bg-gray-100/30 border-gray-50 text-gray-300'
                }`}
              >
                {/* 날짜 표시 */}
                <div className="flex justify-between items-center">
                  <span 
                    className={`text-xs font-bold ${
                      !cell.isCurrentMonth
                        ? 'text-gray-300'
                        : isToday
                          ? 'text-[#7C3AED] bg-purple-100/70 px-1.5 py-0.5 rounded-md'
                          : idx % 7 === 0 
                            ? 'text-red-500' 
                            : idx % 7 === 6 
                              ? 'text-blue-500' 
                              : 'text-gray-700'
                    }`}
                  >
                    {cell.day}
                  </span>
                  
                  {/* 주문 수 뱃지 */}
                  {hasData && data.orders > 0 && (
                    <span className="text-[9px] font-extrabold bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded-full border border-blue-100/50 group-hover:scale-105 transition-transform">
                      {data.orders}건
                    </span>
                  )}
                </div>

                {/* 매출/환불 정보 */}
                <div className="mt-2 space-y-0.5 text-right overflow-hidden">
                  {hasData ? (
                    <>
                      {data.sales > 0 && (
                        <div className="text-[10px] font-bold text-gray-900 truncate">
                          ₩{data.sales.toLocaleString()}
                        </div>
                      )}
                      {data.refunds > 0 && (
                        <div className="text-[9px] font-bold text-red-500 truncate">
                          -₩{data.refunds.toLocaleString()}
                        </div>
                      )}
                    </>
                  ) : (
                    cell.isCurrentMonth && (
                      <div className="text-[9px] text-gray-300 italic">-</div>
                    )
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
