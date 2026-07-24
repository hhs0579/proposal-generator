import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pptx import Presentation

prs = Presentation("C:/Users/Esser/Desktop/ESSER_B2B_상품제안서_수정본.pptx")
slide = prs.slides[7] # Slide 8

# Find the online lowest price label
label_idx = None
for idx, shape in enumerate(slide.shapes):
    if shape.has_text_frame and shape.text.strip() == "온라인 최저가":
        label_idx = idx
        break

if label_idx is not None:
    val_shape = slide.shapes[label_idx+2]
    print(f"Value shape index {label_idx+2}: {repr(val_shape.text)}")
    print(f"Value shape position: left={val_shape.left}, top={val_shape.top}, width={val_shape.width}, height={val_shape.height}")
    
    # Check all other shapes to see if they overlap
    print("\nOverlapping shapes:")
    for idx, shape in enumerate(slide.shapes):
        if idx != label_idx+2 and shape.has_text_frame and shape.text.strip():
            # Check for intersection or exact match
            if shape.left == val_shape.left and shape.top == val_shape.top:
                print(f"  EXACT MATCH! Shape {idx}: {repr(shape.text)}")
