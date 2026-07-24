import json
from pptx import Presentation

def extract_products(ppt_path, output_json):
    prs = Presentation(ppt_path)
    products = []
    
    # 슬라이드 7(인덱스 6)부터 55(인덱스 54)까지 상품 슬라이드라고 가정
    for i, slide in enumerate(prs.slides):
        if i < 6 or i > 54:
            continue
            
        product_name = f"알 수 없는 상품 (슬라이드 {i+1})"
        
        # 상품명 찾기 (주로 TextBox 6 또는 그 근처에 있음)
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            text = shape.text.strip().replace('\n', ' ')
            # '베스트하임', '니카사', '프랑스', '매직그린행주' 등 상품명 추출 로직
            if text and ("베스트하임" in text or "니카사" in text or "사본느리" in text or "잠이솔솔" in text or "행주" in text or "옷걸이" in text or "치약" in text or "올리브오일" in text or "그린백" in text):
                if len(text) < 50: # 너무 긴 상세설명 제외
                    product_name = text
                    break
        
        products.append({
            "slide_index": i,
            "product_name": product_name
        })
        
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"총 {len(products)}개의 상품을 성공적으로 추출했습니다.")

extract_products("template.pptx", "products.json")
