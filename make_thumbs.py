#!/usr/bin/env python3
"""산출물 썸네일 생성: files/*/ 의 html → 첫 화면 캡처, png → 축소본. 결과는 thumbs/ 아래 같은 경로 + .jpg
사용법: python make_thumbs.py   (이미 있는 썸네일은 건너뜀, --force 로 다시)"""
import os,glob,sys
from PIL import Image
ROOT=os.path.dirname(os.path.abspath(__file__)); force='--force' in sys.argv
def out(p): return os.path.join(ROOT,'thumbs',os.path.relpath(p,ROOT))+'.jpg'
htmls=[p for p in glob.glob(os.path.join(ROOT,'files','**','*.html'),recursive=True)]
pngs=[p for p in glob.glob(os.path.join(ROOT,'files','**','*.png'),recursive=True)]
todo=[p for p in htmls if force or not os.path.exists(out(p))]
if todo:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b=pw.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':800})
        for p in todo:
            os.makedirs(os.path.dirname(out(p)),exist_ok=True)
            pg.goto('file://'+p); pg.wait_for_timeout(900)
            tmp=out(p)+'.png'; pg.screenshot(path=tmp)
            im=Image.open(tmp).convert('RGB'); im.thumbnail((640,400)); im.save(out(p),quality=82); os.remove(tmp)
            print('html',os.path.relpath(p,ROOT))
for p in pngs:
    if force or not os.path.exists(out(p)):
        os.makedirs(os.path.dirname(out(p)),exist_ok=True)
        im=Image.open(p).convert('RGB'); im.thumbnail((420,420)); im.save(out(p),quality=80)
