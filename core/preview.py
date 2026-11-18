import math
import os
import re
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter, ImageFont

Image.MAX_IMAGE_PIXELS = None
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _hex_rgba(hex_str, alpha=1.0):
    if not hex_str or not isinstance(hex_str, str):
        return (0, 0, 0, 0)
    h = hex_str.lstrip('#').strip()
    if len(h) != 6:
        return (0, 0, 0, int(round(255 * alpha)))
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    a = max(0, min(255, int(round(255 * float(alpha)))))
    return (r, g, b, a)


@lru_cache(maxsize=64)
def _get_font(size_px, bold=False):
    px = max(8, int(round(size_px)))
    candidates = (
        [r'C:\Windows\Fonts\msyhbd.ttc', r'C:\Windows\Fonts\simhei.ttf', r'C:\Windows\Fonts\msyh.ttc']
        if bold else
        [r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\segoeui.ttf', r'C:\Windows\Fonts\simhei.ttf']
    )
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=px)
            except Exception:
                pass
    return ImageFont.load_default()


def _resolve_asset_path(web_path):
    if not web_path:
        return None
    rel = str(web_path).lstrip('/').replace('/', os.sep)
    full = os.path.join(BASE_DIR, rel)
    return full if os.path.isfile(full) else None


def _make_gradient_image(w, h, grad_data):
    w = max(1, int(round(w)))
    h = max(1, int(round(h)))
    stops = sorted((grad_data or {}).get('stops') or [], key=lambda s: float(s.get('pos', 0.0)))
    if not stops:
        return Image.new('RGBA', (w, h), (255, 255, 255, 0))

    parsed = []
    for s in stops:
        pos = float(s.get('pos', 0.0))
        if pos > 1.0:
            pos /= 100000.0
        col = _hex_rgba(s.get('color', '#FFFFFF'), s.get('alpha', 1.0))
        parsed.append((pos, col))

    # 在小栅格计算线性渐变再双线性放大，兼顾高精度与毫秒级渲染速度
    gw, gh = min(w, 160), min(h, 90)
    ang = math.radians(float((grad_data or {}).get('angle', 0.0)))
    dx, dy = math.cos(ang), math.sin(ang)
    span = abs(dx) + abs(dy)
    inv_span = 1.0 / (span if span > 1e-6 else 1.0)

    def interp_color(t):
        t = max(0.0, min(1.0, t))
        if t <= parsed[0][0]:
            return parsed[0][1]
        for idx in range(len(parsed) - 1):
            p0, c0 = parsed[idx]
            p1, c1 = parsed[idx + 1]
            if t <= p1:
                u = (t - p0) / max(1e-6, (p1 - p0))
                return tuple(int(round(c0[k] + (c1[k] - c0[k]) * u)) for k in range(4))
        return parsed[-1][1]

    small = Image.new('RGBA', (gw, gh))
    px = small.load()
    for yy in range(gh):
        ny = (yy / max(1, gh - 1)) - 0.5
        for xx in range(gw):
            nx = (xx / max(1, gw - 1)) - 0.5
            t = (nx * dx + ny * dy) * inv_span + 0.5
            px[xx, yy] = interp_color(t)
    if gw != w or gh != h:
        return small.resize((w, h), Image.BILINEAR)
    return small


def _geom_polygon_pts(geom, w, h, adj=10000):
    adj_f = 10000.0 if adj is None else float(adj)
    if geom == 'diamond':
        return [(w * 0.5, 0), (w, h * 0.5), (w * 0.5, h), (0, h * 0.5)]
    if geom == 'triangle':
        return [(w * 0.5, 0), (w, h), (0, h)]
    if geom == 'hexagon':
        return [(w * 0.22, 0), (w * 0.78, 0), (w, h * 0.5), (w * 0.78, h), (w * 0.22, h), (0, h * 0.5)]
    if geom == 'parallelogram':
        off = min(w * 0.45, (adj_f / 100000.0) * w)
        return [(off, 0), (w, 0), (w - off, h), (0, h)]
    if geom == 'chevron':
        tip = min(w * 0.22, max(6.0, h * 0.48))
        return [(0, 0), (w - tip, 0), (w, h * 0.5), (w - tip, h), (0, h), (tip, h * 0.5)]
    if geom in ('pentagon', 'homePlate'):
        tip = min(w * 0.22, max(6.0, h * 0.48))
        return [(0, 0), (w - tip, 0), (w, h * 0.5), (w - tip, h), (0, h)]
    if geom == 'plaque':
        c = min(w, h) * min(0.35, max(0.12, adj_f / 100000.0))
        return [(c, 0), (w - c, 0), (w, c), (w, h - c), (w - c, h), (c, h), (0, h - c), (0, c)]
    return None


