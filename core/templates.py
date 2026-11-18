import copy
import json
import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
BUILTIN_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, 'builtin')
LOCAL_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, 'local')
EXAMPLE_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, 'example')

os.makedirs(BUILTIN_TEMPLATES_DIR, exist_ok=True)
os.makedirs(LOCAL_TEMPLATES_DIR, exist_ok=True)

DEFAULT_TEMPLATE_ID = 'academic'

DEFAULT_SEMANTIC_TOKENS = {
    'pass': {
        'bg': '#F6FAF8', 'border': '#2E6F54', 'stripe': '#2E6F54',
        'badgeBg': '#2E6F54', 'badgeFg': '#FFFFFF', 'title': '#1E523C', 'body': '#334155'
    },
    'warn': {
        'bg': '#FAF7F2', 'border': '#A1681E', 'stripe': '#B87A28',
        'badgeBg': '#A1681E', 'badgeFg': '#FFFFFF', 'title': '#7C4E12', 'body': '#334155'
    },
    'reject': {
        'bg': '#FAF4F5', 'border': '#8C2D3C', 'stripe': '#8C2D3C',
        'badgeBg': '#8C2D3C', 'badgeFg': '#FFFFFF', 'title': '#7A2048', 'body': '#334155'
    },
    'info': {
        'bg': '#F4F7FB', 'border': '#2B547E', 'stripe': '#1B365D',
        'badgeBg': '#1B365D', 'badgeFg': '#FFFFFF', 'title': '#1B365D', 'body': '#334155'
    },
    'neutral': {
        'bg': '#F8FAFC', 'border': '#94A3B8', 'stripe': '#64748B',
        'badgeBg': '#475569', 'badgeFg': '#FFFFFF', 'title': '#334155', 'body': '#475569'
    }
}

SEMANTIC_PROTECTED_COLORS = {
    '#16A34A', '#F0FDF4', '#15803D', '#2E7D32', '#F1F8F4', '#2E6F54', '#6B7F04', '#FAFAF3',
    '#D97706', '#FFFBEB', '#B45309', '#B87D18', '#D49B27', '#A67014', '#FAF6ED',
    '#DC2626', '#FEF2F2', '#B91C1C', '#C62828', '#FFF3F3', '#A63429', '#962D24', '#8C2D3C', '#F8F3F1'
}

KNOWN_BRAND_PRIMARY = {
    '#1B365D', '#1E6CFF', '#0D9488', '#F26B21', '#F26421',
    '#7B32D9', '#B45309', '#234370', '#18181B'
}
KNOWN_BRAND_ACCENT = {
    '#7A2048', '#00B4D8', '#9B1B3E', '#F39A1E', '#D97706', '#D0E516'
}
KNOWN_TITLE_COLORS = KNOWN_BRAND_PRIMARY | KNOWN_BRAND_ACCENT | {
    '#2B547E', '#0F4CD6', '#0F766E', '#134E4A', '#D45500', '#DB5312', '#5B18B2', '#141413'
}
KNOWN_CARD_BG = {
    '#F6F8FB', '#F4F6F9', '#EDF2F8', '#F0F5FF', '#EAF2FF', '#EFF6FF',
    '#F0FDFA', '#CCFBF1', '#FFF5EE', '#FFF2E6', '#FFF7F0', '#FFF7ED',
    '#FFF8F3', '#F7F0FF', '#F3E8FF', '#F6F4EA', '#F7F4EB'
}
KNOWN_ALT_BG = {
    '#FAF4F6', '#FDF2F5', '#ECFEFF', '#FEF3C7', '#FFFBEB', '#EFECE1'
}
KNOWN_BORDER_COLORS = {
    '#CBD5E1', '#BFDBFE', '#99F6E4', '#1B365D', '#1E6CFF', '#0D9488',
    '#F26B21', '#7A2048', '#E2C6D1', '#27272A'
}


def _sanitize_template_id(raw_id):
    cleaned = re.sub(r'[^a-zA-Z0-9_-]+', '_', str(raw_id or '').strip()).strip('_').lower()
    return cleaned or 'custom_template'


def _load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _resolve_asset_ref(ref_str, asset_base_url):
    if not ref_str or not isinstance(ref_str, str):
        return ref_str
    s = ref_str.strip()
    if s.startswith(('/', 'http://', 'https://', 'data:')):
        return s
    clean = s.lstrip('./')
    if clean.startswith('assets/'):
        clean = clean[len('assets/'):]
    return f"{asset_base_url}/{clean}"


def _resolve_bundle_asset_urls(tpl, source, tid, bundle_dir=None):
    """将模板包内相对路径（如 'assets/cover_bg.png'）统一规范化为 Web/导出引擎可直接读取的绝对逻辑路径。"""
    tpl['id'] = tpl.get('id') or tid
    tpl['source'] = source
    if bundle_dir:
        tpl['bundleDir'] = bundle_dir
    asset_base_url = f"/templates/{source}/{tpl['id']}/assets"
    tpl['assetBaseUrl'] = asset_base_url

    bgs = tpl.get('backgrounds') or {}
    for k in ('cover', 'body'):
        bg = bgs.get(k)
        if isinstance(bg, dict) and bg.get('image'):
            bg['image'] = _resolve_asset_ref(bg['image'], asset_base_url)

    decs = tpl.get('decorations')
    if isinstance(decs, dict):
        for k in ('cover', 'section', 'body'):
            arr = decs.get(k)
            if isinstance(arr, list):
                for item in arr:
                    if isinstance(item, dict) and item.get('src'):
                        item['src'] = _resolve_asset_ref(item['src'], asset_base_url)

    manifest = tpl.get('assetsManifest')
    if isinstance(manifest, dict):
        for k, v in list(manifest.items()):
            manifest[k] = _resolve_asset_ref(v, asset_base_url)

    pal = tpl.setdefault('palette', {})
    sem = pal.setdefault('semantic', {})
    for sk, sdef in DEFAULT_SEMANTIC_TOKENS.items():
        if sk not in sem or not isinstance(sem[sk], dict):
            sem[sk] = copy.deepcopy(sdef)
        else:
            for fk, fv in sdef.items():
                sem[sk].setdefault(fk, fv)
    return tpl


