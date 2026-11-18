import argparse
import colorsys
import io
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}
COMMERCIAL_FONT_PREFIXES = ('字魂', '汉仪', '方正', '造字工房', '文鼎', '叶根友', '锐字', 'Aa', 'HY', 'FZ')
SAFE_FONTS = ('微软雅黑', 'Microsoft YaHei', '思源黑体', '思源宋体', '宋体', '黑体', 'SimHei', 'SimSun', 'PingFang SC', 'Arial')


def _emu_to_px(emu):
    return round(float(emu) / 914400.0 * 96.0, 2)


def _hex_to_rgb(hx):
    h = str(hx or '').lstrip('#').strip()
    if not re.fullmatch(r'[0-9A-Fa-f]{6}', h):
        return (0, 0, 0)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return '#{:02X}{:02X}{:02X}'.format(*[max(0, min(255, int(round(v)))) for v in rgb])


def _luminance(hx):
    r, g, b = [c / 255.0 for c in _hex_to_rgb(hx)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _saturation(hx):
    r, g, b = [c / 255.0 for c in _hex_to_rgb(hx)]
    _, _, s = colorsys.rgb_to_hls(r, g, b)
    return s


def _blend(hx1, hx2, ratio):
    c1 = _hex_to_rgb(hx1)
    c2 = _hex_to_rgb(hx2)
    return _rgb_to_hex([c1[i] * (1.0 - ratio) + c2[i] * ratio for i in range(3)])


def _is_safe_system_font(font_name):
    if not font_name:
        return True
    if any(font_name.startswith(p) or p in font_name for p in COMMERCIAL_FONT_PREFIXES):
        return False
    return True


def _pick_safe_font(font_counter, major_font):
    raw_ranked = [f for f, _ in font_counter.most_common()]
    commercial_hits = [f for f in raw_ranked if not _is_safe_system_font(f)]
    for f in raw_ranked:
        if any(s.lower() in f.lower() for s in ('微软雅黑', 'yahei', '黑体', 'simhei', 'pingfang', '思源黑体 CN')):
            # "思源黑体 CN Light" 等带子重量的字体名在 PowerPoint fallback 下统一规整
            if '微软雅黑' in f or 'YaHei' in f:
                return '微软雅黑', commercial_hits
            if _is_safe_system_font(f):
                return f, commercial_hits
    for f in raw_ranked:
        if _is_safe_system_font(f):
            return f, commercial_hits
    if _is_safe_system_font(major_font):
        return major_font, commercial_hits
    return '微软雅黑', commercial_hits


def _build_harmonized_semantic_tokens(primary_hex, accent_hex, bg_hex):
    """依据提取到的主色、点缀色与背景暖度自动调和生成五态低饱和同源功能色令牌。"""
    r, g, b = _hex_to_rgb(bg_hex)
    is_warm = (r >= b + 3) or _hex_to_rgb(accent_hex)[1] > _hex_to_rgb(accent_hex)[2] + 15
    paper_base = _blend('#FAF9F2' if is_warm else '#F8FAFC', '#FFFFFF', 0.40)
    dark_ink = '#1A1A1A' if is_warm else '#0F172A'
    body_ink = '#2E2D2A' if is_warm else '#334155'

    acc_lum = _luminance(accent_hex)
    # 若主题强调色本身偏清新绿色系，pass 直接与主题强调色同源深化
    acc_r, acc_g, acc_b = _hex_to_rgb(accent_hex)
    is_green_accent = (acc_g >= acc_r + 12 and acc_g >= acc_b + 20)
    pass_border = _blend(accent_hex, '#2A4208', 0.42) if is_green_accent else ('#556B12' if is_warm else '#2E6F54')
    pass_badge_bg = accent_hex if (is_green_accent or acc_lum > 0.45) else pass_border
    pass_badge_fg = dark_ink if _luminance(pass_badge_bg) > 0.50 else '#FFFFFF'
    pass_title = _blend(pass_border, dark_ink, 0.35)

    warn_col = '#B58428' if is_warm else '#B06D19'
    rej_col = '#A64654' if is_green_accent else ('#A63429' if is_warm else '#9E343B')

    pri_title = primary_hex if _luminance(primary_hex) < 0.35 else _blend(primary_hex, dark_ink, 0.55)
    pri_fg = dark_ink if _luminance(primary_hex) > 0.55 else '#FFFFFF'

    return {
        'pass': {
            'bg': _blend(paper_base, pass_border, 0.06),
            'border': pass_border,
            'stripe': pass_badge_bg,
            'badgeBg': pass_badge_bg,
            'badgeFg': pass_badge_fg,
            'title': pass_title,
            'body': body_ink
        },
        'warn': {
            'bg': _blend(paper_base, warn_col, 0.06),
            'border': warn_col,
            'stripe': warn_col,
            'badgeBg': warn_col,
            'badgeFg': '#FFFFFF',
            'title': _blend(warn_col, dark_ink, 0.32),
            'body': body_ink
        },
        'reject': {
            'bg': _blend(paper_base, rej_col, 0.055),
            'border': rej_col,
            'stripe': rej_col,
            'badgeBg': rej_col,
            'badgeFg': '#FFFFFF',
            'title': _blend(rej_col, dark_ink, 0.25),
            'body': body_ink
        },
        'info': {
            'bg': '#FFFFFF',
            'border': _blend(primary_hex, '#D2D4C8', 0.65),
            'stripe': primary_hex,
            'badgeBg': primary_hex,
            'badgeFg': pri_fg,
            'title': pri_title,
            'body': body_ink
        },
        'neutral': {
            'bg': _blend(paper_base, '#94A3B8', 0.08),
            'border': '#8E9289' if is_warm else '#94A3B8',
            'stripe': '#5E616B',
            'badgeBg': '#5E616B',
            'badgeFg': '#FFFFFF',
            'title': '#3E3C38' if is_warm else '#334155',
            'body': '#52504C' if is_warm else '#475569'
        }
    }


def _resolve_color_el(clr_container, theme_colors):
    if clr_container is None:
        return None
    sf = clr_container.find('./a:srgbClr', NS)
    if sf is not None:
        val = sf.attrib.get('val', '')
        if re.fullmatch(r'[0-9A-Fa-f]{6}', val):
            return '#' + val.upper()
    sy = clr_container.find('./a:sysClr', NS)
    if sy is not None:
        last_clr = sy.attrib.get('lastClr', '')
        if re.fullmatch(r'[0-9A-Fa-f]{6}', last_clr):
            return '#' + last_clr.upper()
        if sy.attrib.get('val') == 'windowText':
            return '#000000'
        if sy.attrib.get('val') == 'window':
            return '#FFFFFF'
    pr = clr_container.find('./a:prstClr', NS)
    if pr is not None:
        prst = pr.attrib.get('val', '').lower()
        if prst == 'black':
            return '#000000'
        if prst == 'white':
            return '#FFFFFF'
    sc = clr_container.find('./a:schemeClr', NS)
    if sc is not None:
        key = sc.attrib.get('val', '')
        alias = {'tx1': 'dk1', 'bg1': 'lt1', 'tx2': 'dk2', 'bg2': 'lt2'}
        raw = theme_colors.get(alias.get(key, key))
        if raw and re.fullmatch(r'#[0-9A-Fa-f]{6}', raw):
            return raw
        if key in ('dk1', 'tx1'):
            return '#000000'
        if key in ('lt1', 'bg1'):
            return '#FFFFFF'
    return None


def _parse_rels_map(z, rels_path):
    mapping = {}
    if rels_path not in z.namelist():
        return mapping
    root = ET.fromstring(z.read(rels_path))
    for rel in root:
        rid = rel.attrib.get('Id')
        target = rel.attrib.get('Target', '')
        if rid and target:
            norm = os.path.normpath(os.path.join('ppt/slides', target)).replace('\\', '/')
            mapping[rid] = norm
    return mapping


def _parse_grad_fill_el(gf_el, theme_colors, fallback_hex='#FFFFFF'):
    stops = []
    for gs in gf_el.findall('./a:gsLst/a:gs', NS):
        pos = round(int(gs.attrib.get('pos', 0)) / 100000.0, 3)
        col = _resolve_color_el(gs, theme_colors) or fallback_hex
        al_el = gs.find('.//a:alpha', NS)
        al = round(int(al_el.attrib['val']) / 100000.0, 3) if al_el is not None else 1.0
        stops.append({'pos': pos, 'color': col, 'alpha': al})
    lin = gf_el.find('./a:lin', NS)
    ang = round(int(lin.attrib.get('ang', 0)) / 60000.0, 1) if lin is not None else 25.0
    if not stops:
        return None
    return {'type': 'gradient', 'color': stops[0]['color'], 'angle': ang, 'stops': stops, 'image': None}


def _extract_bg_or_pseudo_bg(sroot, rels_map, theme_colors, cw, ch, default_bg_hex='#FFFFFF'):
    """优先提取 <p:bg>；若为空，则智能检测覆盖画布 >=92% 的底层全幅 <p:pic>/<p:sp> 伪背景。"""
    bg_pr = sroot.find('.//p:bg/p:bgPr', NS)
    if bg_pr is not None:
        gf = bg_pr.find('./a:gradFill', NS)
        if gf is not None:
            g = _parse_grad_fill_el(gf, theme_colors, default_bg_hex)
            if g:
                return g, None
        bf = bg_pr.find('./a:blipFill/a:blip', NS)
        if bf is not None:
            rid = bf.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            return {'type': 'image', 'color': default_bg_hex, 'image': None}, rels_map.get(rid)
        col = _resolve_color_el(bg_pr.find('./a:solidFill', NS), theme_colors)
        if col:
            return {'type': 'color', 'color': col, 'image': None}, None

    sp_tree = sroot.find('.//p:cSld/p:spTree', NS)
    if sp_tree is not None:
        for child in list(sp_tree)[:4]:
            tag = child.tag.split('}')[-1]
            if tag not in ('pic', 'sp'):
                continue
            xfrm = child.find('./p:spPr/a:xfrm', NS)
            if xfrm is None:
                continue
            off, ext = xfrm.find('./a:off', NS), xfrm.find('./a:ext', NS)
            if off is None or ext is None:
                continue
            x = _emu_to_px(off.attrib.get('x', 0))
            y = _emu_to_px(off.attrib.get('y', 0))
            w = _emu_to_px(ext.attrib.get('cx', 0))
            h = _emu_to_px(ext.attrib.get('cy', 0))
            if abs(x) <= 24.0 and abs(y) <= 24.0 and w >= cw * 0.92 and h >= ch * 0.92:
                if tag == 'pic':
                    blip = child.find('.//a:blip', NS)
                    if blip is not None:
                        rid = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                        mref = rels_map.get(rid)
                        if mref:
                            return {'type': 'image', 'color': default_bg_hex, 'image': None}, mref
                else:
                    spPr = child.find('./p:spPr', NS)
                    if spPr is not None:
                        gf = spPr.find('./a:gradFill', NS)
                        if gf is not None:
                            g = _parse_grad_fill_el(gf, theme_colors, default_bg_hex)
                            if g:
                                return g, None
                        col = _resolve_color_el(spPr.find('./a:solidFill', NS), theme_colors)
                        if col:
                            return {'type': 'color', 'color': col, 'image': None}, None

    return {'type': 'color', 'color': default_bg_hex, 'image': None}, None


def _save_optimized_asset(raw_bytes, out_path, max_dim=1920, is_full_bg=False):
    """提取图像并在超分辨率时执行 LANCZOS 压缩瘦身，防止数 MB 原图膨胀模板包。"""
    ext = os.path.splitext(out_path)[1].lower()
    im = Image.open(io.BytesIO(raw_bytes))
    orig_size = im.size
    resized = False
    if max(im.size) > max_dim:
        scale = max_dim / float(max(im.size))
        new_sz = (max(1, int(round(im.size[0] * scale))), max(1, int(round(im.size[1] * scale))))
        im = im.resize(new_sz, Image.LANCZOS)
        resized = True

    if is_full_bg and ext in ('.jpg', '.jpeg') and im.mode != 'RGB':
        im = im.convert('RGB')

    if resized or (is_full_bg and len(raw_bytes) > 350 * 1024 and ext in ('.jpg', '.jpeg')):
        if ext in ('.jpg', '.jpeg'):
            im.convert('RGB').save(out_path, format='JPEG', quality=88, optimize=True)
        else:
            im.save(out_path, optimize=True)
    else:
        with open(out_path, 'wb') as out_f:
            out_f.write(raw_bytes)
    return orig_size, im.size, os.path.getsize(out_path)


def convert_pptx_to_template_bundle(
    pptx_path,
    template_id,
    name=None,
    tier='local',
    out_dir=None,
    commercial=False
):
    if not os.path.isfile(pptx_path):
        raise FileNotFoundError(f"输入 PPTX 文件不存在: {pptx_path}")

    tid = re.sub(r'[^a-zA-Z0-9_-]+', '_', str(template_id).strip()).strip('_').lower()
    if not tid:
        raise ValueError("template_id 不能为空")

    base_tier = 'builtin' if commercial else tier
    root_dest = os.path.abspath(out_dir) if out_dir else os.path.join(BASE_DIR, 'templates', base_tier)
    bundle_dir = os.path.join(root_dest, tid)
    assets_dir = os.path.join(bundle_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)

    with zipfile.ZipFile(pptx_path, 'r') as z:
        names = set(z.namelist())
        embedded_font_files = [n for n in names if n.startswith('ppt/fonts/')]

        # 1. 画布尺寸
        emu_cx, emu_cy = 12192000, 6858000
        if 'ppt/presentation.xml' in names:
            proot = ET.fromstring(z.read('ppt/presentation.xml'))
            sld_sz = proot.find('.//p:sldSz', NS)
            if sld_sz is not None:
                emu_cx = int(sld_sz.attrib.get('cx', emu_cx))
                emu_cy = int(sld_sz.attrib.get('cy', emu_cy))
        cw, ch = _emu_to_px(emu_cx), _emu_to_px(emu_cy)

        # 2. 主题配色与字体
        theme_colors = {'dk1': '#000000', 'lt1': '#FFFFFF'}
        major_font = '微软雅黑'
        if 'ppt/theme/theme1.xml' in names:
            troot = ET.fromstring(z.read('ppt/theme/theme1.xml'))
            clr = troot.find('.//a:clrScheme', NS)
            if clr is not None:
                for ch_el in clr:
                    tag = ch_el.tag.split('}')[-1]
                    if len(ch_el):
                        last_v = ch_el[0].attrib.get('lastClr', '')
                        val_v = ch_el[0].attrib.get('val', '')
                        if re.fullmatch(r'[0-9A-Fa-f]{6}', last_v):
                            theme_colors[tag] = '#' + last_v.upper()
                        elif re.fullmatch(r'[0-9A-Fa-f]{6}', val_v):
                            theme_colors[tag] = '#' + val_v.upper()
                        elif val_v == 'windowText':
                            theme_colors[tag] = '#000000'
                        elif val_v == 'window':
                            theme_colors[tag] = '#FFFFFF'
            ea_f = troot.find('.//a:fontScheme/a:minorFont/a:ea', NS)
            if ea_f is not None and ea_f.attrib.get('typeface'):
                major_font = ea_f.attrib['typeface']

        # 3. 遍历幻灯片统计全通道颜色（solidFill + gradFill + schemeClr）、几何形状与字体
        slide_files = sorted(
            [n for n in names if re.match(r'^ppt/slides/slide\d+\.xml$', n)],
            key=lambda s: int(re.findall(r'\d+', s)[0])
        )

        fill_counter = Counter()
        grad_pair_counter = Counter()
        text_color_counter = Counter()
        geom_counter = Counter()
        font_counter = Counter()
        media_slides = {}
        body_y_tops = []
        footer_ys = []

        cover_bg = {'type': 'color', 'color': '#FFFFFF', 'image': None}
        body_bg = {'type': 'color', 'color': '#FFFFFF', 'image': None}
        cover_bg_media = None
        body_bg_media = None

        for s_idx, sname in enumerate(slide_files[:35]):
            sroot = ET.fromstring(z.read(sname))
            snum = re.findall(r'\d+', os.path.basename(sname))[0]
            rels_map = _parse_rels_map(z, f"ppt/slides/_rels/slide{snum}.xml.rels")

            bg_obj, bg_media = _extract_bg_or_pseudo_bg(sroot, rels_map, theme_colors, cw, ch)
            if s_idx == 0:
                cover_bg, cover_bg_media = bg_obj, bg_media
            elif s_idx == 1 or (s_idx > 1 and body_bg.get('type') == 'color' and bg_obj.get('type') != 'color' and s_idx < len(slide_files) - 1):
                body_bg, body_bg_media = bg_obj, bg_media

            for sp in sroot.findall('.//p:sp', NS):
                spPr = sp.find('./p:spPr', NS)
                if spPr is not None:
                    xfrm = spPr.find('./a:xfrm', NS)
                    if xfrm is not None:
                        off = xfrm.find('./a:off', NS)
                        ext = xfrm.find('./a:ext', NS)
                        if off is not None and ext is not None:
                            sy = _emu_to_px(off.attrib.get('y', 0))
                            sh = _emu_to_px(ext.attrib.get('cy', 0))
                            if 110.0 <= sy <= 180.0 and sh > 25.0:
                                body_y_tops.append(sy)
                            elif (ch - 120.0) <= sy <= (ch - 30.0) and 24.0 <= sh <= 70.0:
                                footer_ys.append(sy)
                    prst = spPr.find('./a:prstGeom', NS)
                    if prst is not None:
                        geom_counter[prst.attrib.get('prst', 'rect')] += 1
                    col = _resolve_color_el(spPr.find('./a:solidFill', NS), theme_colors)
                    if col:
                        fill_counter[col] += 1
                    gf = spPr.find('./a:gradFill', NS)
                    if gf is not None:
                        g_cols = []
                        for gs in gf.findall('./a:gsLst/a:gs', NS):
                            gc = _resolve_color_el(gs, theme_colors)
                            if gc:
                                fill_counter[gc] += 1
                                g_cols.append(gc)
                        if len(g_cols) >= 2:
                            grad_pair_counter[(g_cols[0], g_cols[-1])] += 1

                for r in sp.findall('.//a:r', NS):
                    rPr = r.find('./a:rPr', NS)
                    if rPr is not None:
                        tcol = _resolve_color_el(rPr.find('./a:solidFill', NS), theme_colors)
                        if tcol:
                            text_color_counter[tcol] += 1
                        ea = rPr.find('./a:ea', NS)
                        if ea is not None and ea.attrib.get('typeface'):
                            font_counter[ea.attrib['typeface']] += 1

            for pic in sroot.findall('.//p:pic', NS):
                blip = pic.find('.//a:blip', NS)
                if blip is not None:
                    rid = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if rid and rid in rels_map:
                        media_slides.setdefault(rels_map[rid], set()).add(s_idx + 1)

        # 4. 提取、分拣与瘦身静态媒体资产
        extracted_assets = []
        skipped_media = []
        recommended_decors = []

        for mpath in sorted(names):
            if not mpath.startswith('ppt/media/'):
                continue
            ext = os.path.splitext(mpath)[1].lower()
            base_fn = os.path.basename(mpath)
            if ext not in IMAGE_EXTS:
                skipped_media.append({'file': base_fn, 'reason': f'非静态位图格式 ({ext or "unknown"})'})
                continue
            raw_bytes = z.read(mpath)
            if len(raw_bytes) < 512:
                skipped_media.append({'file': base_fn, 'reason': '过小噪点图片 (<512B)'})
                continue
            try:
                im = Image.open(io.BytesIO(raw_bytes)).convert('RGBA')
                iw, ih = im.size
                alpha_ch = im.getchannel('A')
                hist = alpha_ch.histogram()
                vis_px = sum(hist[20:])
                vis_ratio = round(vis_px / float(max(1, iw * ih)), 4)
                has_alpha = (vis_ratio < 0.995)
            except Exception as exc:
                skipped_media.append({'file': base_fn, 'reason': f'无法解码: {exc}'})
                continue

            slide_refs = sorted(media_slides.get(mpath, set()))
            is_bg = (mpath == cover_bg_media or mpath == body_bg_media)
            if mpath == cover_bg_media:
                out_name = f"bg_cover{ext if ext != '.jpeg' else '.jpg'}"
                cover_bg['image'] = f"assets/{out_name}"
                category = 'background-cover'
            elif mpath == body_bg_media:
                out_name = f"bg_body{ext if ext != '.jpeg' else '.jpg'}"
                body_bg['image'] = f"assets/{out_name}"
                category = 'background-body'
            elif has_alpha and len(slide_refs) >= 2 and vis_ratio < 0.25:
                out_name = f"decor_{base_fn}"
                category = 'recurring-decor'
                recommended_decors.append(f"assets/{out_name}")
            elif iw <= 512 and ih <= 512 and has_alpha:
                out_name = f"icon_{base_fn}"
                category = 'icon'
            elif has_alpha and (len(slide_refs) >= 2 or max(iw, ih) >= 512):
                out_name = f"decor_{base_fn}"
                category = 'decor'
            else:
                out_name = f"media_{base_fn}"
                category = 'content-photo'

            out_path = os.path.join(assets_dir, out_name)
            orig_sz, saved_sz, out_bytes = _save_optimized_asset(raw_bytes, out_path, max_dim=1920, is_full_bg=is_bg)
            extracted_assets.append({
                'source': base_fn,
                'savedAs': f"assets/{out_name}",
                'category': category,
                'origSize': list(orig_sz),
                'savedSize': list(saved_sz),
                'sizeKB': round(out_bytes / 1024.0, 1),
                'visibleRatio': vis_ratio,
                'hasAlpha': has_alpha,
                'slideRefs': len(slide_refs),
                'slides': slide_refs
            })

        # 5. 智能识别调色板（主色、高频渐变强调色、辅助衬底色与安全字体）
        ranked_fills = [c for c, _ in fill_counter.most_common(35)]
        dark_fills = [c for c in ranked_fills if _luminance(c) < 0.28]
        vivid_fills = [c for c in ranked_fills if _saturation(c) >= 0.30 and 0.12 <= _luminance(c) <= 0.88]
        soft_fills = [c for c in ranked_fills if 0.72 <= _luminance(c) <= 0.94]

        primary = (dark_fills[0] if dark_fills else None) or (vivid_fills[0] if vivid_fills else None) or theme_colors.get('accent1', '#1B365D')
        top_grad_pair = grad_pair_counter.most_common(1)[0][0] if grad_pair_counter else None
        if top_grad_pair and top_grad_pair[0] != primary:
            accent = top_grad_pair[0]
            alt_card_bg = top_grad_pair[1]
        else:
            accent = next((c for c in vivid_fills if c != primary), None) or theme_colors.get('accent2', '#7A2048')
            alt_card_bg = soft_fills[0] if soft_fills else '#F4F6F9'

        bg_ref = body_bg.get('color') or cover_bg.get('color') or '#FFFFFF'
        safe_font, commercial_fonts = _pick_safe_font(font_counter, major_font)
        title_col = next((c for c, _ in text_color_counter.most_common(12) if _luminance(c) < 0.35), primary if _luminance(primary) < 0.35 else '#141413')

        sem_tokens = _build_harmonized_semantic_tokens(primary, accent, bg_ref)
        margin_x = round(cw * 0.047, 1)
        content_top = round(sum(body_y_tops) / len(body_y_tops), 1) if body_y_tops else 132.0
        footer_y = round(sum(footer_ys) / len(footer_ys), 1) if footer_ys else round(ch - 78.0, 1)

        has_star4 = geom_counter.get('star4', 0) >= 3
        has_aura_grad = bool(top_grad_pair)
        rec_skin = 'editorial_aura' if (has_star4 or has_aura_grad) else None

        skeleton_cfg = {
            'coverStyle': 'editorial_aura' if rec_skin == 'editorial_aura' else 'academic_banner',
            'headerStyle': 'editorial_star' if has_star4 else 'academic_ribbon',
            'cardTopBar': True,
            'defaultMarginX': margin_x,
            'contentTopY': max(116.0, min(160.0, content_top)),
            'footerY': max(ch - 110.0, min(ch - 54.0, footer_y))
        }
        if rec_skin:
            skeleton_cfg['skin'] = rec_skin

        tpl_json = {
            'id': tid,
            'name': name or f"{os.path.splitext(os.path.basename(pptx_path))[0]} (自动提取)",
            'description': f"由 convert_pptx_to_template.py 自动解析提取（画布 {int(cw)}x{int(ch)}，{'公开可商用' if commercial else '本地私有/非商用'}）。",
            'commercial': bool(commercial),
            'isDefault': False,
            'canvas': {
                'width': cw,
                'height': ch,
                'emuCx': emu_cx,
                'emuCy': emu_cy
            },
            'palette': {
                'primary': primary,
                'secondary': next((c for c in ranked_fills if 0.30 <= _luminance(c) <= 0.55 and c not in (primary, accent)), _blend(primary, '#64748B', 0.45)),
                'accent': accent,
                'titleColor': title_col,
                'bodyColor': '#2E2D2A' if _luminance(bg_ref) > 0.4 else '#F1F5F9',
                'mutedColor': '#64625D' if _luminance(bg_ref) > 0.4 else '#94A3B8',
                'cardBg': '#FFFFFF',
                'cardAltBg': alt_card_bg,
                'cardBorder': sem_tokens['info']['border'],
                'bannerBg': _blend('#FFFFFF', accent, 0.14),
                'bannerBorder': primary,
                'tableHeaderBg': primary,
                'tableHeaderFg': '#FFFFFF' if _luminance(primary) < 0.5 else '#141413',
                'tableStripeBg': _blend('#FFFFFF', accent, 0.06),
                'fontFamily': safe_font,
                'semantic': sem_tokens
            },
            'backgrounds': {
                'cover': cover_bg,
                'body': body_bg
            },
            'skeleton': skeleton_cfg
        }

        if recommended_decors:
            tpl_json['decorations'] = {
                'cover': [],
                'section': [
                    {
                        'rawType': 'image',
                        'role': 'decor',
                        'name': 'recurring-decor-section',
                        'x': 78.0,
                        'y': 40.0,
                        'w': 420.0,
                        'h': 420.0,
                        'src': recommended_decors[0],
                        'opacity': 0.25
                    }
                ],
                'body': [
                    {
                        'rawType': 'image',
                        'role': 'decor',
                        'name': 'recurring-decor-body',
                        'x': round(cw - 290.0, 2),
                        'y': round(ch - 290.0, 2),
                        'w': 260.0,
                        'h': 260.0,
                        'src': recommended_decors[0],
                        'opacity': 0.14
                    }
                ]
            }

        with open(os.path.join(bundle_dir, 'template.json'), 'w', encoding='utf-8') as f:
            json.dump(tpl_json, f, ensure_ascii=False, indent=2)

        report = {
            'sourcePptx': os.path.basename(pptx_path),
            'slideCount': len(slide_files),
            'canvas': tpl_json['canvas'],
            'recommendedSkin': rec_skin,
            'topFillAndGradColors': fill_counter.most_common(15),
            'topGradientPairs': [[list(pair), cnt] for pair, cnt in grad_pair_counter.most_common(8)],
            'topTextColors': text_color_counter.most_common(10),
            'topGeometries': geom_counter.most_common(12),
            'topFonts': font_counter.most_common(10),
            'fontSafety': {
                'selectedSafeFont': safe_font,
                'embeddedFontFiles': len(embedded_font_files),
                'commercialFontsDetected': commercial_fonts,
                'note': '检测到第三方商用/艺术字库时已自动回退至安全通用字体，避免无授权风险或跨机缺字排版崩坏。' if commercial_fonts else '未发现需回退的商业字体风险。'
            },
            'extractedAssets': extracted_assets,
            'skippedMedia': skipped_media,
            'nextSteps': [
                '1. 检查 assets/：移除不需要的局部装饰或带特定内容的 media_* 照片。',
                '2. 检查 palette.semantic（特别是 reject 莫兰迪警示色、pass 主题高亮色）是否完全融于背景气氛。',
                '3. 若使用自定义皮肤 (如 editorial_aura)，在 core/preview.py 输出 6 页示范集和复杂业务页 PNG 做目视验收。'
            ]
        }
        with open(os.path.join(bundle_dir, 'analysis_report.json'), 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    return bundle_dir, tpl_json, report


def main():
    parser = argparse.ArgumentParser(description='Convert a .pptx file into a self-contained Pretty PPT template bundle.')
    parser.add_argument('--pptx', required=True, help='Path to input .pptx file')
    parser.add_argument('--id', required=True, help='Target template ID (snake_case)')
    parser.add_argument('--name', default=None, help='Display name for the template')
    parser.add_argument('--tier', default='local', choices=['local', 'builtin', 'example'], help='Target folder tier under templates/ (default: local)')
    parser.add_argument('--out-dir', default=None, help='Optional custom base output directory')
    parser.add_argument('--commercial', action='store_true', help='Mark as commercial-safe (only use if all assets are 100% original/CC0)')
    args = parser.parse_args()

    bundle_dir, tpl_json, report = convert_pptx_to_template_bundle(
        pptx_path=args.pptx,
        template_id=args.id,
        name=args.name,
        tier=args.tier,
        out_dir=args.out_dir,
        commercial=args.commercial
    )
    print(f"[OK] Generated self-contained template bundle: {bundle_dir}")
    print(f"     canvas={int(tpl_json['canvas']['width'])}x{int(tpl_json['canvas']['height'])}, skin={tpl_json['skeleton'].get('skin')}, primary={tpl_json['palette']['primary']}, accent={tpl_json['palette']['accent']}")
    print(f"     safe_font={tpl_json['palette']['fontFamily']} (commercial hits: {report['fontSafety']['commercialFontsDetected']})")
    print(f"     extracted assets={len(report['extractedAssets'])}, skipped media={len(report['skippedMedia'])}")


if __name__ == '__main__':
    main()
