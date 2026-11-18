import zipfile
import xml.etree.ElementTree as ET
import json
import os
import re
import copy

NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_MEDIA_DIR = os.path.join(BASE_DIR, 'assets', 'media')

THEME_MAP = {
    'dk1': '#000000',
    'lt1': '#FFFFFF',
    'dk2': '#44546A',
    'lt2': '#E7E6E6',
    'accent1': '#4472C4',
    'accent2': '#ED7D31',
    'accent3': '#A5A5A5',
    'accent4': '#FFC000',
    'accent5': '#5B9BD5',
    'accent6': '#70AD47',
    'hlink': '#0563C1',
    'folHlink': '#954F72',
    'bg1': '#FFFFFF',
    'tx1': '#000000',
    'bg2': '#E7E6E6',
    'tx2': '#44546A'
}

COMPONENT_TYPE_LABELS = {
    'slide-header': 'slide-header',
    'footer-banner': 'footer-banner',
    'info-card': 'info-card',
    'kpi-card': 'kpi-card',
    'process-flow': 'process-flow',
    'data-table': 'data-table',
    'image-frame': 'image-frame',
    'tag-badge': 'tag-badge',
    'toc-list': 'toc-list',
    'cover-divider': 'cover-divider',
    'vertical-stack': 'vertical-stack',
    'decision-gate': 'decision-gate',
    'stage-funnel': 'stage-funnel',
    'iteration-lanes': 'iteration-lanes',
    'rule-checklist': 'rule-checklist'
}

GEOM_ALIAS = {
    'straightConnector1': 'line',
    'bentConnector2': 'elbowConnector',
    'bentConnector3': 'elbowConnector',
    'bentConnector4': 'elbowConnector',
    'bentConnector5': 'elbowConnector',
    'elbowConnector': 'elbowConnector',
    'ellipse': 'oval',
    'homePlate': 'pentagon'
}

PCS_NAME_RE = re.compile(r'^\[PCS:([^|\]]+)\|([^|\]]+)\|([^\]]+)\]\s*(.*)$')


def emu_to_px(emu):
    if emu is None:
        return 0.0
    return round(float(emu) / 914400.0 * 96.0, 2)


def resolve_color(elem):
    if elem is None:
        return None
    srgb = elem.find('.//a:srgbClr', NS)
    if srgb is not None:
        alpha = srgb.find('./a:alpha', NS)
        if alpha is not None and int(alpha.attrib.get('val', '100000')) == 0:
            return None
        return '#' + srgb.attrib.get('val', '000000').upper()
    scheme = elem.find('.//a:schemeClr', NS)
    if scheme is not None:
        alpha = scheme.find('./a:alpha', NS)
        if alpha is not None and int(alpha.attrib.get('val', '100000')) == 0:
            return None
        val = scheme.attrib.get('val', '')
        return THEME_MAP.get(val, '#333333')
    return None


def parse_rPr(rPr, defRPr=None):
    sz = None
    bold = None
    italic = None
    color = None
    font = None
    for pr in [defRPr, rPr]:
        if pr is None:
            continue
        if 'sz' in pr.attrib:
            sz = round(int(pr.attrib['sz']) / 100.0, 2)
        if 'b' in pr.attrib:
            bold = (pr.attrib['b'] == '1')
        if 'i' in pr.attrib:
            italic = (pr.attrib['i'] == '1')
        sf = pr.find('./a:solidFill', NS)
        if sf is not None:
            c = resolve_color(sf)
            if c:
                color = c
        ea = pr.find('./a:ea', NS)
        latin = pr.find('./a:latin', NS)
        if ea is not None and ea.attrib.get('typeface'):
            font = ea.attrib.get('typeface')
        elif latin is not None and latin.attrib.get('typeface'):
            font = latin.attrib.get('typeface')
    return {
        'fontSize': sz,
        'bold': bool(bold),
        'italic': bool(italic),
        'color': color,
        'fontFamily': font or '微软雅黑'
    }


def parse_txBody(txBody):
    if txBody is None:
        return None
    bodyPr = txBody.find('./a:bodyPr', NS)
    valign = 'top'
    wrap = True
    padding = {'left': 7.2, 'top': 3.6, 'right': 7.2, 'bottom': 3.6}
    if bodyPr is not None:
        anc = bodyPr.attrib.get('anchor')
        if anc == 'ctr':
            valign = 'middle'
        elif anc == 'b':
            valign = 'bottom'
        if bodyPr.attrib.get('wrap') == 'none':
            wrap = False
        for side, attr in [('left', 'lIns'), ('top', 'tIns'), ('right', 'rIns'), ('bottom', 'bIns')]:
            if attr in bodyPr.attrib:
                padding[side] = emu_to_px(bodyPr.attrib[attr])

    paragraphs = []
    for p in txBody.findall('./a:p', NS):
        pPr = p.find('./a:pPr', NS)
        align = 'left'
        defRPr = None
        spaceBefore = 0.0
        spaceAfter = 0.0
        lineSpacing = None
        lineSpacingPct = None
        if pPr is not None:
            algn = pPr.attrib.get('algn')
            if algn == 'ctr':
                align = 'center'
            elif algn == 'r':
                align = 'right'
            defRPr = pPr.find('./a:defRPr', NS)
            spcBef = pPr.find('./a:spcBef/a:spcPts', NS)
            if spcBef is not None and 'val' in spcBef.attrib:
                spaceBefore = round(int(spcBef.attrib['val']) / 100.0, 2)
            spcAft = pPr.find('./a:spcAft/a:spcPts', NS)
            if spcAft is not None and 'val' in spcAft.attrib:
                spaceAfter = round(int(spcAft.attrib['val']) / 100.0, 2)
            lnSpcPts = pPr.find('./a:lnSpc/a:spcPts', NS)
            if lnSpcPts is not None and 'val' in lnSpcPts.attrib:
                lineSpacing = round(int(lnSpcPts.attrib['val']) / 100.0, 2)
            lnSpcPct = pPr.find('./a:lnSpc/a:spcPct', NS)
            if lnSpcPct is not None and 'val' in lnSpcPct.attrib:
                lineSpacingPct = round(int(lnSpcPct.attrib['val']) / 100000.0, 2)

        runs = []
        for child in p:
            ctag = child.tag.split('}')[-1]
            if ctag in ('r', 'fld'):
                t = child.find('./a:t', NS)
                if t is not None and t.text is not None:
                    rPr = child.find('./a:rPr', NS)
                    style = parse_rPr(rPr, defRPr)
                    runs.append({
                        'text': t.text,
                        **style
                    })
            elif ctag == 'br':
                runs.append({'text': '\n', **parse_rPr(None, defRPr)})
        full_text = ''.join(r['text'] for r in runs)
        if runs or full_text:
            paragraphs.append({
                'align': align,
                'spaceBefore': spaceBefore,
                'spaceAfter': spaceAfter,
                'lineSpacing': lineSpacing,
                'lineSpacingPct': lineSpacingPct,
                'runs': runs,
                'text': full_text
            })
    return {
        'valign': valign,
        'wrap': wrap,
        'padding': padding,
        'paragraphs': paragraphs
    }


