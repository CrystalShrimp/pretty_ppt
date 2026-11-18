import copy
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
BUILTIN_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, 'builtin')
LOCAL_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, 'local')

os.makedirs(BUILTIN_TEMPLATES_DIR, exist_ok=True)
os.makedirs(LOCAL_TEMPLATES_DIR, exist_ok=True)

DEFAULT_TEMPLATE_ID = 'academic'

SEMANTIC_PROTECTED_COLORS = {
    '#16A34A', '#F0FDF4', '#15803D', '#2E7D32', '#F1F8F4',
    '#D97706', '#FFFBEB', '#B45309', '#DC2626', '#FEF2F2',
    '#B91C1C', '#C62828', '#FFF3F3'
}

KNOWN_BRAND_PRIMARY = {
    '#1B365D', '#1E6CFF', '#0D9488', '#F26B21', '#F26421',
    '#7B32D9', '#B45309', '#234370'
}
KNOWN_BRAND_ACCENT = {
    '#7A2048', '#00B4D8', '#9B1B3E', '#F39A1E', '#D97706'
}
KNOWN_TITLE_COLORS = KNOWN_BRAND_PRIMARY | KNOWN_BRAND_ACCENT | {
    '#2B547E', '#0F4CD6', '#0F766E', '#134E4A', '#D45500', '#DB5312', '#5B18B2'
}
KNOWN_CARD_BG = {
    '#F6F8FB', '#F4F6F9', '#EDF2F8', '#F0F5FF', '#EAF2FF', '#EFF6FF',
    '#F0FDFA', '#CCFBF1', '#FFF5EE', '#FFF2E6', '#FFF7F0', '#FFF7ED',
    '#FFF8F3', '#F7F0FF', '#F3E8FF'
}
KNOWN_ALT_BG = {
    '#FAF4F6', '#FDF2F5', '#ECFEFF', '#FEF3C7', '#FFFBEB'
}
KNOWN_BORDER_COLORS = {
    '#CBD5E1', '#BFDBFE', '#99F6E4', '#1B365D', '#1E6CFF', '#0D9488',
    '#F26B21', '#7A2048', '#E2C6D1'
}


def _sanitize_template_id(raw_id):
    cleaned = re.sub(r'[^a-zA-Z0-9_-]+', '_', str(raw_id or '').strip()).strip('_').lower()
    return cleaned or 'custom_template'


