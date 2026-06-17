import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Users, Loader2, Store, Monitor } from 'lucide-react';

interface KioskSummary {
  active_count: number;
  inactive_count: number;
}

interface UserItem {
  id: string;
  email: string;
  name: string;
  phone: string | null;
  role: string;
  status: string;
  is_business_verified: boolean;
  created_at: string;
  store_names_summary: string;
  kiosks_summary: KioskSummary;
}

export default function UserManagement() {
  const { token, user: currentUser } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`/users/?t=${Date.now()}`, {
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

  const handleVerifyToggle = async (userId: string, currentStatus: boolean) => {
    try {
      const res = await fetch(`/users/${userId}/verify-business?is_verified=${!currentStatus}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || '사업자 승인 상태 변경에 실패했습니다.');
      }
      fetchUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      const res = await fetch(`/users/${userId}/role?role=${newRole}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || '권한 변경에 실패했습니다.');
      }
      alert('사용자 권한이 성공적으로 변경되었습니다.');
      fetchUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleStatusToggle = async (userId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'ACTIVE' ? 'BANNED' : 'ACTIVE';
    const msg = nextStatus === 'ACTIVE' ? '계정을 다시 활성화하시겠습니까?' : '정말로 이 계정을 정지(비활성화)하시겠습니까?';
    if (!window.confirm(msg)) return;

    try {
      const res = await fetch(`/users/${userId}/status?user_status=${nextStatus}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || '상태 변경에 실패했습니다.');
      }
      alert('사용자 계정 상태가 변경되었습니다.');
      fetchUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleAdminDeleteUser = async (userId: string, userName: string) => {
    if (!window.confirm(`⚠️ 경고: 정말 [${userName}] 사용자를 완전히 삭제하시겠습니까?\n삭제 시 이 사용자와 연결된 모든 매장, 키오스크, 메뉴 데이터가 영구적으로 파괴되며 복구할 수 없습니다.`)) return;

    try {
      const res = await fetch(`/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || '사용자 삭제에 실패했습니다.');
      }
      alert('사용자가 성공적으로 삭제되었습니다.');
      fetchUsers();
    } catch (err: any) {
      alert(err.message);
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
                <th className="px-6 py-4">사업자 확인</th>
                <th className="px-6 py-4">권한</th>
                <th className="px-6 py-4">계정 상태</th>
                <th className="px-6 py-4">가입일</th>
                {(currentUser?.role === 'DEV' || currentUser?.role === 'HEAD') && (
                  <th className="px-6 py-4 text-center">관리</th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700 text-base">
              {users.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-12 text-gray-400 font-medium">
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
                        <div className="flex items-center gap-1.5 text-gray-900 font-bold text-left">
                          <Store size={16} className="text-gray-400" />
                          {u.store_names_summary}
                        </div>
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
                      {u.role === 'STAFF' ? (
                        <span className="text-gray-400 text-sm">해당 없음</span>
                      ) : (
                        <button
                          onClick={() => handleVerifyToggle(u.id, u.is_business_verified)}
                          className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer shadow-sm ${
                            u.is_business_verified
                              ? 'bg-green-100 text-green-700 hover:bg-green-200'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          {u.is_business_verified ? '확인 완료' : '대기 / 미인증'}
                        </button>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {(currentUser?.role === 'DEV' || currentUser?.role === 'HEAD') && u.id !== currentUser.id ? (
                        <select
                          value={u.role}
                          onChange={(e) => handleRoleChange(u.id, e.target.value)}
                          className="px-2.5 py-1 rounded-xl text-xs font-bold border border-gray-200 focus:outline-none focus:ring-1 focus:ring-[#7C3AED] cursor-pointer bg-white"
                        >
                          <option value="DEV">DEV</option>
                          <option value="HEAD">HEAD</option>
                          <option value="MASTER">MASTER</option>
                          <option value="MANAGER">MANAGER</option>
                          <option value="STAFF">STAFF</option>
                          <option value="NONE">NONE</option>
                        </select>
                      ) : (
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                          u.role === 'DEV' ? 'bg-purple-100 text-purple-700' :
                          u.role === 'MASTER' ? 'bg-red-100 text-red-700' :
                          u.role === 'HEAD' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {u.role}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        u.status === 'ACTIVE' ? 'bg-green-100 text-green-700' :
                        u.status === 'PENDING' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {u.status === 'ACTIVE' ? '정상 활성' :
                         u.status === 'PENDING' ? '승인 대기' : '정지 / 탈퇴'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(u.created_at).toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit'
                      })}
                    </td>
                    {(currentUser?.role === 'DEV' || currentUser?.role === 'HEAD') && (
                      <td className="px-6 py-4 text-center flex justify-center gap-2">
                        {u.id !== currentUser.id ? (
                          <>
                            <button
                              onClick={() => handleStatusToggle(u.id, u.status)}
                              className={`px-2.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer shadow-sm ${
                                u.status === 'ACTIVE'
                                  ? 'bg-red-50 text-red-600 hover:bg-red-100'
                                  : 'bg-green-50 text-green-600 hover:bg-green-100'
                              }`}
                            >
                              {u.status === 'ACTIVE' ? '정지' : '활성화'}
                            </button>
                            <button
                              onClick={() => handleAdminDeleteUser(u.id, u.name)}
                              className="px-2.5 py-1.5 rounded-xl text-xs font-bold bg-gray-50 hover:bg-red-650 hover:text-white text-gray-500 transition-all cursor-pointer shadow-sm"
                            >
                              삭제
                            </button>
                          </>
                        ) : (
                          <span className="text-gray-400 text-xs font-medium">본인 계정</span>
                        )}
                      </td>
                    )}
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
