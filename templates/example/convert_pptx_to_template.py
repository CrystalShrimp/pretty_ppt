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


def _emu_to_px(emu):
    return round(float(emu) / 914400.0 * 96.0, 2)


def _hex_to_rgb(hx):
    h = hx.lstrip('#').strip()
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


def _is_dark_theme(bg_hex, primary_hex):
    return _luminance(bg_hex) < 0.35 or _luminance(primary_hex) < 0.22


def _build_harmonized_semantic_tokens(primary_hex, accent_hex, bg_hex):
    """依据提取到的主色与背景暖度自动调和生成五态低饱和同源功能色令牌，避免高饱和红绿违和。"""
    r, g, b = _hex_to_rgb(bg_hex)
    is_warm = (r >= b + 4)
    paper_base = _blend('#FAF7EF' if is_warm else '#F8FAFC', '#FFFFFF', 0.35)
    dark_ink = '#1E1D1B' if is_warm else '#0F172A'
    body_ink = '#2E2D2A' if is_warm else '#334155'

    # 通过微调饱和度并向暖纸感融合，产出沉稳耐看的功能色
    pass_col = '#2E6F54' if not is_warm else '#556B12'
    warn_col = '#B06D19'
    rej_col = '#9E343B' if not is_warm else '#A63429'

    # 若原主色明度偏亮且饱和度高（如高亮青柠/明橙），适度提深标题字色确保对比度 >= 4.5:1
    pri_title = primary_hex if _luminance(primary_hex) < 0.38 else _blend(primary_hex, dark_ink, 0.55)
    acc_fg = dark_ink if _luminance(accent_hex) > 0.55 else '#FFFFFF'

    return {
        'pass': {
            'bg': _blend(paper_base, pass_col, 0.06),
            'border': pass_col,
            'stripe': accent_hex if _luminance(accent_hex) > 0.45 else pass_col,
            'badgeBg': accent_hex if _luminance(accent_hex) > 0.45 else pass_col,
            'badgeFg': acc_fg if _luminance(accent_hex) > 0.45 else '#FFFFFF',
            'title': _blend(pass_col, dark_ink, 0.35),
            'body': body_ink
        },
        'warn': {
            'bg': _blend(paper_base, warn_col, 0.06),
            'border': warn_col,
            'stripe': warn_col,
            'badgeBg': warn_col,
            'badgeFg': '#FFFFFF',
            'title': _blend(warn_col, dark_ink, 0.30),
            'body': body_ink
        },
        'reject': {
            'bg': _blend(paper_base, rej_col, 0.06),
            'border': rej_col,
            'stripe': rej_col,
            'badgeBg': rej_col,
            'badgeFg': '#FFFFFF',
            'title': _blend(rej_col, dark_ink, 0.25),
            'body': body_ink
        },
        'info': {
            'bg': '#FFFFFF',
            'border': _blend(primary_hex, '#CBD5E1', 0.55),
            'stripe': primary_hex,
            'badgeBg': primary_hex,
            'badgeFg': acc_fg if _luminance(primary_hex) > 0.55 else '#FFFFFF',
            'title': pri_title,
            'body': body_ink
        },
        'neutral': {
            'bg': _blend(paper_base, '#94A3B8', 0.08),
            'border': '#78756E' if is_warm else '#94A3B8',
            'stripe': '#64625D' if is_warm else '#64748B',
            'badgeBg': '#52504C' if is_warm else '#475569',
            'badgeFg': '#FFFFFF',
            'title': '#3E3C38' if is_warm else '#334155',
            'body': '#52504C' if is_warm else '#475569'
        }
    }


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


