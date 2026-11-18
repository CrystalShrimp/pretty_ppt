import os
import re
import json
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONNECTOR_GEOMS = {
    'line', 'straightConnector1', 'elbowConnector',
    'bentConnector2', 'bentConnector3', 'bentConnector4', 'bentConnector5'
}
ELBOW_GEOMS = {'elbowConnector', 'bentConnector2', 'bentConnector3', 'bentConnector4', 'bentConnector5'}

SHAPE_GEOM_MAP = {
    'rect': MSO_SHAPE.RECTANGLE,
    'roundRect': MSO_SHAPE.ROUNDED_RECTANGLE,
    'diamond': MSO_SHAPE.DIAMOND,
    'chevron': MSO_SHAPE.CHEVRON,
    'pentagon': MSO_SHAPE.PENTAGON,
    'homePlate': MSO_SHAPE.PENTAGON,
    'oval': MSO_SHAPE.OVAL,
    'ellipse': MSO_SHAPE.OVAL,
    'hexagon': MSO_SHAPE.HEXAGON,
    'parallelogram': MSO_SHAPE.PARALLELOGRAM,
    'triangle': MSO_SHAPE.ISOSCELES_TRIANGLE,
    'rightArrow': MSO_SHAPE.RIGHT_ARROW,
    'plaque': MSO_SHAPE.PLAQUE,
}


def _alpha_to_amt(alpha):
    v = float(alpha)
    if v <= 1.0:
        return max(0, min(100000, int(round(v * 100000))))
    return max(0, min(100000, int(round(v))))


def _apply_alpha_to_solid_fill(parent_el, alpha):
    if alpha is None or parent_el is None:
        return
    amt = _alpha_to_amt(alpha)
    if amt >= 99990:
        return
    sf = parent_el.find(qn('a:solidFill'))
    if sf is None:
        return
    clr = sf.find(qn('a:srgbClr'))
    if clr is None and len(sf):
        clr = sf[0]
    if clr is None:
        return
    for old_a in clr.findall(qn('a:alpha')):
        clr.remove(old_a)
    clr.append(parse_xml(f'<a:alpha {nsdecls("a")} val="{amt}"/>'))


def _build_grad_fill_xml(grad_data, include_ns=True):
    stops = (grad_data or {}).get('stops') or []
    gs_parts = []
    for st in stops:
        raw_pos = float(st.get('pos', 0.0))
        pos = max(0, min(100000, int(round(raw_pos * 100000)) if raw_pos <= 1.0 else int(round(raw_pos))))
        hex_c = str(st.get('color') or '#FFFFFF').lstrip('#').strip().upper()
        if len(hex_c) != 6:
            hex_c = 'FFFFFF'
        alpha_xml = ''
        if st.get('alpha') is not None:
            amt = _alpha_to_amt(st['alpha'])
            if amt < 99990:
                alpha_xml = f'<a:alpha val="{amt}"/>'
        gs_parts.append(f'<a:gs pos="{pos}"><a:srgbClr val="{hex_c}">{alpha_xml}</a:srgbClr></a:gs>')
    ang = int(round(float((grad_data or {}).get('angle', 0.0)) * 60000)) % 21600000
    ns_attr = f' {nsdecls("a")}' if include_ns else ''
    return (
        f'<a:gradFill{ns_attr} rotWithShape="1">'
        f'<a:gsLst>{"".join(gs_parts)}</a:gsLst>'
        f'<a:lin ang="{ang}" scaled="1"/>'
        f'</a:gradFill>'
    )


def _insert_fill_into_spPr(spPr, fill_el):
    for tag in ('a:noFill', 'a:solidFill', 'a:gradFill', 'a:blipFill', 'a:pattFill', 'a:grpFill'):
        for old in spPr.findall(qn(tag)):
            spPr.remove(old)
    insert_idx = len(spPr)
    for idx, child in enumerate(list(spPr)):
        local = child.tag.split('}')[-1]
        if local in ('ln', 'effectLst', 'effectDag', 'scene3d', 'sp3d', 'extLst'):
            insert_idx = idx
            break
    spPr.insert(insert_idx, fill_el)