def map_rect(x, y, w, h, tf):
    if tf is None:
        return round(x, 2), round(y, 2), round(w, 2), round(h, 2)
    nx = tf['gx'] + (x - tf['chx']) * tf['sx']
    ny = tf['gy'] + (y - tf['chy']) * tf['sy']
    nw = w * tf['sx']
    nh = h * tf['sy']
    return round(nx, 2), round(ny, 2), round(nw, 2), round(nh, 2)


def _extract_pcs_tag(raw_name, default_role, default_name):
    if not raw_name:
        return None, None, default_role, default_name, False
    m = PCS_NAME_RE.match(raw_name.strip())
    if m:
        pcs_cid, pcs_ctype, pcs_role, clean_name = m.group(1), m.group(2), m.group(3), m.group(4).strip()
        return pcs_cid, pcs_ctype, pcs_role or default_role, (clean_name or pcs_role or default_name), True
    return None, None, default_role, raw_name or default_name, False


def _attach_pcs_meta(elem_dict, pcs_cid, pcs_ctype, locked):
    if pcs_cid:
        elem_dict['_pcsCompId'] = pcs_cid
        elem_dict['_pcsCompType'] = pcs_ctype
    if locked:
        elem_dict['_pcsLockedRole'] = True
    return elem_dict


def parse_raw_element(el, rels_map, deck_name, tf=None):
    tag = el.tag.split('}')[-1]
    nvPr = el.find('.//p:cNvPr', NS)
    raw_name = nvPr.attrib.get('name', '') if nvPr is not None else ''

    xfrm = None
    for path in ['./p:spPr/a:xfrm', './p:grpSpPr/a:xfrm', './p:xfrm']:
        found = el.find(path, NS)
        if found is not None:
            xfrm = found
            break
    rx = ry = rw = rh = 0.0
    flipH = flipV = False
    if xfrm is not None:
        off = xfrm.find('a:off', NS)
        ext = xfrm.find('a:ext', NS)
        if off is not None:
            rx = float(off.attrib.get('x', 0))
            ry = float(off.attrib.get('y', 0))
        if ext is not None:
            rw = float(ext.attrib.get('cx', 0))
            rh = float(ext.attrib.get('cy', 0))
        flipH = xfrm.attrib.get('flipH') == '1'
        flipV = xfrm.attrib.get('flipV') == '1'

    px, py, pw, ph = map_rect(emu_to_px(rx), emu_to_px(ry), emu_to_px(rw), emu_to_px(rh), tf)

    if tag == 'grpSp':
        chOff = xfrm.find('a:chOff', NS) if xfrm is not None else None
        chExt = xfrm.find('a:chExt', NS) if xfrm is not None else None
        chx = emu_to_px(chOff.attrib.get('x', 0)) if chOff is not None else 0.0
        chy = emu_to_px(chOff.attrib.get('y', 0)) if chOff is not None else 0.0
        chcw = emu_to_px(chExt.attrib.get('cx', 1)) if chExt is not None else pw
        chch = emu_to_px(chExt.attrib.get('cy', 1)) if chExt is not None else ph
        sx = (pw / chcw) if chcw else 1.0
        sy = (ph / chch) if chch else 1.0
        child_tf = {'gx': px, 'gy': py, 'chx': chx, 'chy': chy, 'sx': sx, 'sy': sy}
        children = []
        for ch in el:
            ctag = ch.tag.split('}')[-1]
            if ctag in ('sp', 'grpSp', 'pic', 'cxnSp', 'graphicFrame'):
                parsed_ch = parse_raw_element(ch, rels_map, deck_name, child_tf)
                if parsed_ch:
                    if parsed_ch['rawType'] == 'group':
                        children.extend(parsed_ch['children'])
                    else:
                        children.append(parsed_ch)
        return {
            'rawType': 'group',
            'name': raw_name,
            'x': px, 'y': py, 'w': pw, 'h': ph,
            'children': children
        }

    if tag == 'pic':
        pcs_cid, pcs_ctype, role, clean_name, locked = _extract_pcs_tag(raw_name, 'image', 'image')
        blip = el.find('.//a:blip', NS)
        img_file = None
        if blip is not None:
            rid = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            target = rels_map.get(rid, '')
            if target:
                img_file = f"/assets/media/{deck_name}/{os.path.basename(target)}"
        return _attach_pcs_meta({
            'rawType': 'image',
            'role': role,
            'name': clean_name,
            'x': px, 'y': py, 'w': pw, 'h': ph,
            'src': img_file
        }, pcs_cid, pcs_ctype, locked)

    if tag == 'graphicFrame':
        tbl = el.find('.//a:tbl', NS)
        if tbl is not None:
            pcs_cid, pcs_ctype, role, clean_name, locked = _extract_pcs_tag(raw_name, 'table', 'table')
            gridCols = [emu_to_px(c.attrib.get('w', 0)) for c in tbl.findall('./a:tblGrid/a:gridCol', NS)]
            rows = []
            rowHeights = []
            for tr in tbl.findall('./a:tr', NS):
                rowHeights.append(emu_to_px(tr.attrib.get('h', 0)))
                row_cells = []
                for tc in tbl_row_cells(tr):
                    row_cells.append(tc)
                rows.append(row_cells)
            return _attach_pcs_meta({
                'rawType': 'table',
                'role': role,
                'name': clean_name,
                'x': px, 'y': py, 'w': pw, 'h': ph,
                'colWidths': gridCols,
                'rowHeights': rowHeights,
                'rows': rows
            }, pcs_cid, pcs_ctype, locked)
        return None

    pcs_cid, pcs_ctype, role, clean_name, locked = _extract_pcs_tag(raw_name, 'shape', 'shape')
    spPr = el.find('./p:spPr', NS)
    geom = 'line' if tag == 'cxnSp' else 'rect'
    adj = None
    fill = None
    borderColor = None
    borderWidth = 0.0
    headEnd = None
    tailEnd = None
    dashStyle = None
    if spPr is not None:
        prstGeom = spPr.find('./a:prstGeom', NS)
        if prstGeom is not None:
            raw_geom = prstGeom.attrib.get('prst', geom)
            geom = GEOM_ALIAS.get(raw_geom, raw_geom)
            gd = prstGeom.find('./a:avLst/a:gd', NS)
            if gd is not None and 'fmla' in gd.attrib:
                fmla = gd.attrib['fmla']
                if fmla.startswith('val '):
                    try:
                        adj = int(fmla.replace('val ', ''))
                    except Exception:
                        pass
        sf = spPr.find('./a:solidFill', NS)
        if sf is not None:
            fill = resolve_color(sf)
        ln = spPr.find('./a:ln', NS)
        if ln is not None and ln.find('./a:noFill', NS) is None:
            borderWidth = emu_to_px(ln.attrib.get('w', 12700))
            lsf = ln.find('./a:solidFill', NS)
            if lsf is not None:
                borderColor = resolve_color(lsf)
            pd = ln.find('./a:prstDash', NS)
            if pd is not None:
                d_val = pd.attrib.get('val')
                if d_val and d_val != 'solid':
                    dashStyle = d_val
            he = ln.find('./a:headEnd', NS)
            if he is not None and he.attrib.get('type', 'none') != 'none':
                headEnd = he.attrib.get('type')
            te = ln.find('./a:tailEnd', NS)
            if te is not None and te.attrib.get('type', 'none') != 'none':
                tailEnd = te.attrib.get('type')

    tx = parse_txBody(el.find('./p:txBody', NS))
    res = {
        'rawType': 'shape',
        'role': role,
        'name': clean_name,
        'x': px, 'y': py, 'w': pw, 'h': ph,
        'geom': geom,
        'adj': adj,
        'flipH': flipH,
        'flipV': flipV,
        'fill': fill,
        'borderColor': borderColor,
        'borderWidth': borderWidth,
        'headEnd': headEnd,
        'tailEnd': tailEnd,
        'textBody': tx
    }
    if dashStyle:
        res['dashStyle'] = dashStyle
    return _attach_pcs_meta(res, pcs_cid, pcs_ctype, locked)


