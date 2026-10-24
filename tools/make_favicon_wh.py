#!/usr/bin/env python3
"""Pixel favicon for warhammersurvivors.com (original 16x16 skull mark).
Run from repo root: python3 tools/make_favicon_wh.py"""
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]; A=ROOT/"extra_sites/warhammer-survivors/assets"; SRC=ROOT/"extra_sites/warhammer-survivors"
G=[
"................",
".KKKKKKKKKKKKKK.",
"KRRRRRRRRRRRRRRK",
"KRRRRGGGGGGRRRRK",
"KRRRGGGGGGGGRRRK",
"KRRGGGGGGGGGGRRK",
"KRRGGKKGGKKGGRRK",
"KRRGGKKGGKKGGRRK",
"KRRGGGGKKGGGGRRK",
"KRRRGGGKKGGGRRRK",
"KRRRRGGGGGGRRRRK",
"KRRRRGKGKGKRRRRK",
"KRRRRGGGGGGRRRRK",
"KRRRRRRRRRRRRRRK",
".KKKKKKKKKKKKKK.",
"................",
]
C={'K':(18,10,8,255),'R':(138,20,20,255),'G':(240,196,92,255),'.':(0,0,0,0)}
def base():
    im=Image.new("RGBA",(16,16))
    for y,row in enumerate(G):
        for x,c in enumerate(row): im.putpixel((x,y),C[c])
    return im
b=base()
for n in (16,32,48): b.resize((n,n),Image.NEAREST).save(A/f"favicon-{n}x{n}.png")
t=Image.new("RGBA",(180,180),C['R']); t.alpha_composite(b.resize((160,160),Image.NEAREST),(10,10)); t.save(A/"apple-touch-icon.png")
b.resize((48,48),Image.NEAREST).save(SRC/"favicon.ico",sizes=[(16,16),(32,32),(48,48)])
hexc=lambda c:'#%02x%02x%02x'%c[:3]
rects=''.join(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{hexc(C[c])}"/>' for y,r in enumerate(G) for x,c in enumerate(r) if c!='.')
(A/"favicon.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" shape-rendering="crispEdges">{rects}</svg>\n')
print("ok")
