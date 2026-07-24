import io
import os
import json
import base64
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from typing import List, Optional
from pptx import Presentation
from pptx.util import Pt

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_PATH = os.path.join(BASE_DIR, "products_rich.json")
CUSTOM_PRODUCTS_PATH = os.path.join(BASE_DIR, "custom_products.json")
DRAFT_PATH = os.path.join(BASE_DIR, "saved_draft.json")
TEMPLATE_PATH = os.path.join(BASE_DIR, "template.pptx")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SelectedProduct(BaseModel):
    id: Optional[int] = None
    catalog_id: Optional[str] = None
    slide_index: int
    name: Optional[str] = ""
    onlineLowestPrice: str = ""
    supplyPrice: str = ""
    stockQuantity: str = ""
    shippingFee: str = ""
    cartonQuantity: str = ""
    options: str = ""
    image_base64: Optional[str] = None
    is_new: Optional[bool] = False

class ProposalRequest(BaseModel):
    products: List[SelectedProduct]

def delete_slide(prs, index):
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    try:
        xml_slides.remove(slides[index])
    except Exception as e:
        print(f"Failed to delete slide {index}: {e}")

def replace_text_in_shape(shape, new_text, font_size=9, is_bold=False):
    if not shape.has_text_frame:
        return
    text_frame = shape.text_frame

    # 기존 문단/run/줄바꿈을 모두 제거한 뒤 한 번만 작성한다.
    # 옷걸이 슬라이드처럼 여러 run으로 구성된 값이 새 값과 겹치는 것을 방지한다.
    text_frame.clear()
    paragraph = text_frame.paragraphs[0]
    run = paragraph.add_run()
    run.text = str(new_text).replace("\x0b", "\n")
    run.font.size = Pt(font_size)
    if is_bold:
        run.font.bold = True