def _extract_bg_from_slide_xml(root, rels_map, default_bg_hex='#FFFFFF'):
    bg_pr = root.find('.//p:bg/p:bgPr', NS)
    if bg_pr is None:
        return {'type': 'color', 'color': default_bg_hex, 'image': None}, None
    gf = bg_pr.find('./a:gradFill', NS)
    if gf is not None:
        stops = []
        for gs in gf.findall('./a:gsLst/a:gs', NS):
            pos = round(int(gs.attrib.get('pos', 0)) / 100000.0, 3)
            sr = gs.find('.//a:srgbClr', NS)
            col = '#' + sr.attrib.get('val', 'FFFFFF').upper() if sr is not None else default_bg_hex
            al_el = gs.find('.//a:alpha', NS)
            al = round(int(al_el.attrib['val']) / 100000.0, 3) if al_el is not None else 1.0
            stops.append({'pos': pos, 'color': col, 'alpha': al})
        lin = gf.find('./a:lin', NS)
        ang = round(int(lin.attrib.get('ang', 0)) / 60000.0, 1) if lin is not None else 25.0
        if stops:
            return {'type': 'gradient', 'color': stops[0]['color'], 'angle': ang, 'stops': stops, 'image': None}, None
    bf = bg_pr.find('./a:blipFill/a:blip', NS)
    if bf is not None:
        rid = bf.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
        media_ref = rels_map.get(rid)
        return {'type': 'image', 'color': default_bg_hex, 'image': None}, media_ref
    sf = bg_pr.find('./a:solidFill/a:srgbClr', NS)
    if sf is not None:
        return {'type': 'color', 'color': '#' + sf.attrib.get('val', 'FFFFFF').upper(), 'image': None}, None
    return {'type': 'color', 'color': default_bg_hex, 'image': None}, None


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
        theme_colors = {}
        major_font = '微软雅黑'
        if 'ppt/theme/theme1.xml' in names:
            troot = ET.fromstring(z.read('ppt/theme/theme1.xml'))
            clr = troot.find('.//a:clrScheme', NS)
            if clr is not None:
                for ch_el in clr:
                    tag = ch_el.tag.split('}')[-1]
                    if len(ch_el):
                        v = ch_el[0].attrib.get('val') or ch_el[0].attrib.get('lastClr')
                        if v and len(v) == 6:
                            theme_colors[tag] = '#' + v.upper()
            ea_f = troot.find('.//a:fontScheme/a:minorFont/a:ea', NS)
            if ea_f is not None and ea_f.attrib.get('typeface'):
                major_font = ea_f.attrib['typeface']

        # 3. 遍历幻灯片统计颜色、几何形状、字体与背景引用
        slide_files = sorted(
            [n for n in names if re.match(r'^ppt/slides/slide\d+\.xml$', n)],
            key=lambda s: int(re.findall(r'\d+', s)[0])
        )

        fill_counter = Counter()
        text_color_counter = Counter()
        geom_counter = Counter()
        font_counter = Counter()
        media_usage = Counter()
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

            bg_obj, bg_media = _extract_bg_from_slide_xml(sroot, rels_map)
            if s_idx == 0:
                cover_bg, cover_bg_media = bg_obj, bg_media
            elif s_idx == 1:
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
                    sf = spPr.find('./a:solidFill/a:srgbClr', NS)
                    if sf is not None and len(sf.attrib.get('val', '')) == 6:
                        fill_counter['#' + sf.attrib['val'].upper()] += 1
                for r in sp.findall('.//a:r', NS):
                    rPr = r.find('./a:rPr', NS)
                    if rPr is not None:
                        rsf = rPr.find('./a:solidFill/a:srgbClr', NS)
                        if rsf is not None and len(rsf.attrib.get('val', '')) == 6:
                            text_color_counter['#' + rsf.attrib['val'].upper()] += 1
                        ea = rPr.find('./a:ea', NS)
                        if ea is not None and ea.attrib.get('typeface'):
                            font_counter[ea.attrib['typeface']] += 1

            for pic in sroot.findall('.//p:pic', NS):
                blip = pic.find('.//a:blip', NS)
                if blip is not None:
                    rid = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if rid and rid in rels_map:
                        media_usage[rels_map[rid]] += 1

        # 4. 提取与分拣静态媒体资产到 <bundle_dir>/assets/
        extracted_assets = []
        skipped_media = []
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
                im = Image.open(io.BytesIO(raw_bytes))
                iw, ih = im.size
                has_alpha = im.mode in ('RGBA', 'LA') or ('transparency' in im.info)
            except Exception as exc:
                skipped_media.append({'file': base_fn, 'reason': f'无法解码: {exc}'})
                continue

            if mpath == cover_bg_media:
                out_name = f"bg_cover{ext}"
                cover_bg['image'] = f"assets/{out_name}"
                category = 'background-cover'
            elif mpath == body_bg_media:
                out_name = f"bg_body{ext}"
                body_bg['image'] = f"assets/{out_name}"
                category = 'background-body'
            elif iw <= 512 and ih <= 512 and has_alpha:
                out_name = f"icon_{base_fn}"
                category = 'icon'
            elif has_alpha and (media_usage.get(mpath, 0) >= 2 or max(iw, ih) >= 512):
                out_name = f"decor_{base_fn}"
                category = 'decor'
            else:
                # 若是单页人物大插画或不透明大图则仅归类提示，不直接覆盖为背景图
                out_name = f"media_{base_fn}"
                category = 'content-photo'

            with open(os.path.join(assets_dir, out_name), 'wb') as out_f:
                out_f.write(raw_bytes)
            extracted_assets.append({
                'source': base_fn,
                'savedAs': f"assets/{out_name}",
                'category': category,
                'size': [iw, ih],
                'hasAlpha': has_alpha,
                'slideRefs': int(media_usage.get(mpath, 0))
            })

        # 5. 计算协调调色板
        ranked_fills = [c for c, _ in fill_counter.most_common(30)]
        dark_fills = [c for c in ranked_fills if _luminance(c) < 0.28]
        vivid_fills = [c for c in ranked_fills if _saturation(c) >= 0.35 and 0.12 <= _luminance(c) <= 0.85]
        light_fills = [c for c in ranked_fills if _luminance(c) >= 0.85]

        primary = (dark_fills[0] if dark_fills else None) or (vivid_fills[0] if vivid_fills else None) or theme_colors.get('accent1', '#1B365D')
        accent = next((c for c in vivid_fills if c != primary), None) or theme_colors.get('accent2', '#7A2048')
        bg_ref = body_bg.get('color') or cover_bg.get('color') or '#FFFFFF'
        card_bg = light_fills[0] if light_fills else '#FFFFFF'
        font_family = font_counter.most_common(1)[0][0] if font_counter else major_font
        title_col = next((c for c, _ in text_color_counter.most_common(10) if _luminance(c) < 0.35), '#141413')

        sem_tokens = _build_harmonized_semantic_tokens(primary, accent, bg_ref)
        margin_x = round(cw * 0.047, 1)
        content_top = round(sum(body_y_tops) / len(body_y_tops), 1) if body_y_tops else 132.0
        footer_y = round(sum(footer_ys) / len(footer_ys), 1) if footer_ys else round(ch - 78.0, 1)

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
                'secondary': _blend(primary, '#64748B', 0.45),
                'accent': accent,
                'titleColor': title_col,
                'bodyColor': '#2E2D2A' if _luminance(bg_ref) > 0.4 else '#F1F5F9',
                'mutedColor': '#736F68' if _luminance(bg_ref) > 0.4 else '#94A3B8',
                'cardBg': card_bg,
                'cardAltBg': sem_tokens['neutral']['bg'],
                'cardBorder': sem_tokens['info']['border'],
                'bannerBg': _blend(bg_ref, primary, 0.08),
                'bannerBorder': primary,
                'tableHeaderBg': primary,
                'tableHeaderFg': '#FFFFFF' if _luminance(primary) < 0.5 else '#141413',
                'tableStripeBg': _blend(card_bg, primary, 0.04),
                'fontFamily': font_family,
                'semantic': sem_tokens
            },
            'backgrounds': {
                'cover': cover_bg,
                'body': body_bg
            },
            'skeleton': {
                'coverStyle': 'academic_banner',
                'headerStyle': 'academic_ribbon',
                'cardTopBar': True,
                'defaultMarginX': margin_x,
                'contentTopY': max(116.0, min(160.0, content_top)),
                'footerY': max(ch - 110.0, min(ch - 54.0, footer_y))
            }
        }

        with open(os.path.join(bundle_dir, 'template.json'), 'w', encoding='utf-8') as f:
            json.dump(tpl_json, f, ensure_ascii=False, indent=2)

        report = {
            'sourcePptx': os.path.basename(pptx_path),
            'slideCount': len(slide_files),
            'canvas': tpl_json['canvas'],
            'topFillColors': fill_counter.most_common(15),
            'topTextColors': text_color_counter.most_common(10),
            'topGeometries': geom_counter.most_common(12),
            'topFonts': font_counter.most_common(8),
            'extractedAssets': extracted_assets,
            'skippedMedia': skipped_media,
            'nextSteps': [
                '1. 审查 assets/：移除单页角色立绘或带有特定版权标识的 media_* 图片。',
                '2. 检查 palette.semantic 中 pass/warn/reject 颜色是否符合原 PPT 材质氛围。',
                '3. 在模板根目录补充 decorations 字段挂载透明底纹，然后用 core/preview.py 目视检验。'
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
    print(f"     canvas={int(tpl_json['canvas']['width'])}x{int(tpl_json['canvas']['height'])}, primary={tpl_json['palette']['primary']}, accent={tpl_json['palette']['accent']}")
    print(f"     extracted assets={len(report['extractedAssets'])}, skipped media={len(report['skippedMedia'])}")


if __name__ == '__main__':
    main()
