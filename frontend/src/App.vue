<script setup lang="ts">
import { ref, onMounted } from 'vue';

interface TemplateProduct {
  catalog_id: string;
  slide_index: number;
  product_name: string;
  options: string;
  onlineLowestPrice?: string;
  supplyPrice?: string;
  stockQuantity?: string;
  shippingFee?: string;
  cartonQuantity?: string;
  image_base64?: string | null;
  is_custom?: boolean;
}

interface SelectedProduct {
  id: number;
  catalog_id?: string;
  slide_index: number;
  name: string;
  supplyPrice: string;
  stockQuantity: string;
  onlineLowestPrice: string;
  shippingFee: string;
  cartonQuantity: string;
  image_base64?: string | null;
  is_new?: boolean;

  options: string;
}

const templateProducts = ref<TemplateProduct[]>([]);
const selectedProducts = ref<SelectedProduct[]>([]);
const isGenerating = ref(false);
const showModal = ref(false);
const checkedTemplateIds = ref<string[]>([]);
let productIdSequence = Date.now();

const createProductId = () => ++productIdSequence;

const fetchTemplateProducts = async () => {
  try {
    const res = await fetch('/products');
    if (res.ok) {
      templateProducts.value = await res.json();
    }
  } catch (e) {
    console.error("Failed to fetch template products", e);
  }
};

onMounted(() => {
  fetchTemplateProducts();
});

const getTemplateId = (product: TemplateProduct) =>
  product.catalog_id || `template:${product.slide_index}`;

const isTemplateAdded = (template: TemplateProduct) =>
  selectedProducts.value.some(product =>
    product.catalog_id
      ? product.catalog_id === getTemplateId(template)
      : !template.is_custom && product.slide_index === template.slide_index
  );

const openTemplateModal = () => {
  checkedTemplateIds.value = [];
  showModal.value = true;
};

const addFromTemplate = (t: TemplateProduct) => {
  if (isTemplateAdded(t)) {
    return;
  }
  
  selectedProducts.value.push({
    id: createProductId(),
    catalog_id: getTemplateId(t),
    slide_index: t.is_custom ? -1 : t.slide_index,
    name: t.product_name,
    supplyPrice: t.supplyPrice || '',
    stockQuantity: t.stockQuantity || '',
    onlineLowestPrice: t.onlineLowestPrice || '',
    shippingFee: t.shippingFee || '',
    cartonQuantity: t.cartonQuantity || '',
    options: t.options || '',
    image_base64: t.image_base64 || null,
    is_new: Boolean(t.is_custom)
  });
};

const addCheckedTemplates = () => {
  const checkedIds = new Set(checkedTemplateIds.value);
  templateProducts.value
    .filter(template => checkedIds.has(getTemplateId(template)))
    .forEach(addFromTemplate);

  checkedTemplateIds.value = [];
  showModal.value = false;
};

const addCustomProduct = () => {
  selectedProducts.value.push({
    id: createProductId(),
    slide_index: -1, // 백엔드에서 남는 슬라이드 인덱스를 할당해줌
    name: '',
    supplyPrice: '',
    stockQuantity: '',
    onlineLowestPrice: '',
    shippingFee: '',
    cartonQuantity: '',
    options: '',
    image_base64: null,
    is_new: true
  });
};

const saveCustomProduct = async (product: SelectedProduct) => {
  if (!product.name.trim()) {
    alert("저장할 상품명을 입력해 주세요.");
    return;
  }

  try {
    const res = await fetch('/products/custom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(product)
    });
    if (!res.ok) throw new Error("Custom product save failed");

    const saved = await res.json();
    product.catalog_id = saved.catalog_id;
    await fetchTemplateProducts();
    alert("상품이 저장되었습니다. 다음 작업부터 기존 상품 목록에서 다시 선택할 수 있습니다.");
  } catch (e) {
    console.error(e);
    alert("상품 저장 중 오류가 발생했습니다.");
  }
};

const handleImageUpload = (event: Event, product: SelectedProduct) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    product.image_base64 = e.target?.result as string;
  };
  reader.readAsDataURL(file);
};


const removeProduct = (id: number) => {
  selectedProducts.value = selectedProducts.value.filter(p => p.id !== id);
};

