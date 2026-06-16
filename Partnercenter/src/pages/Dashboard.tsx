import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useKiosk } from '../context/KioskContext';
import { LayoutDashboard, Receipt, Package, Users, LogOut, Store, UserCircle, Monitor, ChevronDown, Play, CheckCircle2, Loader2, Layers } from 'lucide-react';
import EmptyPage from './EmptyPage';
import DashboardHome from './DashboardHome';
import ProfilePage from './ProfilePage';
import KioskManagement from './KioskManagement';
import KioskDetail from './KioskDetail';
import OrdersPage from './OrdersPage';
import ProductManagement from './ProductManagement';
import UserManagement from './UserManagement';
import CounterBoard from './CounterBoard';
import BillingProductManagement from './BillingProductManagement';

export default function Dashboard() {
  const { user, isLoading, logout, token, refreshUser } = useAuth();
  const { currentKioskId, currentKioskName, currentStoreName, myKiosks, setCurrentKioskId } = useKiosk();
  const [isKioskDropdownOpen, setIsKioskDropdownOpen] = useState(false);
  const location = useLocation();

  // 본인인증 관련 상태
  const [verifyName, setVerifyName] = useState('');
  const [verifyPhone, setVerifyPhone] = useState('');
  const [verifyOperator, setVerifyOperator] = useState('SKT');
  const [verifyBirthDate, setVerifyBirthDate] = useState('');
  const [verifyGender, setVerifyGender] = useState('MALE');
  const [verifyOtp, setVerifyOtp] = useState('');
  
  const [isOtpSent, setIsOtpSent] = useState(false);
  const [verificationId, setVerificationId] = useState('');
  const [verificationTimer, setVerificationTimer] = useState(0);
  const [isVerifying, setIsVerifying] = useState(false);

  // 본인인증 타이머 설정
  useEffect(() => {
    if (verificationTimer <= 0) return;
    const interval = setInterval(() => {
      setVerificationTimer(prev => prev - 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [verificationTimer]);

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsVerifying(true);
    try {
      const res = await fetch('/auth/identity-verification/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: verifyName,
          phone: verifyPhone,
          operator: verifyOperator,
          birth_date: verifyBirthDate,
          gender: verifyGender
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || '인증번호 발송에 실패했습니다.');
      }
      const data = await res.json();
      setVerificationId(data.verification_id);
      setIsOtpSent(true);
      setVerificationTimer(180);
      alert('인증번호 문자가 발송되었습니다. 수신하신 6자리 번호를 입력해주세요.');
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleConfirmOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verificationId) return;
    setIsVerifying(true);
    try {
      const res = await fetch('/auth/identity-verification/confirm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          verification_id: verificationId,
          otp: verifyOtp
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || '인증번호 확인에 실패했습니다.');
      }
      alert('본인확인 실명인증이 성공적으로 완료되었습니다!');
      await refreshUser();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsVerifying(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F9FAFB] flex justify-center items-center">
        <p className="text-xl text-gray-500 font-medium">로딩 중...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // 본인인증(실명인증) 미완료 시 온보딩 화면을 강제 노출하여 대시보드 접근 차단
  // 단, 개발 관리 및 업무 신속성을 위해 개발자(DEV) 및 본사(HEAD) 관리자는 본인인증 온보딩 가드를 우회할 수 있도록 예외 적용합니다.
  if (user && !user.is_identity_verified && user.role !== 'DEV' && user.role !== 'HEAD') {
    return (
      <div className="min-h-screen bg-[#F9FAFB] flex flex-col justify-center items-center p-4 font-sans">
        <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-xl border border-gray-100 space-y-6">
          <div className="text-center relative">
            <button
              onClick={logout}
              className="absolute -top-2 -right-2 p-2 text-gray-400 hover:text-red-500 rounded-full hover:bg-gray-100 transition-colors flex items-center justify-center cursor-pointer"
              title="로그아웃"
            >
              <LogOut size={22} />
            </button>
            <div className="w-16 h-16 bg-[#7C3AED]/10 text-[#7C3AED] rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 size={32} />
            </div>
            <h3 className="text-3xl font-extrabold text-gray-900">본인확인 실명인증</h3>
            <p className="text-gray-500 text-sm mt-2 leading-relaxed">
              MOKI 파트너의 안전한 결제 및 서비스 이용을 위해 휴대폰 본인인증(실명인증)을 완료해 주세요.
            </p>
          </div>

          <form onSubmit={handleSendOtp} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">이름</label>
              <input
                type="text"
                value={verifyName}
                onChange={(e) => setVerifyName(e.target.value)}
                disabled={isOtpSent}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base font-semibold disabled:bg-gray-50"
                placeholder="실명 입력"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">생년월일 (8자리)</label>
                <input
                  type="text"
                  maxLength={8}
                  value={verifyBirthDate}
                  onChange={(e) => setVerifyBirthDate(e.target.value)}
                  disabled={isOtpSent}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base font-semibold disabled:bg-gray-50"
                  placeholder="예: 19900101"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">성별</label>
                <div className="flex border border-gray-300 rounded-xl p-0.5 bg-gray-50">
                  <button
                    type="button"
                    disabled={isOtpSent}
                    onClick={() => setVerifyGender('MALE')}
                    className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all ${
                      verifyGender === 'MALE' ? 'bg-[#7C3AED] text-white shadow-sm' : 'text-gray-500 hover:bg-gray-100'
                    }`}
                  >
                    남성
                  </button>
                  <button
                    type="button"
                    disabled={isOtpSent}
                    onClick={() => setVerifyGender('FEMALE')}
                    className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all ${
                      verifyGender === 'FEMALE' ? 'bg-[#7C3AED] text-white shadow-sm' : 'text-gray-500 hover:bg-gray-100'
                    }`}
                  >
                    여성
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="col-span-1">
                <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">통신사</label>
                <select
                  value={verifyOperator}
                  onChange={(e) => setVerifyOperator(e.target.value)}
                  disabled={isOtpSent}
                  className="w-full px-3 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none bg-white text-sm font-bold disabled:bg-gray-50"
                >
                  <option value="SKT">SKT</option>
                  <option value="KT">KT</option>
                  <option value="LGU">LGU</option>
                  <option value="SKT_MVNO">SKT 알뜰</option>
                  <option value="KT_MVNO">KT 알뜰</option>
                  <option value="LGU_MVNO">LGU 알뜰</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-bold text-gray-500 mb-1.5 uppercase tracking-wider">휴대폰 번호</label>
                <input
                  type="text"
                  value={verifyPhone}
                  onChange={(e) => setVerifyPhone(e.target.value)}
                  disabled={isOtpSent}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base font-semibold disabled:bg-gray-50"
                  placeholder="숫자만 입력"
                  required
                />
              </div>
            </div>

            {!isOtpSent && (
              <button
                type="submit"
                disabled={isVerifying}
                className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-4 rounded-xl transition-all flex justify-center items-center cursor-pointer shadow-sm text-base"
              >
                {isVerifying ? <Loader2 className="animate-spin" size={22} /> : '인증번호 발송 요청'}
              </button>
            )}
          </form>

          {isOtpSent && (
            <form onSubmit={handleConfirmOtp} className="space-y-4 pt-6 border-t border-gray-100 animate-fade-in">
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider">인증번호 입력</label>
                  {verificationTimer > 0 && (
                    <span className="text-red-500 font-extrabold text-sm">
                      {Math.floor(verificationTimer / 60)}:{(verificationTimer % 60).toString().padStart(2, '0')}
                    </span>
                  )}
                </div>
                <div className="relative">
                  <input
                    type="text"
                    maxLength={6}
                    value={verifyOtp}
                    onChange={(e) => setVerifyOtp(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base font-extrabold tracking-widest text-center"
                    placeholder="6자리 숫자"
                    required
                  />
                </div>
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsOtpSent(false);
                    setVerificationTimer(0);
                    setVerifyOtp('');
                  }}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-3.5 rounded-xl transition-colors cursor-pointer text-center text-sm"
                >
                  이전으로
                </button>
                <button
                  type="submit"
                  disabled={isVerifying || verificationTimer <= 0}
                  className="flex-1 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3.5 rounded-xl transition-colors flex justify-center items-center cursor-pointer text-center text-sm disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {isVerifying ? <Loader2 className="animate-spin" size={20} /> : '인증 완료'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    );
  }

  // 권한별 사이드바 메뉴 가시성 체크
  const canAccessAdmin = ['DEV', 'HEAD', 'MASTER'].includes(user.role);
  const canAccessKiosk = ['DEV', 'HEAD', 'MASTER', 'MANAGER'].includes(user.role);

  const NavItem = ({ to, icon: Icon, label }: { to: string, icon: any, label: string }) => {
    const isActive = location.pathname.startsWith(to) && (to !== '/' || location.pathname === '/');
    return (
      <Link
        to={to}
        className={`flex items-center space-x-3 px-4 py-3 rounded-xl mb-2 transition-colors text-lg font-medium ${
          isActive 
            ? 'bg-[#7C3AED] text-white shadow-sm' 
            : 'text-gray-600 hover:bg-gray-100'
        }`}
      >
        <Icon size={24} />
        <span>{label}</span>
      </Link>
    );
  };

  return (
    <div className="min-h-screen bg-[#F9FAFB] flex font-sans">
      {/* Sidebar */}
      <aside className="w-72 bg-white shadow-sm flex flex-col border-r border-gray-150">
        <Link to="/" className="p-6 flex items-center space-x-3 border-b border-gray-100 hover:bg-gray-50 transition-colors">
          <div className="bg-[#7C3AED] text-white p-2 rounded-lg">
            <Store size={28} />
          </div>
          <span className="text-2xl font-bold text-gray-900">Partner</span>
        </Link>
        
        <div className="p-4 flex-1">
          <NavItem to="/" icon={LayoutDashboard} label="대시보드" />
          


          {/* 키오스크 기기 관리 (DEV/HEAD/MASTER/MANAGER 전용) */}
          {canAccessKiosk && (
            <NavItem to="/kiosks" icon={Monitor} label="키오스크 관리" />
          )}

          <NavItem to="/orders" icon={Receipt} label="주문 내역" />
          {canAccessKiosk && (
            <NavItem to="/counter-board" icon={Play} label="주방 오더 보드" />
          )}
          <NavItem to="/products" icon={Package} label="상품 관리" />
          {canAccessAdmin && (
            <NavItem to="/users" icon={Users} label="사용자 관리" />
          )}
          {canAccessAdmin && (
            <NavItem to="/billing-products" icon={Layers} label="이용료 관리" />
          )}
        </div>

        {/* Sidebar Bottom: Active Kiosk Indicator and Dropdown */}
        <div className="p-4 border-t border-gray-100 relative">
          <div className="text-xs font-bold text-gray-400 mb-2 uppercase tracking-wider">
            활성 키오스크 설정
          </div>
          <button
            onClick={() => setIsKioskDropdownOpen(!isKioskDropdownOpen)}
            className="w-full flex items-center justify-between space-x-2 px-3 py-2.5 bg-purple-50 hover:bg-purple-100/70 border border-purple-200/50 rounded-xl transition-all cursor-pointer text-left"
          >
            <div className="flex items-center space-x-2.5 overflow-hidden">
              <div className="bg-[#7C3AED] text-white p-1.5 rounded-lg flex-shrink-0">
                <Monitor size={16} />
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-extrabold text-gray-900 truncate">
                  {currentKioskName || '기기 미선택'}
                </span>
                <span className="text-[10px] text-[#7C3AED] font-semibold truncate">
                  {currentStoreName || '매장 미지정'}
                </span>
              </div>
            </div>
            <ChevronDown size={14} className={`text-gray-500 transition-transform flex-shrink-0 ${isKioskDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isKioskDropdownOpen && (
            <div className="absolute bottom-full left-4 right-4 mb-2 bg-white border border-gray-200 rounded-2xl shadow-xl z-25 max-h-60 overflow-y-auto divide-y divide-gray-100">
              {myKiosks.length === 0 ? (
                <div className="p-4 text-xs text-gray-400 text-center font-medium">
                  관리 가능한 기기가 없습니다.
                </div>
              ) : (
                myKiosks.map((kiosk) => {
                  const isActive = kiosk.id === currentKioskId;
                  return (
                    <button
                      key={kiosk.id}
                      onClick={() => {
                        setCurrentKioskId(kiosk.id);
                        setIsKioskDropdownOpen(false);
                        window.location.href = '/';
                      }}
                      className={`w-full text-left px-4 py-3 text-xs transition-colors flex items-center justify-between cursor-pointer ${
                        isActive ? 'bg-purple-50 text-[#7C3AED] font-bold' : 'hover:bg-gray-50 text-gray-700 font-medium'
                      }`}
                    >
                      <div className="flex flex-col min-w-0 pr-2">
                        <span className="font-extrabold truncate">{kiosk.name}</span>
                        <span className="text-[10px] text-gray-400 truncate">{kiosk.store_name || '매장 미지정'}</span>
                      </div>
                      {isActive && <div className="w-1.5 h-1.5 rounded-full bg-[#7C3AED]" />}
                    </button>
                  );
                })
              )}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="bg-white shadow-sm p-6 flex justify-between items-center z-10">
          <h2 className="text-2xl font-bold text-gray-800">
            {location.pathname === '/' ? '대시보드' : 
             location.pathname.startsWith('/kiosks') ? '키오스크 관리' : 
             location.pathname === '/orders' ? '주문 내역' : 
             location.pathname === '/products' ? '상품 관리' : 
             location.pathname === '/profile' ? '내 정보' : 
             location.pathname.startsWith('/users') ? '사용자 관리' : '설정'}
          </h2>
          <div className="flex items-center space-x-4">
            <div className="bg-gray-100 px-4 py-2 rounded-full text-sm font-bold text-gray-600">
              {user.role} 권한으로 접속중
            </div>
            <Link 
              to="/profile" 
              className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-full transition-colors cursor-pointer"
              title="내 정보"
            >
              <UserCircle size={24} />
              <span className="text-sm font-bold text-gray-700">{user.name}</span>
            </Link>
            <button
              onClick={logout}
              className="p-2 text-red-500 hover:bg-red-50 rounded-full transition-colors flex items-center justify-center cursor-pointer"
              title="로그아웃"
            >
              <LogOut size={28} />
            </button>
          </div>
        </header>
        
        <div className="flex-1 overflow-auto bg-[#F9FAFB]">
          <Routes>
            <Route path="/" element={<DashboardHome />} />
            


            {/* 키오스크 관리 라우팅 (가드 적용) */}
            <Route 
              path="/kiosks" 
              element={canAccessKiosk ? <KioskManagement /> : <Navigate to="/" replace />} 
            />
            <Route 
              path="/kiosks/:id" 
              element={canAccessKiosk ? <KioskDetail /> : <Navigate to="/" replace />} 
            />

            <Route path="/orders" element={<OrdersPage />} />
            <Route 
              path="/counter-board" 
              element={canAccessKiosk ? <CounterBoard /> : <Navigate to="/" replace />} 
            />
            <Route path="/products" element={<ProductManagement />} />
            <Route 
              path="/users" 
              element={canAccessAdmin ? <UserManagement /> : <Navigate to="/" replace />} 
            />
            <Route 
              path="/billing-products" 
              element={canAccessAdmin ? <BillingProductManagement /> : <Navigate to="/" replace />} 
            />
            <Route path="/settings" element={<EmptyPage title="매장 설정" />} />
            <Route path="/profile" element={<React.Suspense fallback={<div>Loading...</div>}><ProfilePage /></React.Suspense>} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