def _draw_arrowhead(draw, p_from, p_to, color, size=8.0):
    dx = p_to[0] - p_from[0]
    dy = p_to[1] - p_from[1]
    dist = math.hypot(dx, dy)
    if dist < 1e-4:
        return
    ux, uy = dx / dist, dy / dist
    px, py = -uy, ux
    bx = p_to[0] - ux * size * 1.35
    by = p_to[1] - uy * size * 1.35
    pts = [
        p_to,
        (bx + px * size * 0.65, by + py * size * 0.65),
        (bx - px * size * 0.65, by - py * size * 0.65),
    ]
    draw.polygon(pts, fill=color)


def _draw_dashed_line(draw, p0, p1, color, width, dash_len=8.0, gap_len=5.0):
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    dist = math.hypot(dx, dy)
    if dist < 1e-3:
        return
    ux, uy = dx / dist, dy / dist
    pos = 0.0
    while pos < dist:
        end = min(dist, pos + dash_len)
        draw.line(
            [(p0[0] + ux * pos, p0[1] + uy * pos), (p0[0] + ux * end, p0[1] + uy * end)],
            fill=color, width=max(1, int(round(width)))
        )
        pos += dash_len + gap_len


def _measure_run(draw, txt, font):
    if not txt:
        return 0.0
    try:
        bbox = draw.textbbox((0, 0), txt, font=font)
        return float(bbox[2] - bbox[0])
    except Exception:
        return float(len(txt) * 10)


def _layout_paragraphs(draw, paragraphs, max_w, wrap, scale, default_font='微软雅黑'):
    lines = []
    for p_idx, p in enumerate(paragraphs):
        align = p.get('align', 'left')
        sp_bef = float(p.get('spaceBefore', 0.0)) * scale * 1.25
        sp_aft = float(p.get('spaceAfter', 3.0)) * scale * 1.25
        runs = p.get('runs') or []
        if not runs and p.get('text'):
            runs = [{'text': p['text'], 'fontSize': 10.5, 'bold': False, 'color': '#333333'}]

        # 把每个 run 按显式 '\n' 与自动换行拆成片段列表 [(txt, font, color_rgba, line_h)]
        cur_segs = []
        cur_w = 0.0
        cur_max_h = 0.0
        first_line_of_para = True

        def flush_line(is_last=False):
            nonlocal cur_segs, cur_w, cur_max_h, first_line_of_para
            if not cur_segs:
                return
            lh = cur_max_h if cur_max_h > 0 else 14.0 * scale
            lines.append({
                'segs': cur_segs,
                'width': cur_w,
                'height': lh,
                'align': align,
                'sp_before': sp_bef if first_line_of_para else 0.0,
                'sp_after': sp_aft if is_last else 2.0 * scale,
            })
            cur_segs = []
            cur_w = 0.0
            cur_max_h = 0.0
            first_line_of_para = False

        for r in runs:
            pt = float(r.get('fontSize') or 10.5)
            # Pt 转 96DPI 像素（1pt = 96/72 = 1.333px）
            font_px = pt * (96.0 / 72.0) * scale
            font = _get_font(font_px, bool(r.get('bold')))
            col = _hex_rgba(r.get('color') or '#333333', r.get('alpha', 1.0))
            line_h = font_px * 1.22
            raw_txt = str(r.get('text', ''))

            sub_parts = raw_txt.split('\n')
            for s_i, part in enumerate(sub_parts):
                if s_i > 0:
                    flush_line(is_last=False)
                if not part:
                    continue
                if not wrap or max_w <= 12:
                    pw = _measure_run(draw, part, font)
                    cur_segs.append((part, font, col))
                    cur_w += pw
                    cur_max_h = max(cur_max_h, line_h)
                else:
                    # 按英文数字单词或单个中文字符分词，防止 "81.2%"、"PRTS" 等词中间被劈开
                    tokens = re.findall(r'[A-Za-z0-9_.,:%+/-]+|\s+|.', part)
                    buf = ''
                    for tok in tokens:
                        cw = _measure_run(draw, buf + tok, font)
                        if cur_w + cw > max_w and (buf or cur_segs):
                            if buf:
                                cur_segs.append((buf, font, col))
                                cur_w += _measure_run(draw, buf, font)
                                cur_max_h = max(cur_max_h, line_h)
                            flush_line(is_last=False)
                            if _measure_run(draw, tok, font) > max_w:
                                for ch in tok:
                                    cw2 = _measure_run(draw, buf + ch, font)
                                    if cur_w + cw2 > max_w and (buf or cur_segs):
                                        if buf:
                                            cur_segs.append((buf, font, col))
                                            cur_w += _measure_run(draw, buf, font)
                                            cur_max_h = max(cur_max_h, line_h)
                                        flush_line(is_last=False)
                                        buf = ch
                                    else:
                                        buf += ch
                            else:
                                buf = tok.lstrip() if not tok.strip() else tok
                        else:
                            buf += tok
                    if buf:
                        cur_segs.append((buf, font, col))
                        cur_w += _measure_run(draw, buf, font)
                        cur_max_h = max(cur_max_h, line_h)
        flush_line(is_last=True)
    return lines


