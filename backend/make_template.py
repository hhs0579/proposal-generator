from pptx import Presentation

prs = Presentation("template.pptx")

# 6번 슬라이드부터 54번 슬라이드까지 포맷을 통일합니다.
for i in range(6, 55):
    slide = prs.slides[i]
    # 이름: index 5
    # 이미지: index 3
    # 41: 최저가레이블, 43: 값
    # 45: 공급가레이블, 47: 값
    # 49: 재고레이블, 51: 값
    # 53: 배송비, 55: 값
    # 57: 카톤, 59: 값
    
    # 태그 심기
    if len(slide.shapes) > 63:
        slide.shapes[5].text = "{{product_name}}"
        slide.shapes[43].text = "{{lowest_price}}"
        slide.shapes[47].text = "{{supply_price}}"
        slide.shapes[51].text = "{{stock}}"

prs.save("master_template.pptx")
print("master_template.pptx 생성 완료")
