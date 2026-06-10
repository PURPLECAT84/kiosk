import React, { useState } from 'react';
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useKiosk } from '../context/KioskContext';
import { LayoutDashboard, Receipt, Package, Users, LogOut, Store, UserCircle, Monitor, ChevronDown } from 'lucide-react';
import EmptyPage from './EmptyPage';
import DashboardHome from './DashboardHome';
import ProfilePage from './ProfilePage';
import StoreManagement from './StoreManagement';
import StoreDetail from './StoreDetail';
import KioskManagement from './KioskManagement';
import KioskDetail from './KioskDetail';
import OrdersPage from './OrdersPage';
import ProductManagement from './ProductManagement';
import UserManagement from './UserManagement';

export default function Dashboard() {
  const { user, isLoading, logout, token } = useAuth();
  const { currentKioskId, currentKioskName, currentStoreName, myKiosks, setCurrentKioskId } = useKiosk();
  const [isKioskDropdownOpen, setIsKioskDropdownOpen] = useState(false);
  const location = useLocation();

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

  // 권한별 사이드바 메뉴 가시성 체크
  const canAccessStore = ['DEV', 'HEAD', 'MASTER'].includes(user.role);
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
          
          {/* 매장 관리 (DEV/HEAD/MASTER 전용) */}
          {canAccessStore && (
            <NavItem to="/stores" icon={Store} label="매장 관리" />
          )}

          {/* 키오스크 기기 관리 (DEV/HEAD/MASTER/MANAGER 전용) */}
          {canAccessKiosk && (
            <NavItem to="/kiosks" icon={Monitor} label="키오스크 관리" />
          )}

          <NavItem to="/orders" icon={Receipt} label="주문 내역" />
          <NavItem to="/products" icon={Package} label="상품 관리" />
          {canAccessStore && (
            <NavItem to="/users" icon={Users} label="사용자 관리" />
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
             location.pathname.startsWith('/stores') ? '매장 관리' : 
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
            
            {/* 매장 관리 라우팅 (가드 적용) */}
            <Route 
              path="/stores" 
              element={canAccessStore ? <StoreManagement /> : <Navigate to="/" replace />} 
            />
            <Route 
              path="/stores/:id" 
              element={canAccessStore || user.role === 'MANAGER' ? <StoreDetail /> : <Navigate to="/" replace />} 
            />

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
            <Route path="/products" element={<ProductManagement />} />
            <Route 
              path="/users" 
              element={canAccessStore ? <UserManagement /> : <Navigate to="/" replace />} 
            />
            <Route path="/settings" element={<EmptyPage title="매장 설정" />} />
            <Route path="/profile" element={<React.Suspense fallback={<div>Loading...</div>}><ProfilePage /></React.Suspense>} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
