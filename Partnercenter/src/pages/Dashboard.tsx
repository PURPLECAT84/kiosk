import React from 'react';
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Receipt, Package, Settings, LogOut, Store } from 'lucide-react';
import EmptyPage from './EmptyPage';

export default function Dashboard() {
  const { user, isLoading, logout } = useAuth();
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

  const NavItem = ({ to, icon: Icon, label }: { to: string, icon: any, label: string }) => {
    const isActive = location.pathname === to;
    return (
      <Link
        to={to}
        className={`flex items-center space-x-3 px-4 py-3 rounded-xl mb-2 transition-colors text-lg font-medium ${
          isActive 
            ? 'bg-[#7C3AED] text-white' 
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
      <aside className="w-72 bg-white shadow-sm flex flex-col">
        <div className="p-6 flex items-center space-x-3 border-b border-gray-100">
          <div className="bg-[#7C3AED] text-white p-2 rounded-lg">
            <Store size={28} />
          </div>
          <span className="text-2xl font-bold text-gray-900">Partner</span>
        </div>
        
        <div className="p-4 flex-1">
          <NavItem to="/" icon={LayoutDashboard} label="대시보드" />
          <NavItem to="/orders" icon={Receipt} label="주문 내역" />
          <NavItem to="/products" icon={Package} label="상품 관리" />
          <NavItem to="/settings" icon={Settings} label="설정" />
        </div>

        <div className="p-4 border-t border-gray-100">
          <div className="flex items-center space-x-3 px-4 py-3 mb-4 bg-gray-50 rounded-xl">
            <div className="w-10 h-10 rounded-full bg-[#7C3AED] text-white flex items-center justify-center font-bold text-lg">
              {user.name.charAt(0)}
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold text-gray-900">{user.name}</span>
              <span className="text-xs text-gray-500">{user.email}</span>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-red-600 hover:bg-red-50 transition-colors text-lg font-medium"
          >
            <LogOut size={24} />
            <span>로그아웃</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="bg-white shadow-sm p-6 flex justify-between items-center z-10">
          <h2 className="text-2xl font-bold text-gray-800">
            {location.pathname === '/' ? '대시보드' : 
             location.pathname === '/orders' ? '주문 내역' : 
             location.pathname === '/products' ? '상품 관리' : '설정'}
          </h2>
          <div className="bg-gray-100 px-4 py-2 rounded-full text-sm font-medium text-gray-600">
            {user.role} 권한으로 접속중
          </div>
        </header>
        
        <div className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<EmptyPage title="대시보드 홈" />} />
            <Route path="/orders" element={<EmptyPage title="주문 내역" />} />
            <Route path="/products" element={<EmptyPage title="상품 관리" />} />
            <Route path="/settings" element={<EmptyPage title="매장 설정" />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
