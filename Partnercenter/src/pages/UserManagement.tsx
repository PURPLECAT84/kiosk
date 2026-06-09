import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Users, Loader2, Store, Monitor } from 'lucide-react';

interface KioskSummary {
  active_count: int;
  inactive_count: int;
}

interface UserItem {
  id: string;
  email: string;
  name: string;
  phone: string | null;
  role: string;
  status: string;
  created_at: string;
  store_names_summary: string;
  kiosks_summary: KioskSummary;
}

export default function UserManagement() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/users/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.status === 403 || res.status === 401) {
        throw new Error('사용자 목록 관리 권한이 없습니다.');
      }
      if (!res.ok) throw new Error('사용자 정보를 불러오는 데 실패했습니다.');
      const data = await res.json();
      setUsers(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [token]);

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
          <h3 className="text-xl font-bold mb-2">접근 제한</h3>
          <p className="text-sm font-medium">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-1 flex items-center gap-3">
          <div className="bg-[#7C3AED]/10 text-[#7C3AED] p-2 rounded-xl">
            <Users size={28} />
          </div>
          사용자 관리
        </h1>
        <p className="text-gray-500 text-base">시스템에 가입된 가맹점 사장님(점주) 계정 정보 및 운영 현황을 모니터링합니다.</p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-100">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100 text-gray-600 font-semibold text-sm">
                <th className="px-6 py-4 w-16 text-center">No</th>
                <th className="px-6 py-4">이름</th>
                <th className="px-6 py-4">이메일</th>
                <th className="px-6 py-4">전화번호</th>
                <th className="px-6 py-4">매장 명</th>
                <th className="px-6 py-4">운영 키오스크 수</th>
                <th className="px-6 py-4">권한</th>
                <th className="px-6 py-4">가입일</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700 text-base">
              {users.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-gray-400 font-medium">
                    가입된 사용자가 없습니다.
                  </td>
                </tr>
              ) : (
                users.map((u, index) => (
                  <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-center font-bold text-gray-400">{index + 1}</td>
                    <td className="px-6 py-4 font-bold text-gray-900">{u.name}</td>
                    <td className="px-6 py-4 font-medium text-gray-600">{u.email}</td>
                    <td className="px-6 py-4 text-gray-500">{u.phone || '-'}</td>
                    <td className="px-6 py-4 font-semibold">
                      {u.store_names_summary === '매장 없음' ? (
                        <span className="text-gray-400 font-medium">등록 매장 없음</span>
                      ) : (
                        <button
                          onClick={() => navigate(`/stores?ownerName=${encodeURIComponent(u.name)}`)}
                          className="flex items-center gap-1.5 text-[#7C3AED] hover:underline cursor-pointer font-bold text-left group"
                        >
                          <Store size={16} className="text-gray-400 group-hover:text-[#7C3AED] transition-colors" />
                          {u.store_names_summary}
                        </button>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {u.kiosks_summary.active_count === 0 && u.kiosks_summary.inactive_count === 0 ? (
                        <span className="text-gray-400">0대</span>
                      ) : (
                        <button
                          onClick={() => navigate(`/kiosks?ownerName=${encodeURIComponent(u.name)}`)}
                          className="flex items-center gap-1.5 text-gray-900 hover:text-[#7C3AED] hover:underline cursor-pointer font-bold transition-colors group"
                        >
                          <Monitor size={16} className="text-gray-400 group-hover:text-[#7C3AED] transition-colors" />
                          <span>총 {(u.kiosks_summary.active_count ?? 0) + (u.kiosks_summary.inactive_count ?? 0)}대</span>
                          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-green-50 text-green-600">
                            활성 {u.kiosks_summary.active_count ?? 0}
                          </span>
                          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-yellow-50 text-yellow-600">
                            미활성 {u.kiosks_summary.inactive_count ?? 0}
                          </span>
                        </button>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        u.role === 'DEV' ? 'bg-purple-100 text-purple-700' :
                        u.role === 'MASTER' ? 'bg-red-100 text-red-700' :
                        u.role === 'HEAD' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(u.created_at).toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit'
                      })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
