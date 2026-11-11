import os
import sys
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

def run():
    pptx_path = r"ppt/GIS Day 2026 — Atlasul secetei din 2024 — v2.pptx"
    out_md = r"ppt/_audit/inventar.md"
    
    prs = Presentation(pptx_path)
    sw = prs.slide_width
    sh = prs.slide_height
    
    lines = []
    lines.append(f"# Inventar Prezentare PPTX")
    lines.append(f"- Fișier: `{pptx_path}`")
    lines.append(f"- Dimensiuni slide: {sw} x {sh} EMU ({sw/914400:.2f} x {sh/914400:.2f} inchi, aspect {sw/sh:.2f})")
    lines.append(f"- Număr total slide-uri: {len(prs.slides)}\n")
    
    for idx, slide in enumerate(prs.slides, 1):
        lines.append(f"## Slide {idx}")
        
        # Speaker notes
        notes = ""
        if slide.has_notes_slide:
            notes_tf = slide.notes_slide.notes_text_frame
            if notes_tf:
                notes = notes_tf.text.strip()
        lines.append(f"**Speaker Notes:** {notes if notes else '*(fără note)*'}\n")
        
        # Shapes & text
        lines.append("### Elemente vizuale și text:")
        for s_idx, shape in enumerate(slide.shapes, 1):
            s_type = str(shape.shape_type)
            left = shape.left
            top = shape.top
            width = shape.width
            height = shape.height
            
            # Check if out of slide bounds
            out_bounds = []
            if left < 0: out_bounds.append(f"left < 0 ({left})")
            if top < 0: out_bounds.append(f"top < 0 ({top})")
            if left + width > sw: out_bounds.append(f"right > slide_width ({left+width} > {sw})")
            if top + height > sh: out_bounds.append(f"bottom > slide_height ({top+height} > {sh})")
            
            bound_warn = f" ⚠️ **DEPĂȘEȘTE MARGINEA:** {', '.join(out_bounds)}" if out_bounds else ""
            
            if shape.has_text_frame:
                text = shape.text_frame.text.strip()
                if text:
                    # Summarize paragraphs
                    p_texts = [p.text.strip() for p in shape.text_frame.paragraphs if p.text.strip()]
                    full_p = " | ".join(p_texts)
                    lines.append(f"- **Shape {s_idx} (Text)** [{left/914400:.2f}\", {top/914400:.2f}\", w={width/914400:.2f}\", h={height/914400:.2f}\"]{bound_warn}:")
                    lines.append(f"  > {full_p}")
            elif shape.has_table:
                table = shape.table
                lines.append(f"- **Shape {s_idx} (Tabel {len(table.rows)}x{len(table.columns)})** [{left/914400:.2f}\", {top/914400:.2f}\", w={width/914400:.2f}\", h={height/914400:.2f}\"]{bound_warn}:")
                for r_idx, row in enumerate(table.rows):
                    row_txt = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                    lines.append(f"  | {' | '.join(row_txt)} |")
            elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                image = shape.image
                lines.append(f"- **Shape {s_idx} (Imagine)** [{left/914400:.2f}\", {top/914400:.2f}\", w={width/914400:.2f}\", h={height/914400:.2f}\"]{bound_warn}: Format {image.ext}, Dimensiuni {image.size}")
            elif shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                lines.append(f"- **Shape {s_idx} (Grup)** [{left/914400:.2f}\", {top/914400:.2f}\", w={width/914400:.2f}\", h={height/914400:.2f}\"]{bound_warn}")
            else:
                lines.append(f"- **Shape {s_idx} (Tip: {s_type})** [{left/914400:.2f}\", {top/914400:.2f}\", w={width/914400:.2f}\", h={height/914400:.2f}\"]{bound_warn}")
                
        lines.append("\n---\n")
        
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Inventar extras cu succes în {out_md}")

if __name__ == "__main__":
    run()