def tbl_row_cells(tr):
    cells = []
    for tc in tr.findall('./a:tc', NS):
        tx = parse_txBody(tc.find('./a:txBody', NS))
        tcPr = tc.find('./a:tcPr', NS)
        fill = None
        border = {}
        padding = {'left': 7.2, 'top': 3.6, 'right': 7.2, 'bottom': 3.6}
        valign = 'middle'
        if tcPr is not None:
            sf = tcPr.find('./a:solidFill', NS)
            if sf is not None:
                fill = resolve_color(sf)
            anc = tcPr.attrib.get('anchor')
            if anc == 't':
                valign = 'top'
            elif anc == 'b':
                valign = 'bottom'
            for side, attr in [('left', 'marL'), ('top', 'marT'), ('right', 'marR'), ('bottom', 'marB')]:
                if attr in tcPr.attrib:
                    padding[side] = emu_to_px(tcPr.attrib[attr])
            for bname, btag in [('left', 'lnL'), ('right', 'lnR'), ('top', 'lnT'), ('bottom', 'lnB')]:
                ln = tcPr.find(f'./a:{btag}', NS)
                if ln is not None and ln.find('./a:noFill', NS) is None:
                    bw = emu_to_px(ln.attrib.get('w', 9525))
                    bc = resolve_color(ln.find('./a:solidFill', NS))
                    if bc:
                        border[bname] = {'width': bw, 'color': bc}

        cell_text = '\n'.join(p['text'] for p in tx['paragraphs']) if tx and tx['paragraphs'] else ''
        first_run = tx['paragraphs'][0]['runs'][0] if (tx and tx['paragraphs'] and tx['paragraphs'][0]['runs']) else {}
        align = tx['paragraphs'][0]['align'] if (tx and tx['paragraphs']) else 'left'
        cells.append({
            'text': cell_text,
            'fill': fill,
            'color': first_run.get('color') or '#333333',
            'fontSize': first_run.get('fontSize') or 10.0,
            'bold': first_run.get('bold', False),
            'fontFamily': first_run.get('fontFamily') or '微软雅黑',
            'align': align,
            'valign': valign,
            'padding': padding,
            'border': border,
            'textBody': tx
        })
    return cells


def get_element_text(el):
    if el.get('rawType') == 'table':
        return ' | '.join(c['text'] for c in el['rows'][0]) if el.get('rows') else ''
    tx = el.get('textBody')
    if not tx or not tx.get('paragraphs'):
        return ''
    return '\n'.join(p['text'] for p in tx['paragraphs']).strip()


