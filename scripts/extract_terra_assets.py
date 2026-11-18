import argparse
import io
import math
import os
import zipfile
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_REF_PPTX = os.path.join(BASE_DIR, 'ref', 'source_template.pptx')
OUT_DIR = os.path.join(BASE_DIR, 'templates', 'builtin', 'assets', 'terra_quest')


def _recolor_rgba(img_rgba, rgb_tuple, alpha_scale=1.0, alpha_max=255):
    r, g, b = rgb_tuple
    _, _, _, a = img_rgba.split()
    if alpha_scale != 1.0 or alpha_max < 255:
        a = a.point(lambda v: min(alpha_max, int(round(v * alpha_scale))))
    solid = Image.new('RGBA', img_rgba.size, (r, g, b, 255))
    solid.putalpha(a)
    return solid


def _build_clean_contour_wave(size=1000):
    """生成纯几何多频地形等高线 + 微型十字 HUD 准星波纹底图（暖炭灰细线，无建筑/音符干扰）。"""
    hi = size * 2
    img = Image.new('RGBA', (hi, hi), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 16 条流动地形等高线（自右上延展至左下，渐隐边界衰减）
    num_lines = 16
    steps = 160
    for k in range(num_lines):
        phase = k * 0.28
        base_y = hi * 0.22 + k * (hi * 0.044)
        pts = []
        for s in range(steps + 1):
            u = s / steps
            x = hi * (0.04 + 0.92 * u)
            env = math.sin(u * math.pi)
            wave = (
                42.0 * math.sin(u * 5.2 + phase)
                + 22.0 * math.cos(u * 9.4 - phase * 0.7)
                + 10.0 * math.sin(u * 15.0 + k * 0.5)
            )
            y = base_y + wave * env - u * (hi * 0.14)
            pts.append((x, y))
        alpha_v = int(125 - abs(k - num_lines * 0.5) * 8)
        w_px = 3 if (k % 4 == 0) else 2
        draw.line(pts, fill=(95, 92, 86, max(40, alpha_v)), width=w_px)

    # 若干工业十字准星 (+ ) 与微小刻度点缀
    cross_pts = [(hi * 0.25, hi * 0.28), (hi * 0.72, hi * 0.22), (hi * 0.54, hi * 0.68), (hi * 0.82, hi * 0.76)]
    for cx, cy in cross_pts:
        d = 18
        draw.line([(cx - d, cy), (cx + d, cy)], fill=(24, 24, 27, 110), width=2)
        draw.line([(cx, cy - d), (cx, cy + d)], fill=(24, 24, 27, 110), width=2)

    return img.resize((size, size), Image.LANCZOS)


def _build_precision_ring_hud(size=800):
    """生成精密双同心工业 HUD 刻度圆环（无特定乐谱内容，契合 PRTS 科技星环美学）。"""
    hi = size * 2
    img = Image.new('RGBA', (hi, hi), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = hi // 2, hi // 2

    # 多重同心细环与短刻度弧
    for r, w_px, a in [(hi * 0.44, 4, 175), (hi * 0.36, 2, 130), (hi * 0.25, 3, 155)]:
        bbox = [cx - r, cy - r, cx + r, cy + r]
        draw.arc(bbox, start=18, end=158, fill=(46, 45, 42, a), width=w_px)
        draw.arc(bbox, start=198, end=338, fill=(46, 45, 42, a), width=w_px)

    # 36 个机械仪表刻度线
    for deg in range(0, 360, 10):
        rad = math.radians(deg)
        r0 = hi * (0.39 if deg % 30 == 0 else 0.415)
        r1 = hi * 0.44
        w_px = 4 if deg % 30 == 0 else 2
        p0 = (cx + r0 * math.cos(rad), cy + r0 * math.sin(rad))
        p1 = (cx + r1 * math.cos(rad), cy + r1 * math.sin(rad))
        draw.line([p0, p1], fill=(24, 24, 27, 170), width=w_px)

    # 十字定位线
    d_in, d_out = hi * 0.14, hi * 0.48
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        draw.line([(cx + dx * d_in, cy + dy * d_in), (cx + dx * d_out, cy + dy * d_out)], fill=(46, 45, 42, 110), width=2)

    return img.resize((size, size), Image.LANCZOS)


def extract_assets(pptx_path=DEFAULT_REF_PPTX, out_dir=OUT_DIR):
    if not os.path.isfile(pptx_path):
        raise FileNotFoundError(f"Source reference PPTX not found: {pptx_path}")
    os.makedirs(out_dir, exist_ok=True)

    with zipfile.ZipFile(pptx_path, 'r') as z:
        # 1. ring_hud.png (精密双环工业刻度 HUD)
        _build_precision_ring_hud(800).save(os.path.join(out_dir, 'ring_hud.png'))

        # 2. tech_emblem.png (image2.png: 510x510，调和为 PRTS 炭灰青柠双色兼容风格)
        im2 = Image.open(io.BytesIO(z.read('ppt/media/image2.png'))).convert('RGBA')
        _recolor_rgba(im2, (82, 80, 76), alpha_scale=1.2, alpha_max=180).save(
            os.path.join(out_dir, 'tech_emblem.png')
        )

        # 3. contour_wave.png (通用纯几何等高线波形 + HUD 准星底纹)
        _build_clean_contour_wave(1000).save(os.path.join(out_dir, 'contour_wave.png'))

        # 4. crystal_cluster.png (image4.png: 841x792 -> 420x396)
        im4 = Image.open(io.BytesIO(z.read('ppt/media/image4.png'))).convert('RGBA')
        im4.resize((420, 396), Image.LANCZOS).save(os.path.join(out_dir, 'crystal_cluster.png'))

        # 5. 4 枚科技矢量图标 -> 分别导出深炭黑 (24,24,27) 与荧光青柠 (208,229,22) 两套 200x200 PNG
        icon_map = [
            ('ppt/media/image11.png', 'flask'),
            ('ppt/media/image13.png', 'gear'),
            ('ppt/media/image15.png', 'board'),
            ('ppt/media/image17.png', 'chart'),
        ]
        for zip_name, short_name in icon_map:
            im = Image.open(io.BytesIO(z.read(zip_name))).convert('RGBA').resize((200, 200), Image.LANCZOS)
            _recolor_rgba(im, (24, 24, 27)).save(os.path.join(out_dir, f'icon_{short_name}_dark.png'))
            _recolor_rgba(im, (208, 229, 22)).save(os.path.join(out_dir, f'icon_{short_name}_lime.png'))

    files = sorted(os.listdir(out_dir))
    print(f"Extracted & refined {len(files)} terra_quest assets -> {out_dir}")
    for fn in files:
        sz = round(os.path.getsize(os.path.join(out_dir, fn)) / 1024.0, 1)
        print(f"  - {fn} ({sz} KB)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract & sanitize geometric HUD and icon assets for terra_quest.')
    parser.add_argument('--src', default=DEFAULT_REF_PPTX, help='Path to source .pptx file')
    args = parser.parse_args()
    extract_assets(pptx_path=args.src)