def _load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_templates():
    """列出所有内置模板与本地私有模板（默认把 isDefault / academic 排在最前）。"""
    items = []
    seen = set()
    for source, folder in [('builtin', BUILTIN_TEMPLATES_DIR), ('local', LOCAL_TEMPLATES_DIR)]:
        if not os.path.isdir(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            if not fname.endswith('.json') or fname.startswith('_'):
                continue
            fpath = os.path.join(folder, fname)
            try:
                tpl = _load_json(fpath)
                tid = tpl.get('id') or fname[:-5]
                if tid in seen:
                    continue
                seen.add(tid)
                tpl_copy = copy.deepcopy(tpl)
                tpl_copy['id'] = tid
                tpl_copy['source'] = source
                items.append(tpl_copy)
            except Exception:
                continue

    items.sort(key=lambda t: (
        0 if t.get('id') == DEFAULT_TEMPLATE_ID else 1,
        0 if t.get('isDefault') else 1,
        0 if t.get('source') == 'builtin' else 1,
        t.get('id', '')
    ))
    return items


def get_template(template_id=None):
    """按 ID 获取模板完整定义，未指定或未找到时回退至默认学术模板。"""
    tid = str(template_id or DEFAULT_TEMPLATE_ID).strip()
    for source, folder in [('local', LOCAL_TEMPLATES_DIR), ('builtin', BUILTIN_TEMPLATES_DIR)]:
        cand = os.path.join(folder, f"{tid}.json")
        if os.path.isfile(cand):
            tpl = _load_json(cand)
            tpl['id'] = tpl.get('id') or tid
            tpl['source'] = source
            return tpl

    fallback = os.path.join(BUILTIN_TEMPLATES_DIR, f"{DEFAULT_TEMPLATE_ID}.json")
    if os.path.isfile(fallback):
        tpl = _load_json(fallback)
        tpl['id'] = DEFAULT_TEMPLATE_ID
        tpl['source'] = 'builtin'
        return tpl

    return {
        'id': DEFAULT_TEMPLATE_ID,
        'name': '学术深蓝 (默认)',
        'source': 'builtin',
        'isDefault': True,
        'canvas': {'width': 1020.67, 'height': 680.33, 'emuCx': 9721850, 'emuCy': 6480175},
        'palette': {
            'primary': '#1B365D',
            'secondary': '#2B547E',
            'accent': '#7A2048',
            'titleColor': '#1B365D',
            'bodyColor': '#334155',
            'mutedColor': '#64748B',
            'cardBg': '#F6F8FB',
            'cardAltBg': '#FAF4F6',
            'cardBorder': '#CBD5E1',
            'bannerBg': '#EDF2F8',
            'bannerBorder': '#1B365D',
            'tableHeaderBg': '#1B365D',
            'tableHeaderFg': '#FFFFFF',
            'tableStripeBg': '#F4F6F9',
            'fontFamily': '微软雅黑'
        },
        'backgrounds': {
            'cover': {'type': 'color', 'color': '#FFFFFF', 'image': None},
            'body': {'type': 'color', 'color': '#FFFFFF', 'image': None}
        },
        'skeleton': {
            'coverStyle': 'academic_banner',
            'headerStyle': 'academic_ribbon',
            'cardTopBar': True,
            'defaultMarginX': 48.0,
            'contentTopY': 134.0,
            'footerY': 596.0
        }
    }


def save_custom_template(tpl_data):
    """保存自定义模板到 templates/local/（严禁修改 builtin 模板）。"""
    tid = _sanitize_template_id(tpl_data.get('id') or tpl_data.get('name'))
    base = copy.deepcopy(get_template(DEFAULT_TEMPLATE_ID))
    merged = {
        'id': tid,
        'name': tpl_data.get('name') or tid,
        'description': tpl_data.get('description') or '用户自定义本地模板',
        'isDefault': False,
        'canvas': tpl_data.get('canvas') or base['canvas'],
        'palette': {**base['palette'], **(tpl_data.get('palette') or {})},
        'backgrounds': tpl_data.get('backgrounds') or base['backgrounds'],
        'skeleton': {**base['skeleton'], **(tpl_data.get('skeleton') or {})}
    }
    out_path = os.path.join(LOCAL_TEMPLATES_DIR, f"{tid}.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    merged['source'] = 'local'
    return merged


def delete_custom_template(template_id):
    """删除本地自定义模板（内置模板不可删除）。"""
    tid = _sanitize_template_id(template_id)
    local_path = os.path.join(LOCAL_TEMPLATES_DIR, f"{tid}.json")
    builtin_path = os.path.join(BUILTIN_TEMPLATES_DIR, f"{tid}.json")
    if os.path.isfile(local_path):
        os.remove(local_path)
        return True
    if os.path.isfile(builtin_path):
        raise ValueError(f"内置模板 '{tid}' 不可删除")
    raise FileNotFoundError(f"未找到本地模板 '{tid}'")


def extract_template_from_deck(deck, template_id, name, description=''):
    """从现有 Deck 中提取主色调、背景图与骨架风格，生成本地自定义模板。"""
    base = get_template(deck.get('templateId') or DEFAULT_TEMPLATE_ID)
    theme = deck.get('theme') or {}
    palette = copy.deepcopy(base['palette'])
    if theme.get('primaryColor'):
        palette['primary'] = theme['primaryColor']
        palette['tableHeaderBg'] = theme['primaryColor']
        palette['bannerBorder'] = theme['primaryColor']
    if theme.get('secondaryColor'):
        palette['secondary'] = theme['secondaryColor']
    if theme.get('accentColor'):
        palette['accent'] = theme['accentColor']
    if theme.get('textColor'):
        palette['bodyColor'] = theme['textColor']
    if theme.get('mutedColor'):
        palette['mutedColor'] = theme['mutedColor']
    if theme.get('fontFamily'):
        palette['fontFamily'] = theme['fontFamily']

    cover_bg = copy.deepcopy(base['backgrounds']['cover'])
    body_bg = copy.deepcopy(base['backgrounds']['body'])
    slides = deck.get('slides') or []
    for s in slides:
        bg = s.get('background') or {}
        has_cover = any(c.get('type') == 'cover-divider' for c in (s.get('components') or []))
        if has_cover:
            cover_bg = copy.deepcopy(bg) if bg else cover_bg
        elif bg:
            body_bg = copy.deepcopy(bg)
            break

    # 从首张信息卡片提取卡片默认样式
    for s in slides:
        for c in (s.get('components') or []):
            if c.get('type') == 'info-card':
                st = c.get('style') or {}
                if st.get('fill'):
                    palette['cardBg'] = st['fill']
                if st.get('borderColor'):
                    palette['cardBorder'] = st['borderColor']
                if st.get('titleColor'):
                    palette['titleColor'] = st['titleColor']
                break

    tpl_payload = {
        'id': template_id,
        'name': name or template_id,
        'description': description or f"提取自工程 {deck.get('title') or deck.get('id') or ''}",
        'canvas': deck.get('canvas') or base['canvas'],
        'palette': palette,
        'backgrounds': {'cover': cover_bg, 'body': body_bg},
        'skeleton': base['skeleton']
    }
    return save_custom_template(tpl_payload)


def _map_color_to_palette(hex_str, pal, role_hint=''):
    if not hex_str or not isinstance(hex_str, str):
        return hex_str
    up = hex_str.strip().upper()
    if up in SEMANTIC_PROTECTED_COLORS:
        return up
    if up in KNOWN_BRAND_ACCENT and role_hint in ('accent', 'divider'):
        return pal['accent']
    if up in KNOWN_BRAND_PRIMARY:
        return pal['primary']
    if up in KNOWN_TITLE_COLORS:
        return pal['titleColor'] if role_hint in ('title', 'text') else pal['primary']
    if up in KNOWN_ALT_BG:
        return pal['cardAltBg']
    if up in KNOWN_CARD_BG:
        return pal['cardBg']
    if up in KNOWN_BORDER_COLORS:
        return pal['cardBorder']
    return hex_str


def apply_template_to_deck(deck, template_id=None, scope='deck', slide_index=None):
    """将模板完整应用到 Deck（全文档或指定页）：更新背景、页眉/封面骨架及组件色板。"""
    from core.schema import compile_component

    tpl = get_template(template_id)
    pal = tpl['palette']
    bgs = tpl['backgrounds']

    deck['templateId'] = tpl['id']
    deck['theme'] = {
        'name': tpl['name'],
        'primaryColor': pal['primary'],
        'secondaryColor': pal['secondary'],
        'accentColor': pal['accent'],
        'textColor': pal['bodyColor'],
        'mutedColor': pal['mutedColor'],
        'fontFamily': pal.get('fontFamily', '微软雅黑')
    }

    slides = deck.get('slides') or []
    target_indices = (
        [slide_index] if (scope == 'slide' and slide_index is not None and 0 <= slide_index < len(slides))
        else list(range(len(slides)))
    )

    for s_idx in target_indices:
        slide = slides[s_idx]
        comps = slide.get('components') or []
        is_cover_slide = any(c.get('type') == 'cover-divider' for c in comps)
        slide['background'] = copy.deepcopy(bgs['cover'] if is_cover_slide else bgs['body'])

        for comp in comps:
            ctype = comp.get('type', 'info-card')
            st = comp.setdefault('style', {})
            st['accentColor'] = pal['accent']
            st['fontFamily'] = pal.get('fontFamily', '微软雅黑')

            if ctype in ('slide-header', 'cover-divider'):
                st['fill'] = pal['bannerBg']
                st['borderColor'] = pal['primary']
                st['titleColor'] = pal['titleColor']
                st['bodyColor'] = pal['mutedColor']
                compile_component(comp, tpl)
                continue

            if ctype == 'footer-banner':
                st['fill'] = pal['bannerBg']
                st['borderColor'] = pal['bannerBorder']
                st['titleColor'] = pal['primary']
                st['bodyColor'] = pal['bodyColor']
                compile_component(comp, tpl)
                continue

            if ctype == 'data-table':
                st['accentColor'] = pal['tableHeaderBg']
                for ch in (comp.get('children') or []):
                    if ch.get('rawType') == 'table' and ch.get('rows'):
                        for c_cell in ch['rows'][0]:
                            if c_cell.get('fill'):
                                c_cell['fill'] = pal['tableHeaderBg']
                            c_cell['color'] = pal.get('tableHeaderFg', '#FFFFFF')
                        for r_i, row in enumerate(ch['rows'][1:]):
                            stripe = pal['tableStripeBg'] if r_i % 2 == 0 else '#FFFFFF'
                            for c_cell in row:
                                if (c_cell.get('fill') or '').upper() in KNOWN_CARD_BG | {'#F8FAFC', '#F4F6F9', '#FFF8F3'}:
                                    c_cell['fill'] = stripe
                continue

            if ctype in ('vertical-stack', 'decision-gate', 'stage-funnel', 'iteration-lanes', 'rule-checklist', 'process-flow') and comp.get('subType') == 'declarative':
                if ctype == 'rule-checklist':
                    st['titleColor'] = pal['titleColor']
                st['borderColor'] = pal['primary']
                compile_component(comp, tpl)
                continue

            # 通用其余元件：同步品牌主色/浅底/文字色，同时保留语义绿/红/琥珀状态色
            if st.get('fill'):
                st['fill'] = _map_color_to_palette(st['fill'], pal, 'fill')
            if st.get('borderColor'):
                st['borderColor'] = _map_color_to_palette(st['borderColor'], pal, 'border')
            if st.get('titleColor'):
                st['titleColor'] = _map_color_to_palette(st['titleColor'], pal, 'title')

            for ch in (comp.get('children') or []):
                if ch.get('rawType') != 'shape':
                    continue
                role = ch.get('role') or ''
                if ch.get('fill'):
                    ch['fill'] = _map_color_to_palette(ch['fill'], pal, 'divider' if role == 'divider' else 'fill')
                if ch.get('borderColor'):
                    ch['borderColor'] = _map_color_to_palette(ch['borderColor'], pal, 'border')
                tb = ch.get('textBody') or {}
                for p in (tb.get('paragraphs') or []):
                    for r in (p.get('runs') or []):
                        if r.get('color'):
                            r['color'] = _map_color_to_palette(r['color'], pal, 'title')

    return deck