const saveDraft = async () => {
  try {
    const payload = { products: selectedProducts.value };
    const res = await fetch('/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) alert("현재 작업 상태가 임시 저장되었습니다.");
    else throw new Error("Save failed");
  } catch (e) {
    alert("저장 중 오류가 발생했습니다.");
  }
};

const loadDraft = async () => {
  try {
    const res = await fetch('/load');
    if (res.ok) {
      const data = await res.json();
      if (data.length > 0) {
        selectedProducts.value = data.map((product: Partial<SelectedProduct>) => ({
          id: product.id ?? createProductId(),
          catalog_id: product.catalog_id,
          slide_index: product.slide_index ?? -1,
          name: product.name ?? '',
          supplyPrice: product.supplyPrice ?? '',
          stockQuantity: product.stockQuantity ?? '',
          onlineLowestPrice: product.onlineLowestPrice ?? '',
          shippingFee: product.shippingFee ?? '',
          cartonQuantity: product.cartonQuantity ?? '',
          options: product.options ?? '',
          image_base64: product.image_base64 ?? null,
          is_new: product.is_new ?? false
        }));
        alert("저장된 내역을 성공적으로 불러왔습니다.");
      } else {
        alert("저장된 내역이 없습니다.");
      }
    }
  } catch (e) {
    alert("불러오기 중 오류가 발생했습니다.");
  }
};

const generateProposal = async () => {

  if (selectedProducts.value.length === 0) return alert('상품을 하나 이상 추가해 주세요.');
  
  isGenerating.value = true;
  try {
    const payload = { products: selectedProducts.value };
    
    const response = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error('서버 에러 발생');

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ESSER_맞춤형_상품제안서.pptx';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
    
    alert('제안서 다운로드가 완료되었습니다!');
  } catch (error) {
    console.error(error);
    alert('제안서 생성 중 오류가 발생했습니다.');
  } finally {
    isGenerating.value = false;
  }
};
</script>

<template>
  <div class="app-container">
    <header class="header">
      <h1>ESSER B2B 제안서 자동 생성기</h1>
      <p>기존 템플릿의 상품을 선택하고 단가, 수량 등을 입력하여 제안서를 구성하세요.</p>
    </header>

    <main class="content">
      <div class="product-list">
        <div v-for="(product, index) in selectedProducts" :key="product.id" class="product-card">
          <div class="card-header">
            <span class="product-number">선택 상품 {{ index + 1 }} : {{ product.name }}</span>
            <button class="btn-remove" @click="removeProduct(product.id)">삭제</button>
          </div>

          <div class="card-body">
            <!-- 상품명 (공통) -->
            <div class="input-group full-width">
              <label>상품명</label>
              <input type="text" v-model="product.name" placeholder="상품명 입력" />
            </div>

            <!-- 새 상품 전용 필드 (이미지) -->
            <template v-if="product.is_new">
              <div class="input-group full-width">
                <label>상품 이미지 업로드</label>
                <input type="file" accept="image/*" @change="e => handleImageUpload(e, product)" />
                <img v-if="product.image_base64" :src="product.image_base64" class="preview-img" />
              </div>
              <div class="custom-product-actions full-width">
                <button class="btn-save-product" @click="saveCustomProduct(product)">
                  {{ product.catalog_id ? '등록 상품 업데이트' : '새 상품 저장' }}
                </button>
                <span>저장하면 다음에도 기존 상품 목록에서 불러올 수 있습니다.</span>
              </div>
            </template>

            <div class="input-group">
              <label>온라인 최저가</label>
              <input type="text" v-model="product.onlineLowestPrice" placeholder="예: 39,000원" />
            </div>

            <div class="input-group">
              <label>공급가</label>
              <input type="text" v-model="product.supplyPrice" placeholder="예: 25,000원" />
            </div>

            <div class="input-group">
              <label>재고수량</label>
              <input type="text" v-model="product.stockQuantity" placeholder="예: 화이트 200개" />
            </div>

            <div class="input-group">
              <label>배송비</label>
              <input type="text" v-model="product.shippingFee" placeholder="예: 공급가 포함" />
            </div>

            <div class="input-group">
              <label>카톤수량</label>
              <input type="text" v-model="product.cartonQuantity" placeholder="예: 10개" />
            </div>

            <div class="input-group full-width">
              <label>옵션 및 구성</label>
              <textarea v-model="product.options" rows="3"></textarea>
            </div>
          </div>
        </div>
        <div class="btn-group">
          <button class="btn-add" @click="openTemplateModal">+ 기존 상품 여러 개 선택하기</button>
          <button class="btn-add-custom" @click="addCustomProduct">+ 새로운 상품 직접 등록하기</button>
        </div>
      </div>
    </main>

    <!-- Modal for selecting template products -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-content">
        <h2>기존 상품 선택</h2>
        <div class="template-list">
          <label
            v-for="t in templateProducts"
            :key="getTemplateId(t)"
            class="template-item"
            :class="{ disabled: isTemplateAdded(t) }"
          >
            <input
              v-model="checkedTemplateIds"
              type="checkbox"
              :value="getTemplateId(t)"
              :disabled="isTemplateAdded(t)"
            />
            <span class="t-name">
              {{ t.product_name }}
              <small v-if="t.is_custom">직접 등록</small>
            </span>
            <span class="t-slide">{{ t.is_custom ? '저장 상품' : `슬라이드 ${t.slide_index + 1}` }}</span>
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn-close" @click="showModal = false">닫기</button>
          <button class="btn-confirm" :disabled="checkedTemplateIds.length === 0" @click="addCheckedTemplates">
            선택한 {{ checkedTemplateIds.length }}개 추가
          </button>
        </div>
      </div>
    </div>

    <footer class="footer">
      <div class="summary">
        <span>총 선택된 상품: <strong>{{ selectedProducts.length }}</strong>개</span>
      </div>
      <div class="footer-actions">
        <button class="btn-secondary" @click="loadDraft">불러오기</button>
        <button class="btn-secondary" @click="saveDraft">임시저장</button>
        <button class="btn-generate" :disabled="selectedProducts.length === 0 || isGenerating" @click="generateProposal">
          <span v-if="isGenerating" class="spinner"></span>
          {{ isGenerating ? '생성 중...' : 'PPT 다운로드' }}
        </button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app-container {
  max-width: 800px;
  margin: 0 auto;
  padding-bottom: 100px;
  font-family: 'Pretendard', -apple-system, sans-serif;
  color: #333;
}

.header {
  padding: 30px 20px;
  text-align: center;
  background: #f8f9fa;
  border-radius: 0 0 16px 16px;
  margin-bottom: 20px;
}

.header h1 { margin: 0; font-size: 24px; color: #1a1a1a; }
.header p { margin: 10px 0 0; color: #666; font-size: 15px; }

.product-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 0 20px;
}

.product-card {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #f0f7ff;
  border-bottom: 1px solid #e0e0e0;
}

.product-number {
  font-weight: bold;
  color: #007bff;
}

.btn-remove {
  background: #dc3545;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.card-body {
  padding: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.input-group {
  flex: 1;
  min-width: 45%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.full-width {
  flex: 100%;
}

.input-group label {
  font-size: 13px;
  font-weight: bold;
  color: #495057;
}

.input-group input, .input-group textarea {
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
}

.btn-add {
  background: white;
  border: 2px dashed #007bff;
  color: #007bff;
  padding: 15px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 12px;
  cursor: pointer;
  margin-top: 10px;
}

.btn-add:hover {
  background: #f0f7ff;
}
.btn-group {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.btn-add {
  flex: 1;
}

.btn-add-custom {
  flex: 1;
  background: white;
  border: 2px dashed #28a745;
  color: #28a745;
  padding: 15px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 12px;
  cursor: pointer;
}

.btn-add-custom:hover {
  background: #f8fff9;
}

.preview-img {
  max-width: 150px;
  max-height: 150px;
  margin-top: 10px;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.custom-product-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.custom-product-actions span {
  color: #6c757d;
  font-size: 12px;
}

.btn-save-product {
  padding: 9px 14px;
  border: none;
  border-radius: 6px;
  background: #28a745;
  color: white;
  font-weight: bold;
  cursor: pointer;
}

.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-content h2 { margin-top: 0; }

.template-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.template-item {
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
}

.template-item:hover {
  background: #f8f9fa;
  border-color: #007bff;
}

.template-item.disabled {
  cursor: not-allowed;
  opacity: 0.5;
  background: #f8f9fa;
}

.template-item input {
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
}

.t-name {
  flex: 1;
  font-weight: bold;
}

.t-name small {
  margin-left: 6px;
  padding: 2px 5px;
  border-radius: 4px;
  background: #e8f7ec;
  color: #218838;
  font-size: 10px;
}

.t-slide { color: #888; font-size: 12px; }

.modal-actions {
  display: flex;
  gap: 10px;
}

.btn-close {
  flex: 1;
  padding: 10px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.btn-confirm {
  flex: 2;
  padding: 10px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
}

.btn-confirm:disabled {
  background: #ced4da;
  cursor: not-allowed;
}

.footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 20px;
  box-shadow: 0 -4px 15px rgba(0,0,0,0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 800px;
  margin: 0 auto;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.btn-secondary {
  background: #f8f9fa;
  color: #333;
  border: 1px solid #ced4da;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #e9ecef;
}

.btn-generate {
  background: #007bff;
  color: white;
  border: none;
  padding: 14px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-generate:disabled {
  background: #ced4da;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 3px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