def _insert_shadow_into_spPr(spPr, shadow_cfg=None):
    for old in spPr.findall(qn('a:effectLst')):
        spPr.remove(old)
    cfg = shadow_cfg if isinstance(shadow_cfg, dict) else {}
    blur = int(cfg.get('blurRad', 101600))
    dist = int(cfg.get('dist', 38100))
    alpha = _alpha_to_amt(cfg.get('alpha', 0.13))
    eff = parse_xml(
        f'<a:effectLst {nsdecls("a")}>'
        f'  <a:outerShdw blurRad="{blur}" dist="{dist}" dir="5400000" algn="tl" rotWithShape="0">'
        f'    <a:srgbClr val="000000"><a:alpha val="{alpha}"/></a:srgbClr>'
        f'  </a:outerShdw>'
        f'</a:effectLst>'
    )
    insert_idx = len(spPr)
    for idx, child in enumerate(list(spPr)):
        local = child.tag.split('}')[-1]
        if local in ('scene3d', 'sp3d', 'extLst'):
            insert_idx = idx
            break
    spPr.insert(insert_idx, eff)


def px_to_emu(px):
    if px is None:
        return Emu(0)
    return Emu(int(round(float(px) * 914400.0 / 96.0)))


def hex_to_rgb(hex_str):
    if not hex_str or not isinstance(hex_str, str):
        return None
    h = hex_str.lstrip('#').strip()
    if len(h) == 6:
        try:
            return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except Exception:
            return None
    return None


def resolve_local_asset(web_path):
    if not web_path:
        return None
    rel = web_path.lstrip('/').replace('/', os.sep)
    full = os.path.join(BASE_DIR, rel)
    if os.path.exists(full):
        return full
    return None


def attach_pcs_name(shape_obj, comp_meta, ch):
    """在形状名称中写入轻量 [PCS:comp_id|comp_type|role] 元数据标记，保证 PPTX 往返解析零打散。"""
    if not comp_meta:
        return
    comp_id, comp_type = comp_meta
    role = ch.get('role') or 'shape'
    raw_name = str(ch.get('name') or role)
    clean_name = re.sub(r'^\[PCS:[^\]]+\]\s*', '', raw_name).replace('\r', ' ').replace('\n', ' ').strip()
    shape_obj.name = f"[PCS:{comp_id}|{comp_type}|{role}] {clean_name}"[:120]


def _apply_line_dash(ln_el, dash_style):
    """在 <a:ln> 中按 DrawingML 规范顺序（位于 headEnd/tailEnd 之前）设置 <a:prstDash>。"""
    if not dash_style or dash_style == 'solid':
        return
    for old in ln_el.findall(qn('a:prstDash')):
        ln_el.remove(old)
    dash_el = parse_xml(f'<a:prstDash {nsdecls("a")} val="{dash_style}"/>')
    insert_idx = len(ln_el)
    for idx, child in enumerate(list(ln_el)):
        local_tag = child.tag.split('}')[-1]
        if local_tag in ('round', 'bevel', 'miter', 'headEnd', 'tailEnd'):
            insert_idx = idx
            break
    ln_el.insert(insert_idx, dash_el)


def set_slide_background_image(slide, img_path):
    if not img_path or not os.path.exists(img_path):
        return
    _, rId = slide.part.get_or_add_image_part(img_path)
    cSld = slide._element.cSld
    old_bg = cSld.find(qn('p:bg'))
    if old_bg is not None:
        cSld.remove(old_bg)
    bg_xml = parse_xml(
        f'<p:bg {nsdecls("p", "a", "r")}>'
        f'  <p:bgPr>'
        f'    <a:blipFill rotWithShape="1">'
        f'      <a:blip r:embed="{rId}"/>'
        f'      <a:stretch><a:fillRect/></a:stretch>'
        f'    </a:blipFill>'
        f'    <a:effectLst/>'
        f'  </p:bgPr>'
        f'</p:bg>'
    )
    cSld.insert(0, bg_xml)


def set_slide_background_color(slide, hex_color):
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = rgb


def set_slide_background_gradient(slide, grad_data):
    cSld = slide._element.cSld
    old_bg = cSld.find(qn('p:bg'))
    if old_bg is not None:
        cSld.remove(old_bg)
    grad_inner = _build_grad_fill_xml(grad_data, include_ns=False)
    bg_xml = parse_xml(
        f'<p:bg {nsdecls("p", "a")}>'
        f'  <p:bgPr>'
        f'    {grad_inner}'
        f'    <a:effectLst/>'
        f'  </p:bgPr>'
        f'</p:bg>'
    )
    cSld.insert(0, bg_xml)


def set_east_asian_font(run, font_name):
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = parse_xml(f'<a:ea {nsdecls("a")} typeface="{font_name}"/>')
        rPr.append(ea)
    else:
        ea.set('typeface', font_name)


