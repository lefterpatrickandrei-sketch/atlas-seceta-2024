from PIL import ImageFont
import glob

# Search for inter font in windows or scripts
fonts = glob.glob("C:/Windows/Fonts/*Inter*.ttf") + glob.glob("data/interim/fonts/*.ttf")
font_path = fonts[0] if fonts else None
print("Font path:", font_path)

if font_path:
    # 12 pt at 96 DPI is 16 pixels
    f = ImageFont.truetype(font_path, 16)
else:
    f = ImageFont.load_default()

t1 = "ținta veche era pe NDVI"
t2 = "rotația culturilor falsifica pierderea"
t3 = "„irigarea” din radar nu era irigare"

for t, max_in in [(t1, 1.92), (t2, 2.78), (t3, 2.65)]:
    w_px = f.getlength(t) if hasattr(f, 'getlength') else len(t)*8
    max_px = max_in * 96
    print(f"'{t}': length={w_px:.1f}px, box={max_px:.1f}px -> {'OK' if w_px <= max_px else 'OVERFLOW/WRAPS!'}")

