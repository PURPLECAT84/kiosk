import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useKiosk } from '../context/KioskContext';
import { Receipt, Calendar, CreditCard, RefreshCw, X, AlertTriangle, Eye, Loader2, Download } from 'lucide-react';

interface OrderItemDetail {
  id: number;
  product_name: string;
  product_price: number;
  quantity: number;
}

interface OrderItem {
  id: number;
  order_no: string | null;
  total_amount: number;
  payment_method: string;
  payment_provider: string;
  approval_code: string;
  status: string;
  created_date: string;
  items: OrderItemDetail[];
  refund_amount?: number | null;
  refund_reason?: string | null;
  refund_method?: string | null;
  refunded_at?: string | null;
}

const getOrderStatusBadge = (status: string) => {
  switch (status) {
    case 'REFUNDED':
      return { text: '환불완료', className: 'bg-red-50 text-red-600' };
    case 'Completed':
      return { text: '결제완료', className: 'bg-green-50 text-green-600' };
    case 'Preparing':
      return { text: '준비중', className: 'bg-blue-50 text-blue-600' };
    case 'Cooking':
      return { text: '조리중', className: 'bg-yellow-50 text-yellow-600' };
    case 'Ready':
      return { text: '조리완료', className: 'bg-indigo-50 text-indigo-600' };
    case 'Served':
      return { text: '수령완료', className: 'bg-gray-100 text-gray-500' };
    default:
      return { text: status || '결제완료', className: 'bg-green-50 text-green-600' };
  }
};

const getOrderDetailStatusBadge = (status: string) => {
  if (status === 'REFUNDED') {
    return { text: '취소완료 (환불됨)', className: 'bg-red-50 text-red-600' };
  }
  switch (status) {
    case 'Preparing':
      return { text: '결제승인 (준비중)', className: 'bg-blue-50 text-blue-600' };
    case 'Cooking':
      return { text: '결제승인 (조리중)', className: 'bg-yellow-50 text-yellow-600' };
    case 'Ready':
      return { text: '결제승인 (조리완료)', className: 'bg-indigo-50 text-indigo-600' };
    case 'Served':
      return { text: '결제승인 (수령완료)', className: 'bg-gray-100 text-gray-500' };
    default:
      return { text: '결제완료 승인', className: 'bg-green-50 text-green-600' };
  }
};

