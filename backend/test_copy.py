from pptx import Presentation
import copy

prs = Presentation("template.pptx")

# 1. 7번 슬라이드(인덱스 6)에 태그 달아두기
slide = prs.slides[6]
for i, shape in enumerate(slide.shapes):
    if shape.has_text_frame:
        text = shape.text.strip()
        print(f"Shape {i}: {text}")

