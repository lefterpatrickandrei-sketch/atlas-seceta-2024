from pptx import Presentation

prs = Presentation(r'ppt/GIS Day 2026 — Atlasul secetei din 2024 — v2.pptx')
s6 = prs.slides[5]
for sh_idx in range(24, 30):
    sh = s6.shapes[sh_idx]
    tf = sh.text_frame if sh.has_text_frame else None
    print(f'Shape {sh_idx+1}: type={sh.shape_type}, pos=({sh.left/914400:.2f}", {sh.top/914400:.2f}", w={sh.width/914400:.2f}", h={sh.height/914400:.2f}")')
    if tf:
        print(f'   margins: L={tf.margin_left/914400 if tf.margin_left else 0:.2f}", R={tf.margin_right/914400 if tf.margin_right else 0:.2f}", word_wrap={tf.word_wrap}')
        for p in tf.paragraphs:
            for r in p.runs:
                print(f'   run: text="{r.text}", font_size={r.font.size.pt if r.font.size else "None"}')

