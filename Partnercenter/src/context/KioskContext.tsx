import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

export interface Kiosk {
  id: string;
  code: string;
  store_id: string;
  store_name: string | null;
  name: string;
  model_name: string | null;
  type: string;
  status: string;
  payment_status: string;
  next_payment_date: string | null;
  created_at: string;
}

interface KioskContextType {
  currentKioskId: string | null;
  currentKioskName: string | null;
  currentStoreName: string | null;
  currentStoreId: string | null;
  myKiosks: Kiosk[];
  isLoadingKiosks: boolean;
  setCurrentKioskId: (id: string | null) => void;
  refreshMyKiosks: () => Promise<void>;
}

const KioskContext = createContext<KioskContextType | undefined>(undefined);

export const KioskProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, user } = useAuth();
  const [myKiosks, setMyKiosks] = useState<Kiosk[]>([]);
  const [currentKioskId, setCurrentKioskIdState] = useState<string | null>(
    localStorage.getItem('currentKioskId')
  );
  const [currentKioskName, setCurrentKioskName] = useState<string | null>(null);
  const [currentStoreName, setCurrentStoreName] = useState<string | null>(null);
  const [currentStoreId, setCurrentStoreId] = useState<string | null>(null);
  const [isLoadingKiosks, setIsLoadingKiosks] = useState(false);

  const refreshMyKiosks = async () => {
    if (!token) {
      setMyKiosks([]);
      return;
    }
    setIsLoadingKiosks(true);
    try {
      const res = await fetch('/kiosks/my', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) {
        const data: Kiosk[] = await res.json();
        setMyKiosks(data);

        // 만약 이전에 선택된 기기가 있고, 그 기기가 목록에 존재한다면 유지
        // 그렇지 않다면 첫 번째 기기를 기본값으로 자동 활성화
        if (data.length > 0) {
          const storedId = localStorage.getItem('currentKioskId');
          const exists = data.some((k) => k.id === storedId);
          if (storedId && exists) {
            setCurrentKioskId(storedId);
          } else {
            setCurrentKioskId(data[0].id);
          }
        } else {
          setCurrentKioskId(null);
        }
      }
    } catch (err) {
      console.error('Failed to fetch my kiosks:', err);
    } finally {
      setIsLoadingKiosks(false);
    }
  };

  const setCurrentKioskId = (id: string | null) => {
    if (id) {
      localStorage.setItem('currentKioskId', id);
    } else {
      localStorage.removeItem('currentKioskId');
    }
    setCurrentKioskIdState(id);
  };

  // 로그인 상태나 유저 정보가 바뀔 때 기기 목록 리프레시
  useEffect(() => {
    if (token) {
      refreshMyKiosks();
    } else {
      setMyKiosks([]);
      setCurrentKioskId(null);
    }
  }, [token, user?.id]);

  // 활성 기기 ID가 변경될 때 이름 및 매장명 매핑 업데이트
  useEffect(() => {
    if (currentKioskId && myKiosks.length > 0) {
      const activeKiosk = myKiosks.find((k) => k.id === currentKioskId);
      if (activeKiosk) {
        setCurrentKioskName(activeKiosk.name);
        setCurrentStoreName(activeKiosk.store_name);
        setCurrentStoreId(activeKiosk.store_id);
      } else {
        // 혹시라도 목록에서 찾을 수 없을 때 (예: 기기 삭제 등)
        setCurrentKioskName(null);
        setCurrentStoreName(null);
        setCurrentStoreId(null);
      }
    } else {
      setCurrentKioskName(null);
      setCurrentStoreName(null);
      setCurrentStoreId(null);
    }
  }, [currentKioskId, myKiosks]);

  return (
    <KioskContext.Provider
      value={{
        currentKioskId,
        currentKioskName,
        currentStoreName,
        currentStoreId,
        myKiosks,
        isLoadingKiosks,
        setCurrentKioskId,
        refreshMyKiosks,
      }}
    >
      {children}
    </KioskContext.Provider>
  );
};

export const useKiosk = () => {
  const context = useContext(KioskContext);
  if (context === undefined) {
    throw new Error('useKiosk must be used within a KioskProvider');
  }
  return context;
};