def compute_bounds(elems):
    if not elems:
        return 0.0, 0.0, 100.0, 100.0
    min_x = min(e['x'] for e in elems)
    min_y = min(e['y'] for e in elems)
    max_x = max(e['x'] + e['w'] for e in elems)
    max_y = max(e['y'] + e['h'] for e in elems)
    return round(min_x, 2), round(min_y, 2), round(max(max_x - min_x, 1.0), 2), round(max(max_y - min_y, 1.0), 2)


def rect_contains_center(container, item, tol=8.0):
    cx = item['x'] + item['w'] / 2.0
    cy = item['y'] + item['h'] / 2.0
    return (container['x'] - tol <= cx <= container['x'] + container['w'] + tol and
            container['y'] - tol <= cy <= container['y'] + container['h'] + tol)


def make_component(comp_id, comp_type, elems, sub_type='default', custom_name=None):
    flat = []
    for e in elems:
        if e['rawType'] == 'group':
            for ch in e['children']:
                flat.append(copy.deepcopy(ch))
        else:
            flat.append(copy.deepcopy(e))

    bx, by, bw, bh = compute_bounds(flat)

    locked_flags = []
    for i, ch in enumerate(flat):
        ch.pop('_pcsCompId', None)
        ch.pop('_pcsCompType', None)
        locked = bool(ch.pop('_pcsLockedRole', False))
        locked_flags.append(locked)
        ch['id'] = f"{comp_id}_ch{i+1}"
        ch['relX'] = round(ch['x'] - bx, 2)
        ch['relY'] = round(ch['y'] - by, 2)
        ch['relW'] = round(ch['w'], 2)
        ch['relH'] = round(ch['h'], 2)

    style = {
        'fill': None,
        'borderColor': None,
        'borderWidth': 0.0,
        'borderRadius': 8.0,
        'titleColor': '#333333',
        'titleSize': 12.0,
        'titleBold': True,
        'bodyColor': '#333333',
        'bodySize': 10.0,
        'accentColor': '#F26B21',
        'fontFamily': '微软雅黑'
    }
    layout = {
        'paddingX': 10.0,
        'paddingY': 8.0,
        'headerGap': 6.0,
        'itemGap': 5.0,
        'lineHeight': 1.3,
        'align': 'left',
        'valign': 'top'
    }
    content = {
        'title': '',
        'subtitle': '',
        'prefix': '',
        'items': [],
        'headers': [],
        'rows': []
    }

    has_locked_roles = any(locked_flags)
    containers = [c for c in flat if c['rawType'] == 'shape' and (c.get('fill') or c.get('borderColor')) and c.get('geom') not in ('line', 'elbowConnector')]
    if containers and not has_locked_roles:
        main_bg = max(containers, key=lambda c: c['w'] * c['h'])
        if main_bg['h'] > 12:
            main_bg['role'] = 'container'
            style['fill'] = main_bg.get('fill')
            style['borderColor'] = main_bg.get('borderColor')
            style['borderWidth'] = main_bg.get('borderWidth') or 0.0
            style['borderRadius'] = 10.0 if main_bg.get('geom') == 'roundRect' else 0.0
        for c in containers:
            if c is not main_bg and c['h'] <= 8.0 and c['w'] > 100:
                c['role'] = 'divider'
                c['name'] = 'divider'
                if c.get('fill'):
                    style['accentColor'] = c['fill']

    text_shapes = [c for c in flat if c['rawType'] == 'shape' and get_element_text(c)]
    text_shapes_sorted = sorted(text_shapes, key=lambda c: (c['y'], c['x']))

    if comp_type == 'slide-header':
        for c in flat:
            txt = get_element_text(c)
            if not txt:
                if c.get('geom') in ('line', 'elbowConnector'):
                    c['role'] = 'divider'
                elif not has_locked_roles:
                    c['role'] = 'shape'
                continue
            if c['x'] > 820 and c['y'] < 45:
                c['role'] = 'page-num'
                content['pageNumber'] = txt
            elif c['y'] < 35 and c['w'] < 260 and (c.get('fill') or c.get('borderColor')):
                c['role'] = 'step-box'
                content['sectionTag'] = txt
            elif not content['title']:
                c['role'] = 'title'
                content['title'] = txt
                r0 = c['textBody']['paragraphs'][0]['runs'][0]
                style['titleSize'] = r0.get('fontSize') or 20.0
                style['titleColor'] = r0.get('color') or '#333333'
            else:
                c['role'] = 'subtitle'
                content['subtitle'] = txt
                r0 = c['textBody']['paragraphs'][0]['runs'][0]
                style['bodySize'] = r0.get('fontSize') or 10.5
                style['bodyColor'] = r0.get('color') or '#666666'
        title_sh = next((c for c in flat if c.get('role') == 'title'), None)
        sub_sh = next((c for c in flat if c.get('role') == 'subtitle'), None)
        if title_sh and sub_sh:
            layout['headerGap'] = round(max(0.0, sub_sh['y'] - (title_sh['y'] + title_sh['h'])), 1)

    elif comp_type == 'footer-banner':
        for c in text_shapes_sorted:
            if not has_locked_roles and c.get('role') != 'container':
                c['role'] = 'body'
            paras = c['textBody']['paragraphs']
            full_t = '\n'.join(p['text'] for p in paras)
            if '：' in full_t:
                parts = full_t.split('：', 1)
                content['prefix'] = parts[0] + '：'
                content['title'] = parts[0] + '：'
                content['subtitle'] = parts[1].strip()
            else:
                content['title'] = full_t
            if paras and paras[0]['runs']:
                r0 = paras[0]['runs'][0]
                style['titleColor'] = r0.get('color') or '#D45500'
                style['titleSize'] = r0.get('fontSize') or 10.5
                if len(paras[0]['runs']) > 1:
                    r1 = paras[0]['runs'][1]
                    style['bodyColor'] = r1.get('color') or '#333333'
                    style['bodySize'] = r1.get('fontSize') or 10.0

    elif comp_type == 'data-table':
        tbl = next((c for c in flat if c['rawType'] == 'table'), None)
        if tbl:
            tbl['role'] = 'table'
            if tbl['rows']:
                content['headers'] = [cell['text'] for cell in tbl['rows'][0]]
                content['rows'] = [[cell['text'] for cell in r] for r in tbl['rows'][1:]]
                h_fill = tbl['rows'][0][0].get('fill')
                if h_fill:
                    style['accentColor'] = h_fill
                    style['fill'] = '#FFFFFF'
                style['titleColor'] = tbl['rows'][0][0].get('color') or '#FFFFFF'
                style['titleSize'] = tbl['rows'][0][0].get('fontSize') or 10.5
                if len(tbl['rows']) > 1 and tbl['rows'][1]:
                    style['bodyColor'] = tbl['rows'][1][0].get('color') or '#333333'
                    style['bodySize'] = tbl['rows'][1][0].get('fontSize') or 9.5

    elif comp_type == 'info-card':
        if len(text_shapes_sorted) == 1:
            sh = text_shapes_sorted[0]
            paras = sh['textBody']['paragraphs']
            if sh['textBody'].get('padding'):
                layout['paddingX'] = round(sh['textBody']['padding'].get('left', 10.0), 1)
                layout['paddingY'] = round(sh['textBody']['padding'].get('top', 8.0), 1)
            if paras:
                content['title'] = paras[0]['text']
                if paras[0]['runs']:
                    style['titleSize'] = paras[0]['runs'][0].get('fontSize') or 12.0
                    style['titleColor'] = paras[0]['runs'][0].get('color') or '#333333'
                layout['headerGap'] = paras[0].get('spaceAfter') or 6.0
                content['items'] = [p['text'] for p in paras[1:]]
                if len(paras) > 1:
                    layout['itemGap'] = paras[1].get('spaceAfter') or 4.0
                    if paras[1]['runs']:
                        style['bodySize'] = paras[1]['runs'][0].get('fontSize') or 10.0
                        style['bodyColor'] = paras[1]['runs'][0].get('color') or '#333333'
        elif len(text_shapes_sorted) >= 2:
            t_sh = text_shapes_sorted[0]
            if not has_locked_roles:
                t_sh['role'] = 'title'
            content['title'] = get_element_text(t_sh)
            if t_sh['textBody']['paragraphs'] and t_sh['textBody']['paragraphs'][0]['runs']:
                r0 = t_sh['textBody']['paragraphs'][0]['runs'][0]
                style['titleSize'] = r0.get('fontSize') or 12.0
                style['titleColor'] = r0.get('color') or '#D45500'
            layout['paddingX'] = round(max(4.0, t_sh['relX']), 1)
            layout['paddingY'] = round(max(4.0, t_sh['relY']), 1)

            items = []
            for b_sh in text_shapes_sorted[1:]:
                if not has_locked_roles:
                    b_sh['role'] = 'body'
                for p in b_sh['textBody']['paragraphs']:
                    items.append(p['text'])
                    if p['runs']:
                        style['bodySize'] = p['runs'][0].get('fontSize') or 10.5
                        style['bodyColor'] = p['runs'][0].get('color') or '#333333'
                    if p.get('spaceAfter'):
                        layout['itemGap'] = p['spaceAfter']
            content['items'] = items
            b0 = text_shapes_sorted[1]
            layout['headerGap'] = round(max(2.0, b0['y'] - (t_sh['y'] + t_sh['h'])), 1)

    elif comp_type == 'kpi-card':
        for c in flat:
            if c['rawType'] == 'image':
                c['role'] = 'image'
                content['image'] = c.get('src')
            elif c['rawType'] == 'shape':
                paras = c['textBody']['paragraphs'] if c.get('textBody') else []
                if c['relY'] < 50 and paras:
                    c['role'] = 'title'
                    content['title'] = paras[0]['text']
                    content['subtitle'] = paras[1]['text'] if len(paras) > 1 else ''
                    style['fill'] = c.get('fill') or '#FFF5EE'
                    style['borderColor'] = c.get('borderColor') or '#F26B21'
                elif paras:
                    c['role'] = 'metric-box'
                    content['metricValue'] = paras[0]['text']
                    content['metricLabel'] = paras[1]['text'] if len(paras) > 1 else ''
                    content['items'] = [p['text'] for p in paras[2:]]

    elif comp_type == 'process-flow':
        steps = []
        for c in flat:
            if c['rawType'] == 'shape' and c.get('geom') in ('line', 'elbowConnector'):
                if not has_locked_roles:
                    c['role'] = 'connector'
            elif c['rawType'] == 'shape' and get_element_text(c):
                txt = get_element_text(c)
                steps.append(txt)
                if not has_locked_roles and c.get('role') != 'container':
                    c['role'] = 'step-box'
        step_boxes = sorted([c for c in flat if c.get('role') == 'step-box'], key=lambda x: x['relX'])
        if len(step_boxes) >= 2:
            layout['itemGap'] = round(max(2.0, step_boxes[1]['relX'] - (step_boxes[0]['relX'] + step_boxes[0]['relW'])), 1)
        content['items'] = steps
        content['title'] = 'process-flow'

    elif comp_type == 'toc-list':
        items = []
        for c in text_shapes_sorted:
            txt = get_element_text(c)
            if re.match(r'^0\d$', txt):
                c['role'] = 'step-num'
            elif c['x'] < 350:
                c['role'] = 'title'
                items.append(txt)
            else:
                c['role'] = 'subtitle'
        for c in flat:
            if c.get('geom') in ('line', 'elbowConnector'):
                c['role'] = 'divider'
        content['title'] = 'toc-list'
        content['items'] = items
        layout['itemGap'] = 24.0

    elif comp_type == 'tag-badge':
        txts = [get_element_text(c) for c in text_shapes_sorted if get_element_text(c)]
        content['title'] = txts[0] if txts else 'tag-badge'
        content['subtitle'] = ' | '.join(txts[1:]) if len(txts) > 1 else ''
        if not has_locked_roles:
            for idx_c, c in enumerate(text_shapes_sorted):
                c['role'] = 'title' if idx_c == 0 else 'subtitle'

    elif comp_type == 'image-frame':
        imgs = [c.get('src') for c in flat if c['rawType'] == 'image']
        txts = [get_element_text(c) for c in text_shapes_sorted if get_element_text(c)]
        content['title'] = txts[0] if txts else 'image-frame'
        content['items'] = txts[1:] if len(txts) > 1 else []
        content['images'] = imgs

    elif comp_type == 'cover-divider':
        txts = [get_element_text(c) for c in text_shapes_sorted if get_element_text(c)]
        best_title = txts[0] if txts else 'cover-divider'
        max_sz = 0
        for c in text_shapes_sorted:
            if c.get('textBody') and c['textBody'].get('paragraphs'):
                for p in c['textBody']['paragraphs']:
                    for r in p.get('runs', []):
                        if (r.get('fontSize') or 0) > max_sz:
                            max_sz = r['fontSize']
                            best_title = p['text']
        content['title'] = best_title
        content['subtitle'] = txts[1] if len(txts) > 1 else ''
        content['items'] = txts

    elif comp_type in ('vertical-stack', 'decision-gate', 'stage-funnel', 'iteration-lanes', 'rule-checklist'):
        title_node = next((c for c in text_shapes_sorted if c.get('role') in ('header-bar', 'gate-node', 'title', 'section-bar')), None)
        if title_node is not None:
            content['title'] = get_element_text(title_node)
            txts = [get_element_text(c) for c in text_shapes_sorted if c is not title_node and get_element_text(c)]
        else:
            txts = [get_element_text(c) for c in text_shapes_sorted if get_element_text(c)]
            content['title'] = txts[0] if txts else comp_type
            txts = txts[1:]
        content['items'] = txts
        if title_node and title_node.get('textBody') and title_node['textBody'].get('paragraphs'):
            runs0 = title_node['textBody']['paragraphs'][0].get('runs') or []
            if runs0 and runs0[0].get('fontSize'):
                style['titleSize'] = runs0[0]['fontSize']

    label_prefix = COMPONENT_TYPE_LABELS.get(comp_type, comp_type)
    short_title = (content.get('title') or (content['headers'][0] if content.get('headers') else '')).replace('\n', ' ')[:18]
    if custom_name:
        display_name = custom_name
    elif short_title and short_title != label_prefix:
        display_name = f"{label_prefix}: {short_title}"
    else:
        display_name = label_prefix

    return {
        'id': comp_id,
        'type': comp_type,
        'subType': sub_type,
        'name': display_name,
        'x': bx,
        'y': by,
        'w': bw,
        'h': bh,
        'layout': layout,
        'style': style,
        'content': content,
        'children': flat
    }