def _draw_text_body(canvas, box, tx_data, scale, default_font='微软雅黑'):
    if not tx_data or not tx_data.get('paragraphs'):
        return
    x, y, w, h = box
    if w <= 2 or h <= 2:
        return
    draw = ImageDraw.Draw(canvas)
    pad = tx_data.get('padding') or {}
    pl = float(pad.get('left', 7.2)) * scale
    pt = float(pad.get('top', 3.6)) * scale
    pr = float(pad.get('right', 7.2)) * scale
    pb = float(pad.get('bottom', 3.6)) * scale

    inner_x = x + pl
    inner_y = y + pt
    inner_w = max(8.0, w - pl - pr)
    inner_h = max(8.0, h - pt - pb)

    lines = _layout_paragraphs(draw, tx_data['paragraphs'], inner_w, tx_data.get('wrap', True), scale, default_font)
    if not lines:
        return

    total_h = sum(ln['sp_before'] + ln['height'] + (ln['sp_after'] if i < len(lines) - 1 else 0.0) for i, ln in enumerate(lines))
    valign = tx_data.get('valign', 'top')
    if valign == 'middle':
        cy = inner_y + (inner_h - total_h) * 0.5
    elif valign == 'bottom':
        cy = inner_y + (inner_h - total_h)
    else:
        cy = inner_y

    has_semi_alpha = any(col[3] < 252 for ln in lines for _, _, col in ln['segs'])
    target_img = Image.new('RGBA', canvas.size, (0, 0, 0, 0)) if has_semi_alpha else canvas
    t_draw = ImageDraw.Draw(target_img, 'RGBA') if has_semi_alpha else draw

    for i, ln in enumerate(lines):
        cy += ln['sp_before']
        if cy > y + h - 2:
            break
        align = ln['align']
        if align == 'center':
            cx = inner_x + (inner_w - ln['width']) * 0.5
        elif align == 'right':
            cx = inner_x + (inner_w - ln['width'])
        else:
            cx = inner_x
        for txt, font, col in ln['segs']:
            if col[3] > 0:
                if has_semi_alpha:
                    t_draw.text((cx, cy), txt, font=font, fill=col)
                else:
                    t_draw.text((cx, cy), txt, font=font, fill=col[:3])
            cx += _measure_run(t_draw, txt, font)
        cy += ln['height'] + (ln['sp_after'] if i < len(lines) - 1 else 0.0)

    if has_semi_alpha:
        canvas.alpha_composite(target_img)


