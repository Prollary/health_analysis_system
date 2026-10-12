# -*- coding: utf-8 -*-
"""
生成 HealthAI 智慧舱 .ico 图标
风格：深色圆角背景 + 蓝色心形 + ECG 脉冲线
尺寸：256/128/64/48/32/16 多分辨率合并成 .ico
"""
from PIL import Image, ImageDraw
import math, os

def draw_frame(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size

    # ── 圆角背景 ──────────────────────────────
    radius = int(s * 0.22)
    bg_color = (10, 25, 50, 255)           # 深海蓝
    d.rounded_rectangle([0, 0, s-1, s-1], radius=radius, fill=bg_color)

    # ── 渐变光晕（纯色模拟，叠加圆形） ─────────
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(int(s*0.38), int(s*0.18), -2):
        alpha = int(18 * (1 - (r - s*0.18) / (s*0.2)))
        gd.ellipse([s//2 - r, s//2 - r, s//2 + r, s//2 + r],
                   fill=(0, 140, 255, max(0, alpha)))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)

    # ── 心形 ──────────────────────────────────
    # 心形参数方程: x = 16sin³t, y = 13cost - 5cos2t - 2cos3t - cos4t
    # 缩放到画布
    heart_scale = s * 0.28
    cx, cy = s * 0.5, s * 0.52
    heart_pts = []
    for i in range(360):
        t = math.radians(i)
        hx = 16 * (math.sin(t) ** 3)
        hy = -(13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t))
        heart_pts.append((cx + hx * heart_scale / 16,
                          cy + hy * heart_scale / 13))

    # 心形填充（主色蓝）
    d.polygon(heart_pts, fill=(0, 120, 255, 230))
    # 心形高光边
    d.polygon(heart_pts, outline=(80, 200, 255, 200))

    # ── ECG 脉冲线（横穿心形） ────────────────
    lw = max(1, s // 40)
    line_color = (255, 255, 255, 240)
    line_y = cy + s * 0.02

    # ECG 路径（相对比例坐标）
    seg_w = s * 0.70
    x0 = s * 0.15
    segs = [
        (0.00, 0.0),
        (0.18, 0.0),
        (0.26, -0.22),   # 小上升
        (0.30, 0.0),
        (0.34, -0.55),   # R 峰（高）
        (0.38, 0.32),    # S 谷
        (0.44, 0.0),
        (0.54, 0.14),    # T 波
        (0.62, 0.0),
        (1.00, 0.0),
    ]
    amp = s * 0.20
    pts = [(x0 + r * seg_w, line_y + v * amp) for r, v in segs]
    for i in range(len(pts) - 1):
        d.line([pts[i], pts[i+1]], fill=line_color, width=lw)

    # ── 顶部 "AI" 小标签 ──────────────────────
    if s >= 64:
        tag_w, tag_h = int(s * 0.30), int(s * 0.17)
        tx = int(s * 0.60)
        ty = int(s * 0.12)
        d.rounded_rectangle([tx, ty, tx + tag_w, ty + tag_h],
                             radius=int(tag_h * 0.4),
                             fill=(0, 180, 255, 220))
        if s >= 128:
            try:
                from PIL import ImageFont
                font_size = max(8, int(tag_h * 0.65))
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except Exception:
                    font = ImageFont.load_default()
                text = "AI"
                bbox = d.textbbox((0, 0), text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                d.text((tx + (tag_w - tw) // 2, ty + (tag_h - th) // 2 - 1),
                       text, fill=(255, 255, 255, 255), font=font)
            except Exception:
                pass

    return img


sizes = [256, 128, 64, 48, 32, 16]
frames = [draw_frame(s) for s in sizes]

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "healthai.ico")
frames[0].save(
    output_path,
    format="ICO",
    sizes=[(s, s) for s in sizes],
    append_images=frames[1:]
)
print(f"[OK] 图标已生成: {output_path}")