def apply_text_body(tf, tx_data, default_font='微软雅黑'):
    if not tx_data:
        return
    tf.word_wrap = tx_data.get('wrap', True)
    pad = tx_data.get('padding', {})
    tf.margin_left = px_to_emu(pad.get('left', 7.2))
    tf.margin_top = px_to_emu(pad.get('top', 3.6))
    tf.margin_right = px_to_emu(pad.get('right', 7.2))
    tf.margin_bottom = px_to_emu(pad.get('bottom', 3.6))

    valign = tx_data.get('valign', 'top')
    if valign == 'middle':
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    elif valign == 'bottom':
        tf.vertical_anchor = MSO_ANCHOR.BOTTOM
    else:
        tf.vertical_anchor = MSO_ANCHOR.TOP

    paras = tx_data.get('paragraphs', [])
    for p_idx, p_data in enumerate(paras):
        p = tf.paragraphs[0] if p_idx == 0 else tf.add_paragraph()
        algn = p_data.get('align', 'left')
        if algn == 'center':
            p.alignment = PP_ALIGN.CENTER
        elif algn == 'right':
            p.alignment = PP_ALIGN.RIGHT
        else:
            p.alignment = PP_ALIGN.LEFT

        if p_data.get('spaceBefore'):
            p.space_before = Pt(float(p_data['spaceBefore']))
        if p_data.get('spaceAfter'):
            p.space_after = Pt(float(p_data['spaceAfter']))
        if p_data.get('lineSpacing'):
            p.line_spacing = Pt(float(p_data['lineSpacing']))
        elif p_data.get('lineSpacingPct'):
            p.line_spacing = float(p_data['lineSpacingPct'])

        runs = p_data.get('runs', [])
        if not runs and p_data.get('text'):
            runs = [{'text': p_data['text'], 'fontSize': 10.5, 'bold': False, 'color': '#333333', 'fontFamily': default_font}]

        for r_data in runs:
            run = p.add_run()
            run.text = r_data.get('text', '')
            sz = r_data.get('fontSize')
            if sz:
                run.font.size = Pt(float(sz))
            if r_data.get('bold') is not None:
                run.font.bold = bool(r_data['bold'])
            if r_data.get('italic') is not None:
                run.font.italic = bool(r_data['italic'])
            rgb = hex_to_rgb(r_data.get('color'))
            if rgb:
                run.font.color.rgb = rgb
            if r_data.get('alpha') is not None:
                _apply_alpha_to_solid_fill(run._r.get_or_add_rPr(), r_data['alpha'])
            if r_data.get('letterSpacing') is not None:
                run._r.get_or_add_rPr().set('spc', str(int(round(float(r_data['letterSpacing']) * 100))))
            fname = r_data.get('fontFamily') or default_font
            run.font.name = fname
            set_east_asian_font(run, fname)


def sync_component_children_coords(comp):
    """Ensure children absolute coordinates match component (x, y, w, h) and relative offsets."""
    cx = float(comp.get('x', 0))
    cy = float(comp.get('y', 0))
    children = comp.get('children', [])
    if not children:
        return []
    # Compute original bounding box from relX/relY/relW/relH
    max_rw = max((float(ch.get('relX', 0)) + float(ch.get('relW', 0))) for ch in children)
    max_rh = max((float(ch.get('relY', 0)) + float(ch.get('relH', 0))) for ch in children)
    comp_w = float(comp.get('w', max_rw or 1))
    comp_h = float(comp.get('h', max_rh or 1))
    sx = (comp_w / max_rw) if max_rw > 1 else 1.0
    sy = (comp_h / max_rh) if max_rh > 1 else 1.0

    synced = []
    for ch in children:
        c = dict(ch)
        if 'relX' in c and 'relY' in c:
            c['x'] = round(cx + float(c['relX']) * sx, 2)
            c['y'] = round(cy + float(c['relY']) * sy, 2)
            c['w'] = round(float(c.get('relW', c.get('w', 0))) * sx, 2)
            c['h'] = round(float(c.get('relH', c.get('h', 0))) * sy, 2)
        synced.append(c)
    return synced


