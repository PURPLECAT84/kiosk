import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useKiosk } from '../context/KioskContext';
import { 
  Package, Search, ArrowUp, ArrowDown, Copy, Edit, Trash2, Loader2, 
  Plus, FolderOpen, CheckCircle, AlertTriangle, EyeOff, ClipboardCopy 
} from 'lucide-react';
import CategoryManageModal from '../components/CategoryManageModal';
import ProductFormModal from '../components/ProductFormModal';

interface ProductItem {
  id: string;
  category_id: number;
  barcode: string | null;
  name: string;
  price: number;
  created_date: string;
  image: string;
  stock: number;
  stock_managed: boolean;
  is_active: boolean;
  sequence: number;
  kiosk_id: string;
}

interface CategoryItem {
  id: number;
  name: string;
}

// 이미지 로드 실패 시 무한 루프 방지 및 깔끔한 Fallback을 위한 이미지 컴포넌트
function ProductImage({ src, alt }: { src: string; alt: string }) {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setHasError(false);
  }, [src]);

  if (hasError || !src) {
    return (
      <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center border border-gray-200 text-gray-400">
        <Package size={22} />
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      className="w-12 h-12 rounded-xl object-cover border border-gray-100"
      onError={() => setHasError(true)}
    />
  );
}

export default function ProductManagement() {
  const { token } = useAuth();
  const { currentKioskId } = useKiosk();
  
  // States
  const [currentKiosk, setCurrentKiosk] = useState<any>(null);
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  
  // Search & Filter
  const [searchName, setSearchName] = useState('');
  const [filterActive, setFilterActive] = useState<string>('all'); // 'all', 'active', 'inactive'

  // Loading & Error states
  const [isLoadingKiosk, setIsLoadingKiosk] = useState(true);
  const [isLoadingProducts, setIsLoadingProducts] = useState(false);
  const [error, setError] = useState('');

  // Bulk operation states
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isBulkOperating, setIsBulkOperating] = useState(false);

  // Modals state
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [productToEdit, setProductToEdit] = useState<ProductItem | null>(null);

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

  // 2. 상품 목록 로드
  const fetchProducts = async () => {
    if (!currentKioskId) return;
    setIsLoadingProducts(true);
    setSelectedIds([]);
    try {
      let query = `/products/kiosk/${currentKioskId}`;
      const params: string[] = [];
      if (searchName) {
        params.push(`name=${encodeURIComponent(searchName)}`);
      }
      if (filterActive === 'active') {
        params.push('is_active=true');
      } else if (filterActive === 'inactive') {
        params.push('is_active=false');
      }
      if (params.length > 0) {
        query += `?${params.join('&')}`;
      }

      const res = await fetch(query, {
        headers: { 
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error('상품 목록을 가져오지 못했습니다.');
      const data = await res.json();
      setProducts(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoadingProducts(false);
    }
  };

  // 3. 카테고리 목록 가져오기
  const fetchMetadata = async () => {
    if (!currentKioskId) return;
    try {
      const catRes = await fetch(`/category/kiosk/${currentKioskId}`, {
        headers: { 
          'Authorization': `Bearer ${token}`
        }
      });
      if (catRes.ok) {
        const catData = await catRes.json();
        setCategories(catData);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchKioskDetail();
  }, [token, currentKioskId]);

  useEffect(() => {
    if (currentKioskId) {
      fetchProducts();
      fetchMetadata();
    }
  }, [currentKioskId, searchName, filterActive]);

  // 카테고리 ID -> 카테고리명
  const getCategoryName = (catId: number) => {
    const found = categories.find(c => c.id === catId);
    return found ? found.name : `분류없음 (${catId})`;
  };

  // 상품 노출 순서 이동 (UP/DOWN)
  const handleMoveSequence = async (productId: string, direction: 'up' | 'down') => {
    try {
      const res = await fetch(`/products/${productId}/move?direction=${direction}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || '순서 조정 실패');
      }
      fetchProducts();
    } catch (err: any) {
      alert(err.message);
    }
  };

  // 상품 복사
  const handleCopyProduct = async (productId: string) => {
    try {
      const res = await fetch(`/products/${productId}/copy`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || '복사 실패');
      }
      alert('상품 복사가 완료되었습니다.');
      fetchProducts();
    } catch (err: any) {
      alert(err.message);
    }
  };

  // 개별 삭제
  const handleDeleteProduct = async (productId: string, name: string) => {
    if (!window.confirm(`정말로 상품 [${name}]을 삭제하시겠습니까?`)) return;
    try {
      const res = await fetch(`/products/kiosk/${currentKioskId}/product/${productId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('삭제에 실패했습니다.');
      alert('상품이 성공적으로 삭제되었습니다.');
      fetchProducts();
    } catch (err: any) {
      alert(err.message);
    }
  };

  // 체크박스 다중 선택 제어
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(products.map(p => p.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectOne = (checked: boolean, id: string) => {
    if (checked) {
      setSelectedIds([...selectedIds, id]);
    } else {
      setSelectedIds(selectedIds.filter(item => item !== id));
    }
  };

  // 일괄 상태 활성화/비활성화
  const handleBulkStatus = async (isActive: boolean) => {
    if (selectedIds.length === 0) return;
    setIsBulkOperating(true);
    try {
      const res = await fetch('/products/bulk-status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          product_ids: selectedIds,
          is_active: isActive
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '상태 변경 실패');
      
      alert(data.message);
      setSelectedIds([]);
      fetchProducts();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsBulkOperating(false);
    }
  };

  // 일괄 삭제
  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    if (!window.confirm(`선택한 ${selectedIds.length}개의 상품을 전부 일괄 삭제하시겠습니까? 이 작업은 복구할 수 없습니다.`)) return;
    setIsBulkOperating(true);
    try {
      const res = await fetch('/products/bulk-delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          product_ids: selectedIds
        })
      });
      if (!res.ok) throw new Error('일괄 삭제 실패');
      
      alert('선택한 상품이 모두 삭제되었습니다.');
      setSelectedIds([]);
      fetchProducts();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsBulkOperating(false);
    }
  };

  // 상태 토글 (is_active 개별 토글)
  const handleToggleActive = async (product: ProductItem) => {
    try {
      const res = await fetch(`/products/kiosk/${currentKioskId}/product/${product.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          is_active: !product.is_active
        })
      });
      if (!res.ok) throw new Error('상태 토글 실패');
      fetchProducts();
    } catch (err: any) {
      alert(err.message);
    }
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
        <div className="bg-red-50 text-red-700 px-6 py-4 rounded-2xl shadow-sm text-center">
          <h3 className="text-xl font-bold mb-2">오류 발생</h3>
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
        <p className="text-gray-500 max-w-md">상품 관리를 시작하려면 좌측 하단의 키오스크 선택기 또는 기기 관리 메뉴에서 관리 대상을 먼저 선택해 주세요.</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* 헤더 */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-1">상품 및 메뉴 관리</h1>
          <p className="text-gray-500 text-base">
            현재 관리 기기: <span className="font-bold text-[#7C3AED]">{currentKiosk?.name || '키오스크'}</span> ({currentKiosk?.store_name || '매장'})
          </p>
        </div>

        <div className="flex space-x-3 w-full md:w-auto">
          {/* 카테고리 관리 */}
          <button
            onClick={() => setIsCategoryModalOpen(true)}
            className="flex items-center space-x-1.5 bg-white border border-gray-200 text-gray-700 font-bold px-4 py-2.5 rounded-xl hover:bg-gray-50 shadow-sm transition-all text-sm cursor-pointer"
          >
            <FolderOpen size={16} />
            <span>카테고리 관리</span>
          </button>
          {/* 상품 추가 */}
          <button
            onClick={() => {
              setProductToEdit(null);
              setIsProductModalOpen(true);
            }}
            className="flex items-center space-x-1.5 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold px-4 py-2.5 rounded-xl shadow-sm transition-all text-sm cursor-pointer"
          >
            <Plus size={16} />
            <span>상품 추가</span>
          </button>
        </div>
      </div>

      {/* 필터 및 다중 동작 */}
      <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-4 bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
        {/* 왼쪽: 검색 & 상태 필터 */}
        <div className="flex flex-1 flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              placeholder="상품명 검색..."
              value={searchName}
              onChange={(e) => setSearchName(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-sm font-semibold"
            />
          </div>
          <select
            value={filterActive}
            onChange={(e) => setFilterActive(e.target.value)}
            className="px-4 py-2.5 border border-gray-200 bg-white rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-sm font-semibold cursor-pointer"
          >
            <option value="all">전체 상태</option>
            <option value="active">판매중 (활성)</option>
            <option value="inactive">판매중단 (비활성)</option>
          </select>
        </div>

        {/* 오른쪽: 다중 처리 Action Buttons */}
        {selectedIds.length > 0 && (
          <div className="flex items-center space-x-2.5 bg-[#7C3AED]/5 border border-[#7C3AED]/10 px-4 py-2 rounded-xl">
            <span className="text-xs font-extrabold text-[#7C3AED]">{selectedIds.length}개 선택됨</span>
            <button
              onClick={() => handleBulkStatus(true)}
              disabled={isBulkOperating}
              className="bg-white hover:bg-green-50 text-green-600 border border-green-200 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer"
            >
              일괄 활성화
            </button>
            <button
              onClick={() => handleBulkStatus(false)}
              disabled={isBulkOperating}
              className="bg-white hover:bg-yellow-50 text-yellow-600 border border-yellow-200 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer"
            >
              일괄 비활성화
            </button>
            <button
              onClick={handleBulkDelete}
              disabled={isBulkOperating}
              className="bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer"
            >
              일괄 삭제
            </button>
          </div>
        )}
      </div>

      {/* 테이블 리스트 */}
      <div className="bg-white rounded-3xl shadow-sm overflow-hidden border border-gray-100">
        {isLoadingProducts ? (
          <div className="flex justify-center items-center py-20">
            <Loader2 className="animate-spin text-[#7C3AED]" size={36} />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100 text-gray-600 font-semibold text-sm">
                  <th className="px-6 py-4 w-12 text-center">
                    <input
                      type="checkbox"
                      checked={products.length > 0 && selectedIds.length === products.length}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="rounded text-[#7C3AED] focus:ring-[#7C3AED] w-4 h-4 cursor-pointer"
                    />
                  </th>
                  <th className="px-6 py-4 w-16 text-center">No</th>
                  <th className="px-6 py-4 w-20">이미지</th>
                  <th className="px-6 py-4">상품명</th>
                  <th className="px-6 py-4">카테고리</th>
                  <th className="px-6 py-4">판매가</th>
                  {currentKiosk?.type !== 'Restaurant' && <th className="px-6 py-4">바코드</th>}
                  <th className="px-6 py-4">재고현황</th>
                  <th className="px-6 py-4 text-center">순서</th>
                  <th className="px-6 py-4">상태</th>
                  <th className="px-6 py-4 text-center">작업</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-700">
                {products.length === 0 ? (
                  <tr>
                    <td colSpan={currentKiosk?.type === 'Restaurant' ? 10 : 11} className="text-center py-16 text-gray-400 font-medium">
                      등록된 상품이 존재하지 않습니다.
                    </td>
                  </tr>
                ) : (
                  products.map((product, idx) => {
                    const imgUrl = product.image.startsWith('http') 
                      ? product.image 
                      : `http://localhost:8000${product.image}`;
                      
                    return (
                      <tr key={product.id} className="hover:bg-gray-50 transition-colors">
                        {/* 1. 체크박스 */}
                        <td className="px-6 py-4 text-center">
                          <input
                            type="checkbox"
                            checked={selectedIds.includes(product.id)}
                            onChange={(e) => handleSelectOne(e.target.checked, product.id)}
                            className="rounded text-[#7C3AED] focus:ring-[#7C3AED] w-4 h-4 cursor-pointer"
                          />
                        </td>
                        {/* 2. No */}
                        <td className="px-6 py-4 text-center text-sm font-semibold text-gray-400">
                          {idx + 1}
                        </td>
                        {/* 3. 이미지 */}
                        <td className="px-6 py-4">
                          <ProductImage src={imgUrl} alt={product.name} />
                        </td>
                        {/* 4. 상품명 */}
                        <td className="px-6 py-4">
                          <span className="font-bold text-gray-900 block text-base leading-tight">
                            {product.name}
                          </span>
                        </td>
                        {/* 5. 카테고리 */}
                        <td className="px-6 py-4 font-bold text-sm text-gray-800">
                          {getCategoryName(product.category_id)}
                        </td>
                        {/* 6. 판매가 */}
                        <td className="px-6 py-4 font-extrabold text-gray-900 text-sm">
                          ₩{product.price.toLocaleString()}
                        </td>
                        {/* 7. 바코드 (외식형 아닐때만 노출) */}
                        {currentKiosk?.type !== 'Restaurant' && (
                          <td className="px-6 py-4 font-mono text-xs text-gray-500 font-bold">
                            {product.barcode || '-'}
                          </td>
                        )}
                        {/* 8. 재고현황 */}
                        <td className="px-6 py-4">
                          {product.stock_managed ? (
                            <div className="flex items-center space-x-1.5">
                              <span className={`w-2 h-2 rounded-full ${
                                product.stock === 0 ? 'bg-red-500 animate-pulse' : product.stock < 10 ? 'bg-yellow-500' : 'bg-green-500'
                              }`} />
                              <span className={`font-extrabold text-sm ${product.stock === 0 ? 'text-red-600' : 'text-gray-900'}`}>
                                {product.stock}개
                              </span>
                            </div>
                          ) : (
                            <span className="text-xs font-bold text-[#7C3AED] bg-[#7C3AED]/5 px-2 py-1 rounded-lg">
                              상시 노출
                            </span>
                          )}
                        </td>
                        {/* 9. 순서 이동 버튼 */}
                        <td className="px-6 py-4">
                          <div className="flex flex-col items-center justify-center space-y-1">
                            <button
                              onClick={() => handleMoveSequence(product.id, 'up')}
                              disabled={idx === 0}
                              className="p-1 rounded bg-gray-50 hover:bg-gray-150 text-gray-600 disabled:opacity-30 disabled:hover:bg-gray-50 cursor-pointer"
                            >
                              <ArrowUp size={14} />
                            </button>
                            <button
                              onClick={() => handleMoveSequence(product.id, 'down')}
                              disabled={idx === products.length - 1}
                              className="p-1 rounded bg-gray-50 hover:bg-gray-150 text-gray-600 disabled:opacity-30 disabled:hover:bg-gray-50 cursor-pointer"
                            >
                              <ArrowDown size={14} />
                            </button>
                          </div>
                        </td>
                        {/* 10. 상태 활성 토글 */}
                        <td className="px-6 py-4">
                          <button
                            onClick={() => handleToggleActive(product)}
                            className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                              product.is_active ? 'bg-green-500' : 'bg-gray-200'
                            }`}
                          >
                            <span
                              className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                                product.is_active ? 'translate-x-4' : 'translate-x-0'
                              }`}
                            />
                          </button>
                        </td>
                        {/* 11. 작업 버튼들 */}
                        <td className="px-6 py-4 text-center">
                          <div className="flex items-center justify-center space-x-1">
                            {/* 수정 */}
                            <button
                              onClick={() => {
                                setProductToEdit(product);
                                setIsProductModalOpen(true);
                              }}
                              className="p-2 text-gray-600 hover:text-[#7C3AED] hover:bg-gray-50 rounded-lg transition-colors cursor-pointer"
                              title="수정"
                            >
                              <Edit size={16} />
                            </button>
                            {/* 복사 */}
                            <button
                              onClick={() => handleCopyProduct(product.id)}
                              className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50/50 rounded-lg transition-colors cursor-pointer"
                              title="복사"
                            >
                              <Copy size={16} />
                            </button>
                            {/* 삭제 */}
                            <button
                              onClick={() => handleDeleteProduct(product.id, product.name)}
                              className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50/50 rounded-lg transition-colors cursor-pointer"
                              title="삭제"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 카테고리 관리 팝업 */}
      <CategoryManageModal
        isOpen={isCategoryModalOpen}
        onClose={() => setIsCategoryModalOpen(false)}
        kioskId={currentKioskId || ''}
        token={token || ''}
        onCategoriesUpdated={() => fetchMetadata()}
      />

      {/* 상품 등록 및 수정 팝업 */}
      <ProductFormModal
        isOpen={isProductModalOpen}
        onClose={() => {
          setIsProductModalOpen(false);
          setProductToEdit(null);
        }}
        kioskId={currentKioskId || ''}
        kioskType={currentKiosk?.type || 'Store'}
        token={token || ''}
        productToEdit={productToEdit}
        onSaveSuccess={() => fetchProducts()}
      />
    </div>
  );
}