export default function OrdersPage() {
  const { token } = useAuth();
  const { currentKioskId } = useKiosk();
  const [currentKiosk, setCurrentKiosk] = useState<any>(null);
  const [orders, setOrders] = useState<OrderItem[]>([]);
  
  const [isLoadingKiosk, setIsLoadingKiosk] = useState(true);
  const [isLoadingOrders, setIsLoadingOrders] = useState(false);
  const [error, setError] = useState('');

  // 영수증 상세 및 환불 모달 상태
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
  const [detailedOrder, setDetailedOrder] = useState<OrderItem | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  
  // 환불 입력 필드 상태
  const [isRefundConfirmOpen, setIsRefundConfirmOpen] = useState(false);
  const [isRefundInProgress, setIsRefundInProgress] = useState(false);
  const [refundAmount, setRefundAmount] = useState<number>(0);
  const [refundReason, setRefundReason] = useState<string>('고객 변심');
  const [refundMethod, setRefundMethod] = useState<string>('카드취소');

  // 1. 현재 키오스크 상세 조회
  const fetchKioskDetail = async () => {
    if (!currentKioskId) {
      setIsLoadingKiosk(false);
      return;
    }
    setIsLoadingKiosk(true);
    try {
      const res = await fetch(`/kiosks/${currentKioskId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 403) {
        throw new Error('키오스크 접근 권한이 없습니다 (403).');
      }
      if (!res.ok) throw new Error('키오스크 정보를 가져오지 못했습니다.');
      const data = await res.json();
      setCurrentKiosk(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoadingKiosk(false);
    }
  };

  // 2. 선택된 키오스크의 주문 내역 가져오기
  const fetchOrders = async () => {
    if (!currentKioskId) return;
    setIsLoadingOrders(true);
    try {
      const res = await fetch(`/order/?kiosk_id=${currentKioskId}`, {
        headers: { 
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error('주문 목록을 가져오지 못했습니다.');
      const data = await res.json();
      setOrders(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoadingOrders(false);
    }
  };

  useEffect(() => {
    fetchKioskDetail();
  }, [token, currentKioskId]);

  useEffect(() => {
    if (currentKioskId) {
      fetchOrders();
    }
  }, [currentKioskId]);

  // 3. 영수증 상세 내역 가져오기 (마스킹 해제)
  const handleOpenDetail = async (orderId: number) => {
    setSelectedOrderId(orderId);
    setIsLoadingDetail(true);
    setIsRefundConfirmOpen(false);
    try {
      const res = await fetch(`/order/${orderId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('영수증 상세 내역을 가져오지 못했습니다.');
      const data = await res.json();
      setDetailedOrder(data);
      // 환불 폼 기본값 세팅
      setRefundAmount(data.total_amount);
      setRefundMethod(data.payment_method === 'Card' ? '카드취소' : '현금환불');
      setRefundReason('고객 변심');
    } catch (err: any) {
      alert(err.message);
      setSelectedOrderId(null);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  // 4. 상세 환불 처리
  const handleRefund = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrderId || !detailedOrder) return;
    setIsRefundInProgress(true);
    try {
      const res = await fetch(`/order/${selectedOrderId}/refund`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          refund_amount: Number(refundAmount),
          refund_reason: refundReason,
          refund_method: refundMethod
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '환불 처리에 실패했습니다.');
      
      alert('환불(주문 취소) 처리가 완료되었습니다.');
      setIsRefundConfirmOpen(false);
      
      // 상세 정보 즉시 업데이트
      setDetailedOrder(data);
      
      // 목록 상태 업데이트
      setOrders(orders.map(o => o.id === selectedOrderId ? { 
        ...o, 
        status: 'REFUNDED',
        refund_amount: data.refund_amount,
        refund_reason: data.refund_reason,
        refund_method: data.refund_method,
        refunded_at: data.refunded_at
      } : o));
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsRefundInProgress(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedOrderId(null);
    setDetailedOrder(null);
  };

  // 5. 영수증 이미지 다운로드 (HTML Canvas 렌더링)
  const handleDownloadReceiptImage = () => {
    if (!detailedOrder) return;
    const canvas = document.createElement('canvas');
    canvas.width = 450;
    canvas.height = 650;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Background
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Outer Border
    ctx.strokeStyle = '#E5E7EB';
    ctx.lineWidth = 4;
    ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);

    // Title
    ctx.fillStyle = '#111827';
    ctx.font = 'bold 24px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('전자 영수증', canvas.width / 2, 60);

    // Details info
    ctx.fillStyle = '#6B7280';
    ctx.font = '14px sans-serif';
    ctx.fillText(`승인번호: ${detailedOrder.approval_code}`, canvas.width / 2, 95);
    ctx.fillText(`결제시간: ${new Date(detailedOrder.created_date).toLocaleString()}`, canvas.width / 2, 120);

    // Dash Line
    ctx.strokeStyle = '#D1D5DB';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(30, 145);
    ctx.lineTo(canvas.width - 30, 145);
    ctx.stroke();
    ctx.setLineDash([]); // reset

    // Table Header
    ctx.fillStyle = '#374151';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('상품명', 40, 175);
    ctx.textAlign = 'right';
    ctx.fillText('금액', canvas.width - 40, 175);

    let currentY = 210;
    detailedOrder.items.forEach((item) => {
      ctx.fillStyle = '#4B5563';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(`${item.product_name} x ${item.quantity}`, 40, currentY);
      ctx.textAlign = 'right';
      ctx.fillText(`₩${(item.product_price * item.quantity).toLocaleString()}`, canvas.width - 40, currentY);
      currentY += 30;
    });

    // Dash Line
    ctx.strokeStyle = '#D1D5DB';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(30, currentY + 10);
    ctx.lineTo(canvas.width - 30, currentY + 10);
    ctx.stroke();
    ctx.setLineDash([]);

    // Total Amount
    ctx.fillStyle = '#111827';
    ctx.font = 'bold 18px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('결제 총액', 40, currentY + 45);
    ctx.fillStyle = '#7C3AED';
    ctx.textAlign = 'right';
    ctx.fillText(`₩${detailedOrder.total_amount.toLocaleString()}`, canvas.width - 40, currentY + 45);

    // Refund Info if refunded
    if (detailedOrder.status === 'REFUNDED') {
      currentY += 90;
      ctx.fillStyle = '#FEF2F2';
      ctx.fillRect(30, currentY - 20, canvas.width - 60, 100);
      ctx.strokeStyle = '#FCA5A5';
      ctx.lineWidth = 1;
      ctx.strokeRect(30, currentY - 20, canvas.width - 60, 100);

      ctx.fillStyle = '#B91C1C';
      ctx.font = 'bold 14px sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('[환불 완료 이력]', 45, currentY + 5);
      ctx.fillStyle = '#7F1D1D';
      ctx.font = '12px sans-serif';
      ctx.fillText(`환불금액: ₩${detailedOrder.refund_amount?.toLocaleString()}`, 45, currentY + 28);
      ctx.fillText(`환불사유: ${detailedOrder.refund_reason || '사유 없음'} (${detailedOrder.refund_method})`, 45, currentY + 48);
      ctx.fillText(`환불일시: ${detailedOrder.refunded_at ? new Date(detailedOrder.refunded_at).toLocaleString() : '-'}`, 45, currentY + 68);
    }

    // Footer
    ctx.fillStyle = '#9CA3AF';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('이 영수증은 모바일/인터넷으로 발급된 증빙용입니다.', canvas.width / 2, canvas.height - 40);

    // Download trigger
    const link = document.createElement('a');
    link.download = `receipt_${detailedOrder.approval_code}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  if (isLoadingKiosk) {
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
          <h3 className="text-xl font-bold mb-2 font-sans">조회 권한 제한</h3>
          <p className="text-sm font-medium">{error}</p>
        </div>
      </div>
    );
  }

  if (!currentKioskId) {
    return (
      <div className="flex-grow p-8 flex flex-col justify-center items-center h-[60vh] text-center space-y-4">
        <AlertTriangle size={48} className="text-yellow-500 animate-bounce" />
        <h3 className="text-xl font-bold text-gray-800">관리 대상 키오스크 미선택</h3>
        <p className="text-gray-500 max-w-md">주문 매출 관리를 시작하려면 좌측 하단의 키오스크 선택기 또는 기기 관리 메뉴에서 관리 대상을 먼저 선택해 주세요.</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-1">매출 및 주문 관리</h1>
          <p className="text-gray-500 text-base">
            현재 관리 기기: <span className="font-bold text-[#7C3AED]">{currentKiosk?.name || '키오스크'}</span> ({currentKiosk?.store_name || '매장'})
          </p>
        </div>
      </div>

      {/* 주문 내역 목록 테이블 */}
      <div className="bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-100">
        {isLoadingOrders ? (
          <div className="flex justify-center items-center py-20">
            <Loader2 className="animate-spin text-[#7C3AED]" size={36} />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100 text-gray-600 font-semibold text-sm">
                  <th className="px-6 py-4">주문 일시</th>
                  <th className="px-6 py-4">주문 번호 (고객 휴대폰)</th>
                  <th className="px-6 py-4">구매 품목</th>
                  <th className="px-6 py-4">결제 수단</th>
                  <th className="px-6 py-4">결제 총액</th>
                  <th className="px-6 py-4">상태</th>
                  <th className="px-6 py-4 text-center">작업</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-700">
                {orders.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12 text-gray-400 font-medium">
                      검색 기간 내 주문 결제 데이터가 존재하지 않습니다.
                    </td>
                  </tr>
                ) : (
                  orders.map((order) => (
                    <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 font-medium text-gray-600">
                        {new Date(order.created_date).toLocaleString()}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`font-mono font-bold ${
                          order.order_no && order.order_no.includes('*') 
                            ? 'text-[#7C3AED] bg-[#7C3AED]/5 px-2.5 py-1 rounded-lg text-sm'
                            : 'text-gray-900'
                        }`}>
                          {order.order_no || '일반결제'}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-bold text-gray-900">
                        {order.items && order.items.length > 0 ? (
                          order.items.length === 1 ? (
                            order.items[0].product_name
                          ) : (
                            `${order.items[0].product_name} 외 ${order.items.length - 1}건`
                          )
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="px-6 py-4 flex items-center space-x-1.5 py-5">
                        <CreditCard size={16} className="text-gray-400" />
                        <span className="font-semibold text-gray-800">{order.payment_method} ({order.payment_provider})</span>
                      </td>
                      <td className="px-6 py-4 font-extrabold text-gray-900">
                        ₩{order.total_amount.toLocaleString()}
                      </td>
                      <td className="px-6 py-4">
                        {(() => {
                          const badge = getOrderStatusBadge(order.status);
                          return (
                            <span className={`px-3 py-1 rounded-full text-xs font-bold ${badge.className}`}>
                              {badge.text}
                            </span>
                          );
                        })()}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => handleOpenDetail(order.id)}
                          className="flex items-center space-x-1.5 bg-gray-100 hover:bg-[#7C3AED] hover:text-white text-gray-700 font-bold px-3 py-2 rounded-xl transition-all text-xs cursor-pointer mx-auto"
                        >
                          <Eye size={14} />
                          <span>{order.status === 'Completed' ? '영수증 보기' : '환불 내역 보기'}</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 영수증 상세 내역 및 환불 모달 */}
      {selectedOrderId && (
        <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8 shadow-xl space-y-6 relative overflow-y-auto max-h-[90vh]">
            <button onClick={handleCloseDetail} className="absolute right-6 top-6 text-gray-400 hover:text-gray-600 cursor-pointer">
              <X size={24} />
            </button>

            {isLoadingDetail ? (
              <div className="flex justify-center items-center py-20">
                <Loader2 className="animate-spin text-[#7C3AED]" size={36} />
              </div>
            ) : (
              detailedOrder && (
                <div className="space-y-6">
                  {/* 헤더 */}
                  <div className="text-center pb-4 border-b border-dashed border-gray-200">
                    <Receipt className="mx-auto text-[#7C3AED] mb-2" size={32} />
                    <h3 className="text-2xl font-bold text-gray-900">전자 영수증</h3>
                    <p className="text-xs text-gray-400 mt-1">거래번호: {detailedOrder.approval_code}</p>
                  </div>

                  {/* 세부 항목 */}
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">결제 시간</span>
                      <span className="text-gray-900 font-bold">{new Date(detailedOrder.created_date).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">주문 번호</span>
                      <span className="text-[#7C3AED] font-bold font-mono">
                        {detailedOrder.order_no || '-'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">결제 수단</span>
                      <span className="text-gray-900 font-bold">{detailedOrder.payment_method} ({detailedOrder.payment_provider})</span>
                    </div>
                  </div>

                  {/* 품목 영수증 표 */}
                  <div className="bg-gray-50 rounded-2xl p-5 space-y-3">
                    <span className="text-xs font-bold text-gray-400 block mb-2">구매 품목</span>
                    {detailedOrder.items.map((item, idx) => (
                      <div key={idx} className="flex justify-between text-sm text-gray-800">
                        <span className="font-semibold">{item.product_name} x {item.quantity}</span>
                        <span className="font-bold">₩{(item.product_price * item.quantity).toLocaleString()}</span>
                      </div>
                    ))}
                    <div className="border-t border-gray-200 pt-3 flex justify-between text-base font-extrabold text-gray-900 mt-2">
                      <span>결제 총액</span>
                      <span className="text-[#7C3AED]">₩{detailedOrder.total_amount.toLocaleString()}</span>
                    </div>
                  </div>

                  {/* 환불 완료 내역 노출 */}
                  {detailedOrder.status === 'REFUNDED' && (
                    <div className="bg-red-50 border border-red-200 rounded-2xl p-5 space-y-3">
                      <span className="text-xs font-bold text-red-600 block mb-1">⚠️ 환불 완료 상세 정보</span>
                      <div className="text-sm space-y-2 text-red-900">
                        <div className="flex justify-between">
                           <span className="font-medium text-red-700">환불 금액</span>
                          <span className="font-extrabold">₩{detailedOrder.refund_amount?.toLocaleString() || '0'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium text-red-700">환불 사유</span>
                          <span className="font-bold">{detailedOrder.refund_reason}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium text-red-700">환불 구분</span>
                          <span className="font-bold">{detailedOrder.refund_method}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium text-red-700">환불 일시</span>
                          <span className="font-bold">
                            {detailedOrder.refunded_at ? new Date(detailedOrder.refunded_at).toLocaleString() : '-'}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 상태 배지 */}
                  <div className="text-center">
                    {(() => {
                      const badge = getOrderDetailStatusBadge(detailedOrder.status);
                      return (
                        <span className={`px-4 py-1.5 rounded-full text-xs font-bold inline-block ${badge.className}`}>
                          {badge.text}
                        </span>
                      );
                    })()}
                  </div>

                  {/* 영수증 이미지 다운 및 결제 취소 단추 */}
                  <div className="flex space-x-2 pt-4 border-t border-gray-100">
                    <button
                      onClick={handleDownloadReceiptImage}
                      className="flex-1 flex items-center justify-center space-x-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-3.5 rounded-xl transition-all cursor-pointer text-sm"
                    >
                      <Download size={16} />
                      <span>영수증 다운로드</span>
                    </button>
                    
                    {detailedOrder.status !== 'REFUNDED' && !isRefundConfirmOpen && (
                      <button
                        onClick={() => setIsRefundConfirmOpen(true)}
                        className="flex-1 flex items-center justify-center space-x-1.5 bg-red-50 hover:bg-red-100 text-red-600 font-bold py-3.5 rounded-xl transition-all cursor-pointer text-sm"
                      >
                        <RefreshCw size={16} />
                        <span>결제 취소 (환불)</span>
                      </button>
                    )}
                  </div>

                  {/* 환불 상세 입력 모달 폼 */}
                  {detailedOrder.status !== 'REFUNDED' && isRefundConfirmOpen && (
                    <form onSubmit={handleRefund} className="space-y-4 bg-red-50 border border-red-200 p-5 rounded-2xl">
                      <div className="flex items-center space-x-2 text-red-700 font-bold text-sm">
                        <AlertTriangle size={18} />
                        <span>환불 상세 사유 입력</span>
                      </div>

                      <div className="space-y-3">
                        <div>
                          <label className="block text-xs font-bold text-red-800 mb-1">환불 가능금액 (최대 ₩{detailedOrder.total_amount.toLocaleString()})</label>
                          <input
                            type="number"
                            value={refundAmount}
                            onChange={(e) => setRefundAmount(Math.min(detailedOrder.total_amount, Number(e.target.value)))}
                            className="w-full px-3 py-2 border border-red-200 bg-white rounded-xl focus:ring-1 focus:ring-red-500 focus:border-red-500 outline-none text-sm font-semibold text-gray-800"
                            max={detailedOrder.total_amount}
                            min={0}
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-bold text-red-800 mb-1">환불 수단</label>
                          <select
                            value={refundMethod}
                            onChange={(e) => setRefundMethod(e.target.value)}
                            className="w-full px-3 py-2 border border-red-200 bg-white rounded-xl focus:ring-1 focus:ring-red-500 focus:border-red-500 outline-none text-sm font-semibold text-gray-850 cursor-pointer"
                          >
                            <option value="카드취소">신용카드 승인 취소</option>
                            <option value="현금환불">현금 반환</option>
                            <option value="계좌이체">계좌 이체 환불</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs font-bold text-red-800 mb-1">환불 처리 사유</label>
                          <input
                            type="text"
                            value={refundReason}
                            onChange={(e) => setRefundReason(e.target.value)}
                            placeholder="예: 품절로 인한 주문 취소"
                            className="w-full px-3 py-2 border border-red-200 bg-white rounded-xl focus:ring-1 focus:ring-red-500 focus:border-red-500 outline-none text-sm font-semibold text-gray-800"
                            required
                          />
                        </div>
                      </div>

                      <div className="flex space-x-2 pt-2">
                        <button
                          type="button"
                          onClick={() => setIsRefundConfirmOpen(false)}
                          className="flex-1 bg-white hover:bg-gray-100 text-gray-700 font-bold py-2 rounded-xl text-xs transition-colors cursor-pointer border border-red-200"
                        >
                          취소
                        </button>
                        <button
                          type="submit"
                          disabled={isRefundInProgress}
                          className="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-2 rounded-xl text-xs transition-all flex justify-center items-center cursor-pointer"
                        >
                          {isRefundInProgress ? <Loader2 className="animate-spin" size={16} /> : '환불 완료하기'}
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
}