def render_child_to_slide(slide, ch, default_font='微软雅黑', comp_meta=None):
    rtype = ch.get('rawType', 'shape')
    x = px_to_emu(ch.get('x', 0))
    y = px_to_emu(ch.get('y', 0))
    w = px_to_emu(max(ch.get('w', 0), 0))
    h = px_to_emu(max(ch.get('h', 0), 0))

    if rtype == 'image':
        img_path = resolve_local_asset(ch.get('src'))
        if img_path and w > 0 and h > 0:
            pic = slide.shapes.add_picture(img_path, x, y, w, h)
            attach_pcs_name(pic, comp_meta, ch)
            if ch.get('rotation') is not None:
                pic.rotation = float(ch['rotation'])
            if ch.get('opacity') is not None:
                amt = _alpha_to_amt(ch['opacity'])
                if amt < 99990:
                    blip = pic._element.blipFill.blip
                    for old_a in blip.findall(qn('a:alphaModFix')):
                        blip.remove(old_a)
                    blip.append(parse_xml(f'<a:alphaModFix {nsdecls("a")} amt="{amt}"/>'))
        return

    if rtype == 'table':
        rows_data = ch.get('rows', [])
        if not rows_data or not rows_data[0]:
            return
        r_cnt = len(rows_data)
        c_cnt = len(rows_data[0])
        tbl_shape = slide.shapes.add_table(r_cnt, c_cnt, x, y, max(w, Emu(10000)), max(h, Emu(10000)))
        attach_pcs_name(tbl_shape, comp_meta, ch)
        table = tbl_shape.table

        col_widths = ch.get('colWidths', [])
        for c_i in range(c_cnt):
            if c_i < len(col_widths) and col_widths[c_i] > 0:
                table.columns[c_i].width = px_to_emu(col_widths[c_i])

        row_heights = ch.get('rowHeights', [])
        for r_i in range(r_cnt):
            if r_i < len(row_heights) and row_heights[r_i] > 0:
                table.rows[r_i].height = px_to_emu(row_heights[r_i])
            for c_i in range(c_cnt):
                if c_i >= len(rows_data[r_i]):
                    continue
                cell_data = rows_data[r_i][c_i]
                cell = table.cell(r_i, c_i)

                fill_rgb = hex_to_rgb(cell_data.get('fill'))
                if fill_rgb:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = fill_rgb

                pad = cell_data.get('padding', {})
                cell.margin_left = px_to_emu(pad.get('left', 7.2))
                cell.margin_top = px_to_emu(pad.get('top', 3.6))
                cell.margin_right = px_to_emu(pad.get('right', 7.2))
                cell.margin_bottom = px_to_emu(pad.get('bottom', 3.6))

                valign = cell_data.get('valign', 'middle')
                if valign == 'top':
                    cell.vertical_anchor = MSO_ANCHOR.TOP
                elif valign == 'bottom':
                    cell.vertical_anchor = MSO_ANCHOR.BOTTOM
                else:
                    cell.vertical_anchor = MSO_ANCHOR.MIDDLE

                if cell_data.get('textBody') and cell_data['textBody'].get('paragraphs'):
                    # Use rich textBody if text wasn't overridden
                    orig_txt = '\n'.join(p['text'] for p in cell_data['textBody']['paragraphs'])
                    if cell_data.get('text') == orig_txt:
                        apply_text_body(cell.text_frame, cell_data['textBody'], default_font)
                        continue

                # Render from simplified cell_data fields
                tf = cell.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                algn = cell_data.get('align', 'left')
                p.alignment = PP_ALIGN.CENTER if algn == 'center' else (PP_ALIGN.RIGHT if algn == 'right' else PP_ALIGN.LEFT)
                run = p.add_run()
                run.text = str(cell_data.get('text', ''))
                run.font.size = Pt(float(cell_data.get('fontSize') or 10.0))
                run.font.bold = bool(cell_data.get('bold', False))
                rgb = hex_to_rgb(cell_data.get('color') or '#333333')
                if rgb:
                    run.font.color.rgb = rgb
                fname = cell_data.get('fontFamily') or default_font
                run.font.name = fname
                set_east_asian_font(run, fname)
        return

    # Shape or Connector line
    geom = ch.get('geom', 'rect')
    if geom in CONNECTOR_GEOMS:
        x1 = px_to_emu(ch.get('x', 0))
        y1 = px_to_emu(ch.get('y', 0))
        x2 = px_to_emu(ch.get('x', 0) + ch.get('w', 0))
        y2 = px_to_emu(ch.get('y', 0) + ch.get('h', 0))
        if ch.get('flipH'):
            x1, x2 = x2, x1
        if ch.get('flipV'):
            y1, y2 = y2, y1
        conn_type = MSO_CONNECTOR.ELBOW if geom in ELBOW_GEOMS else MSO_CONNECTOR.STRAIGHT
        conn = slide.shapes.add_connector(conn_type, x1, y1, x2, y2)
        attach_pcs_name(conn, comp_meta, ch)
        b_rgb = hex_to_rgb(ch.get('borderColor') or '#D9D9D9')
        if b_rgb:
            conn.line.color.rgb = b_rgb
        bw = ch.get('borderWidth')
        if bw:
            conn.line.width = px_to_emu(bw)
        ln_el = conn.line._get_or_add_ln()
        if ch.get('borderAlpha') is not None:
            _apply_alpha_to_solid_fill(ln_el, ch['borderAlpha'])
        _apply_line_dash(ln_el, ch.get('dashStyle'))
        for old_end in ln_el.findall(qn('a:headEnd')) + ln_el.findall(qn('a:tailEnd')):
            ln_el.remove(old_end)
        if ch.get('headEnd') and ch.get('headEnd') != 'none':
            ln_el.append(parse_xml(f'<a:headEnd {nsdecls("a")} type="{ch["headEnd"]}"/>'))
        if ch.get('tailEnd') and ch.get('tailEnd') != 'none':
            ln_el.append(parse_xml(f'<a:tailEnd {nsdecls("a")} type="{ch["tailEnd"]}"/>'))
        return

    shape_type = SHAPE_GEOM_MAP.get(geom, MSO_SHAPE.RECTANGLE)
    sp = slide.shapes.add_shape(shape_type, x, y, max(w, Emu(100)), max(h, Emu(100)))
    attach_pcs_name(sp, comp_meta, ch)
    sp.shadow.inherit = False
    if ch.get('rotation') is not None:
        sp.rotation = float(ch['rotation'])

    if geom in ('roundRect', 'parallelogram', 'plaque') and ch.get('adj') is not None:
        try:
            sp.adjustments[0] = float(ch['adj']) / 100000.0
        except Exception:
            pass

    if ch.get('gradFill') and ch['gradFill'].get('stops'):
        sp.fill.background()
        grad_el = parse_xml(_build_grad_fill_xml(ch['gradFill'], include_ns=True))
        _insert_fill_into_spPr(sp._element.spPr, grad_el)
    else:
        fill_rgb = hex_to_rgb(ch.get('fill'))
        if fill_rgb:
            sp.fill.solid()
            sp.fill.fore_color.rgb = fill_rgb
            if ch.get('fillAlpha') is not None:
                _apply_alpha_to_solid_fill(sp._element.spPr, ch['fillAlpha'])
        else:
            sp.fill.background()

    border_rgb = hex_to_rgb(ch.get('borderColor'))
    bw = ch.get('borderWidth') or 0.0
    if border_rgb and bw > 0:
        sp.line.color.rgb = border_rgb
        sp.line.width = px_to_emu(bw)
        ln_el = sp.line._get_or_add_ln()
        if ch.get('borderAlpha') is not None:
            _apply_alpha_to_solid_fill(ln_el, ch['borderAlpha'])
        if ch.get('dashStyle') and ch.get('dashStyle') != 'solid':
            _apply_line_dash(ln_el, ch.get('dashStyle'))
    else:
        sp.line.fill.background()

    if ch.get('shadow'):
        _insert_shadow_into_spPr(sp._element.spPr, ch.get('shadow'))

    if ch.get('textBody'):
        apply_text_body(sp.text_frame, ch['textBody'], default_font)