def _draw_shape_or_decor(canvas, ch, scale, default_font='微软雅黑'):
    rtype = ch.get('rawType', 'shape')
    x = float(ch.get('x', 0.0)) * scale
    y = float(ch.get('y', 0.0)) * scale
    w = max(0.0, float(ch.get('w', 0.0)) * scale)
    h = max(0.0, float(ch.get('h', 0.0)) * scale)

    if rtype == 'image':
        img_path = _resolve_asset_path(ch.get('src'))
        if not img_path or w < 1 or h < 1:
            return
        try:
            im = Image.open(img_path).convert('RGBA')
            im = im.resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
            op = ch.get('opacity')
            if op is not None and float(op) < 0.999:
                r, g, b, a = im.split()
                a = a.point(lambda v: int(round(v * float(op))))
                im = Image.merge('RGBA', (r, g, b, a))
            rot = float(ch.get('rotation') or 0.0)
            if abs(rot) > 0.1:
                im = im.rotate(-rot, expand=True, resample=Image.BICUBIC)
                px = int(round(x + w * 0.5 - im.width * 0.5))
                py = int(round(y + h * 0.5 - im.height * 0.5))
                canvas.alpha_composite(im, (px, py))
            else:
                canvas.alpha_composite(im, (int(round(x)), int(round(y))))
        except Exception:
            pass
        return

    if rtype == 'table':
        rows_data = ch.get('rows') or []
        if not rows_data:
            return
        r_cnt = len(rows_data)
        c_cnt = len(rows_data[0])
        cws = [float(v) * scale for v in (ch.get('colWidths') or [])]
        if len(cws) != c_cnt or sum(cws) <= 0:
            cws = [w / max(1, c_cnt)] * c_cnt
        rhs = [float(v) * scale for v in (ch.get('rowHeights') or [])]
        if len(rhs) != r_cnt or sum(rhs) <= 0:
            rhs = [h / max(1, r_cnt)] * r_cnt
        tot_rh = sum(rhs)
        if tot_rh > 0 and abs(tot_rh - h) > 2:
            rhs = [r * (h / tot_rh) for r in rhs]

        draw = ImageDraw.Draw(canvas)
        ry = y
        for r_i, row in enumerate(rows_data):
            rh = rhs[r_i]
            cx = x
            for c_i, cell in enumerate(row):
                cw = cws[c_i]
                fill_c = cell.get('fill')
                if fill_c:
                    draw.rectangle([cx, ry, cx + cw, ry + rh], fill=_hex_rgba(fill_c, 1.0))
                draw.rectangle([cx, ry, cx + cw, ry + rh], outline=(203, 213, 225, 220), width=max(1, int(round(scale))))
                tb = cell.get('textBody')
                if tb and tb.get('paragraphs'):
                    _draw_text_body(canvas, (cx, ry, cw, rh), tb, scale, default_font)
                else:
                    tx = {
                        'valign': cell.get('valign', 'middle'),
                        'wrap': True,
                        'padding': cell.get('padding') or {'left': 7.2, 'top': 3.6, 'right': 7.2, 'bottom': 3.6},
                        'paragraphs': [{
                            'align': cell.get('align', 'left'),
                            'spaceBefore': 0.0,
                            'spaceAfter': 0.0,
                            'runs': [{
                                'text': str(cell.get('text', '')),
                                'fontSize': float(cell.get('fontSize') or 10.0),
                                'bold': bool(cell.get('bold', False)),
                                'color': cell.get('color') or '#333333',
                                'fontFamily': cell.get('fontFamily') or default_font
                            }]
                        }]
                    }
                    _draw_text_body(canvas, (cx, ry, cw, rh), tx, scale, default_font)
                cx += cw
            ry += rh
        return

    geom = ch.get('geom', 'rect')
    if geom in ('line', 'straightConnector1', 'elbowConnector', 'bentConnector2', 'bentConnector3', 'bentConnector4', 'bentConnector5'):
        x1, y1 = x, y
        x2, y2 = x + w, y + h
        if ch.get('flipH'):
            x1, x2 = x2, x1
        if ch.get('flipV'):
            y1, y2 = y2, y1
        b_col = _hex_rgba(ch.get('borderColor') or '#334155', ch.get('borderAlpha', 1.0))
        bw = max(1.0, float(ch.get('borderWidth') or 1.2) * scale)
        draw = ImageDraw.Draw(canvas)
        is_dash = bool(ch.get('dashStyle') and ch.get('dashStyle') != 'solid')

        if geom in ('elbowConnector', 'bentConnector2', 'bentConnector3', 'bentConnector4', 'bentConnector5'):
            mx = (x1 + x2) * 0.5
            pts = [(x1, y1), (mx, y1), (mx, y2), (x2, y2)]
            for i in range(len(pts) - 1):
                if is_dash:
                    _draw_dashed_line(draw, pts[i], pts[i + 1], b_col, bw)
                else:
                    draw.line([pts[i], pts[i + 1]], fill=b_col, width=max(1, int(round(bw))))
            p_prev, p_last = pts[-2], pts[-1]
        else:
            if is_dash:
                _draw_dashed_line(draw, (x1, y1), (x2, y2), b_col, bw)
            else:
                draw.line([(x1, y1), (x2, y2)], fill=b_col, width=max(1, int(round(bw))))
            p_prev, p_last = (x1, y1), (x2, y2)

        if ch.get('tailEnd') and ch.get('tailEnd') != 'none':
            _draw_arrowhead(draw, p_prev, p_last, b_col, size=6.0 * scale)
        if ch.get('headEnd') and ch.get('headEnd') != 'none':
            _draw_arrowhead(draw, p_last, p_prev, b_col, size=6.0 * scale)
        return

    # 常规形状（含阴影、线性渐变、圆角、多边形与旋转）
    if w < 0.5 or h < 0.5:
        return
    pad = int(math.ceil(16 * scale))
    lw = max(1, int(round(w)) + pad * 2)
    lh = max(1, int(round(h)) + pad * 2)
    lx0, ly0, lx1, ly1 = pad, pad, pad + w, pad + h

    if ch.get('shadow'):
        sh_layer = Image.new('RGBA', (lw, lh), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh_layer)
        sd.rectangle([lx0 + 2 * scale, ly0 + 3 * scale, lx1 + 2 * scale, ly1 + 3 * scale], fill=(0, 0, 0, 34))
        sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(radius=3.8 * scale))
        canvas.alpha_composite(sh_layer, (int(round(x - pad)), int(round(y - pad))))

    shape_layer = Image.new('RGBA', (lw, lh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shape_layer)
    adj_val = 10000.0 if ch.get('adj') is None else float(ch['adj'])
    poly_pts = _geom_polygon_pts(geom, w, h, adj_val)
    fill_hex = ch.get('fill')
    fill_alpha = 1.0 if ch.get('fillAlpha') is None else float(ch['fillAlpha'])
    grad = ch.get('gradFill')
    b_hex = ch.get('borderColor')
    bw = float(ch.get('borderWidth') or 0.0) * scale
    b_alpha = 1.0 if ch.get('borderAlpha') is None else float(ch['borderAlpha'])

    if grad and grad.get('stops'):
        g_img = _make_gradient_image(w, h, grad)
        mask = Image.new('L', (max(1, int(round(w))), max(1, int(round(h)))), 0)
        md = ImageDraw.Draw(mask)
        if geom in ('oval', 'ellipse'):
            md.ellipse([0, 0, w, h], fill=255)
        elif poly_pts:
            md.polygon(poly_pts, fill=255)
        else:
            md.rectangle([0, 0, w, h], fill=255)
        shape_layer.paste(g_img, (pad, pad), mask)
    elif fill_hex:
        f_col = _hex_rgba(fill_hex, fill_alpha)
        if geom in ('oval', 'ellipse'):
            draw.ellipse([lx0, ly0, lx1, ly1], fill=f_col)
        elif geom == 'roundRect':
            rad = min(w, h) * min(0.5, adj_val / 100000.0)
            draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=rad, fill=f_col)
        elif poly_pts:
            draw.polygon([(px + pad, py + pad) for px, py in poly_pts], fill=f_col)
        else:
            draw.rectangle([lx0, ly0, lx1, ly1], fill=f_col)

    if b_hex and bw > 0:
        b_col = _hex_rgba(b_hex, b_alpha)
        is_dash = bool(ch.get('dashStyle') and ch.get('dashStyle') != 'solid')
        b_int = max(1, int(round(bw)))
        if geom in ('oval', 'ellipse'):
            draw.ellipse([lx0, ly0, lx1, ly1], outline=b_col, width=b_int)
        elif geom == 'roundRect':
            rad = min(w, h) * min(0.5, adj_val / 100000.0)
            draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=rad, outline=b_col, width=b_int)
        elif poly_pts:
            shifted = [(px + pad, py + pad) for px, py in poly_pts]
            for i in range(len(shifted)):
                p_a, p_b = shifted[i], shifted[(i + 1) % len(shifted)]
                if is_dash:
                    _draw_dashed_line(draw, p_a, p_b, b_col, bw)
                else:
                    draw.line([p_a, p_b], fill=b_col, width=b_int)
        else:
            corners = [(lx0, ly0), (lx1, ly0), (lx1, ly1), (lx0, ly1)]
            for i in range(4):
                p_a, p_b = corners[i], corners[(i + 1) % 4]
                if is_dash:
                    _draw_dashed_line(draw, p_a, p_b, b_col, bw)
                else:
                    draw.line([p_a, p_b], fill=b_col, width=b_int)

    rot = float(ch.get('rotation') or 0.0)
    if abs(rot) > 0.1:
        shape_layer = shape_layer.rotate(-rot, expand=True, resample=Image.BICUBIC)
        px = int(round(x + w * 0.5 - shape_layer.width * 0.5))
        py = int(round(y + h * 0.5 - shape_layer.height * 0.5))
        canvas.alpha_composite(shape_layer, (px, py))
    else:
        canvas.alpha_composite(shape_layer, (int(round(x - pad)), int(round(y - pad))))

    if ch.get('textBody'):
        _draw_text_body(canvas, (x, y, w, h), ch['textBody'], scale, default_font)