def cluster_slide_elements(slide_num, raw_elems, deck_name, total_slides=20):
    used = [False] * len(raw_elems)
    components = []
    comp_counter = 1

    def next_id():
        nonlocal comp_counter
        cid = f"{deck_name}_s{slide_num}_c{comp_counter}"
        comp_counter += 1
        return cid

    # Step 0: Prioritize exact reconstruction via [PCS:comp_id|comp_type|role] metadata tags
    pcs_groups = {}
    pcs_order = []
    for i, e in enumerate(raw_elems):
        cid = e.get('_pcsCompId')
        ctype = e.get('_pcsCompType')
        if cid and ctype:
            if cid not in pcs_groups:
                pcs_groups[cid] = {'type': ctype, 'indices': []}
                pcs_order.append(cid)
            pcs_groups[cid]['indices'].append(i)
            used[i] = True

    for pcs_cid in pcs_order:
        grp = pcs_groups[pcs_cid]
        grp_elems = [raw_elems[idx] for idx in grp['indices']]
        components.append(make_component(pcs_cid, grp['type'], grp_elems))

    if all(used):
        return components

    all_text = ' '.join(get_element_text(e) for i, e in enumerate(raw_elems) if not used[i])
    rem_elems = [e for i, e in enumerate(raw_elems) if not used[i]]
    has_huge_banner = any(e['rawType'] == 'shape' and e['w'] > 950 and e['h'] >= 100 and e.get('fill') for e in rem_elems)

    # 1. Cover / Section Divider / Ending slide detection (only when no PCS components already present)
    is_ending = (slide_num == total_slides and (len(rem_elems) <= 4 or any(k in all_text for k in ('谢谢', '批评指正', 'THANK', 'Thank'))))
    if not components and (slide_num == 1 or has_huge_banner or is_ending):
        tbl_indices = [i for i, e in enumerate(raw_elems) if not used[i] and e['rawType'] == 'table']
        non_tbl = [raw_elems[i] for i in range(len(raw_elems)) if not used[i] and i not in tbl_indices]
        if non_tbl:
            components.append(make_component(next_id(), 'cover-divider', non_tbl, sub_type='cover' if slide_num == 1 else 'section'))
        for ti in tbl_indices:
            components.append(make_component(next_id(), 'data-table', [raw_elems[ti]]))
        return components

    # 2. Extract standard slide-header
    header_indices = []
    for i, e in enumerate(raw_elems):
        if used[i] or e['rawType'] != 'shape':
            continue
        txt = get_element_text(e)
        if e['y'] < 12 and e['h'] <= 12 and not txt:
            header_indices.append(i)
        elif e.get('geom') in ('line', 'elbowConnector') and 105 <= e['y'] <= 128 and e['w'] > 650:
            header_indices.append(i)
        elif e['y'] < 35 and e['h'] <= 32 and e['w'] <= 260 and txt:
            header_indices.append(i)
        elif e['x'] > 840 and e['y'] < 45 and e['w'] <= 120 and txt:
            header_indices.append(i)
        elif 40 <= e['y'] <= 118 and e['x'] < 100 and e['w'] > 160 and not e.get('fill') and txt:
            header_indices.append(i)

    if header_indices:
        for i in header_indices:
            used[i] = True
        h_elems = [raw_elems[i] for i in header_indices]
        components.append(make_component(next_id(), 'slide-header', h_elems))

    # 3. General TOC Slide Detection
    num_badges = [i for i, e in enumerate(raw_elems) if not used[i] and e['rawType'] == 'shape' and re.match(r'^0[1-9]$', get_element_text(e).strip())]
    if len(num_badges) >= 3:
        toc_indices = [i for i in range(len(raw_elems)) if not used[i]]
        for i in toc_indices:
            used[i] = True
        components.append(make_component(next_id(), 'toc-list', [raw_elems[i] for i in toc_indices], custom_name='toc-list'))
        return components

    # 4. Extract all data-table elements
    for i, e in enumerate(raw_elems):
        if not used[i] and e['rawType'] == 'table':
            used[i] = True
            components.append(make_component(next_id(), 'data-table', [e]))

    # 5. Vertical KPI Showcase Cards (top title box + middle image + bottom metric box aligned vertically)
    unused_imgs = [i for i, e in enumerate(raw_elems) if not used[i] and e.get('rawType') == 'image' and 120 <= e['w'] <= 360]
    for img_idx in unused_imgs:
        if used[img_idx]:
            continue
        im = raw_elems[img_idx]
        col_indices = [
            i for i, e in enumerate(raw_elems)
            if not used[i] and abs(e['x'] - im['x']) < 12.0 and abs(e['w'] - im['w']) < 20.0
        ]
        if len(col_indices) == 3:
            for i in col_indices:
                used[i] = True
            components.append(make_component(next_id(), 'kpi-card', [raw_elems[i] for i in col_indices]))

    # 6. General Horizontal Process Flows detection
    horiz_conns = [i for i, e in enumerate(raw_elems) if not used[i] and e['rawType'] == 'shape' and e.get('geom') in ('line', 'elbowConnector') and e['w'] <= 60 and e['h'] <= 5]
    if len(horiz_conns) >= 2:
        avg_conn_y = sum(raw_elems[i]['y'] for i in horiz_conns) / len(horiz_conns)
        flow_indices = []
        for i, e in enumerate(raw_elems):
            if used[i]:
                continue
            cy = e['y'] + e['h'] / 2.0
            if abs(cy - avg_conn_y) <= 75 and e['h'] <= 165 and e['w'] <= 320:
                flow_indices.append(i)
        if len(flow_indices) >= 5:
            for i in flow_indices:
                used[i] = True
            components.append(make_component(next_id(), 'process-flow', [raw_elems[i] for i in flow_indices]))
    else:
        # 无连接线但同排存在 4 个以上等高窄圆角节点卡片时自动聚类为 process-flow
        cand_row = [i for i, e in enumerate(raw_elems) if not used[i] and 130.0 <= e['y'] <= 210.0 and 100 <= e['w'] <= 230 and 60 <= e['h'] <= 150]
        if len(cand_row) >= 4:
            for i in cand_row:
                used[i] = True
            components.append(make_component(next_id(), 'process-flow', [raw_elems[i] for i in cand_row]))

    # 7. Spatial Containment Clustering for Containers
    container_indices = []
    for i, e in enumerate(raw_elems):
        if used[i]:
            continue
        if e['rawType'] == 'shape' and e.get('geom') not in ('line', 'elbowConnector') and (e.get('fill') or e.get('borderColor')) and e['w'] > 40 and e['h'] > 18:
            container_indices.append(i)

    container_indices.sort(key=lambda idx: raw_elems[idx]['w'] * raw_elems[idx]['h'], reverse=True)

    clusters = []
    for ci in container_indices:
        if used[ci]:
            continue
        used[ci] = True
        c_elem = raw_elems[ci]
        member_indices = [ci]
        for j, other in enumerate(raw_elems):
            if used[j]:
                continue
            if other['rawType'] in ('shape', 'image', 'group'):
                if rect_contains_center(c_elem, other, tol=10.0) and (other['w'] * other['h'] <= c_elem['w'] * c_elem['h'] * 1.15):
                    used[j] = True
                    member_indices.append(j)
                elif (c_elem['h'] <= 36 and c_elem['w'] <= 200 and c_elem.get('fill') in ('#F26B21', '#F26421', '#1B365D', '#7A2048') and
                      other['rawType'] == 'shape' and not other.get('fill') and abs(other['y'] - c_elem['y']) < 12 and
                      0 <= (other['x'] - (c_elem['x'] + c_elem['w'])) <= 25 and other['h'] <= 40):
                    used[j] = True
                    member_indices.append(j)
        clusters.append(member_indices)

    for member_indices in clusters:
        member_indices.sort()
        c_elems = [raw_elems[idx] for idx in member_indices]
        bx, by, bw, bh = compute_bounds(c_elems)
        has_img = any(e['rawType'] == 'image' or (e['rawType'] == 'group' and any(ch['rawType'] == 'image' for ch in e['children'])) for e in c_elems)
        combined_txt = ' '.join(get_element_text(e) for e in c_elems)

        if has_img:
            ctype = 'image-frame'
        elif (by >= 520 and bw >= 600 and bh <= 95) or (by >= 485 and bw >= 600 and bh <= 70) or any(k in combined_txt[:14] for k in ('说明与结论', '执行边界', '边界说明', '适用判断', '管理边界', '控制边界', '使用场景：', '问题导向定位', '核心假说主线', '文献切入点', '可行性保障', '前期准备进度', '政策落脚点')):
            ctype = 'footer-banner'
        elif bh <= 42 and bw <= 420 and any(e.get('fill') in ('#F26B21', '#F26421', '#1B365D', '#7A2048') for e in c_elems if e['rawType'] == 'shape'):
            ctype = 'tag-badge'
        else:
            ctype = 'info-card'

        components.append(make_component(next_id(), ctype, c_elems))

    # 8. Remaining standalone elements
    for i, e in enumerate(raw_elems):
        if used[i]:
            continue
        used[i] = True
        if e['rawType'] == 'group':
            has_img = any(ch['rawType'] == 'image' for ch in e['children'])
            ctype = 'image-frame' if has_img else ('tag-badge' if e['h'] <= 45 and e['w'] < 350 else ('footer-banner' if e['h'] <= 55 and e['w'] >= 600 else 'info-card'))
            components.append(make_component(next_id(), ctype, [e]))
        elif e['rawType'] == 'image':
            components.append(make_component(next_id(), 'image-frame', [e]))
        elif e['rawType'] == 'shape':
            txt = get_element_text(e)
            if not txt and e.get('geom') in ('line', 'elbowConnector'):
                components.append(make_component(next_id(), 'tag-badge', [e], sub_type='connector', custom_name='tag-badge: connector'))
            elif e['h'] <= 36 and len(txt) <= 20:
                components.append(make_component(next_id(), 'tag-badge', [e]))
            else:
                components.append(make_component(next_id(), 'info-card', [e]))

    def sort_key(comp):
        if comp['type'] == 'slide-header':
            return (0, comp['y'], comp['x'])
        if comp['type'] == 'footer-banner':
            return (2, comp['y'], comp['x'])
        return (1, round(comp['y'] / 20.0), comp['x'])

    components.sort(key=sort_key)
    return components


