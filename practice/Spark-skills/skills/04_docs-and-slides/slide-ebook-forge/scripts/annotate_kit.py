# -*- coding: utf-8 -*-
r"""
標註四件套：把實機截圖加工成成書用圖。
用法：
    from annotate_kit import Annotator
    a = Annotator(r'F:\專案\講義製作\U01\real')
    im = a.load('raw_menu.png')
    a.frame(im, (120, 80, 300, 40))          # 紅框
    a.badge(im, 110, 70, 1)                  # 數字圓標
    a.pill(im, 430, 85, '點這裡開啟選單')      # 說明籤
    a.cover(im, (900, 12, 180, 20), '（時間）')  # 遮蓋日期
    a.save(im, 'm01.png')
來源：F:\GAS 專案已驗證工法（U01~U09 共數百張圖）
"""
from PIL import Image, ImageDraw, ImageFont
import os

RED    = (229, 57, 53)
TEAL   = (0, 105, 92)
ORANGE = (230, 81, 0)
NAVY   = (40, 53, 147)
WHITE  = (255, 255, 255)

_FONT_BD = r'C:\Windows\Fonts\msjhbd.ttc'   # 微軟正黑體 粗
_FONT_RG = r'C:\Windows\Fonts\msjh.ttc'     # 微軟正黑體 一般


class Annotator:
    def __init__(self, real_dir, out_sub='annotated'):
        self.d = real_dir
        self.out = os.path.join(real_dir, out_sub)
        os.makedirs(self.out, exist_ok=True)
        self.f_pill  = ImageFont.truetype(_FONT_BD, 20)
        self.f_badge = ImageFont.truetype(_FONT_BD, 22)
        self.f_cover = ImageFont.truetype(_FONT_RG, 15)

    # ---------- 讀寫 ----------
    def load(self, name):
        return Image.open(os.path.join(self.d, name)).convert('RGB')

    def save(self, im, name, box=None):
        """box=(x,y,w,h) 則先裁切再存，讓成書圖只留要看的區域"""
        if box:
            x, y, w, h = box
            im = im.crop((x, y, x + w, y + h))
        path = os.path.join(self.out, name)
        im.save(path)
        print('saved %s  %dx%d' % (name, im.width, im.height))
        return path

    # ---------- 四件套 ----------
    def frame(self, im, box, w=4, pad=6):
        """紅色圈選框（含半透明外暈），box=(x,y,寬,高)"""
        dr = ImageDraw.Draw(im)
        x, y, bw, bh = box
        r = [x - pad, y - pad, x + bw + pad, y + bh + pad]
        dr.rounded_rectangle([r[0]-3, r[1]-3, r[2]+3, r[3]+3],
                             radius=12, outline=(245, 150, 148), width=3)
        dr.rounded_rectangle(r, radius=10, outline=RED, width=w)
        return r

    def badge(self, im, x, y, n, R=17):
        """步驟數字圓標：紅底白字，外圈白色"""
        dr = ImageDraw.Draw(im)
        dr.ellipse([x-R-2, y-R-2, x+R+2, y+R+2], fill=WHITE)
        dr.ellipse([x-R, y-R, x+R, y+R], fill=RED)
        t = str(n)
        tb = dr.textbbox((0, 0), t, font=self.f_badge)
        dr.text((x-(tb[2]-tb[0])/2, y-(tb[3]-tb[1])/2-tb[1]),
                t, font=self.f_badge, fill=WHITE)

    def pill(self, im, x, y, text, color=TEAL):
        """藥丸型說明籤"""
        dr = ImageDraw.Draw(im)
        tb = dr.textbbox((0, 0), text, font=self.f_pill)
        w, h = tb[2]-tb[0], tb[3]-tb[1]
        px, py = 14, 8
        dr.rounded_rectangle([x, y, x+w+px*2, y+h+py*2],
                             radius=(h+py*2)//2, fill=color)
        dr.text((x+px, y+py-tb[1]), text, font=self.f_pill, fill=WHITE)
        return (x, y, w+px*2, h+py*2)

    def cover(self, im, box, text='（時間）', bg=(238, 238, 238)):
        """遮蓋：蓋掉日期/帳號/金鑰，換成中性標籤。box=(x,y,寬,高)"""
        dr = ImageDraw.Draw(im)
        x, y, w, h = box
        dr.rectangle([x, y, x+w, y+h], fill=bg)
        if text:
            tb = dr.textbbox((0, 0), text, font=self.f_cover)
            dr.text((x+(w-(tb[2]-tb[0]))/2, y+(h-(tb[3]-tb[1]))/2-tb[1]),
                    text, font=self.f_cover, fill=(120, 120, 120))

    # ---------- 組合 ----------
    def step(self, im, box, n, text, color=TEAL, side='right'):
        """一次畫完「框＋圓標＋說明籤」，最常用"""
        r = self.frame(im, box)
        self.badge(im, r[0], r[1], n)
        if side == 'right':
            self.pill(im, r[2] + 14, r[1], text, color)
        else:
            self.pill(im, r[0], r[3] + 12, text, color)