def export_deck_to_pptx(deck_data, out_pptx_path):
    """Compile a Deck JSON object or file into a standard .pptx file."""
    if isinstance(deck_data, str):
        with open(deck_data, 'r', encoding='utf-8') as f:
            deck = json.load(f)
    else:
        deck = deck_data

    prs = Presentation()
    canvas = deck.get('canvas', {})
    prs.slide_width = Emu(int(canvas.get('emuCx', 9721850)))
    prs.slide_height = Emu(int(canvas.get('emuCy', 6480175)))
    blank_layout = prs.slide_layouts[6]
    default_font = deck.get('theme', {}).get('fontFamily', '微软雅黑')

    for s_data in deck.get('slides', []):
        slide = prs.slides.add_slide(blank_layout)
        bg = s_data.get('background', {})
        if bg.get('type') == 'image' and bg.get('image'):
            bg_path = resolve_local_asset(bg['image'])
            if bg_path:
                set_slide_background_image(slide, bg_path)
        elif bg.get('type') == 'gradient' and bg.get('stops'):
            set_slide_background_gradient(slide, bg)
        elif bg.get('color'):
            set_slide_background_color(slide, bg['color'])

        for dec in s_data.get('decorations', []):
            render_child_to_slide(slide, dec, default_font, comp_meta=('decor', 'decor'))

        for comp in s_data.get('components', []):
            comp_meta = (comp.get('id', ''), comp.get('type', 'info-card'))
            children = sync_component_children_coords(comp)
            for ch in children:
                render_child_to_slide(slide, ch, default_font, comp_meta=comp_meta)

    os.makedirs(os.path.dirname(os.path.abspath(out_pptx_path)), exist_ok=True)
    prs.save(out_pptx_path)
    return out_pptx_path
