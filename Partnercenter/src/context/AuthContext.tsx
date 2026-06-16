import React, { createContext, useContext, useState, useEffect } from 'react';

// 사용자 정보
export interface BusinessInfo {
  id: number;
  user_id: string;
  business_number: string;
  business_name: string;
  representative_name: string;
  representative_phone: string | null;
  store_name: string;
  document_url: string | null;
  is_verified: boolean;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  login_provider?: string;
  phone?: string | null;
  is_business_verified?: boolean;
  is_identity_verified?: boolean;
  businesses?: BusinessInfo[];
  portone_store_id?: string | null;
  portone_channel_key?: string | null;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    if (!token) return;
    try {
      const res = await fetch('/users/me', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      }
    } catch (err) {
      console.error('Failed to refresh user:', err);
    }
  };

  // 토큰이 생기면 /users/me 를 호출해 내 정보를 가져옴
  useEffect(() => {
    if (token) {
      setIsLoading(true);
      fetch('/users/me', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      .then(res => {
        if (!res.ok) throw new Error('Token invalid');
        return res.json();
      })
      .then(data => {
        setUser(data);
        setIsLoading(false);
      })
      .catch(() => {
        logout(); // 실패시 자동 로그아웃
        setIsLoading(false);
      });
    } else {
      setUser(null);
      setIsLoading(false);
    }
  }, [token]);

  const login = (newToken: string) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setIsLoading(true); // 즉각적인 로딩 상태 진입으로 깜빡임/튕김 방지
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