def render_slide_to_image(deck, slide_index=0, scale=1.5):
    """将 Deck 中指定索引页（0-based）高保真渲染为 PIL RGB Image。"""
    slides = deck.get('slides') or []
    if not (0 <= slide_index < len(slides)):
        raise IndexError(f"Slide index {slide_index} out of range (0..{len(slides)-1})")
    canvas_info = deck.get('canvas') or {}
    cw = float(canvas_info.get('width', 1280.0))
    ch = float(canvas_info.get('height', 720.0))
    out_w = max(1, int(round(cw * scale)))
    out_h = max(1, int(round(ch * scale)))

    slide = slides[slide_index]
    bg = slide.get('background') or {}
    default_font = (deck.get('theme') or {}).get('fontFamily', '微软雅黑')

    if bg.get('type') == 'gradient' and bg.get('stops'):
        base_img = _make_gradient_image(out_w, out_h, bg)
    elif bg.get('type') == 'image' and bg.get('image'):
        ip = _resolve_asset_path(bg['image'])
        if ip:
            base_img = Image.open(ip).convert('RGBA').resize((out_w, out_h), Image.LANCZOS)
        else:
            base_img = Image.new('RGBA', (out_w, out_h), _hex_rgba(bg.get('color') or '#FFFFFF', 1.0))
    else:
        base_img = Image.new('RGBA', (out_w, out_h), _hex_rgba(bg.get('color') or '#FFFFFF', 1.0))

    for dec in (slide.get('decorations') or []):
        _draw_shape_or_decor(base_img, dec, scale, default_font)

    from core.exporter import sync_component_children_coords
    for comp in (slide.get('components') or []):
        children = sync_component_children_coords(comp)
        for child in children:
            _draw_shape_or_decor(base_img, child, scale, default_font)

    return base_img.convert('RGB')


def render_deck_previews(deck, slide_indices, out_dir, prefix='preview', scale=1.4):
    """批量渲染指定 1-based 页码列表并保存 PNG，返回生成路径字典。"""
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    slides = deck.get('slides') or []
    for s_idx_1b in slide_indices:
        idx0 = int(s_idx_1b) - 1
        if not (0 <= idx0 < len(slides)):
            continue
        im = render_slide_to_image(deck, idx0, scale=scale)
        out_p = os.path.join(out_dir, f"{prefix}_s{int(s_idx_1b):02d}.png")
        im.save(out_p, format='PNG', optimize=True)
        paths[int(s_idx_1b)] = out_p
    return paths
