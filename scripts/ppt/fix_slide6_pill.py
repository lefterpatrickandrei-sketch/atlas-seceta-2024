from pptx import Presentation
from pptx.util import Inches

prs = Presentation(r'ppt/GIS Day 2026 — Atlasul secetei din 2024 — v2.pptx')
s6 = prs.slides[5]

# Shape 29 is the background pill (index 28)
# Shape 30 is the text box (index 29)
bg_shape = s6.shapes[28]
txt_shape = s6.shapes[29]

print("Inainte:", txt_shape.left/914400, txt_shape.width/914400, txt_shape.text_frame.text)

# Slightly widen background pill to 3.05" so text has breathing room
bg_shape.width = Inches(3.05)

# Align and widen text box
txt_shape.left = Inches(6.30)
txt_shape.width = Inches(2.90)
txt_shape.text_frame.margin_left = Inches(0.0)
txt_shape.text_frame.margin_right = Inches(0.0)
txt_shape.text_frame.word_wrap = False

print("Dupa:", txt_shape.left/914400, txt_shape.width/914400, txt_shape.text_frame.text)

prs.save(r'ppt/GIS Day 2026 — Atlasul secetei din 2024 — v2.pptx')
print("Salvat cu succes in v2.pptx!")

