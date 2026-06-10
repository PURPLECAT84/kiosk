import React, { useEffect, useState } from 'react';
import { X, Plus, Trash2, Loader2, FolderPlus } from 'lucide-react';

interface CategoryItem {
  id: number;
  name: string;
  shelve_id: string;
  kiosk_id: string;
}

interface ShelveItem {
  id: string;
  name: string;
}

interface CategoryManageModalProps {
  isOpen: boolean;
  onClose: () => void;
  kioskId: string;
  token: string;
  onCategoriesUpdated?: () => void;
}

export default function CategoryManageModal({
  isOpen,
  onClose,
  kioskId,
  token,
  onCategoriesUpdated
}: CategoryManageModalProps) {
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState('');

  // 1. 카테고리 목록 가져오기
  const fetchCategories = async () => {
    if (!kioskId) return;
    setIsLoading(true);
    try {
      const res = await fetch(`/category/kiosk/${kioskId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('카테고리 조회를 실패했습니다.');
      const data = await res.json();
      setCategories(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && kioskId) {
      fetchCategories();
      setError('');
    }
  }, [isOpen, kioskId]);

  // 2. 매대의 ID를 찾거나 없으면 생성하기
  const getOrCreateShelveId = async (): Promise<string> => {
    // 매대 목록 조회
    const res = await fetch(`/shelves/kiosk/${kioskId}/shelve`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('매대 정보 조회에 실패했습니다.');
    const shelves: ShelveItem[] = await res.json();

    if (shelves.length > 0) {
      return shelves[0].id;
    }

    // 없으면 기본 매대 생성
    const createRes = await fetch(`/shelves/kiosk/${kioskId}/shelve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        name: '기본 매대',
        terminal_id: 'TERM01',
        business_number: '123-45-67890',
        vender_code: 'VEND01'
      })
    });
    if (!createRes.ok) throw new Error('기본 매대 생성에 실패했습니다.');
    const newShelve = await createRes.json();
    return newShelve.id;
  };

  // 3. 카테고리 추가
  const handleAddCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCategoryName.trim()) return;
    setIsAdding(true);
    setError('');
    try {
      const shelveId = await getOrCreateShelveId();
      const res = await fetch('/category/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newCategoryName.trim(),
          shelve_id: shelveId
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '카테고리 등록에 실패했습니다.');

      setNewCategoryName('');
      fetchCategories();
      if (onCategoriesUpdated) onCategoriesUpdated();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsAdding(false);
    }
  };

  // 4. 카테고리 삭제
  const handleDeleteCategory = async (categoryId: number) => {
    if (!window.confirm('이 카테고리를 삭제하시겠습니까? 카테고리에 속한 모든 상품 매핑이 제거됩니다.')) return;
    setError('');
    try {
      const res = await fetch(`/category/${categoryId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || '카테고리 삭제에 실패했습니다.');
      }
      fetchCategories();
      if (onCategoriesUpdated) onCategoriesUpdated();
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50 p-4">
      <div className="bg-white rounded-3xl max-w-md w-full p-8 shadow-xl space-y-6 relative overflow-hidden">
        <button
          onClick={onClose}
          className="absolute right-6 top-6 text-gray-400 hover:text-gray-600 cursor-pointer"
        >
          <X size={24} />
        </button>

        <div>
          <h3 className="text-2xl font-bold text-gray-900 flex items-center">
            <FolderPlus className="mr-2 text-[#7C3AED]" size={26} /> 카테고리 관리
          </h3>
          <p className="text-gray-500 text-sm mt-1">상품 분류에 필요한 카테고리를 등록하고 관리합니다.</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 p-3.5 rounded-xl text-sm font-semibold">
            {error}
          </div>
        )}

        {/* 카테고리 추가 폼 */}
        <form onSubmit={handleAddCategory} className="flex space-x-2">
          <input
            type="text"
            placeholder="신규 카테고리 명"
            value={newCategoryName}
            onChange={(e) => setNewCategoryName(e.target.value)}
            disabled={isAdding}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-sm font-medium"
            required
          />
          <button
            type="submit"
            disabled={isAdding}
            className="bg-[#7C3AED] hover:bg-[#6D28D9] text-white px-4 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center justify-center cursor-pointer"
          >
            {isAdding ? <Loader2 className="animate-spin" size={16} /> : <Plus size={16} />}
          </button>
        </form>

        {/* 카테고리 목록 */}
        <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
          {isLoading ? (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="animate-spin text-[#7C3AED]" size={24} />
            </div>
          ) : categories.length === 0 ? (
            <p className="text-center py-8 text-gray-400 text-sm font-medium">등록된 카테고리가 없습니다.</p>
          ) : (
            categories.map((category) => (
              <div
                key={category.id}
                className="flex justify-between items-center bg-gray-50 px-4 py-3 rounded-xl border border-gray-100 hover:border-gray-200 transition-all"
              >
                <span className="text-gray-800 font-bold text-sm">{category.name}</span>
                <button
                  onClick={() => handleDeleteCategory(category.id)}
                  className="text-red-500 hover:bg-red-50 p-1.5 rounded-lg transition-colors cursor-pointer"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