def _iter_dir_templates(folder, source):
    """扫描目录内的自包含模板包 (<tid>/template.json) 与兼容旧式单文件 (<tid>.json)。"""
    found = []
    if not os.path.isdir(folder):
        return found
    for entry in sorted(os.listdir(folder)):
        if entry.startswith('_') or entry == 'assets':
            continue
        full_entry = os.path.join(folder, entry)
        if os.path.isdir(full_entry):
            manifest = os.path.join(full_entry, 'template.json')
            if os.path.isfile(manifest):
                try:
                    tpl = _load_json(manifest)
                    tid = tpl.get('id') or entry
                    tpl = _resolve_bundle_asset_urls(copy.deepcopy(tpl), source, tid, bundle_dir=full_entry)
                    found.append(tpl)
                except Exception:
                    continue
        elif entry.endswith('.json') and os.path.isfile(full_entry):
            try:
                tpl = _load_json(full_entry)
                tid = tpl.get('id') or entry[:-5]
                tpl = _resolve_bundle_asset_urls(copy.deepcopy(tpl), source, tid, bundle_dir=folder)
                found.append(tpl)
            except Exception:
                continue
    return found


def list_templates():
    """列出所有内置可商用模板包与本地私有模板包（默认将 academic 排在最前）。"""
    items = []
    seen = set()
    for source, folder in [('builtin', BUILTIN_TEMPLATES_DIR), ('local', LOCAL_TEMPLATES_DIR)]:
        for tpl in _iter_dir_templates(folder, source):
            tid = tpl['id']
            if tid in seen:
                continue
            seen.add(tid)
            items.append(tpl)

    items.sort(key=lambda t: (
        0 if t.get('id') == DEFAULT_TEMPLATE_ID else 1,
        0 if t.get('isDefault') else 1,
        0 if t.get('source') == 'builtin' else 1,
        t.get('id', '')
    ))
    return items