def read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.get("/products")
async def get_products():
    try:
        products = read_json(PRODUCTS_PATH, [])
        built_in_products = [
            {
                **product,
                "catalog_id": f"template:{product['slide_index']}",
                "is_custom": False,
            }
            for product in products
        ]
        return built_in_products + read_json(CUSTOM_PRODUCTS_PATH, [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/products/custom")
async def save_custom_product(product: SelectedProduct):
    try:
        if not product.name or not product.name.strip():
            raise HTTPException(status_code=400, detail="상품명을 입력해 주세요.")

        custom_products = read_json(CUSTOM_PRODUCTS_PATH, [])
        catalog_id = product.catalog_id or f"custom:{uuid.uuid4().hex}"
        saved_product = {
            "catalog_id": catalog_id,
            "slide_index": -1,
            "product_name": product.name.strip(),
            "options": product.options,
            "onlineLowestPrice": product.onlineLowestPrice,
            "supplyPrice": product.supplyPrice,
            "stockQuantity": product.stockQuantity,
            "shippingFee": product.shippingFee,
            "cartonQuantity": product.cartonQuantity,
            "image_base64": product.image_base64,
            "is_custom": True,
        }

        existing_index = next(
            (
                index
                for index, item in enumerate(custom_products)
                if item.get("catalog_id") == catalog_id
            ),
            None,
        )
        if existing_index is None:
            custom_products.append(saved_product)
        else:
            custom_products[existing_index] = saved_product

        write_json(CUSTOM_PRODUCTS_PATH, custom_products)
        return saved_product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save")
async def save_draft(req: ProposalRequest):
    try:
        write_json(DRAFT_PATH, [p.model_dump() for p in req.products])
        return {"message": "Saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/load")
async def load_draft():
    try:
        return read_json(DRAFT_PATH, [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
async def generate_proposal(req: ProposalRequest):
    try:
        prs = Presentation(TEMPLATE_PATH) # 원본 템플릿 사용
        
        # 기존 상품과 새로운 상품 분리
        existing_products = [p for p in req.products if not p.is_new]
        new_products = [p for p in req.products if p.is_new]
        
        selected_indices = [p.slide_index for p in existing_products]
        unselected_indices = [i for i in range(6, 55) if i not in selected_indices]
        
        # 새로운 상품에게 사용하지 않은 슬라이드 할당
        for p in new_products:
            if not unselected_indices:
                raise Exception("템플릿에 사용 가능한 여분 슬라이드가 부족합니다. (최대 49개 상품 제안 가능)")
            reused_idx = unselected_indices.pop(0) # 앞에서부터 남는 슬라이드 하나 가져옴
            p.slide_index = reused_idx
            selected_indices.append(reused_idx)
            
        # 모든 상품 리스트 병합 (이제 모두 slide_index를 가짐)
        all_products = existing_products + new_products
        
        # 1. 선택된 슬라이드의 데이터 채우기
        for i, prod in enumerate(all_products):
            slide = prs.slides[prod.slide_index]
            
            # 모든 상품에 대해 상품명 교체
            for idx, shape in enumerate(slide.shapes):
                if shape.has_text_frame and "KEY SELLING POINTS" in shape.text:
                    # 상품명 변경 (보통 KEY SELLING POINTS 바로 이전 텍스트)
                    if idx > 0 and slide.shapes[idx-1].has_text_frame:
                        if prod.name and prod.name.strip() != "":
                            replace_text_in_shape(slide.shapes[idx-1], prod.name, font_size=18, is_bold=True)
                        
                    # 새로운 상품인 경우 상세설명 초기화
                    if prod.is_new:
                        if idx + 1 < len(slide.shapes) and slide.shapes[idx+1].has_text_frame:
                            replace_text_in_shape(slide.shapes[idx+1], "• 상세 설명 참고")
                    break
                    
            # 새로운 상품인 경우 이미지 교체
            if prod.is_new and prod.image_base64:
                try:
                    img_shape = None
                    for s in slide.shapes:
                        if s.shape_type == 13: # PICTURE
                            img_shape = s
                            break
                    if img_shape:
                        left, top, width, height = img_shape.left, img_shape.top, img_shape.width, img_shape.height
                        sp = img_shape.element
                        sp.getparent().remove(sp)
                        
                        img_data = prod.image_base64.split(",")[1] if "," in prod.image_base64 else prod.image_base64
                        img_bytes = base64.b64decode(img_data)
                        tmp_img_path = f"temp_img_{i}.png"
                        with open(tmp_img_path, "wb") as f:
                            f.write(img_bytes)
                        
                        slide.shapes.add_picture(tmp_img_path, left, top, width, height)
                        if os.path.exists(tmp_img_path):
                            os.remove(tmp_img_path)
                except Exception as img_err:
                    print(f"이미지 교체 오류: {img_err}")

            # 공통 데이터(가격, 수량 등) 채우기
            for idx, shape in enumerate(slide.shapes):
                if shape.has_text_frame:
                    text = shape.text.strip()
                    if text == "온라인 최저가" and idx + 2 < len(slide.shapes):
                        if prod.onlineLowestPrice and prod.onlineLowestPrice.strip() != "":
                            replace_text_in_shape(slide.shapes[idx+2], prod.onlineLowestPrice)
                    elif text == "공급가" and idx + 2 < len(slide.shapes):
                        if prod.supplyPrice and prod.supplyPrice.strip() != "":
                            replace_text_in_shape(slide.shapes[idx+2], prod.supplyPrice)
                    elif text == "재고수량" and idx + 2 < len(slide.shapes):
                        if prod.stockQuantity and prod.stockQuantity.strip() != "":
                            replace_text_in_shape(slide.shapes[idx+2], prod.stockQuantity)
                    elif text == "배송비" and idx + 2 < len(slide.shapes):
                        if prod.shippingFee and prod.shippingFee.strip() != "":
                            replace_text_in_shape(slide.shapes[idx+2], prod.shippingFee)
                    elif text == "카톤수량" and idx + 2 < len(slide.shapes):
                        if prod.cartonQuantity and prod.cartonQuantity.strip() != "":
                            replace_text_in_shape(slide.shapes[idx+2], prod.cartonQuantity)
                    elif text == "옵션 및 구성" and idx + 2 < len(slide.shapes):
                        if prod.options and prod.options.strip() != "":
                            replace_text_in_shape(slide.shapes[idx+2], prod.options)
        
        # 2. 선택되지 않은 상품 슬라이드 삭제 (역순으로 삭제해야 인덱스 안 꼬임)
        unselected_indices.sort(reverse=True)
        for i in unselected_indices:
            delete_slide(prs, i)

        output = io.BytesIO()
        prs.save(output)
        output.seek(0)

        return StreamingResponse(
            output, 
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": "attachment; filename=ESSER_Custom_Proposal.pptx"}
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Mount frontend dist folder
frontend_dist = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