def convert_pptx_to_deck(pptx_path, deck_id, deck_title=None, out_json_path=None):
    if not deck_title:
        deck_title = os.path.splitext(os.path.basename(pptx_path))[0]
    if not out_json_path:
        out_json_path = os.path.join(BASE_DIR, 'decks', f'{deck_id}.json')

    media_out_dir = os.path.join(ASSETS_MEDIA_DIR, deck_id)
    os.makedirs(media_out_dir, exist_ok=True)

    with zipfile.ZipFile(pptx_path, 'r') as z:
        for f in z.namelist():
            if f.startswith('ppt/media/'):
                fname = os.path.basename(f)
                if fname:
                    with open(os.path.join(media_out_dir, fname), 'wb') as out_f:
                        out_f.write(z.read(f))

        pres_xml = ET.fromstring(z.read('ppt/presentation.xml'))
        sldSz = pres_xml.find('.//p:sldSz', NS)
        emu_cx = int(sldSz.attrib.get('cx', 9721850)) if sldSz is not None else 9721850
        emu_cy = int(sldSz.attrib.get('cy', 6480175)) if sldSz is not None else 6480175
        width_px = emu_to_px(emu_cx)
        height_px = emu_to_px(emu_cy)

        slide_files = sorted(
            [f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')],
            key=lambda x: int(x.replace('ppt/slides/slide', '').replace('.xml', ''))
        )
        total_slides = len(slide_files)

        slides = []
        type_summary = {}
        for idx, sf in enumerate(slide_files, 1):
            rels_path = f"ppt/slides/_rels/slide{idx}.xml.rels"
            rels_map = {}
            if rels_path in z.namelist():
                r_xml = ET.fromstring(z.read(rels_path))
                for rel in r_xml:
                    rels_map[rel.attrib.get('Id')] = rel.attrib.get('Target')

            s_xml = ET.fromstring(z.read(sf))

            bg_data = {'type': 'color', 'color': '#FFFFFF', 'image': None}
            bg_el = s_xml.find('.//p:bg', NS)
            if bg_el is not None:
                blip = bg_el.find('.//a:blip', NS)
                if blip is not None:
                    rid = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if rid in rels_map:
                        bg_data = {
                            'type': 'image',
                            'color': '#FFFFFF',
                            'image': f"/assets/media/{deck_id}/{os.path.basename(rels_map[rid])}"
                        }
                else:
                    sf_bg = bg_el.find('.//a:solidFill', NS)
                    if sf_bg is not None:
                        c = resolve_color(sf_bg)
                        if c:
                            bg_data = {'type': 'color', 'color': c, 'image': None}

            spTree = s_xml.find('.//p:cSld/p:spTree', NS)
            raw_elems = []
            if spTree is not None:
                for child in spTree:
                    ctag = child.tag.split('}')[-1]
                    if ctag in ('sp', 'grpSp', 'pic', 'cxnSp', 'graphicFrame'):
                        parsed = parse_raw_element(child, rels_map, deck_id)
                        if parsed:
                            raw_elems.append(parsed)

            comps = cluster_slide_elements(idx, raw_elems, deck_id, total_slides)
            for c in comps:
                type_summary[c['type']] = type_summary.get(c['type'], 0) + 1

            slide_title = f"第 {idx} 页"
            for c in comps:
                if c['type'] in ('slide-header', 'cover-divider') and c['content'].get('title'):
                    slide_title = c['content']['title'].replace('\n', ' ')
                    break

            slides.append({
                'id': f"{deck_id}_slide_{idx}",
                'index': idx,
                'title': slide_title,
                'background': bg_data,
                'components': comps
            })

    deck = {
        'id': deck_id,
        'title': deck_title,
        'sourceFile': os.path.abspath(pptx_path),
        'canvas': {
            'width': width_px,
            'height': height_px,
            'emuCx': emu_cx,
            'emuCy': emu_cy,
            'gridSize': 8,
            'showGrid': False
        },
        'theme': {
            'name': '自适应工程主题',
            'primaryColor': '#F26B21',
            'secondaryColor': '#1B365D',
            'textColor': '#333333',
            'mutedColor': '#666666',
            'fontFamily': '微软雅黑'
        },
        'componentStats': type_summary,
        'slides': slides
    }

    os.makedirs(os.path.dirname(os.path.abspath(out_json_path)), exist_ok=True)
    with open(out_json_path, 'w', encoding='utf-8') as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
    print(f"Converted {pptx_path} -> {out_json_path}: {len(slides)} slides, stats={type_summary}")
    return deck
