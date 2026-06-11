import React, { useEffect, useState, useRef } from 'react';
import { X, Upload, Loader2, Barcode, Check } from 'lucide-react';

interface CategoryItem {
  id: number;
  name: string;
}

interface ProductItem {
  id: string;
  category_id: number;
  barcode: string | null;
  name: string;
  price: number;
  image: string;
  stock: number;
  stock_managed: boolean;
  kiosk_id: string;
}

interface ProductFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  kioskId: string;
  kioskType: string; // 'Store' or 'Restaurant'
  token: string;
  productToEdit?: ProductItem | null;
  onSaveSuccess: () => void;
}

export default function ProductFormModal({
  isOpen,
  onClose,
  kioskId,
  kioskType,
  token,
  productToEdit,
  onSaveSuccess
}: ProductFormModalProps) {
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  
  const [isLoadingMeta, setIsLoadingMeta] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [error, setError] = useState('');

  // Form Fields
  const [name, setName] = useState('');
  const [price, setPrice] = useState(0);
  const [categoryId, setCategoryId] = useState<number | ''>('');
  const [barcode, setBarcode] = useState('');
  const [image, setImage] = useState('');
  const [stockManaged, setStockManaged] = useState(true);
  const [stock, setStock] = useState(0);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load Meta Data (categories)
  const loadMetaData = async () => {
    if (!kioskId) return;
    setIsLoadingMeta(true);
    try {
      const catRes = await fetch(`/category/kiosk/${kioskId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (catRes.ok) {
        const catData = await catRes.json();
        setCategories(catData);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoadingMeta(false);
    }
  };

  useEffect(() => {
    if (isOpen && kioskId) {
      loadMetaData();
      setError('');
      
      if (productToEdit) {
        setName(productToEdit.name);
        setPrice(productToEdit.price);
        setCategoryId(productToEdit.category_id);
        setBarcode(productToEdit.barcode || '');
        setImage(productToEdit.image || '');
        setStockManaged(productToEdit.stock_managed);
        setStock(productToEdit.stock);
      } else {
        setName('');
        setPrice(0);
        setCategoryId('');
        setBarcode('');
        setImage('');
        setStockManaged(true);
        setStock(0);
      }
    }
  }, [isOpen, kioskId, productToEdit]);

  // Image File Upload
  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      setError('이미지 파일 크기는 2MB 이하여야 합니다.');
      return;
    }

    setUploadingImage(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`/products/image?kiosk_id=${kioskId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '이미지 업로드에 실패했습니다.');
      
      setImage(data.image_url);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploadingImage(false);
    }
  };

  // Barcode Simulator
  const simulateBarcodeScan = () => {
    const randomDigits = Array.from({ length: 12 }, () => Math.floor(Math.random() * 10)).join('');
    setBarcode('880' + randomDigits.substring(3));
  };

  // Submit Handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (categoryId === '') {
      setError('카테고리를 선택해 주세요.');
      return;
    }

    setIsSaving(true);
    setError('');

    const payload = {
      category_id: Number(categoryId),
      name,
      price: Number(price),
      image: image || '/static/images/placeholder.png',
      stock: stockManaged ? Number(stock) : 0,
      stock_managed: stockManaged,
      kiosk_id: kioskId,
      barcode: kioskType === 'Restaurant' ? null : (barcode || null)
    };

    try {
      let res;
      if (productToEdit) {
        // Edit Mode
        res = await fetch(`/products/kiosk/${kioskId}/product/${productToEdit.id}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });
      } else {
        // Create Mode
        res = await fetch('/products/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });
      }

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '상품 저장 도중 오류가 발생했습니다.');

      onSaveSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50 p-4">
      <div className="bg-white rounded-3xl max-w-lg w-full p-8 shadow-xl space-y-6 relative overflow-y-auto max-h-[90vh]">
        <button
          onClick={onClose}
          className="absolute right-6 top-6 text-gray-400 hover:text-gray-600 cursor-pointer"
        >
          <X size={24} />
        </button>

        <div>
          <h3 className="text-2xl font-bold text-gray-900">
            {productToEdit ? '상품 수정' : '신규 상품 등록'}
          </h3>
          <p className="text-gray-500 text-sm mt-1">키오스크 및 사용자 화면에 노출될 상품을 생성/수정합니다.</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-2xl text-sm font-semibold">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* 상품명 */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-1.5">상품명</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base font-semibold"
              placeholder="예: 아이스 아메리카노"
              required
            />
          </div>

          <div>
            {/* 판매 가격 */}
            <label className="block text-sm font-bold text-gray-700 mb-1.5">판매 가격 (₩)</label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(Number(e.target.value))}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base font-semibold"
              placeholder="0"
              min="0"
              required
            />
          </div>

          {/* 카테고리 선택 */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-1.5">카테고리</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full px-4 py-3 border border-gray-300 bg-white rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base font-semibold"
              required
            >
              <option value="">카테고리 선택</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>

          {/* 바코드 입력란 (외식형이 아닐 때만 노출) */}
          {kioskType !== 'Restaurant' && (
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-1.5">바코드 번호</label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={barcode}
                  onChange={(e) => setBarcode(e.target.value)}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base font-semibold"
                  placeholder="바코드 숫자를 입력하거나 스캔"
                />
                <button
                  type="button"
                  onClick={simulateBarcodeScan}
                  className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold px-4 py-3 rounded-xl transition-all text-sm flex items-center space-x-1.5 cursor-pointer"
                >
                  <Barcode size={18} />
                  <span>스캔 모사</span>
                </button>
              </div>
            </div>
          )}

          {/* 재고 관리 설정 및 재고 입력 */}
          <div className="bg-gray-50 p-5 rounded-2xl border border-gray-100 space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <span className="text-base font-extrabold text-gray-900 block">재고 관리 활성화</span>
                <span className="text-xs text-gray-400">재고가 0이 되면 키오스크에서 자동으로 품절 처리됩니다.</span>
              </div>
              <button
                type="button"
                onClick={() => setStockManaged(!stockManaged)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  stockManaged ? 'bg-[#7C3AED]' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    stockManaged ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            {stockManaged && (
              <div className="pt-2 border-t border-gray-200/50">
                <label className="block text-sm font-bold text-gray-700 mb-1.5">현재고 수량</label>
                <input
                  type="number"
                  value={stock}
                  onChange={(e) => setStock(Math.max(0, Number(e.target.value)))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#7C3AED] focus:border-[#7C3AED] outline-none text-base font-semibold"
                  placeholder="0"
                  min="0"
                />
              </div>
            )}
            {!stockManaged && (
              <div className="pt-2 border-t border-gray-200/50 text-center py-2">
                <span className="text-sm font-bold text-[#7C3AED] bg-[#7C3AED]/5 px-3 py-1.5 rounded-lg">
                  상시 판매 중 (재고 미제한)
                </span>
              </div>
            )}
          </div>

          {/* 상품 이미지 업로드 */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-1.5">상품 이미지 (최대 2MB)</label>
            <div className="flex items-center space-x-4">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageUpload}
                accept="image/*"
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadingImage}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold px-4 py-4 rounded-2xl transition-all text-sm flex flex-col items-center justify-center border-2 border-dashed border-gray-300 w-32 h-32 cursor-pointer"
              >
                {uploadingImage ? (
                  <Loader2 className="animate-spin text-[#7C3AED]" size={24} />
                ) : (
                  <>
                    <Upload size={24} className="text-gray-400 mb-1.5" />
                    <span className="text-xs text-gray-500">이미지 업로드</span>
                  </>
                )}
              </button>

              {image && (
                <div className="relative w-32 h-32 rounded-2xl overflow-hidden border border-gray-200 group">
                  <img src={image.startsWith('http') ? image : `http://localhost:8000${image}`} alt="Preview" className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-black/40 flex justify-center items-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      type="button"
                      onClick={() => setImage('')}
                      className="bg-white/80 p-1.5 rounded-full hover:bg-white text-gray-900 transition-all cursor-pointer"
                    >
                      <X size={16} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 하단 단추 */}
          <div className="flex space-x-3 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-3.5 rounded-xl transition-colors cursor-pointer text-center text-sm"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isSaving || uploadingImage}
              className="flex-1 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-bold py-3.5 rounded-xl transition-all flex justify-center items-center cursor-pointer shadow-sm text-sm"
            >
              {isSaving ? <Loader2 className="animate-spin" size={20} /> : <><Check size={18} className="mr-1.5" /> 저장하기</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