def get_template(template_id=None):
    """按 ID 获取自包含模板包完整定义（local -> builtin -> example），未找到则回退默认学术模板。"""
    tid = str(template_id or DEFAULT_TEMPLATE_ID).strip()
    search_roots = [
        ('local', LOCAL_TEMPLATES_DIR),
        ('builtin', BUILTIN_TEMPLATES_DIR),
        ('example', EXAMPLE_TEMPLATES_DIR),
    ]
    for source, folder in search_roots:
        bundle_dir = os.path.join(folder, tid)
        bundle_manifest = os.path.join(bundle_dir, 'template.json')
        if os.path.isfile(bundle_manifest):
            tpl = _load_json(bundle_manifest)
            return _resolve_bundle_asset_urls(tpl, source, tid, bundle_dir=bundle_dir)
        legacy_json = os.path.join(folder, f"{tid}.json")
        if os.path.isfile(legacy_json):
            tpl = _load_json(legacy_json)
            return _resolve_bundle_asset_urls(tpl, source, tid, bundle_dir=folder)

    # 回退到默认学术模板包
    def_dir = os.path.join(BUILTIN_TEMPLATES_DIR, DEFAULT_TEMPLATE_ID)
    def_manifest = os.path.join(def_dir, 'template.json')
    if os.path.isfile(def_manifest):
        tpl = _load_json(def_manifest)
        return _resolve_bundle_asset_urls(tpl, 'builtin', DEFAULT_TEMPLATE_ID, bundle_dir=def_dir)

    fallback_tpl = {
        'id': DEFAULT_TEMPLATE_ID,
        'name': '学术深蓝 (默认)',
        'commercial': True,
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
            'fontFamily': '微软雅黑',
            'semantic': copy.deepcopy(DEFAULT_SEMANTIC_TOKENS)
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
    return _resolve_bundle_asset_urls(fallback_tpl, 'builtin', DEFAULT_TEMPLATE_ID)


def save_custom_template(tpl_data):
    """以自包含模板包形式保存到 templates/local/<tid>/（严禁修改 builtin 模板）。"""
    tid = _sanitize_template_id(tpl_data.get('id') or tpl_data.get('name'))
    base = copy.deepcopy(get_template(DEFAULT_TEMPLATE_ID))
    bundle_dir = os.path.join(LOCAL_TEMPLATES_DIR, tid)
    assets_dir = os.path.join(bundle_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)

    merged_pal = {**base['palette'], **(tpl_data.get('palette') or {})}
    if 'semantic' not in merged_pal:
        merged_pal['semantic'] = copy.deepcopy(DEFAULT_SEMANTIC_TOKENS)

    merged = {
        'id': tid,
        'name': tpl_data.get('name') or tid,
        'description': tpl_data.get('description') or '用户自定义本地模板包',
        'commercial': bool(tpl_data.get('commercial', False)),
        'isDefault': False,
        'canvas': tpl_data.get('canvas') or base['canvas'],
        'palette': merged_pal,
        'backgrounds': tpl_data.get('backgrounds') or base['backgrounds'],
        'skeleton': {**base['skeleton'], **(tpl_data.get('skeleton') or {})}
    }
    if tpl_data.get('decorations'):
        merged['decorations'] = tpl_data['decorations']

    out_path = os.path.join(bundle_dir, 'template.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    return _resolve_bundle_asset_urls(merged, 'local', tid, bundle_dir=bundle_dir)


def delete_custom_template(template_id):
    """删除本地自定义模板包（内置模板不可删除）。"""
    tid = _sanitize_template_id(template_id)
    local_dir = os.path.join(LOCAL_TEMPLATES_DIR, tid)
    local_legacy = os.path.join(LOCAL_TEMPLATES_DIR, f"{tid}.json")
    builtin_dir = os.path.join(BUILTIN_TEMPLATES_DIR, tid)
    builtin_legacy = os.path.join(BUILTIN_TEMPLATES_DIR, f"{tid}.json")

    if os.path.isdir(local_dir):
        shutil.rmtree(local_dir)
        return True
    if os.path.isfile(local_legacy):
        os.remove(local_legacy)
        return True
    if os.path.isdir(builtin_dir) or os.path.isfile(builtin_legacy):
        raise ValueError(f"内置模板 '{tid}' 不可删除")
    raise FileNotFoundError(f"未找到本地模板 '{tid}'")


def extract_template_from_deck(deck, template_id, name, description=''):
    """从现有 Deck 中提取主色调、背景图与骨架风格，生成本地自定义自包含模板包。"""
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


def _infer_tone_from_colors(fill_hex=None, border_hex=None, text_hint='', default='info'):
    """
    结合颜色与文本职能标签推断结构化语义 tone ('pass' | 'warn' | 'reject' | 'neutral' | 'info')。
    普通品牌装饰色（如原企业橙 #F26B21 或科技蓝 #1E6CFF）不强行绑定刺眼独立色，交由 'info' 接入目标模板皮肤。
    """
    vals = {str(x).strip().upper() for x in (fill_hex, border_hex) if x}
    txt = str(text_hint or '').strip()

    # 优先依据功能职能关键词裁决（解决同职能卡片因原稿配色不统一造成的色彩混乱，如 P10 的“禁/准/警”）
    if txt:
        if any(k in txt for k in ('禁', '×', 'REJECT', '强制回退', '已证伪', '红线', '恶化', '回滚')):
            return 'reject'
        if any(k in txt for k in ('警', '慎', '!', 'WARN', '瓶颈', '空值')):
            return 'warn'
        if any(k in txt for k in ('准', '✓', 'PASS', 'PROMOTED', 'FINAL', '定稿', '晋升', '交付标准', '验收', '硬误杀 0')):
            return 'pass'

    if vals & {'#DC2626', '#B91C1C', '#C62828', '#FEF2F2', '#FFF3F3', '#A63429', '#962D24', '#8C2D3C', '#F8F3F1'}:
        return 'reject'
    if vals & {'#16A34A', '#15803D', '#2E7D32', '#F0FDF4', '#F1F8F4', '#2E6F54', '#6B7F04', '#FAFAF3'}:
        return 'pass'
    if vals & {'#D97706', '#B45309', '#FFFBEB', '#B87D18', '#D49B27', '#A67014', '#FAF6ED'}:
        return 'warn'
    if vals & {'#475569', '#44546A', '#94A3B8', '#F8FAFC', '#736F68', '#52504C', '#F4F2EA'}:
        return 'neutral'
    return default


def _extract_paras_text(ch):
    tb = ch.get('textBody') or {}
    out = []
    for p in (tb.get('paragraphs') or []):
        t = (p.get('text') or ''.join(r.get('text', '') for r in (p.get('runs') or []))).strip()
        if t:
            out.append(t)
    return out


def hydrate_component_content(comp):
    """
    对从 PPTX 解析得到或仅含 children 树的历史元件，无损水合出结构化 content 字段与功能语义 tone，
    使 compile_component(comp, tpl) 能够重绘全套皮肤而不丢失内容与功能分级。
    """
    ctype = comp.get('type', 'info-card')
    content = comp.setdefault('content', {})
    children = comp.get('children') or []

    if ctype == 'cover-divider':
        items = [str(x).strip() for x in (content.get('items') or []) if str(x).strip()]
        cur_t = str(content.get('title') or '').strip()
        if items and ('\n' in items[0] or (cur_t and items[0].startswith(cur_t) and len(items[0]) > len(cur_t))):
            content['title'] = items[0]
        if not content.get('meta') and len(items) > 2:
            content['meta'] = items[2:]
        return comp

    if ctype == 'slide-header':
        for ch in children:
            role = ch.get('role')
            ps = _extract_paras_text(ch)
            if not ps:
                continue
            if role == 'title' and not content.get('title'):
                content['title'] = ps[0]
            elif role == 'subtitle' and not content.get('subtitle'):
                content['subtitle'] = ps[0]
            elif role == 'step-box' and not content.get('sectionTag'):
                content['sectionTag'] = ps[0]
            elif role == 'page-num' and not content.get('pageNumber'):
                content['pageNumber'] = ps[0]
        return comp

    if ctype == 'footer-banner':
        raw_sub = str(content.get('subtitle') or content.get('text') or '').strip()
        raw_pre = str(content.get('prefix') or '').strip()
        raw_title = str(content.get('title') or '').strip()
        if not raw_sub:
            full_txt = raw_title
            if not full_txt and children:
                full_txt = ' '.join(_extract_paras_text(children[0])).strip()
            if full_txt:
                if '：' in full_txt and full_txt.index('：') <= 16:
                    p0, p1 = full_txt.split('：', 1)
                    content['prefix'] = p0.strip() + '：'
                    content['subtitle'] = p1.strip()
                else:
                    content['prefix'] = raw_pre or '核心结论：'
                    content['subtitle'] = full_txt
        return comp

    if ctype == 'tag-badge':
        if not content.get('tone') and children:
            ch0 = children[0]
            t_txt = ' '.join(_extract_paras_text(ch0))
            inferred = _infer_tone_from_colors(ch0.get('fill'), ch0.get('borderColor'), text_hint=t_txt, default=None)
            if inferred in ('reject', 'pass', 'warn'):
                content['tone'] = inferred
        return comp

    if ctype == 'info-card':
        multi_cards = sum(1 for ch in children if ch.get('role') == 'card') >= 2
        if comp.get('subType') == 'primitives-demo' or multi_cards:
            comp['_preserveMultiCard'] = True
            return comp

        if not content.get('tone') and children:
            for ch in children:
                if ch.get('role') in ('container', 'card', 'shape'):
                    ch_txt = ' '.join(_extract_paras_text(ch)[:1])
                    inferred = _infer_tone_from_colors(ch.get('fill'), ch.get('borderColor'), text_hint=ch_txt, default=None)
                    # 对单卡片仅识别明确状态信号色，防止正常普通信息卡标题含"准"字被误染
                    inferred_col_only = _infer_tone_from_colors(ch.get('fill'), ch.get('borderColor'), text_hint='', default=None)
                    if inferred_col_only in ('reject', 'pass', 'warn'):
                        content['tone'] = inferred_col_only
                        break
                    if ch_txt.startswith('← 强制回退') or ch_txt.startswith('条件 3：违背'):
                        content['tone'] = 'reject'
                        break
        if not content.get('title') and not content.get('items') and children:
            all_p = []
            for ch in children:
                all_p.extend(_extract_paras_text(ch))
            if all_p:
                content['title'] = all_p[0]
                content['items'] = all_p[1:]
        return comp

    if ctype == 'kpi-card':
        if not content.get('image'):
            for ch in children:
                if ch.get('rawType') == 'image' and ch.get('src'):
                    content['image'] = ch['src']
                    break
        if not content.get('metricValue'):
            for ch in children:
                if ch.get('role') == 'metric-box':
                    ps = _extract_paras_text(ch)
                    if ps:
                        content['metricValue'] = ps[0]
                        if len(ps) > 1 and not content.get('metricLabel'):
                            content['metricLabel'] = ps[1]
                        if len(ps) > 2 and not content.get('items'):
                            content['items'] = ps[2:]
                    break
        return comp

    if ctype == 'vertical-stack':
        if not content.get('layers'):
            hdr = next((ch for ch in children if ch.get('role') == 'header-bar'), None)
            content['title'] = ' '.join(_extract_paras_text(hdr)) if hdr else ''
            badges = sorted([ch for ch in children if ch.get('role') == 'badge'], key=lambda c: float(c.get('y', 0)))
            cards = sorted([ch for ch in children if ch.get('role') == 'layer-card'], key=lambda c: float(c.get('y', 0)))
            layers = []
            for i in range(max(len(badges), len(cards))):
                b = badges[i] if i < len(badges) else None
                c = cards[i] if i < len(cards) else None
                b_txt = ' '.join(_extract_paras_text(b)) if b else f'L{i+1}'
                c_ps = _extract_paras_text(c) if c else []
                l_title = c_ps[0] if c_ps else ''
                l_desc = '\n'.join(c_ps[1:]) if len(c_ps) > 1 else ''
                tone = _infer_tone_from_colors(
                    (b or {}).get('fill') or (c or {}).get('borderColor'),
                    (c or {}).get('fill'),
                    default='info'
                )
                layers.append({'tag': b_txt, 'title': l_title, 'desc': l_desc, 'tone': tone})
            if layers:
                content['layers'] = layers
        return comp

    if ctype == 'decision-gate':
        if not content.get('branches'):
            gate = next((ch for ch in children if ch.get('role') == 'gate-node'), None)
            if gate:
                content['gateText'] = ' '.join(_extract_paras_text(gate)) or content.get('gateText') or content.get('title', '')
                content.pop('gateShape', None)
            badges = sorted([ch for ch in children if ch.get('role') == 'badge'], key=lambda c: float(c.get('x', 0)))
            cards = sorted([ch for ch in children if ch.get('role') == 'branch-card'], key=lambda c: float(c.get('x', 0)))
            branches = []
            for i in range(max(len(badges), len(cards))):
                b = badges[i] if i < len(badges) else None
                c = cards[i] if i < len(cards) else None
                b_txt = ' '.join(_extract_paras_text(b)) if b else f'分支 {i+1}'
                c_ps = _extract_paras_text(c) if c else []
                tone = _infer_tone_from_colors(
                    (b or {}).get('fill') or (c or {}).get('fill'),
                    (c or {}).get('borderColor'),
                    default='info'
                )
                branches.append({
                    'label': b_txt,
                    'tone': tone,
                    'title': c_ps[0] if c_ps else '',
                    'items': c_ps[1:] if len(c_ps) > 1 else []
                })
            if branches:
                content['branches'] = branches
        return comp

    if ctype == 'stage-funnel':
        if not content.get('stages'):
            hdr = next((ch for ch in children if ch.get('role') == 'header-bar'), None)
            content['title'] = ' '.join(_extract_paras_text(hdr)) if hdr else ''
            sbar = next((ch for ch in children if ch.get('role') == 'summary-bar'), None)
            if sbar:
                content['summary'] = ' '.join(_extract_paras_text(sbar))
            badges = sorted([ch for ch in children if ch.get('role') == 'badge'], key=lambda c: float(c.get('x', 0)))
            boxes = sorted([ch for ch in children if ch.get('role') == 'stage-box'], key=lambda c: float(c.get('x', 0)))
            stages = []
            for i in range(max(len(badges), len(boxes))):
                b = badges[i] if i < len(badges) else None
                bx = boxes[i] if i < len(boxes) else None
                b_txt = ' '.join(_extract_paras_text(b)) if b else f'S{i+1}'
                bx_ps = _extract_paras_text(bx) if bx else []
                tone = _infer_tone_from_colors(
                    (b or {}).get('fill') or (bx or {}).get('fill'),
                    (bx or {}).get('borderColor'),
                    default='info'
                )
                stages.append({
                    'code': '',
                    'name': b_txt,
                    'metric': bx_ps[0] if bx_ps else '',
                    'desc': '\n'.join(bx_ps[1:]) if len(bx_ps) > 1 else '',
                    'tone': tone
                })
            if stages:
                content['stages'] = stages
        return comp

    if ctype == 'iteration-lanes':
        if not content.get('lanes'):
            topo = next((ch for ch in children if ch.get('role') == 'topology-bar'), None)
            if topo:
                content['topology'] = ' '.join(_extract_paras_text(topo))
            badges = sorted([ch for ch in children if ch.get('role') == 'badge'], key=lambda c: float(c.get('x', 0)))
            lane_cards = sorted([ch for ch in children if ch.get('role') == 'lane-card'], key=lambda c: float(c.get('x', 0)))
            lanes = []
            if badges and lane_cards:
                for i in range(max(len(badges), len(lane_cards))):
                    b = badges[i] if i < len(badges) else None
                    lc = lane_cards[i] if i < len(lane_cards) else None
                    ps = _extract_paras_text(lc) if lc else []
                    b_txt = ' '.join(_extract_paras_text(b)) if b else f'R{i}'
                    tone = _infer_tone_from_colors(
                        (b or {}).get('fill') or (lc or {}).get('fill'),
                        (lc or {}).get('borderColor'),
                        text_hint=b_txt + ' ' + (' '.join(ps[-1:]) if ps else ''),
                        default='neutral'
                    )
                    lanes.append({
                        'round': b_txt,
                        'tone': tone,
                        'title': ps[0] if ps else '',
                        'metric': ps[1] if len(ps) > 1 else '',
                        'items': ps[2:-1] if len(ps) > 3 else ps[2:],
                        'verdict': ps[-1] if len(ps) > 3 else ''
                    })
            else:
                raw_cards = sorted([ch for ch in children if ch.get('role') in ('card', 'lane-card', 'container')], key=lambda c: float(c.get('x', 0)))
                for i, rc in enumerate(raw_cards):
                    ps = _extract_paras_text(rc)
                    if not ps:
                        continue
                    head = ps[0]
                    if '｜' in head:
                        r_lbl, l_title = [x.strip() for x in head.split('｜', 1)]
                    elif '|' in head:
                        r_lbl, l_title = [x.strip() for x in head.split('|', 1)]
                    else:
                        r_lbl, l_title = f'R{i}', head
                    rest = ps[1:]
                    verdict = ''
                    if rest and any(k in rest[-1] for k in ('门禁', '终态', '状态', 'PROMOTED', 'REJECT', '锚点')):
                        verdict = rest[-1]
                        rest = rest[:-1]
                    tone = _infer_tone_from_colors(
                        rc.get('fill'),
                        rc.get('borderColor'),
                        text_hint=f"{head} {verdict}",
                        default='neutral'
                    )
                    lanes.append({
                        'round': r_lbl,
                        'tone': tone,
                        'title': l_title,
                        'metric': '',
                        'items': rest,
                        'verdict': verdict
                    })
            if lanes:
                content['lanes'] = lanes
        return comp

    if ctype == 'rule-checklist':
        if not content.get('rows'):
            t_ch = next((ch for ch in children if ch.get('role') == 'title'), None)
            if t_ch and not content.get('title'):
                content['title'] = ' '.join(_extract_paras_text(t_ch))
            badges = sorted([ch for ch in children if ch.get('role') == 'badge'], key=lambda c: float(c.get('y', 0)))
            items = sorted([ch for ch in children if ch.get('role') == 'rule-item'], key=lambda c: float(c.get('y', 0)))
            rows = []
            for i in range(max(len(badges), len(items))):
                b = badges[i] if i < len(badges) else None
                it = items[i] if i < len(items) else None
                b_txt = ' '.join(_extract_paras_text(b)) if b else '•'
                full_txt = ' '.join(_extract_paras_text(it)) if it else ''
                if '：' in full_txt and full_txt.index('：') <= 24:
                    rt, rd = full_txt.split('：', 1)
                else:
                    rt, rd = '', full_txt
                tone = _infer_tone_from_colors((b or {}).get('fill'), None, text_hint=b_txt, default='info')
                rows.append({'badge': b_txt, 'tone': tone, 'title': rt.strip(), 'desc': rd.strip()})
            if rows:
                content['rows'] = rows
        return comp

    if ctype == 'process-flow':
        if not content.get('items'):
            steps = sorted([ch for ch in children if ch.get('role') in ('step-box', 'container')], key=lambda c: float(c.get('x', 0)))
            built = []
            for st_ch in steps:
                ps = _extract_paras_text(st_ch)
                if ps:
                    built.append(f"{ps[0]} | {' '.join(ps[1:])}" if len(ps) > 1 else ps[0])
            if built:
                content['items'] = built
        return comp

    if ctype == 'data-table':
        tbl = next((ch for ch in children if ch.get('rawType') == 'table' and ch.get('rows')), None)
        if tbl:
            rows = tbl['rows']
            if not content.get('headers') and rows:
                content['headers'] = [str(c.get('text', '')) for c in rows[0]]
            if not content.get('rows') and len(rows) > 1:
                content['rows'] = [[str(c.get('text', '')) for c in r] for r in rows[1:]]
            if not content.get('colRatios') and tbl.get('colWidths'):
                cws = [float(x) for x in tbl['colWidths'] if float(x) > 0]
                if cws and len(cws) == len(content.get('headers', [])):
                    content['colRatios'] = cws
        return comp

    if ctype == 'image-frame':
        if not content.get('image'):
            imgs = content.get('images') or []
            if imgs:
                content['image'] = imgs[0]
            else:
                im_ch = next((ch for ch in children if ch.get('rawType') == 'image' and ch.get('src')), None)
                if im_ch:
                    content['image'] = im_ch['src']
        return comp

    return comp


def _restyle_preserved_multicard(comp, tpl):
    """为包含多张内部自定义子卡片的组合式 info-card 同步尺寸与同源功能色皮肤，消除杂色冲突。"""
    from core.exporter import sync_component_children_coords
    pal = tpl['palette']
    sem_map = pal.get('semantic') or DEFAULT_SEMANTIC_TOKENS
    is_terra = (tpl.get('skeleton', {}).get('skin') == 'terra_quest')
    font = pal.get('fontFamily', '微软雅黑')

    synced = sync_component_children_coords(comp)
    bx, by = float(comp.get('x', 0)), float(comp.get('y', 0))
    for ch in synced:
        ch['relX'] = round(float(ch.get('x', 0)) - bx, 2)
        ch['relY'] = round(float(ch.get('y', 0)) - by, 2)
        ch['relW'] = round(float(ch.get('w', 0)), 2)
        ch['relH'] = round(float(ch.get('h', 0)), 2)
        if ch.get('rawType') != 'shape':
            continue
        role = ch.get('role') or ''
        fill_up = str(ch.get('fill') or '').upper()
        border_up = str(ch.get('borderColor') or '').upper()
        ch_txt = ' '.join(_extract_paras_text(ch))

        if is_terra:
            if ch.get('geom') == 'roundRect':
                ch['geom'] = 'rect'
            if role in ('header-bar', 'section-bar'):
                ch['fill'] = '#18181B'
                ch['borderColor'] = None
                ch['shadow'] = True
                _update_runs_style(ch, color='#D0E516', font=font)
            elif role == 'card':
                ch['shadow'] = True
                sem_key = _infer_tone_from_colors(fill_up, border_up, text_hint=ch_txt, default='info')
                tok = sem_map.get(sem_key, sem_map['info'])
                ch['fill'] = tok['bg']
                ch['fillAlpha'] = 0.92
                ch['borderColor'] = tok['border']
                ch['borderAlpha'] = 0.50 if sem_key in ('pass', 'warn', 'reject') else 0.30
                _update_runs_style(ch, title_color=tok['title'], body_color=tok['body'], font=font, force_override=True)
            elif role == 'container':
                ch['shadow'] = True
                ch['fill'] = '#FFFFFF'
                ch['fillAlpha'] = 0.92
                ch['borderColor'] = '#27272A'
                ch['borderAlpha'] = 0.28
            elif ch.get('fill'):
                # primitives-demo 内置几何演示节点保持明暗高对比
                is_sem = (fill_up in SEMANTIC_PROTECTED_COLORS or border_up in SEMANTIC_PROTECTED_COLORS)
                if not is_sem:
                    mapped_fill = _map_color_to_palette(ch['fill'], pal, 'accent' if fill_up in KNOWN_BRAND_ACCENT else 'fill')
                    ch['fill'] = mapped_fill
                    if ch.get('borderColor'):
                        ch['borderColor'] = _map_color_to_palette(ch['borderColor'], pal, 'border')
                    if mapped_fill == '#D0E516':
                        _update_runs_style(ch, color='#141413', font=font)
                    elif mapped_fill == '#18181B':
                        _update_runs_style(ch, color='#D0E516', font=font)
        else:
            if role == 'card':
                sem_key = _infer_tone_from_colors(fill_up, border_up, text_hint=ch_txt, default='info')
                tok = sem_map.get(sem_key, sem_map['info'])
                ch['fill'] = tok['bg']
                ch['borderColor'] = tok['border']
                _update_runs_style(ch, title_color=tok['title'], body_color=tok['body'], font=font, force_override=True)
            else:
                if ch.get('fill'):
                    ch['fill'] = _map_color_to_palette(ch['fill'], pal, 'divider' if role == 'divider' else 'fill')
                if ch.get('borderColor'):
                    ch['borderColor'] = _map_color_to_palette(ch['borderColor'], pal, 'border')
                _update_runs_style(ch, title_color=pal['titleColor'], font=font, map_palette=pal)
    comp['children'] = synced
    return comp


def _update_runs_style(ch, color=None, title_color=None, body_color=None, font=None, map_palette=None, force_override=False):
    tb = ch.get('textBody') or {}
    for p_i, p in enumerate(tb.get('paragraphs') or []):
        for r in (p.get('runs') or []):
            if font:
                r['fontFamily'] = font
            if color:
                r['color'] = color
                continue
            rc = str(r.get('color') or '').upper()
            if (not force_override) and rc in SEMANTIC_PROTECTED_COLORS:
                continue
            if map_palette:
                if r.get('color'):
                    r['color'] = _map_color_to_palette(r['color'], map_palette, 'title')
            else:
                if p_i == 0 or r.get('bold'):
                    if title_color and rc not in ('#FFFFFF',):
                        r['color'] = title_color
                elif body_color and rc not in ('#FFFFFF',):
                    r['color'] = body_color


def rescale_deck_canvas(deck, old_canvas, new_canvas, old_skel, new_skel):
    """在不同纵横比/分辨率模板间切换时，将主体元件坐标与尺寸线性映射到新安全区。"""
    old_w = float((old_canvas or {}).get('width', 1020.67))
    old_h = float((old_canvas or {}).get('height', 680.33))
    new_w = float((new_canvas or {}).get('width', old_w))
    new_h = float((new_canvas or {}).get('height', old_h))

    deck_canvas = deck.setdefault('canvas', {})
    deck_canvas['width'] = new_w
    deck_canvas['height'] = new_h
    if new_canvas.get('emuCx'):
        deck_canvas['emuCx'] = int(new_canvas['emuCx'])
    if new_canvas.get('emuCy'):
        deck_canvas['emuCy'] = int(new_canvas['emuCy'])

    if abs(old_w - new_w) <= 2.0 and abs(old_h - new_h) <= 2.0:
        return

    old_mx = float((old_skel or {}).get('defaultMarginX', 48.0))
    old_top = float((old_skel or {}).get('contentTopY', 134.0))
    old_ftr_y = float((old_skel or {}).get('footerY', old_h - 86.0))

    new_mx = float((new_skel or {}).get('defaultMarginX', 48.0))
    new_top = float((new_skel or {}).get('contentTopY', 134.0))
    new_ftr_y = float((new_skel or {}).get('footerY', new_h - 78.0))

    for slide in (deck.get('slides') or []):
        comps = slide.get('components') or []
        has_ftr = any(c.get('type') == 'footer-banner' for c in comps)
        body_comps = [c for c in comps if c.get('type') not in ('slide-header', 'cover-divider', 'section-divider', 'footer-banner')]

        for c in comps:
            if c.get('type') == 'footer-banner':
                c['x'] = new_mx
                c['y'] = new_ftr_y
                c['w'] = round(new_w - new_mx * 2, 2)
                c['h'] = 46.0

        if not body_comps:
            continue

        min_bx = min(float(c.get('x', old_mx)) for c in body_comps)
        max_bx2 = max(float(c.get('x', 0)) + float(c.get('w', 0)) for c in body_comps)
        min_by = min(float(c.get('y', old_top)) for c in body_comps)
        max_by2 = max(float(c.get('y', 0)) + float(c.get('h', 0)) for c in body_comps)

        src_x0 = min(old_mx, min_bx)
        src_x1 = max(old_w - old_mx, max_bx2)
        src_y0 = min(old_top, min_by)
        src_y1 = max(max_by2, (old_ftr_y - 8.0) if has_ftr else (old_h - 40.0))

        dst_x0 = new_mx
        dst_x1 = new_w - new_mx
        dst_y0 = new_top
        dst_y1 = (new_ftr_y - 12.0) if has_ftr else (new_h - 38.0)

        sx = (dst_x1 - dst_x0) / max(1.0, src_x1 - src_x0)
        sy = (dst_y1 - dst_y0) / max(1.0, src_y1 - src_y0)

        for c in body_comps:
            ox = float(c.get('x', src_x0))
            oy = float(c.get('y', src_y0))
            ow = float(c.get('w', 200.0))
            oh = float(c.get('h', 100.0))
            c['x'] = round(dst_x0 + (ox - src_x0) * sx, 2)
            c['y'] = round(dst_y0 + (oy - src_y0) * sy, 2)
            c['w'] = round(max(40.0, ow * sx), 2)
            c['h'] = round(max(24.0, oh * sy), 2)


def build_slide_decorations(tpl, is_cover=False, is_section=False, slide_idx=1):
    """生成模板包专属页面底层锁定装饰元素（支持自定义 decorations 宣言与动态包内资产路径）。"""
    if not tpl:
        return []
    asset_base = tpl.get('assetBaseUrl') or f"/templates/{tpl.get('source', 'local')}/{tpl.get('id', 'academic')}/assets"

    # 优先读取模板包自身声明的通用 decorations 列表
    custom_decs = tpl.get('decorations')
    if isinstance(custom_decs, dict):
        key = 'cover' if is_cover else ('section' if is_section and custom_decs.get('section') else 'body')
        raw_list = custom_decs.get(key) or []
        out = []
        for idx, d in enumerate(raw_list, start=1):
            dc = copy.deepcopy(d)
            dc['id'] = f"decor_{key}_{slide_idx}_{idx}"
            if dc.get('src'):
                dc['src'] = _resolve_asset_ref(dc['src'], asset_base)
            out.append(dc)
        if out:
            return out

    if tpl.get('skeleton', {}).get('skin') != 'terra_quest':
        return []

    cw = float(tpl.get('canvas', {}).get('width', 1280.0))
    ch = float(tpl.get('canvas', {}).get('height', 720.0))

    decors = []
    if is_cover or is_section:
        decors.append({
            'id': f'decor_wave_{slide_idx}',
            'rawType': 'image',
            'role': 'decor',
            'name': 'contour-wave-bg',
            'x': round(cw - 560.0, 2),
            'y': 40.0,
            'w': 560.0,
            'h': 560.0,
            'src': f'{asset_base}/contour_wave.png',
            'opacity': 0.22
        })
        decors.append({
            'id': f'decor_glow_top_{slide_idx}',
            'rawType': 'shape',
            'role': 'decor',
            'name': 'lime-ambient-glow',
            'x': round(cw - 480.0, 2),
            'y': -80.0,
            'w': 460.0,
            'h': 300.0,
            'geom': 'oval',
            'rotation': -16.0,
            'gradFill': {
                'angle': 45,
                'stops': [
                    {'pos': 0.0, 'color': '#D0E516', 'alpha': 0.22},
                    {'pos': 0.65, 'color': '#D0E516', 'alpha': 0.08},
                    {'pos': 1.0, 'color': '#D0E516', 'alpha': 0.0}
                ]
            }
        })
        return decors

    decors.append({
        'id': f'decor_body_wave_{slide_idx}',
        'rawType': 'image',
        'role': 'decor',
        'name': 'contour-wave-body',
        'x': round(cw - 440.0, 2),
        'y': round(ch - 410.0, 2),
        'w': 430.0,
        'h': 430.0,
        'src': f'{asset_base}/contour_wave.png',
        'opacity': 0.16
    })
    decors.append({
        'id': f'decor_body_ring_{slide_idx}',
        'rawType': 'image',
        'role': 'decor',
        'name': 'ring-hud-body',
        'x': round(cw - 245.0, 2),
        'y': round(ch - 230.0, 2),
        'w': 220.0,
        'h': 220.0,
        'src': f'{asset_base}/ring_hud.png',
        'opacity': 0.13
    })
    decors.append({
        'id': f'decor_body_glow_{slide_idx}',
        'rawType': 'shape',
        'role': 'decor',
        'name': 'lime-corner-glow',
        'x': -60.0,
        'y': -60.0,
        'w': 320.0,
        'h': 220.0,
        'geom': 'oval',
        'rotation': -12.0,
        'gradFill': {
            'angle': 30,
            'stops': [
                {'pos': 0.0, 'color': '#D0E516', 'alpha': 0.16},
                {'pos': 1.0, 'color': '#D0E516', 'alpha': 0.0}
            ]
        }
    })
    decors.append({
        'id': f'decor_bot_bar_{slide_idx}',
        'rawType': 'shape',
        'role': 'decor',
        'name': 'bottom-hud-tick',
        'x': 60.0,
        'y': round(ch - 14.0, 2),
        'w': 68.0,
        'h': 4.0,
        'geom': 'rect',
        'fill': '#18181B',
        'fillAlpha': 0.70
    })
    decors.append({
        'id': f'decor_bot_lime_{slide_idx}',
        'rawType': 'shape',
        'role': 'decor',
        'name': 'bottom-hud-lime',
        'x': 134.0,
        'y': round(ch - 14.0, 2),
        'w': 28.0,
        'h': 4.0,
        'geom': 'rect',
        'fill': '#D0E516'
    })
    return decors


def render_component_with_template(comp, template_id=None, box=None):
    """对单个任意 Component JSON 按指定模板执行无损水合与全皮肤重渲染。"""
    from core.schema import compile_component
    tpl = get_template(template_id)
    comp_copy = copy.deepcopy(comp)
    if box and isinstance(box, (list, tuple)) and len(box) == 4:
        comp_copy['x'], comp_copy['y'], comp_copy['w'], comp_copy['h'] = [float(v) for v in box]

    hydrate_component_content(comp_copy)
    st = comp_copy.setdefault('style', {})
    pal = tpl['palette']
    st['accentColor'] = pal['accent']
    st['fontFamily'] = pal.get('fontFamily', '微软雅黑')

    if comp_copy.pop('_preserveMultiCard', False):
        return _restyle_preserved_multicard(comp_copy, tpl)

    tone_key = (comp_copy.get('content') or {}).get('tone')
    if tone_key not in ('pass', 'promoted', 'warn', 'reject', 'rollback'):
        for k in ('fill', 'borderColor', 'titleColor', 'bodyColor'):
            st[k] = None
    return compile_component(comp_copy, tpl)


def apply_template_to_deck(
    deck,
    template_id=None,
    scope='deck',
    slide_index=None,
    rerender_components=True,
    adapt_canvas=True
):
    """
    将模板包完整应用到 Deck（全文档或指定页）：
    - 自动自适应画布纵横比与安全区坐标
    - 更新页面背景与包内底层锁定装饰层
    - 对所有元件执行 content 水合 + compile_component 全套功能有色卡片与皮肤重渲染
    """
    from core.schema import compile_component

    old_tpl = get_template(deck.get('templateId') or DEFAULT_TEMPLATE_ID)
    old_canvas = copy.deepcopy(deck.get('canvas') or old_tpl.get('canvas'))
    tpl = get_template(template_id)
    pal = tpl['palette']
    bgs = tpl['backgrounds']

    if scope == 'deck' and adapt_canvas:
        rescale_deck_canvas(deck, old_canvas, tpl['canvas'], old_tpl.get('skeleton'), tpl.get('skeleton'))

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
        is_sec_slide = any(c.get('type') == 'section-divider' for c in comps)

        slide['background'] = copy.deepcopy(bgs['cover'] if (is_cover_slide or is_sec_slide) else bgs['body'])
        slide['decorations'] = build_slide_decorations(tpl, is_cover=is_cover_slide, is_section=is_sec_slide, slide_idx=s_idx + 1)

        if not rerender_components:
            continue

        for comp in comps:
            ctype = comp.get('type', 'info-card')
            st = comp.setdefault('style', {})
            st['accentColor'] = pal['accent']
            st['fontFamily'] = pal.get('fontFamily', '微软雅黑')

            hydrate_component_content(comp)

            if comp.pop('_preserveMultiCard', False):
                _restyle_preserved_multicard(comp, tpl)
                continue

            tone_key = (comp.get('content') or {}).get('tone')
            if tone_key not in ('pass', 'promoted', 'warn', 'reject', 'rollback'):
                if ctype in ('slide-header', 'cover-divider', 'section-divider'):
                    st['fill'] = pal['bannerBg']
                    st['borderColor'] = pal['primary']
                    st['titleColor'] = pal['titleColor']
                    st['bodyColor'] = pal['mutedColor']
                elif ctype == 'footer-banner':
                    st['fill'] = pal['bannerBg']
                    st['borderColor'] = pal['bannerBorder']
                    st['titleColor'] = pal['primary']
                    st['bodyColor'] = pal['bodyColor']
                else:
                    for k in ('fill', 'borderColor', 'titleColor', 'bodyColor'):
                        st[k] = None
            else:
                for k in ('fill', 'borderColor', 'titleColor', 'bodyColor'):
                    st[k] = None

            compile_component(comp, tpl)

    return deck
