import copy
import uuid
from core.templates import get_template, DEFAULT_TEMPLATE_ID, DEFAULT_SEMANTIC_TOKENS

COMPONENT_TYPES = [
    {
        'type': 'info-card',
        'name': 'info-card',
        'icon': '',
        'desc': '圆角容器 + 强调条/光晕 + 标题 + 结构化条目列表（最高频通用信息卡片）'
    },
    {
        'type': 'slide-header',
        'name': 'slide-header',
        'icon': '',
        'desc': '顶栏色条/高亮砖 + 章节胶囊 + 页面主标题 + 副标题导语 + 右上角页码'
    },
    {
        'type': 'footer-banner',
        'name': 'footer-banner',
        'icon': '',
        'desc': '底部结论横幅（含加粗结论前缀/终端符号与核心结论正文）'
    },
    {
        'type': 'kpi-card',
        'name': 'kpi-card',
        'icon': '',
        'desc': '顶部铭牌胶囊 + 中部图表 + 底部大字号指标与要点'
    },
    {
        'type': 'process-flow',
        'name': 'process-flow',
        'icon': '',
        'desc': '横向等距排列的多个步骤节点卡片 + 节点间连接线/箭头'
    },
    {
        'type': 'data-table',
        'name': 'data-table',
        'icon': '',
        'desc': '主题色表头 + 斑马纹结构化多列数据表格'
    },
    {
        'type': 'image-frame',
        'name': 'image-frame',
        'icon': '',
        'desc': '精装画框容器 + 内嵌图表/图片 + HUD取景框/图注说明'
    },
    {
        'type': 'tag-badge',
        'name': 'tag-badge',
        'icon': '',
        'desc': '实心主题色胶囊标签或机能切角序号条'
    },
    {
        'type': 'toc-list',
        'name': 'toc-list',
        'icon': '',
        'desc': '多章节序号铭牌 + 章节主标题 + 摘要 + 分割线'
    },
    {
        'type': 'cover-divider',
        'name': 'cover-divider',
        'icon': '',
        'desc': '封面/主题大横幅、几何装饰矩阵与汇报人元信息区'
    },
    {
        'type': 'section-divider',
        'name': 'section-divider',
        'icon': '',
        'desc': '独立章节过渡页（穿透色带 + 大号章节标题 + 半透明序号水印）'
    },
    {
        'type': 'milestone-timeline',
        'name': 'milestone-timeline',
        'icon': '',
        'desc': '双环科技图标里程碑时间轴（年代/阶段胶囊 + 图标徽章 + 演进摘要）'
    },
    {
        'type': 'vertical-stack',
        'name': 'vertical-stack',
        'icon': '',
        'desc': '纵向分层架构栈/优先级阶梯 + 层间自动居中箭头'
    },
    {
        'type': 'decision-gate',
        'name': 'decision-gate',
        'icon': '',
        'desc': '顶部判定节点（菱形/圆角框）+ 正交分叉线 + 多状态分支结果卡'
    },
    {
        'type': 'stage-funnel',
        'name': 'stage-funnel',
        'icon': '',
        'desc': '横向多级筛选与归因漏斗（燕尾导向头 + 定量损耗框 + 总结横条）'
    },
    {
        'type': 'iteration-lanes',
        'name': 'iteration-lanes',
        'icon': '',
        'desc': '多轮实验演进泳道（四态语义头 + 实虚线流转箭头 + 演进拓扑条）'
    },
    {
        'type': 'rule-checklist',
        'name': 'rule-checklist',
        'icon': '',
        'desc': '带矢量语义徽章的红线规则清单与键值参数矩阵'
    }
]

TONE_PALETTE = {
    'navy':     {'bg': '#F4F6F9', 'border': '#1B365D', 'stripe': '#1B365D', 'badgeBg': '#1B365D', 'badgeFg': '#FFFFFF', 'title': '#1B365D', 'body': '#334155'},
    'burgundy': {'bg': '#FAF4F6', 'border': '#7A2048', 'stripe': '#7A2048', 'badgeBg': '#7A2048', 'badgeFg': '#FFFFFF', 'title': '#7A2048', 'body': '#334155'},
    'orange':   {'bg': '#FFF5EE', 'border': '#F26B21', 'stripe': '#F26B21', 'badgeBg': '#F26B21', 'badgeFg': '#FFFFFF', 'title': '#D45500', 'body': '#333333'},
    'blue':     {'bg': '#F0F5FF', 'border': '#1E6CFF', 'stripe': '#1E6CFF', 'badgeBg': '#1E6CFF', 'badgeFg': '#FFFFFF', 'title': '#0F4CD6', 'body': '#334155'},
    'pass':     {'bg': '#F6FAF8', 'border': '#2E6F54', 'stripe': '#2E6F54', 'badgeBg': '#2E6F54', 'badgeFg': '#FFFFFF', 'title': '#1E523C', 'body': '#334155'},
    'promoted': {'bg': '#F6FAF8', 'border': '#2E6F54', 'stripe': '#2E6F54', 'badgeBg': '#2E6F54', 'badgeFg': '#FFFFFF', 'title': '#1E523C', 'body': '#334155'},
    'warn':     {'bg': '#FAF7F2', 'border': '#A1681E', 'stripe': '#B87A28', 'badgeBg': '#A1681E', 'badgeFg': '#FFFFFF', 'title': '#7C4E12', 'body': '#334155'},
    'reject':   {'bg': '#FAF4F5', 'border': '#8C2D3C', 'stripe': '#8C2D3C', 'badgeBg': '#8C2D3C', 'badgeFg': '#FFFFFF', 'title': '#7A2048', 'body': '#334155'},
    'rollback': {'bg': '#FAF4F5', 'border': '#8C2D3C', 'stripe': '#8C2D3C', 'badgeBg': '#8C2D3C', 'badgeFg': '#FFFFFF', 'title': '#7A2048', 'body': '#334155'},
    'neutral':  {'bg': '#F8FAFC', 'border': '#94A3B8', 'stripe': '#64748B', 'badgeBg': '#475569', 'badgeFg': '#FFFFFF', 'title': '#334155', 'body': '#475569'},
    'baseline': {'bg': '#F8FAFC', 'border': '#94A3B8', 'stripe': '#64748B', 'badgeBg': '#475569', 'badgeFg': '#FFFFFF', 'title': '#334155', 'body': '#475569'},
    'final':    {'bg': '#EDF2F8', 'border': '#1B365D', 'stripe': '#1B365D', 'badgeBg': '#1B365D', 'badgeFg': '#FFFFFF', 'title': '#1B365D', 'body': '#334155'},
    'emerald':  {'bg': '#F0FDFA', 'border': '#0D9488', 'stripe': '#0D9488', 'badgeBg': '#0D9488', 'badgeFg': '#FFFFFF', 'title': '#0F766E', 'body': '#334155'},
    'terra':    {'bg': '#FFFFFF', 'border': '#27272A', 'stripe': '#18181B', 'badgeBg': '#18181B', 'badgeFg': '#D0E516', 'title': '#141413', 'body': '#2E2D2A'}
}


def _get_asset_base(tpl):
    if tpl and tpl.get('assetBaseUrl'):
        return tpl['assetBaseUrl']
    src = (tpl or {}).get('source', 'local')
    tid = (tpl or {}).get('id', 'terra_quest')
    return f"/templates/{src}/{tid}/assets"


def _get_icon_paths(tpl, variant='lime'):
    base = _get_asset_base(tpl)
    return [
        f'{base}/icon_flask_{variant}.png',
        f'{base}/icon_gear_{variant}.png',
        f'{base}/icon_board_{variant}.png',
        f'{base}/icon_chart_{variant}.png',
    ]


def _is_terra_skin(tpl):
    return bool(tpl and tpl.get('skeleton', {}).get('skin') == 'terra_quest')


def _is_editorial_skin(tpl):
    return bool(tpl and tpl.get('skeleton', {}).get('skin') == 'editorial_aura')


def get_tone(tone_key, template=None, default='info'):
    """基于模板原生 palette.semantic 令牌返回同源功能色，彻底消除跨模板撞色违和。"""
    key = str(tone_key or '').lower().strip()
    alias = {
        'promoted': 'pass', 'emerald': 'pass', 'lime': 'pass',
        'amber': 'warn',
        'rollback': 'reject',
        'baseline': 'neutral',
        'primary': 'info', 'final': 'info', 'navy': 'info', 'blue': 'info', 'terra': 'info', 'orange': 'info',
        'accent': 'accent', 'burgundy': 'accent',
    }
    norm = alias.get(key, key) or default
    pal = (template or {}).get('palette', {}) if template else {}
    sem_map = pal.get('semantic') or DEFAULT_SEMANTIC_TOKENS

    if norm in sem_map and isinstance(sem_map[norm], dict):
        tok = dict(sem_map[norm])
        tok.setdefault('stripe', tok.get('badgeBg') or tok.get('border'))
        return tok

    if norm == 'accent':
        if _is_terra_skin(template) or _is_editorial_skin(template):
            return dict(sem_map.get('pass', DEFAULT_SEMANTIC_TOKENS['pass']))
        if template:
            c = pal.get('accent', '#7A2048')
            hx = str(c).lstrip('#').strip()
            lum = 0.2
            if len(hx) == 6:
                try:
                    lum = (0.2126 * int(hx[0:2], 16) + 0.7152 * int(hx[2:4], 16) + 0.0722 * int(hx[4:6], 16)) / 255.0
                except Exception:
                    lum = 0.2
            if lum > 0.48:
                return dict(sem_map.get('pass', DEFAULT_SEMANTIC_TOKENS['pass']))
            return {
                'bg': pal.get('cardAltBg', '#FAF4F6'),
                'border': c,
                'stripe': c,
                'badgeBg': c,
                'badgeFg': '#FFFFFF',
                'title': c,
                'body': pal.get('bodyColor', '#334155')
            }

    if template:
        tok = dict(sem_map.get('info', DEFAULT_SEMANTIC_TOKENS['info']))
        tok.setdefault('stripe', tok.get('badgeBg') or tok.get('border'))
        return tok

    return TONE_PALETTE.get(key, TONE_PALETTE.get(default, TONE_PALETTE['navy']))


def make_run(text, fontSize=10.5, bold=False, color='#333333', fontFamily='微软雅黑', alpha=None, letterSpacing=None):
    r = {
        'text': text,
        'fontSize': fontSize,
        'bold': bold,
        'italic': False,
        'color': color,
        'fontFamily': fontFamily
    }
    if alpha is not None and alpha < 0.999:
        r['alpha'] = round(float(alpha), 3)
    if letterSpacing is not None:
        r['letterSpacing'] = round(float(letterSpacing), 2)
    return r


def make_para(runs, align='left', spaceBefore=0.0, spaceAfter=4.0):
    return {
        'align': align,
        'spaceBefore': spaceBefore,
        'spaceAfter': spaceAfter,
        'lineSpacing': None,
        'lineSpacingPct': None,
        'runs': runs,
        'text': ''.join(r['text'] for r in runs)
    }


def _make_child_shape(cid, idx, role, name, bx, by, rel_x, rel_y, rel_w, rel_h,
                      geom='roundRect', fill=None, border_color=None, border_width=1.2,
                      text_body=None, adj=10000, flip_h=False, flip_v=False,
                      head_end=None, tail_end=None, dash_style=None,
                      rotation=None, fill_alpha=None, border_alpha=None, grad_fill=None, shadow=False):
    ch = {
        'id': f"{cid}_ch{idx}",
        'rawType': 'shape',
        'role': role,
        'name': name,
        'x': round(bx + rel_x, 2),
        'y': round(by + rel_y, 2),
        'w': round(max(rel_w, 0.0), 2),
        'h': round(max(rel_h, 0.0), 2),
        'relX': round(rel_x, 2),
        'relY': round(rel_y, 2),
        'relW': round(max(rel_w, 0.0), 2),
        'relH': round(max(rel_h, 0.0), 2),
        'geom': geom,
        'fill': fill,
        'borderColor': border_color,
        'borderWidth': border_width,
        'textBody': text_body
    }
    if geom in ('roundRect', 'parallelogram', 'plaque') and adj is not None:
        ch['adj'] = adj
    if flip_h:
        ch['flipH'] = True
    if flip_v:
        ch['flipV'] = True
    if head_end:
        ch['headEnd'] = head_end
    if tail_end:
        ch['tailEnd'] = tail_end
    if dash_style and dash_style != 'solid':
        ch['dashStyle'] = dash_style
    if rotation:
        ch['rotation'] = round(float(rotation), 2)
    if fill_alpha is not None and fill_alpha < 0.999:
        ch['fillAlpha'] = round(float(fill_alpha), 3)
    if border_alpha is not None and border_alpha < 0.999:
        ch['borderAlpha'] = round(float(border_alpha), 3)
    if grad_fill:
        ch['gradFill'] = grad_fill
    if shadow:
        ch['shadow'] = True
    return ch


def _make_child_image(cid, idx, role, name, bx, by, rel_x, rel_y, rel_w, rel_h, src, opacity=None, rotation=None):
    im = {
        'id': f"{cid}_ch{idx}",
        'rawType': 'image',
        'role': role,
        'name': name,
        'x': round(bx + rel_x, 2),
        'y': round(by + rel_y, 2),
        'w': round(max(rel_w, 1.0), 2),
        'h': round(max(rel_h, 1.0), 2),
        'relX': round(rel_x, 2),
        'relY': round(rel_y, 2),
        'relW': round(max(rel_w, 1.0), 2),
        'relH': round(max(rel_h, 1.0), 2),
        'src': src
    }
    if opacity is not None and opacity < 0.999:
        im['opacity'] = round(float(opacity), 3)
    if rotation:
        im['rotation'] = round(float(rotation), 2)
    return im


def _split_item_prefix(item_str, bold_color='#1E293B', body_color='#334155', font_sz=10.0, font='微软雅黑'):
    """智能拆分条目中的小标题与正文（支持 '标签：正文'、'标签 | 正文' 或 '标签\\n正文'）。"""
    txt = str(item_str or '')
    for sep in ('：', ': ', ' | ', '\n'):
        if sep in txt:
            pre, rest = txt.split(sep, 1)
            if len(pre.strip()) <= 26:
                lead = pre + ('\n' if sep == '\n' else ('：' if sep in ('：', ' | ') else ': '))
                return [
                    make_run(lead, font_sz, True, bold_color, font),
                    make_run(rest, font_sz, False, body_color, font)
                ]
    return [make_run(txt, font_sz, False, body_color, font)]


def _terra_glow(accent_hex='#D0E516', alpha_start=0.28, angle=0.0):
    return {
        'angle': angle,
        'stops': [
            {'pos': 0.0, 'color': accent_hex, 'alpha': alpha_start},
            {'pos': 0.55, 'color': accent_hex, 'alpha': round(alpha_start * 0.45, 3)},
            {'pos': 1.0, 'color': accent_hex, 'alpha': 0.0}
        ]
    }


def compile_component(comp, template=None):
    """根据外框尺寸、layout 参数、style、template 皮肤与结构化 content 编译全 17 类元件的 children。"""
    tpl = template or get_template(DEFAULT_TEMPLATE_ID)
    pal = tpl.get('palette', {})
    skel = tpl.get('skeleton', {})
    is_terra = _is_terra_skin(tpl)
    is_editorial = _is_editorial_skin(tpl)
    canvas_w = float(tpl.get('canvas', {}).get('width', 1020.67))
    canvas_h = float(tpl.get('canvas', {}).get('height', 680.33))

    ctype = comp.get('type', 'info-card')
    cid = comp.get('id') or f"comp_{uuid.uuid4().hex[:8]}"
    comp['id'] = cid
    bx = float(comp.get('x', 60.0))
    by = float(comp.get('y', 160.0))
    w = max(float(comp.get('w', 360.0)), 60.0)
    h = max(float(comp.get('h', 180.0)), 24.0)
    layout = comp.setdefault('layout', {})
    style = comp.setdefault('style', {})
    content = comp.setdefault('content', {})

    font = style.get('fontFamily') or pal.get('fontFamily', '微软雅黑')
    title_font = pal.get('titleFont') or font
    tpl_primary = pal.get('primary', '#1B365D')
    tpl_accent = pal.get('accent', '#7A2048')
    title_sz = float(style.get('titleSize') or 12.0)
    body_sz = float(style.get('bodySize') or 10.0)
    px = float(layout.get('paddingX', 12.0))
    py = float(layout.get('paddingY', 10.0))
    header_gap = float(layout.get('headerGap', 8.0))
    item_gap = float(layout.get('itemGap', 5.5))

    children = []
    idx = 0

    def next_idx():
        nonlocal idx
        idx += 1
        return idx

    # -------------------- 1. slide-header --------------------
    if ctype == 'slide-header':
        title = str(content.get('title') or '页面主标题')
        subtitle = str(content.get('subtitle') or '')
        section_tag = str(content.get('sectionTag') or content.get('tag') or '').strip()
        page_num = str(content.get('pageNumber') or '').strip()
        hdr_style = skel.get('headerStyle', 'academic_ribbon')
        t_color = style.get('titleColor') or pal.get('titleColor', '#1B365D')
        b_color = style.get('bodyColor') or pal.get('mutedColor', '#64748B')
        margin_x = float(skel.get('defaultMarginX', 48.0))

        if hdr_style == 'terra_hud' or is_terra:
            comp['x'], comp['y'] = 0.0, 0.0
            bx, by = 0.0, 0.0
            w, h = canvas_w, 118.0
            comp['w'], comp['h'] = w, h
            # 左上角微标签 + 短粗标尺线
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'hud-anchor', bx, by,
                margin_x, 21.0, 10.0, 10.0, geom='rect', fill='#18181B', border_color=None, border_width=0.0
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'connector', 'hud-top-rule', bx, by,
                margin_x + 12.0, 26.0, 140.0, 0.0, geom='line', border_color='#18181B', border_width=1.0, border_alpha=0.6
            ))
            sec_txt = section_tag or 'PRTS // MODULE'
            children.append(_make_child_shape(
                cid, next_idx(), 'step-box', '章节微标', bx, by,
                margin_x + 158.0, 14.0, min(260.0, max(128.0, len(sec_txt) * 11.5 + 24.0)), 22.0,
                geom='rect', fill=None, border_color=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(sec_txt, 9.0, True, '#736F68', font, letterSpacing=0.8)], spaceAfter=0.0)]}
            ))
            # 主标题底部左斜切亮荧光青柠砖块（复刻 Slide 13 经典设计）
            hl_w = min(220.0, max(90.0, len(title) * 14.5))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'lime-highlight-brick', bx, by,
                margin_x - 2.0, 62.0, hl_w, 15.0, geom='rect', fill='#D0E516', border_color=None, border_width=0.0
            ))
            inner_w = round(w - margin_x * 2 - 220.0, 2)
            children.append(_make_child_shape(
                cid, next_idx(), 'title', '页面主标题', bx, by,
                margin_x, 38.0, inner_w, 40.0, geom='rect', fill=None, border_color=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(title, 20.5, True, '#141413', title_font)], spaceAfter=0.0)]}
            ))
            # 标题下方水平标尺线 + 左侧黑方块锚点
            children.append(_make_child_shape(
                cid, next_idx(), 'connector', 'hud-divider', bx, by,
                margin_x, 82.0, round(w - margin_x * 2, 2), 0.0, geom='line',
                border_color='#18181B', border_width=1.0, border_alpha=0.55
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'hud-line-cap', bx, by,
                round(w - margin_x - 12.0, 2), 77.0, 12.0, 10.0, geom='rect', fill='#18181B', border_color=None, border_width=0.0
            ))
            if subtitle:
                children.append(_make_child_shape(
                    cid, next_idx(), 'subtitle', '页面副标题', bx, by,
                    margin_x, 88.0, round(w - margin_x * 2 - 40.0, 2), 26.0, geom='rect',
                    fill=None, border_color=None, border_width=0.0,
                    text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                               'paragraphs': [make_para([make_run(subtitle, 10.5, False, '#52504C', font)], spaceAfter=0.0)]}
                ))
            # 右上角曜石黑铭牌胶囊 + 页码 + TERRA SYSTEM
            badge_w = 185.0
            badge_x = round(w - margin_x - badge_w - 28.0, 2)
            p_display = f"P // {page_num}" if page_num else "ANALYSIS"
            children.append(_make_child_shape(
                cid, next_idx(), 'page-num', '机能页码胶囊', bx, by,
                badge_x, 18.0, badge_w, 24.0, geom='rect', fill='#18181B', border_color=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 8, 'top': 1, 'right': 8, 'bottom': 1},
                           'paragraphs': [make_para([make_run(f"TERRA LAB   |   {p_display}", 9.0, True, '#D0E516', font)], align='center', spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'hud-right-bar', bx, by,
                round(w - margin_x - 20.0, 2), 18.0, 14.0, 44.0, geom='rect', fill='#18181B', border_color=None, border_width=0.0
            ))
            # 右侧边缘微型四图形序列 (菱形/圆/三角/方, 复刻 Slide 13)
            for m_i, m_geom in enumerate(['diamond', 'oval', 'triangle', 'rect']):
                children.append(_make_child_shape(
                    cid, next_idx(), 'shape', f'hud-glyph-{m_i+1}', bx, by,
                    round(w - 30.0, 2), 22.0 + m_i * 15.0, 10.0, 10.0,
                    geom=m_geom, fill=None, border_color='#18181B', border_width=0.8, border_alpha=0.5
                ))
        elif hdr_style == 'editorial_star' or is_editorial:
            comp['x'], comp['y'] = 0.0, 0.0
            bx, by = 0.0, 0.0
            w, h = canvas_w, 120.0
            comp['w'], comp['h'] = w, h
            # 左上标志性 star4 四角星芒 + 纤细水平连接线 + 章节标签
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'star-anchor', bx, by,
                margin_x, 15.0, 24.0, 24.0, geom='star4', fill=tpl_primary, border_width=0.0, adj=16000
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'connector', 'star-rule', bx, by,
                margin_x + 28.0, 27.0, 96.0, 0.0, geom='line', border_color=tpl_primary, border_width=1.0, border_alpha=0.75
            ))
            sec_txt = section_tag or 'EDITORIAL REPORT'
            children.append(_make_child_shape(
                cid, next_idx(), 'step-box', '章节微标', bx, by,
                margin_x + 132.0, 15.0, min(300.0, max(120.0, len(sec_txt) * 11.0 + 24.0)), 24.0,
                geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(sec_txt, 9.5, True, pal.get('mutedColor', '#5E616B'), font, letterSpacing=0.8)], spaceAfter=0.0)]}
            ))
            # 标题下衬托柔和抹茶-燕麦渐变柔光条
            hl_w = min(300.0, max(120.0, len(title) * 16.0))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'editorial-aura-hl', bx, by,
                margin_x - 2.0, 62.0, hl_w, 16.0, geom='roundRect', fill=None, border_width=0.0, adj=30000,
                grad_fill={'angle': 0, 'stops': [
                    {'pos': 0.0, 'color': tpl_accent, 'alpha': 0.62},
                    {'pos': 0.65, 'color': pal.get('cardAltBg', '#E0E0CC'), 'alpha': 0.35},
                    {'pos': 1.0, 'color': '#FFFFFF', 'alpha': 0.0}
                ]}
            ))
            inner_w = round(w - margin_x * 2 - 140.0, 2)
            children.append(_make_child_shape(
                cid, next_idx(), 'title', '页面主标题', bx, by,
                margin_x, 40.0, inner_w, 38.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(title, 20.5, True, tpl_primary, title_font)], spaceAfter=0.0)]}
            ))
            if subtitle:
                children.append(_make_child_shape(
                    cid, next_idx(), 'subtitle', '页面副标题', bx, by,
                    margin_x, 82.0, round(w - margin_x * 2 - 20.0, 2), 26.0, geom='rect', fill=None, border_width=0.0,
                    text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                               'paragraphs': [make_para([make_run(subtitle, 10.5, False, b_color, font)], spaceAfter=0.0)]}
                ))
            # 右上角细框杂志页码胶囊 + 小星点
            p_txt = f"No. {int(page_num):02d}" if page_num.isdigit() else (f"No. {page_num}" if page_num else "AURA")
            children.append(_make_child_shape(
                cid, next_idx(), 'page-num', '页码胶囊', bx, by,
                round(w - margin_x - 102.0, 2), 18.0, 102.0, 26.0, geom='roundRect',
                fill='#FFFFFF', fill_alpha=0.75, border_color=tpl_primary, border_width=0.9, adj=30000,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 6, 'top': 1, 'right': 6, 'bottom': 1},
                           'paragraphs': [make_para([make_run(p_txt, 9.5, True, tpl_primary, font)], align='center', spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'divider', '页眉分割线', bx, by,
                margin_x, 114.0, round(w - margin_x * 2, 2), 0.0, geom='line',
                border_color=tpl_primary, border_width=0.8, border_alpha=0.25
            ))
        elif hdr_style == 'corporate_minimal':
            mx = 0.0 if bx >= 30.0 else margin_x
            tw = max(200.0, w - mx * 2 - 40.0)
            if page_num:
                children.append(_make_child_shape(
                    cid, next_idx(), 'page-num', 'page-num', bx, by,
                    w - mx - 60.0, 2.0, 60.0, 18.0, geom='rect',
                    fill=None, border_color=None, border_width=0.0,
                    text_body={'valign': 'top', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                               'paragraphs': [make_para([make_run(page_num, 8.8, False, b_color, font)], align='right', spaceAfter=0.0)]}
                ))
            children.append(_make_child_shape(
                cid, next_idx(), 'title', 'title', bx, by,
                mx, 36.0, tw, 36.0, geom='rect',
                fill=None, border_color=None, border_width=0.0,
                text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(title, 20.0, True, '#333333', font)], spaceAfter=0.0)]}
            ))
            if subtitle:
                children.append(_make_child_shape(
                    cid, next_idx(), 'subtitle', 'subtitle', bx, by,
                    mx, 76.0, tw, 28.0, geom='rect',
                    fill=None, border_color=None, border_width=0.0,
                    text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                               'paragraphs': [make_para([make_run(subtitle, 10.5, False, b_color, font)], spaceAfter=0.0)]}
                ))
        else:
            comp['x'], comp['y'] = 0.0, 0.0
            bx, by = 0.0, 0.0
            w = canvas_w
            comp['w'] = w
            comp['h'] = 120.0
            h = 120.0
            split_x = round(w * 0.803, 2)
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', '顶栏色条-主色', bx, by,
                0.0, 0.0, split_x, 4.82, geom='rect', fill=tpl_primary, border_color=None, border_width=0.0
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', '顶栏色条-强调色', bx, by,
                split_x, 0.0, round(w - split_x, 2), 4.82, geom='rect', fill=tpl_accent, border_color=None, border_width=0.0
            ))
            inner_w = round(w - margin_x * 2, 2)
            if section_tag:
                pill_w = min(280.0, max(120.0, len(section_tag) * 12.5 + 32.0))
                children.append(_make_child_shape(
                    cid, next_idx(), 'step-box', '章节胶囊标签', bx, by,
                    margin_x, 16.5, pill_w, 23.5, geom='roundRect',
                    fill=pal.get('bannerBg', '#EDF2F8'), border_color=tpl_primary, border_width=0.8,
                    text_body={
                        'valign': 'middle', 'wrap': False,
                        'padding': {'left': 8.0, 'top': 1.0, 'right': 8.0, 'bottom': 1.0},
                        'paragraphs': [make_para([make_run(section_tag, 8.8, True, tpl_primary, font)], align='center', spaceAfter=0.0)]
                    },
                    adj=20000
                ))
            if page_num:
                children.append(_make_child_shape(
                    cid, next_idx(), 'page-num', '页码', bx, by,
                    w - margin_x - 90.0, 16.5, 90.0, 23.5, geom='rect', fill=None, border_color=None, border_width=0.0,
                    text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                               'paragraphs': [make_para([make_run(page_num, 9.5, False, b_color, font)], align='right', spaceAfter=0.0)]}
                ))
            title_y = 46.5 if (section_tag or page_num) else 24.0
            children.append(_make_child_shape(
                cid, next_idx(), 'title', '页面主标题', bx, by,
                margin_x, title_y, inner_w, 36.5, geom='rect', fill=None, border_color=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(title, 19.0, True, t_color, font)], spaceAfter=0.0)]}
            ))
            if subtitle:
                children.append(_make_child_shape(
                    cid, next_idx(), 'subtitle', '页面副标题', bx, by,
                    margin_x, round(title_y + 39.5, 2), inner_w, 25.5, geom='rect', fill=None, border_color=None, border_width=0.0,
                    text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                               'paragraphs': [make_para([make_run(subtitle, 10.5, False, b_color, font)], spaceAfter=0.0)]}
                ))
            children.append(_make_child_shape(
                cid, next_idx(), 'divider', '页眉分割线', bx, by,
                margin_x, 119.5, inner_w, 0.0, geom='line', fill=None, border_color='#CBD5E1', border_width=1.0
            ))
        comp['children'] = children
        return comp

    # -------------------- 2. cover-divider --------------------
    if ctype == 'cover-divider':
        cover_style = skel.get('coverStyle', 'academic_banner')
        tag_txt = str(content.get('tag') or content.get('badge') or '').strip()
        title_txt = str(content.get('title') or '汇报核心主题名称')
        sub_txt = str(content.get('subtitle') or '')
        items = content.get('items') or []
        meta_lines = content.get('meta') or ([str(x) for x in items[2:]] if len(items) > 2 else [])
        if not tag_txt and items and str(items[0]).strip() != title_txt.strip() and len(str(items[0])) <= 28:
            tag_txt = str(items[0]).strip()

        if cover_style == 'terra_prts' or is_terra:
            asset_base = _get_asset_base(tpl)
            comp['x'], comp['y'] = 0.0, 0.0
            bx, by = 0.0, 0.0
            w, h = canvas_w, canvas_h
            comp['w'], comp['h'] = w, h
            # 右侧环形 HUD 与右下几何晶体簇底纹
            children.append(_make_child_image(
                cid, next_idx(), 'shape', 'ring-hud-cover', bx, by,
                round(w - 430.0, 2), 95.0, 460.0, 460.0, f'{asset_base}/ring_hud.png', opacity=0.22
            ))
            children.append(_make_child_image(
                cid, next_idx(), 'shape', 'tech-emblem-cover', bx, by,
                round(w - 255.0, 2), round(h - 165.0, 2), 115.0, 108.0, f'{asset_base}/crystal_cluster.png', opacity=0.26
            ))
            # 顶部 HUD 标头
            children.append(_make_child_shape(cid, next_idx(), 'shape', 'top-sq', bx, by, 92.0, 56.0, 14.0, 14.0, geom='rect', fill='#18181B', border_width=0.0))
            children.append(_make_child_shape(cid, next_idx(), 'connector', 'top-ln', bx, by, 108.0, 63.0, 96.0, 0.0, geom='line', border_color='#18181B', border_width=1.4))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'top-sys-lbl', bx, by, 212.0, 48.0, 260.0, 28.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(tag_txt or 'PRTS // SYNTHESIS', 11.5, True, '#18181B', font, letterSpacing=1.2)], spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'top-right-lab', bx, by, round(w - 310.0, 2), 48.0, 180.0, 38.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [
                               make_para([make_run('TERRA LAB // DATA', 11.0, True, '#18181B', font)], align='right', spaceAfter=1.0),
                               make_para([make_run('COMPONENT ENGINE 05', 9.0, False, '#736F68', font)], align='right', spaceAfter=0.0)
                           ]}
            ))
            children.append(_make_child_shape(cid, next_idx(), 'shape', 'top-rbar', bx, by, round(w - 118.0, 2), 46.0, 18.0, 48.0, geom='rect', fill='#18181B', border_width=0.0))

            # 左侧六边形蜂巢装饰群（复刻 Slide 1 六边形集群）
            hex_specs = [
                (96.0, 240.0, 48.0, 42.0, '#18181B', None, 0.0),
                (142.0, 232.0, 22.0, 19.0, '#18181B', None, 0.0),
                (108.0, 204.0, 32.0, 28.0, '#D0E516', None, 0.0),
                (176.0, 204.0, 15.0, 13.0, '#18181B', None, 0.0),
                (44.0, 230.0, 74.0, 64.0, None, '#52504C', 1.8),
                (128.0, 298.0, 48.0, 42.0, '#D0E516', None, 0.0),
            ]
            for hx, hy, hw, hh, hf, hb, hbw in hex_specs:
                children.append(_make_child_shape(
                    cid, next_idx(), 'shape', 'hex-node', bx, by, hx, hy, hw, hh,
                    geom='hexagon', fill=hf, border_color=hb, border_width=hbw
                ))

            # 主标题前垂直渐隐青柠装饰柱
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'hero-lime-pillar', bx, by, 260.0, 180.0, 44.0, 240.0, geom='rect',
                fill='#D0E516', border_width=0.0,
                grad_fill={'angle': 90, 'stops': [{'pos': 0.0, 'color': '#D0E516', 'alpha': 0.92}, {'pos': 1.0, 'color': '#D0E516', 'alpha': 0.15}]}
            ))

            # 上下双黑细线 + 曜石黑主标题 + 副标题铭牌
            children.append(_make_child_shape(cid, next_idx(), 'connector', 'hero-top-ln', bx, by, 326.0, 196.0, 620.0, 0.0, geom='line', border_color='#18181B', border_width=1.5))
            t_len = len(title_txt.replace('\n', ''))
            t_sz = 38.0 if t_len <= 18 else (30.0 if t_len <= 30 else 25.0)
            children.append(_make_child_shape(
                cid, next_idx(), 'title', '封面主标题', bx, by, 326.0, 206.0, 680.0, 136.0, geom='rect',
                fill=None, border_width=0.0, shadow=False,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 4, 'right': 0, 'bottom': 4},
                           'paragraphs': [make_para([make_run(title_txt, t_sz, True, '#141413', title_font)], spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'hero-badge', bx, by, 326.0, 354.0, 268.0, 26.0, geom='rect',
                fill='#18181B', border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 10, 'top': 1, 'right': 10, 'bottom': 1},
                           'paragraphs': [make_para([make_run('SYNTHESIZE  //  INFORMATION', 10.5, True, '#D0E516', font)], spaceAfter=0.0)]}
            ))
            if sub_txt:
                children.append(_make_child_shape(
                    cid, next_idx(), 'subtitle', '封面副标题', bx, by, 326.0, 390.0, 680.0, 56.0, geom='rect',
                    fill=None, border_width=0.0,
                    text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 0, 'top': 2, 'right': 0, 'bottom': 2},
                               'paragraphs': [make_para([make_run(sub_txt, 14.0, False, '#3E3C38', font)], spaceAfter=0.0)]}
                ))
            children.append(_make_child_shape(cid, next_idx(), 'connector', 'hero-bot-ln', bx, by, 326.0, 456.0, 620.0, 0.0, geom='line', border_color='#18181B', border_width=1.5))

            # 左下垂直黑标尺 + 元信息文字 + 底部渐变小块
            children.append(_make_child_shape(cid, next_idx(), 'shape', 'bot-vbar', bx, by, 86.0, 520.0, 11.0, 140.0, geom='rect', fill='#18181B', border_width=0.0))
            if not meta_lines:
                meta_lines = items[:4] if (items and not (len(items) == 1 and items[0] == tag_txt)) else [
                    '系统引擎：Pretty PPT · PRTS Visual System',
                    '设计范式：17 类标准组件 · 声明式栅格与多模板渲染'
                ]
            m_paras = [make_para(_split_item_prefix(ml, bold_color='#141413', body_color='#52504C', font_sz=11.0, font=font), spaceAfter=4.0) for ml in meta_lines[:4]]
            children.append(_make_child_shape(
                cid, next_idx(), 'subtitle', '封面底部元信息', bx, by, 110.0, 522.0, 740.0, 130.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0}, 'paragraphs': m_paras}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'bot-badge-05', bx, by, round(w - 140.0, 2), round(h - 90.0, 2), 48.0, 42.0, geom='rect',
                fill='#18181B', border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 2, 'top': 2, 'right': 2, 'bottom': 2},
                           'paragraphs': [make_para([make_run('PRTS', 8.5, True, '#D0E516', font)], align='center', spaceAfter=0.0)]}
            ))
        elif cover_style == 'editorial_aura' or is_editorial:
            comp['x'], comp['y'] = 0.0, 0.0
            bx, by = 0.0, 0.0
            w, h = canvas_w, canvas_h
            comp['w'], comp['h'] = w, h
            # 半透明柔和椭圆形杂志边框 + 标志性 star4 四角星芒
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'cover-aura-ring', bx, by,
                round(w * 0.14, 2), round(h * 0.21, 2), round(w * 0.72, 2), round(h * 0.42, 2), geom='oval',
                fill='#FFFFFF', fill_alpha=0.38, border_color=tpl_primary, border_width=1.1, border_alpha=0.65
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'cover-star-main', bx, by,
                round(w * 0.79, 2), round(h * 0.17, 2), 54.0, 54.0, geom='star4', fill=tpl_primary, border_width=0.0, adj=14500
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'cover-star-sub', bx, by,
                round(w * 0.15, 2), round(h * 0.56, 2), 26.0, 26.0, geom='star4', fill=tpl_primary, border_width=0.0, adj=14500
            ))
            # 顶部杂志序号胶囊与细线（按标签长度自适应宽度避免长文本溢出）
            top_tag = tag_txt or 'No. 01 // REPORT'
            est_w = sum(11.0 if ord(ch) > 127 else 6.8 for ch in top_tag) + 28.0
            tag_w = max(148.0, min(round(w * 0.48, 1), round(est_w, 1)))
            line_x = round(64.0 + tag_w + 10.0, 2)
            children.append(_make_child_shape(
                cid, next_idx(), 'step-box', '封面左上编号', bx, by,
                64.0, 46.0, tag_w, 28.0, geom='roundRect', fill=tpl_primary, border_width=0.0, adj=25000,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 10, 'top': 2, 'right': 10, 'bottom': 2},
                           'paragraphs': [make_para([make_run(top_tag, 9.5, True, '#FFFFFF', font)], align='center', spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'connector', '封面顶部细线', bx, by,
                line_x, 60.0, round(max(40.0, w - 64.0 - line_x), 2), 0.0, geom='line', border_color=tpl_primary, border_width=0.9, border_alpha=0.55
            ))
            # 居中大号封面主副标题
            t_len = len(title_txt.replace('\n', ''))
            t_sz = 36.0 if t_len <= 18 else (28.0 if t_len <= 30 else 24.0)
            hero_paras = [make_para([make_run(title_txt, t_sz, True, tpl_primary, title_font)], align='center', spaceAfter=12.0)]
            if sub_txt:
                hero_paras.append(make_para([make_run(sub_txt, 13.0, False, pal.get('bodyColor', '#2E2D2A'), font)], align='center', spaceAfter=0.0))
            children.append(_make_child_shape(
                cid, next_idx(), 'title', '封面主副标题', bx, by,
                round(w * 0.17, 2), round(h * 0.25, 2), round(w * 0.66, 2), round(h * 0.34, 2), geom='rect',
                fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 12, 'top': 6, 'right': 12, 'bottom': 6}, 'paragraphs': hero_paras}
            ))
            # 底部双胶囊横连桥 + 左下元信息衬底
            children.append(_make_child_shape(
                cid, next_idx(), 'connector', '底部连接桥线', bx, by,
                round(w * 0.28, 2), round(h * 0.72, 2), round(w * 0.44, 2), 0.0, geom='line', border_color=tpl_primary, border_width=1.2
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', '底部左胶囊', bx, by,
                round(w * 0.23, 2), round(h * 0.72 - 15.0, 2), 92.0, 30.0, geom='roundRect', fill=tpl_primary, border_width=0.0, adj=25000,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 4, 'top': 1, 'right': 4, 'bottom': 1},
                           'paragraphs': [make_para([make_run('No. 01', 10.0, True, '#FFFFFF', font)], align='center', spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', '底部右胶囊', bx, by,
                round(w * 0.77 - 92.0, 2), round(h * 0.72 - 15.0, 2), 92.0, 30.0, geom='roundRect',
                fill='#FFFFFF', fill_alpha=0.85, border_color=tpl_primary, border_width=1.0, adj=25000,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 4, 'top': 1, 'right': 4, 'bottom': 1},
                           'paragraphs': [make_para([make_run('DESIGN', 9.5, True, tpl_primary, font)], align='center', spaceAfter=0.0)]}
            ))
            if not meta_lines:
                meta_lines = items[:4] if (items and not (len(items) == 1 and items[0] == tag_txt)) else [
                    f"模板风格：{tpl.get('name', '极简弥散杂志风')}",
                    '17 类标准化组件 · 同源低饱和语义配色'
                ]
            m_paras = [make_para(_split_item_prefix(ml, bold_color=tpl_primary, body_color=pal.get('bodyColor', '#2E2D2A'), font_sz=10.5, font=font), spaceAfter=4.0) for ml in meta_lines[:4]]
            children.append(_make_child_shape(
                cid, next_idx(), 'subtitle', '封面元信息区', bx, by,
                64.0, round(h * 0.80, 2), round(w - 128.0, 2), 96.0, geom='roundRect',
                fill='#FFFFFF', fill_alpha=0.72, border_color=tpl_primary, border_width=0.6, border_alpha=0.25, adj=12000,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 16, 'top': 6, 'right': 16, 'bottom': 6}, 'paragraphs': m_paras}
            ))
        elif cover_style == 'corporate_stripe':
            comp['x'], comp['y'] = 0.0, 99.8
            bx, by = 0.0, 99.8
            w, h = 1020.67, 441.7
            comp['w'], comp['h'] = w, h
            step_code = tag_txt if (tag_txt and len(tag_txt) <= 4) else '01'
            children.append(_make_child_shape(
                cid, next_idx(), 'step-num', 'step-num', bx, by,
                59.7, 0.0, 53.6, 49.9, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'top', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(step_code, 26.4, True, '#333333', font)], spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'title', 'title', bx, by,
                126.3, 5.4, 650.7, 40.8, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(title_txt, 20.25, True, '#333333', font)], spaceAfter=0.0)]}
            ))
            band_paras = [make_para([make_run(title_txt, 20.0, True, '#FFFFFF', font)], spaceAfter=10.0)]
            if sub_txt:
                band_paras.append(make_para([make_run(sub_txt, 12.0, False, '#FFF7ED', font)], spaceAfter=0.0))
            children.append(_make_child_shape(
                cid, next_idx(), 'container', 'container', bx, by,
                0.0, 119.7, w, 322.0, geom='rect', fill=tpl_primary, border_color=tpl_primary, border_width=1.2,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 60.0, 'top': 20.0, 'right': 340.0, 'bottom': 20.0}, 'paragraphs': band_paras}
            ))
            children.append(_make_child_shape(cid, next_idx(), 'shape', 'decor-1', bx, by, 708.1, 119.7, 122.5, 322.0, geom='rect', fill='#F39A1E', border_width=0.0))
            children.append(_make_child_shape(cid, next_idx(), 'shape', 'decor-2', bx, by, 830.6, 119.7, 122.5, 322.0, geom='rect', fill=tpl_accent, border_width=0.0))
        else:
            comp['x'], comp['y'] = 0.0, 0.0
            bx, by = 0.0, 0.0
            w, h = canvas_w, canvas_h
            comp['w'], comp['h'] = w, h
            hero_h = round(h * 0.627, 2)
            children.append(_make_child_shape(cid, next_idx(), 'container', '封面主背景块', bx, by, 0.0, 0.0, w, hero_h, geom='rect', fill=tpl_primary, border_width=0.0))
            children.append(_make_child_shape(cid, next_idx(), 'shape', '右侧辅助装饰块', bx, by, round(w - 160.67, 2), 0.0, 160.67, hero_h, geom='rect', fill=pal.get('secondary', '#2B547E'), border_width=0.0))
            children.append(_make_child_shape(cid, next_idx(), 'divider', '中部强调色条', bx, by, 0.0, hero_h, w, 7.94, geom='rect', fill=tpl_accent, border_width=0.0))
            pill_label = tag_txt or 'RESEARCH & TECHNICAL REPORT'
            children.append(_make_child_shape(
                cid, next_idx(), 'step-box', '封面顶部标签胶囊', bx, by,
                64.0, 68.0, min(340.0, max(190.0, len(pill_label) * 11.0 + 48.0)), 38.0, geom='roundRect',
                fill=pal.get('secondary', '#2B547E'), border_color='#93C5FD', border_width=0.8,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 10.0, 'top': 2.0, 'right': 10.0, 'bottom': 2.0},
                           'paragraphs': [make_para([make_run(pill_label, 11.0, True, '#E2E8F0', font)], align='center', spaceAfter=0.0)]},
                adj=18000
            ))
            hero_paras = [make_para([make_run(title_txt, 27.0, True, '#FFFFFF', font)], spaceAfter=14.0)]
            if sub_txt:
                hero_paras.append(make_para([make_run(sub_txt, 13.5, False, '#E2E8F0', font)], spaceAfter=0.0))
            children.append(_make_child_shape(
                cid, next_idx(), 'title', '封面主副标题框', bx, by,
                64.0, 136.0, round(w - 160.0, 2), 250.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 0.0, 'top': 0.0, 'right': 0.0, 'bottom': 0.0}, 'paragraphs': hero_paras}
            ))
            if not meta_lines:
                meta_lines = items[:4] if (items and not (len(items) == 1 and items[0] == tag_txt)) else [
                    '汇报体系：17 类可复用标准化设计元件',
                    f"模板风格：{tpl.get('name', '学术深蓝')}"
                ]
            meta_paras = [make_para(_split_item_prefix(mline, bold_color=tpl_primary, body_color='#334155', font_sz=12.0, font=font), spaceAfter=6.0) for mline in meta_lines]
            children.append(_make_child_shape(
                cid, next_idx(), 'subtitle', '封面底部信息区', bx, by,
                84.0, round(hero_h + 50.0, 2), 740.0, 175.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 0.0, 'top': 4.0, 'right': 0.0, 'bottom': 0.0}, 'paragraphs': meta_paras}
            ))
        comp['children'] = children
        return comp

    # -------------------- 3. section-divider (新增) --------------------
    if ctype == 'section-divider':
        comp['x'], comp['y'] = 0.0, 0.0
        bx, by = 0.0, 0.0
        w, h = canvas_w, canvas_h
        comp['w'], comp['h'] = w, h
        sec_num = str(content.get('sectionNumber') or content.get('partCode') or 'PART 01').strip()
        sec_title = str(content.get('title') or '第一部分').strip()
        left_tag = str(content.get('leftLabel') or 'METHODOLOGY').strip()
        right_tag = str(content.get('rightLabel') or 'ARCHITECTURE').strip()

        band_w = round(w * 0.44, 2)
        band_x = round((w - band_w) / 2.0, 2)
        cy_mid = round(h * 0.50, 2)

        if is_terra:
            asset_base = _get_asset_base(tpl)
            children.append(_make_child_image(
                cid, next_idx(), 'shape', 'ring-hud-section', bx, by,
                round(w * 0.5 - 120.0, 2), round(cy_mid - 120.0, 2), 240.0, 240.0, f'{asset_base}/ring_hud.png', opacity=0.38
            ))
            # 居中穿透式荧光青柠横带（复刻 Slide 6 / Slide 12）
            band_w2 = round(w * 0.52, 2)
            band_x2 = round((w - band_w2) / 2.0, 2)
            children.append(_make_child_shape(
                cid, next_idx(), 'divider', 'section-lime-band', bx, by,
                band_x2, cy_mid - 11.0, band_w2, 22.0, geom='rect', fill='#D0E516', border_width=0.0
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'section-dot', bx, by,
                round(w * 0.5 - 14.0, 2), cy_mid - 14.0, 28.0, 28.0, geom='oval',
                fill=None, border_color='#18181B', border_width=1.8
            ))
            t_len = len(sec_title)
            sec_sz = 40.0 if t_len <= 10 else (31.0 if t_len <= 16 else 25.0)
            children.append(_make_child_shape(
                cid, next_idx(), 'title', '章节主标题', bx, by,
                round(w * 0.5 - 420.0, 2), cy_mid - 42.0, 840.0, 84.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(sec_title, sec_sz, True, '#141413', title_font)], align='center', spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'subtitle', '左英文标签', bx, by,
                band_x2 - 10.0, cy_mid - 74.0, 240.0, 30.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(left_tag, 15.0, True, '#736F68', font, letterSpacing=1.2)], align='left', spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'subtitle', '右英文标签', bx, by,
                round(band_x2 + band_w2 - 230.0, 2), cy_mid + 46.0, 240.0, 30.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(right_tag, 15.0, True, '#736F68', font, letterSpacing=1.2)], align='right', spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'step-num', '章节超大号水印', bx, by,
                round(w - 560.0, 2), round(h - 190.0, 2), 490.0, 150.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'bottom', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(sec_num, 82.0, True, '#18181B', font, alpha=0.14)], align='right', spaceAfter=0.0)]}
            ))
        elif is_editorial:
            # 左侧柔和双色渐变弥散圆晕 + 细黑描边环 + 右侧杂志编号与星芒标题
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'section-aura-orb', bx, by,
                round(w * 0.10, 2), round(h * 0.22, 2), round(h * 0.56, 2), round(h * 0.56, 2), geom='oval',
                fill=None, border_width=0.0,
                grad_fill={'angle': 135, 'stops': [
                    {'pos': 0.0, 'color': tpl_accent, 'alpha': 0.90},
                    {'pos': 0.72, 'color': pal.get('cardAltBg', '#E0E0CC'), 'alpha': 0.65},
                    {'pos': 1.0, 'color': '#FFFFFF', 'alpha': 0.0}
                ]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'section-wire-orb', bx, by,
                round(w * 0.13, 2), round(h * 0.26, 2), round(h * 0.48, 2), round(h * 0.48, 2), geom='oval',
                fill=None, border_color=tpl_primary, border_width=1.0, border_alpha=0.45
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'step-num', '章节序号', bx, by,
                round(w * 0.46, 2), round(h * 0.30, 2), 260.0, 56.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(sec_num, 28.0, True, tpl_primary, title_font)], spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'section-star', bx, by,
                round(w * 0.84, 2), round(h * 0.31, 2), 36.0, 36.0, geom='star4', fill=tpl_primary, border_width=0.0, adj=15000
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'divider', '章节细分割线', bx, by,
                round(w * 0.46, 2), round(h * 0.41, 2), round(w * 0.44, 2), 0.0, geom='line', border_color=tpl_primary, border_width=1.1
            ))
            t_len = len(sec_title)
            sec_sz = 34.0 if t_len <= 12 else (27.0 if t_len <= 18 else 23.0)
            children.append(_make_child_shape(
                cid, next_idx(), 'title', '章节主标题', bx, by,
                round(w * 0.46, 2), round(h * 0.44, 2), round(w * 0.46, 2), 110.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 0, 'top': 4, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(sec_title, sec_sz, True, tpl_primary, title_font)], spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'subtitle', '底部分类标尺', bx, by,
                round(w * 0.46, 2), round(h * 0.65, 2), round(w * 0.44, 2), 28.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(f"{left_tag}  //  {right_tag}", 11.0, True, pal.get('mutedColor', '#5E616B'), font, letterSpacing=1.2)], spaceAfter=0.0)]}
            ))
        else:
            children.append(_make_child_shape(
                cid, next_idx(), 'container', '章节背景横带', bx, by,
                0.0, round(h * 0.30, 2), w, round(h * 0.40, 2), geom='rect', fill=tpl_primary, border_width=0.0
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'step-num', '章节号', bx, by,
                80.0, round(h * 0.33, 2), 360.0, 60.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(sec_num, 20.0, True, '#E2E8F0', font)], spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'title', '章节主标题', bx, by,
                80.0, round(h * 0.42, 2), round(w - 160.0, 2), 90.0, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(sec_title, 34.0, True, '#FFFFFF', font)], spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'divider', '强调细带', bx, by,
                80.0, round(h * 0.62, 2), 260.0, 5.0, geom='rect', fill=tpl_accent, border_width=0.0
            ))
        comp['children'] = children
        return comp

    # -------------------- 4. milestone-timeline (新增) --------------------
    if ctype == 'milestone-timeline':
        milestones = content.get('milestones') or []
        if not milestones:
            return comp
        m_cnt = len(milestones)
        gap = max(14.0, float(layout.get('itemGap', 22.0)))
        col_w = round((w - max(0, m_cnt - 1) * gap) / m_cnt, 2)
        node_y = 22.0 if h >= 210.0 else 10.0

        # 横向穿越主干科技线
        line_y = round(node_y + 30.0, 2)
        children.append(_make_child_shape(
            cid, next_idx(), 'connector', 'timeline-axis', bx, by,
            round(col_w * 0.5, 2), line_y, round(max(40.0, w - col_w), 2), 0.0, geom='line',
            border_color='#18181B' if is_terra else tpl_primary, border_width=1.6, border_alpha=0.55 if is_terra else 0.7,
            tail_end='triangle'
        ))

        icons = _get_icon_paths(tpl, 'lime') if is_terra else []
        for i, ms in enumerate(milestones):
            mx_rel = round(i * (col_w + gap), 2)
            step_txt = str(ms.get('step') or ms.get('year') or f'0{i+1}')
            m_tag = str(ms.get('tag') or f'STAGE {i+1}')
            m_title = str(ms.get('title') or f'阶段 {i+1}')
            m_desc = str(ms.get('desc') or '')
            icon_key = str(ms.get('icon') or '').lower()
            icon_map = {'flask': 0, 'gear': 1, 'board': 2, 'chart': 3}

            # 双环科技圆形徽章（terra_quest 使用包内青柠科技图标，公开模板使用纯矢量双环序号零依赖）
            badge_d = 60.0
            badge_x = round(mx_rel + (col_w - badge_d) / 2.0, 2)
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', f'outer-ring_{i+1}', bx, by,
                badge_x - 4.0, node_y - 4.0, badge_d + 8.0, badge_d + 8.0, geom='oval',
                fill=None, border_color='#18181B' if is_terra else tpl_primary, border_width=1.2, border_alpha=0.55 if is_terra else 0.75
            ))
            if is_terra:
                icon_src = icons[icon_map.get(icon_key, i % len(icons))]
                children.append(_make_child_shape(
                    cid, next_idx(), 'badge', f'icon-circle_{i+1}', bx, by,
                    badge_x, node_y, badge_d, badge_d, geom='oval',
                    fill='#18181B', border_color='#D0E516', border_width=1.8
                ))
                children.append(_make_child_image(
                    cid, next_idx(), 'image', f'icon_{i+1}', bx, by,
                    round(badge_x + 14.0, 2), round(node_y + 14.0, 2), 32.0, 32.0, icon_src
                ))
            else:
                children.append(_make_child_shape(
                    cid, next_idx(), 'badge', f'icon-circle_{i+1}', bx, by,
                    badge_x, node_y, badge_d, badge_d, geom='oval',
                    fill=pal.get('bannerBg', '#EDF2F8'), border_color=tpl_primary, border_width=1.8,
                    text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 2, 'top': 2, 'right': 2, 'bottom': 2},
                               'paragraphs': [make_para([make_run(step_txt, 15.5, True, tpl_primary, font)], align='center', spaceAfter=0.0)]}
                ))

            # 下方内容卡片
            card_y = round(node_y + badge_d + 16.0, 2)
            card_h = round(max(110.0, h - card_y), 2)
            if is_terra:
                children.append(_make_child_shape(
                    cid, next_idx(), 'lane-card', f'milestone-card_{i+1}', bx, by,
                    mx_rel, card_y, col_w, card_h, geom='rect',
                    fill='#FFFFFF', fill_alpha=0.88, border_color='#27272A', border_width=0.9, border_alpha=0.3, shadow=True
                ))
                children.append(_make_child_shape(
                    cid, next_idx(), 'shape', f'milestone-top-glow_{i+1}', bx, by,
                    mx_rel, card_y, col_w, 26.0, geom='rect', fill=None, border_width=0.0,
                    grad_fill=_terra_glow('#D0E516', 0.30, angle=0.0)
                ))
                children.append(_make_child_shape(
                    cid, next_idx(), 'shape', f'milestone-bar_{i+1}', bx, by,
                    mx_rel, card_y, 6.0, card_h, geom='rect', fill='#D0E516' if i % 2 == 0 else '#18181B', border_width=0.0
                ))
                paras = [
                    make_para([make_run(f"{step_txt}  ·  {m_tag}", 11.5, True, '#141413', font)], spaceAfter=4.0),
                    make_para([make_run(m_title, max(11.0, title_sz), True, '#141413', title_font)], spaceAfter=5.0),
                    make_para([make_run(m_desc, max(9.5, body_sz), False, '#3E3C38', font)], spaceAfter=0.0)
                ]
                children.append(_make_child_shape(
                    cid, next_idx(), 'body', f'milestone-text_{i+1}', bx, by,
                    round(mx_rel + 12.0, 2), round(card_y + 4.0, 2), round(col_w - 18.0, 2), round(card_h - 10.0, 2),
                    geom='rect', fill=None, border_width=0.0,
                    text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 4, 'top': 4, 'right': 4, 'bottom': 4}, 'paragraphs': paras}
                ))
            else:
                paras = [
                    make_para([make_run(f"{step_txt} | {m_tag}", 11.0, True, tpl_primary, font)], spaceAfter=4.0),
                    make_para([make_run(m_title, max(11.0, title_sz), True, '#1E293B', font)], spaceAfter=5.0),
                    make_para([make_run(m_desc, max(9.5, body_sz), False, pal.get('bodyColor', '#334155'), font)], spaceAfter=0.0)
                ]
                children.append(_make_child_shape(
                    cid, next_idx(), 'lane-card', f'milestone-card_{i+1}', bx, by,
                    mx_rel, card_y, col_w, card_h, geom='roundRect',
                    fill=pal.get('cardBg', '#F6F8FB'), border_color=pal.get('cardBorder', '#CBD5E1'), border_width=1.1,
                    text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 10, 'top': 10, 'right': 10, 'bottom': 10}, 'paragraphs': paras},
                    adj=8000
                ))
        comp['children'] = children
        return comp

    # -------------------- 5. footer-banner --------------------
    if ctype == 'footer-banner':
        raw_pre = str(content.get('prefix') or '').strip()
        raw_title = str(content.get('title') or '').strip()
        raw_sub = str(content.get('subtitle') or content.get('text') or '').strip()
        if not raw_sub and raw_title:
            if '：' in raw_title and raw_title.index('：') <= 16:
                p0, p1 = raw_title.split('：', 1)
                prefix = p0.strip() + '：'
                body_txt = p1.strip()
            else:
                prefix = raw_pre or '核心结论：'
                body_txt = raw_title
        else:
            prefix = raw_pre or raw_title or '核心结论与边界：'
            body_txt = raw_sub or '在此输入本页核心发现、实证含义或设计边界说明。'
        if prefix and not prefix.endswith(('：', ':')):
            prefix += '：'

        if is_terra:
            tag_w = 48.0
            children.append(_make_child_shape(
                cid, next_idx(), 'container', 'footer-shell', bx, by,
                0.0, 0.0, w, h, geom='rect', fill='#F6F4EA', fill_alpha=0.92,
                border_color='#18181B', border_width=0.9, border_alpha=0.45, shadow=True
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'badge', 'footer-cmd-tag', bx, by,
                0.0, 0.0, tag_w, h, geom='rect', fill='#18181B', border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 2, 'top': 2, 'right': 2, 'bottom': 2},
                           'paragraphs': [make_para([make_run('>>>', 10.5, True, '#D0E516', font)], align='center', spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'body', 'footer-text', bx, by,
                tag_w + 10.0, 0.0, round(w - tag_w - 22.0, 2), h, geom='rect', fill=None, border_width=0.0,
                text_body={
                    'valign': 'middle', 'wrap': True,
                    'padding': {'left': 4.0, 'top': 3.0, 'right': 6.0, 'bottom': 3.0},
                    'paragraphs': [make_para([
                        make_run(prefix, max(9.5, body_sz), True, '#141413', font),
                        make_run(body_txt, max(9.5, body_sz - 0.3), False, '#2E2D2A', font)
                    ], spaceAfter=0.0)]
                }
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'divider', 'footer-lime-cap', bx, by,
                round(w - 7.0, 2), 0.0, 7.0, h, geom='rect', fill='#D0E516', border_width=0.0
            ))
        else:
            f_fill = style.get('fill') or pal.get('bannerBg', '#EDF2F8')
            f_border = style.get('borderColor') or pal.get('bannerBorder', tpl_primary)
            p_color = style.get('titleColor') or tpl_primary
            b_color = style.get('bodyColor') or pal.get('bodyColor', '#334155')
            children.append(_make_child_shape(
                cid, next_idx(), 'container', 'container', bx, by,
                0.0, 0.0, w, h, geom='roundRect', fill=f_fill, border_color=f_border,
                border_width=float(style.get('borderWidth') or 1.1),
                text_body={
                    'valign': 'middle', 'wrap': True,
                    'padding': {'left': px, 'top': min(py, 6.0), 'right': px, 'bottom': min(py, 6.0)},
                    'paragraphs': [make_para([
                        make_run(prefix, max(10.0, title_sz - 1.5), True, p_color, font),
                        make_run(body_txt, body_sz, False, b_color, font)
                    ], spaceAfter=0.0)]
                },
                adj=12000
            ))
        comp['children'] = children
        return comp

    # -------------------- 6. tag-badge --------------------
    if ctype == 'tag-badge':
        label = str(content.get('title') or content.get('text') or '核心模块标签')
        tone_key = content.get('tone')
        if is_terra:
            pal_t = get_tone(tone_key, tpl, 'info')
            is_sem = tone_key in ('pass', 'promoted', 'warn', 'reject', 'rollback')
            if is_sem:
                # 机能分组/警示铭牌：曜石黑主壳 + 左侧 10px 实心功能信号条 + 右侧 4px 收尾点缀
                sig_c = pal_t.get('stripe') or pal_t['badgeBg']
                children.append(_make_child_shape(
                    cid, next_idx(), 'container', 'container', bx, by,
                    0.0, 0.0, w, h, geom='rect', fill='#18181B', border_color=sig_c, border_width=0.9, border_alpha=0.5, shadow=True,
                    text_body={
                        'valign': 'middle', 'wrap': False,
                        'padding': {'left': 18.0, 'top': 2.0, 'right': 12.0, 'bottom': 2.0},
                        'paragraphs': [make_para([make_run(label, min(title_sz, 11.5), True, '#F8F7F2', font)], align='center', spaceAfter=0.0)]
                    }
                ))
                children.append(_make_child_shape(
                    cid, next_idx(), 'divider', 'tag-signal-left', bx, by,
                    0.0, 0.0, 10.0, h, geom='rect', fill=sig_c, border_width=0.0
                ))
                children.append(_make_child_shape(
                    cid, next_idx(), 'shape', 'tag-signal-right', bx, by,
                    round(w - 5.0, 2), 0.0, 5.0, h, geom='rect', fill=sig_c, border_width=0.0
                ))
            else:
                bg = pal_t['badgeBg']
                fg = pal_t['badgeFg']
                children.append(_make_child_shape(
                    cid, next_idx(), 'container', 'container', bx, by,
                    0.0, 0.0, w, h, geom='plaque', fill=bg, border_color='#D0E516' if bg == '#18181B' else bg, border_width=0.8,
                    text_body={
                        'valign': 'middle', 'wrap': False,
                        'padding': {'left': 10.0, 'top': 2.0, 'right': 10.0, 'bottom': 2.0},
                        'paragraphs': [make_para([make_run(label, min(title_sz, 11.5), True, fg, font)], align='center', spaceAfter=0.0)]
                    },
                    adj=18000
                ))
        elif is_editorial:
            # 极简弥散标签胶囊：语义标签采用低饱和功能色胶囊，常规标签采用细黑边框白底配左侧四角星
            pal_t = get_tone(tone_key, tpl, 'info')
            is_sem = tone_key in ('pass', 'promoted', 'warn', 'reject', 'rollback')
            if is_sem:
                bg = pal_t['badgeBg']
                fg = pal_t['badgeFg']
                bd = pal_t['border']
                children.append(_make_child_shape(
                    cid, next_idx(), 'container', 'container', bx, by,
                    0.0, 0.0, w, h, geom='roundRect', fill=bg, border_color=bd, border_width=0.85,
                    text_body={
                        'valign': 'middle', 'wrap': False,
                        'padding': {'left': 10.0, 'top': 2.0, 'right': 10.0, 'bottom': 2.0},
                        'paragraphs': [make_para([make_run(label, min(title_sz, 11.0), True, fg, font)], align='center', spaceAfter=0.0)]
                    },
                    adj=24000
                ))
            else:
                children.append(_make_child_shape(
                    cid, next_idx(), 'container', 'container', bx, by,
                    0.0, 0.0, w, h, geom='roundRect', fill='#FFFFFF', fill_alpha=0.95,
                    border_color=tpl_primary, border_width=0.9, border_alpha=0.75,
                    text_body={
                        'valign': 'middle', 'wrap': False,
                        'padding': {'left': 20.0 if w >= 64.0 else 8.0, 'top': 2.0, 'right': 10.0, 'bottom': 2.0},
                        'paragraphs': [make_para([make_run(label, min(title_sz, 11.0), True, tpl_primary, font)], align='center' if w < 64.0 else 'left', spaceAfter=0.0)]
                    },
                    adj=24000
                ))
                if w >= 64.0:
                    st_sz = min(10.0, round(h * 0.42, 1))
                    children.append(_make_child_shape(
                        cid, next_idx(), 'shape', 'tag-star-dot', bx, by,
                        7.0, round((h - st_sz) * 0.5, 2), st_sz, st_sz,
                        geom='star4', fill=tpl_accent, border_color=tpl_primary, border_width=0.4
                    ))
        else:
            if tone_key:
                pal_t = get_tone(tone_key, tpl)
                bg, fg = pal_t['badgeBg'], pal_t['badgeFg']
            else:
                bg = style.get('fill') or tpl_primary
                fg = style.get('titleColor') or '#FFFFFF'
            children.append(_make_child_shape(
                cid, next_idx(), 'container', 'container', bx, by,
                0.0, 0.0, w, h, geom='roundRect', fill=bg, border_color=bg, border_width=0.0,
                text_body={
                    'valign': 'middle', 'wrap': False,
                    'padding': {'left': 8.0, 'top': 2.0, 'right': 8.0, 'bottom': 2.0},
                    'paragraphs': [make_para([make_run(label, title_sz, True, fg, font)], align='center', spaceAfter=0.0)]
                },
                adj=12000
            ))
        comp['children'] = children
        return comp

    # -------------------- 7. info-card --------------------
    if ctype == 'info-card':
        title = str(content.get('title') or '').strip()
        items = content.get('items') or []
        subtitle = str(content.get('subtitle') or '').strip()
        tone_key = content.get('tone')

        if is_terra:
            is_sem = tone_key in ('pass', 'promoted', 'warn', 'reject', 'rollback')
            if is_sem:
                pal_t = get_tone(tone_key, tpl)
                c_fill = pal_t['bg']
                c_border = pal_t['border']
                c_title = pal_t['title']
                bar_color = pal_t.get('stripe') or pal_t['badgeBg']
                glow_color = bar_color
                c_body = pal_t['body']
                dash = 'dash' if tone_key in ('reject', 'rollback') else None
                b_alpha = 0.55
                glow_alpha = 0.13
            else:
                c_fill = '#FFFFFF'
                c_border = '#27272A'
                c_title = '#141413'
                bar_color = '#D0E516' if (content.get('variant') != 'dark') else '#18181B'
                glow_color = '#D0E516'
                c_body = '#2E2D2A'
                dash = None
                b_alpha = 0.28
                glow_alpha = 0.22

            compact = (h < 88.0)
            bar_w = 7.0
            children.append(_make_child_shape(
                cid, next_idx(), 'container', 'card-shell', bx, by,
                0.0, 0.0, w, h, geom='rect', fill=c_fill, fill_alpha=0.90 if not is_sem else 0.94,
                border_color=c_border, border_width=1.0 if is_sem else 0.9, border_alpha=b_alpha,
                dash_style=dash, shadow=True
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'divider', 'card-left-bar', bx, by,
                0.0, 0.0, bar_w, h, geom='rect', fill=bar_color, border_width=0.0
            ))
            glow_h = min(30.0, round(h * 0.48, 1)) if compact else 32.0
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'card-title-glow', bx, by,
                bar_w, 0.0, round(max(10.0, w - bar_w), 2), glow_h, geom='rect',
                fill=None, border_width=0.0, grad_fill=_terra_glow(glow_color, glow_alpha, angle=0.0)
            ))
            if not compact and w >= 180.0:
                children.append(_make_child_shape(
                    cid, next_idx(), 'shape', 'card-corner-chip', bx, by,
                    round(w - 16.0, 2), 6.0, 10.0, 10.0, geom='rect', fill='#18181B' if not is_sem else bar_color, border_width=0.0, fill_alpha=0.75
                ))

            t_sz = min(12.0, max(10.5, title_sz)) if not compact else min(10.5, title_sz)
            b_sz = min(10.0, max(9.0, body_sz)) if not compact else min(9.5, body_sz)
            # 粗略根据卡片面积自动收紧间距防文字溢出
            line_est = len(items) + (1 if title else 0)
            eff_gap = 2.0 if compact else (3.5 if line_est >= 5 or h < 190 else min(5.5, item_gap))
            eff_hgap = 2.5 if compact else min(6.0, header_gap)

            paras = []
            if title:
                paras.append(make_para([make_run(title, t_sz, True, c_title, font)], spaceAfter=eff_hgap))
            if subtitle:
                paras.append(make_para([make_run(subtitle, b_sz, True, '#52504C', font)], spaceAfter=eff_gap))
            for i_idx, raw_it in enumerate(items):
                sa = 0.0 if i_idx == len(items) - 1 else eff_gap
                runs = _split_item_prefix(raw_it, bold_color='#141413' if not is_sem else c_title, body_color=c_body, font_sz=b_sz, font=font)
                paras.append(make_para(runs, spaceAfter=sa))
            if not paras:
                paras.append(make_para([make_run(' ', b_sz, False, c_body, font)], spaceAfter=0.0))

            children.append(_make_child_shape(
                cid, next_idx(), 'body', 'card-text', bx, by,
                bar_w + 4.0, 0.0, round(max(20.0, w - bar_w - 8.0), 2), h, geom='rect',
                fill=None, border_width=0.0,
                text_body={
                    'valign': 'middle' if compact else layout.get('valign', 'top'),
                    'wrap': True,
                    'padding': {'left': 8.0, 'top': 4.0 if compact else 8.0, 'right': 10.0, 'bottom': 4.0 if compact else 7.0},
                    'paragraphs': paras
                }
            ))
        elif is_editorial:
            # 极简弥散卡片：纯白高明度底 + 细框轻影 + 顶部柔和双色渐变信号带
            if tone_key:
                pal_t = get_tone(tone_key, tpl)
                c_fill = pal_t['bg']
                c_border = pal_t['border']
                c_title = pal_t['title']
                c_body = pal_t['body']
                top_c = pal_t.get('stripe') or pal_t['badgeBg']
                dash = 'dash' if tone_key in ('reject', 'rollback') else None
                is_sem = tone_key in ('pass', 'promoted', 'warn', 'reject', 'rollback')
            else:
                c_fill = '#FFFFFF'
                c_border = pal.get('cardBorder', '#D2D4C8')
                c_title = pal.get('titleColor', tpl_primary)
                c_body = pal.get('bodyColor', '#2E2D2A')
                top_c = tpl_accent
                dash = None
                is_sem = False

            compact = (h < 88.0)
            t_sz = min(12.0, max(10.5, title_sz)) if not compact else min(10.5, title_sz)
            b_sz = min(10.0, max(9.0, body_sz)) if not compact else min(9.5, body_sz)
            line_est = len(items) + (1 if title else 0)
            eff_gap = 2.5 if compact else (3.8 if line_est >= 5 or h < 190 else min(5.5, item_gap))
            eff_hgap = 3.0 if compact else min(6.5, header_gap)

            paras = []
            if title:
                paras.append(make_para([make_run(title, t_sz, True, c_title, font)], spaceAfter=eff_hgap))
            if subtitle:
                paras.append(make_para([make_run(subtitle, b_sz, True, pal.get('mutedColor', '#5E616B'), font)], spaceAfter=eff_gap))
            for i_idx, raw_it in enumerate(items):
                sa = 0.0 if i_idx == len(items) - 1 else eff_gap
                runs = _split_item_prefix(raw_it, bold_color=c_title if is_sem else tpl_primary, body_color=c_body, font_sz=b_sz, font=font)
                paras.append(make_para(runs, spaceAfter=sa))
            if not paras:
                paras.append(make_para([make_run(' ', b_sz, False, c_body, font)], spaceAfter=0.0))

            children.append(_make_child_shape(
                cid, next_idx(), 'container', 'container', bx, by,
                0.0, 0.0, w, h, geom='roundRect', fill=c_fill, fill_alpha=0.94,
                border_color=c_border, border_width=0.95, border_alpha=0.65 if is_sem else 0.55,
                dash_style=dash, shadow=True, adj=4000
            ))
            # 顶部/左侧柔和渐变弥散色条 + 左星/圆角信号点
            children.append(_make_child_shape(
                cid, next_idx(), 'divider', '顶部弥散强调带', bx, by,
                0.0, 0.0, w, 4.0 if not compact else 3.5, geom='rect', fill=None, border_width=0.0,
                grad_fill={'angle': 0, 'stops': [
                    {'pos': 0.0, 'color': top_c, 'alpha': 0.92},
                    {'pos': 0.72, 'color': pal.get('cardAltBg', '#E0E0CC'), 'alpha': 0.45 if not is_sem else 0.18},
                    {'pos': 1.0, 'color': c_fill, 'alpha': 0.0}
                ]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'body', 'card-text', bx, by,
                0.0, 4.0, w, round(max(16.0, h - 4.0), 2), geom='rect', fill=None, border_width=0.0,
                text_body={
                    'valign': 'middle' if compact else layout.get('valign', 'top'),
                    'wrap': True,
                    'padding': {'left': px, 'top': 4.0 if compact else max(7.0, py - 2.0), 'right': px, 'bottom': 4.0 if compact else max(6.0, py - 3.0)},
                    'paragraphs': paras
                }
            ))
        else:
            if tone_key:
                pal_t = get_tone(tone_key, tpl)
                c_fill = style.get('fill') or pal_t['bg']
                c_border = style.get('borderColor') or pal_t['border']
                c_title = style.get('titleColor') or pal_t['title']
                top_bar_color = pal_t['badgeBg']
            else:
                c_fill = style.get('fill') or pal.get('cardBg', '#F6F8FB')
                c_border = style.get('borderColor') or pal.get('cardBorder', '#CBD5E1')
                c_title = style.get('titleColor') or pal.get('titleColor', '#1B365D')
                top_bar_color = style.get('accentColor') or tpl_primary
            c_body = style.get('bodyColor') or pal.get('bodyColor', '#334155')

            paras = []
            if title:
                paras.append(make_para([make_run(title, title_sz, True, c_title, font)], spaceAfter=header_gap))
            if subtitle:
                paras.append(make_para([make_run(subtitle, body_sz, True, pal.get('mutedColor', '#64748B'), font)], spaceAfter=item_gap))
            for i_idx, raw_it in enumerate(items):
                sa = 0.0 if i_idx == len(items) - 1 else item_gap
                runs = _split_item_prefix(raw_it, bold_color='#1E293B', body_color=c_body, font_sz=body_sz, font=font)
                paras.append(make_para(runs, spaceAfter=sa))
            if not paras:
                paras.append(make_para([make_run(' ', body_sz, False, c_body, font)], spaceAfter=0.0))

            show_top_bar = bool(layout.get('topBar', skel.get('cardTopBar', True)))
            pad_top = py + (3.0 if show_top_bar else 0.0)
            children.append(_make_child_shape(
                cid, next_idx(), 'container', 'container', bx, by,
                0.0, 0.0, w, h, geom='roundRect', fill=c_fill, border_color=c_border,
                border_width=float(style.get('borderWidth') or 1.0),
                text_body={
                    'valign': layout.get('valign', 'top'),
                    'wrap': True,
                    'padding': {'left': px, 'top': pad_top, 'right': px, 'bottom': py},
                    'paragraphs': paras
                },
                adj=6000
            ))
            if show_top_bar and w > 20.0:
                children.append(_make_child_shape(
                    cid, next_idx(), 'divider', '顶部强调色条', bx, by,
                    1.0, 0.0, round(w - 2.0, 2), 3.5, geom='rect',
                    fill=top_bar_color, border_width=0.0
                ))
        comp['children'] = children
        return comp

    # -------------------- 8. toc-list --------------------
    if ctype == 'toc-list':
        raw_items = content.get('items') or []
        if not raw_items:
            return comp
        n = len(raw_items)
        gap_y = max(12.0, float(layout.get('itemGap', 24.0)))
        box_h = round(max(36.0, min(52.0, (h - max(0, n - 1) * gap_y) / n)), 2)
        step_y = round(h / n, 2) if n > 1 else h
        badge_w = 58.0
        title_w = round(min(280.0, max(160.0, (w - 80.0) * 0.34)), 2)
        sub_x = round(badge_w + 18.0 + title_w + 14.0, 2)
        sub_w = round(max(120.0, w - sub_x), 2)

        for i, item in enumerate(raw_items):
            if isinstance(item, dict):
                num_s = str(item.get('num') or f"{i+1:02d}")
                t_s = str(item.get('title') or '')
                d_s = str(item.get('desc') or item.get('subtitle') or '')
            else:
                parts = [p.strip() for p in str(item).split('|')]
                if len(parts) >= 3:
                    num_s, t_s, d_s = parts[0], parts[1], parts[2]
                elif len(parts) == 2:
                    num_s, t_s, d_s = f"{i+1:02d}", parts[0], parts[1]
                else:
                    num_s, t_s, d_s = f"{i+1:02d}", parts[0], ''

            ry = round(i * step_y, 2)
            is_first = (i == 0)
            if is_terra:
                b_fill = '#18181B' if is_first else '#D0E516'
                b_fg = '#D0E516' if is_first else '#141413'
                b_geom = 'plaque'
                b_border = '#18181B'
            else:
                b_fill = tpl_primary if is_first else pal.get('bannerBg', '#EDF2F8')
                b_fg = '#FFFFFF' if is_first else tpl_primary
                b_geom = 'roundRect'
                b_border = tpl_primary
            children.append(_make_child_shape(
                cid, next_idx(), 'step-num', f'目录序号 {num_s}', bx, by,
                0.0, ry, badge_w, box_h, geom=b_geom, fill=b_fill, border_color=b_border, border_width=1.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 6.0, 'top': 4.0, 'right': 6.0, 'bottom': 4.0},
                           'paragraphs': [make_para([make_run(num_s, 15.0, True, b_fg, font)], align='center', spaceAfter=0.0)]},
                adj=14000
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'title', f'章节标题 {num_s}', bx, by,
                round(badge_w + 18.0, 2), round(ry + 3.0, 2), title_w, round(box_h - 6.0, 2), geom='rect',
                fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(t_s, max(13.5, title_sz + 1.5), True, '#141413' if is_terra else '#1E293B', font)], spaceAfter=0.0)]}
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'subtitle', f'章节摘要 {num_s}', bx, by,
                sub_x, round(ry + 3.0, 2), sub_w, round(box_h - 6.0, 2), geom='rect',
                fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                           'paragraphs': [make_para([make_run(d_s, max(10.0, body_sz), False, pal.get('bodyColor', '#334155'), font)], spaceAfter=0.0)]}
            ))
            if i < n - 1:
                line_y = round(ry + box_h + (step_y - box_h) * 0.5, 2)
                children.append(_make_child_shape(
                    cid, next_idx(), 'divider', '目录分割线', bx, by,
                    0.0, line_y, w, 0.0, geom='line',
                    border_color='#18181B' if is_terra else '#CBD5E1', border_width=0.9,
                    border_alpha=0.25 if is_terra else 1.0
                ))
        comp['children'] = children
        return comp

    # -------------------- 9. data-table --------------------
    if ctype == 'data-table':
        headers = content.get('headers') or ['维度', '指标定义', '目标阈值']
        rows = content.get('rows') or [['样例一', '口径说明', '>= 95%']]
        c_cnt = max(len(headers), max((len(r) for r in rows), default=0))
        if c_cnt == 0:
            return comp
        r_cnt = 1 + len(rows)
        hdr_bg = pal.get('tableHeaderBg', tpl_primary)
        hdr_fg = pal.get('tableHeaderFg', '#FFFFFF')
        stripe_bg = pal.get('tableStripeBg', '#F4F6F9')
        b_color = pal.get('bodyColor', '#334155')

        t_rows = [[
            {
                'text': str(headers[c_i] if c_i < len(headers) else ''),
                'fill': hdr_bg, 'color': hdr_fg, 'fontSize': max(10.0, body_sz + 0.5),
                'bold': True, 'fontFamily': font, 'align': 'center', 'valign': 'middle',
                'padding': {'left': 8, 'top': 4, 'right': 8, 'bottom': 4}, 'border': {}
            }
            for c_i in range(c_cnt)
        ]]
        for r_i, r in enumerate(rows):
            bg = stripe_bg if r_i % 2 == 0 else '#FFFFFF'
            t_rows.append([
                {
                    'text': str(r[c_i] if c_i < len(r) else ''),
                    'fill': bg, 'color': b_color, 'fontSize': body_sz,
                    'bold': (c_i == 0), 'fontFamily': font,
                    'align': 'center' if c_i == 0 else 'left', 'valign': 'middle',
                    'padding': {'left': 8, 'top': 4, 'right': 8, 'bottom': 4}, 'border': {}
                }
                for c_i in range(c_cnt)
            ])

        ratios = content.get('colRatios')
        if ratios and len(ratios) == c_cnt and sum(ratios) > 0:
            s_r = float(sum(ratios))
            col_widths = [round(w * float(rt) / s_r, 2) for rt in ratios]
        else:
            col_widths = [round(w / c_cnt, 2) for _ in range(c_cnt)]

        row_h = round(max(24.0, h / max(1, r_cnt)), 2)
        comp['children'] = [{
            'id': f"{cid}_ch1",
            'rawType': 'table',
            'role': 'table',
            'name': 'table',
            'x': bx, 'y': by, 'w': w, 'h': h,
            'relX': 0.0, 'relY': 0.0, 'relW': w, 'relH': h,
            'colWidths': col_widths,
            'rowHeights': [row_h for _ in range(r_cnt)],
            'rows': t_rows
        }]
        return comp

    # -------------------- 10. image-frame --------------------
    if ctype == 'image-frame':
        img_src = content.get('image') or (content.get('images') or ['/assets/showcase/factor_attribution.png'])[0]
        caption = str(content.get('caption') or '').strip()
        if is_terra:
            children.append(_make_child_shape(
                cid, next_idx(), 'container', 'frame-shell', bx, by,
                0.0, 0.0, w, h, geom='rect', fill='#FFFFFF', fill_alpha=0.92,
                border_color='#18181B', border_width=1.0, border_alpha=0.35, shadow=True
            ))
            # 左上角与右下角 HUD 机能角标框
            children.append(_make_child_shape(cid, next_idx(), 'shape', 'hud-tl', bx, by, 0.0, 0.0, 20.0, 4.0, geom='rect', fill='#18181B', border_width=0.0))
            children.append(_make_child_shape(cid, next_idx(), 'shape', 'hud-tl2', bx, by, 0.0, 0.0, 4.0, 20.0, geom='rect', fill='#18181B', border_width=0.0))
            children.append(_make_child_shape(cid, next_idx(), 'shape', 'hud-br', bx, by, round(w - 22.0, 2), round(h - 4.0, 2), 22.0, 4.0, geom='rect', fill='#D0E516', border_width=0.0))
            cap_h = 28.0 if caption else 0.0
            img_w = round(max(40.0, w - 16.0), 2)
            img_h = round(max(40.0, h - 16.0 - cap_h), 2)
            children.append(_make_child_image(cid, next_idx(), 'image', 'image', bx, by, 8.0, 8.0, img_w, img_h, img_src))
            if caption:
                children.append(_make_child_shape(
                    cid, next_idx(), 'subtitle', 'caption-bar', bx, by,
                    0.0, round(h - cap_h, 2), w, cap_h, geom='rect', fill='#18181B', border_width=0.0,
                    text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 10, 'top': 2, 'right': 10, 'bottom': 2},
                               'paragraphs': [make_para([make_run(caption, 9.5, True, '#D0E516', font)], align='center', spaceAfter=0.0)]}
                ))
        else:
            f_fill = style.get('fill') or '#FFFFFF'
            f_border = style.get('borderColor') or pal.get('cardBorder', '#CBD5E1')
            children.append(_make_child_shape(
                cid, next_idx(), 'container', 'container', bx, by,
                0.0, 0.0, w, h, geom='roundRect', fill=f_fill, border_color=f_border,
                border_width=float(style.get('borderWidth') or 1.0), adj=6000
            ))
            cap_h = 26.0 if caption else 0.0
            img_w = round(max(40.0, w - px * 2), 2)
            img_h = round(max(40.0, h - py * 2 - cap_h), 2)
            children.append(_make_child_image(cid, next_idx(), 'image', 'image', bx, by, px, py, img_w, img_h, img_src))
            if caption:
                children.append(_make_child_shape(
                    cid, next_idx(), 'subtitle', 'caption', bx, by,
                    px, round(py + img_h + 2.0, 2), img_w, 22.0, geom='rect', fill=None, border_width=0.0,
                    text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                               'paragraphs': [make_para([make_run(caption, max(9.0, body_sz - 0.5), False, pal.get('mutedColor', '#64748B'), font)], align='center', spaceAfter=0.0)]}
                ))
        comp['children'] = children
        return comp

    # -------------------- 11. kpi-card --------------------
    if ctype == 'kpi-card':
        title = str(content.get('title') or '核心实验组对比')
        subtitle = str(content.get('subtitle') or '样本外表现概览')
        m_val = str(content.get('metricValue') or '97.7%')
        m_lbl = str(content.get('metricLabel') or '平均命中率 / 拟合优度')
        img_src = content.get('image') or '/assets/showcase/nav_benchmark.png'
        items = content.get('items') or ['• 覆盖周期：多期交叉验证', '• 核心优势：结构鲁棒性显著提升']

        top_h = 52.0
        gap = max(6.0, float(layout.get('itemGap', 6.0)))
        rem_h = max(140.0, h - top_h - gap * 2)
        img_h = round(rem_h * 0.48, 2)
        box_h = round(rem_h - img_h, 2)

        if is_terra:
            children.append(_make_child_shape(
                cid, next_idx(), 'title', 'kpi-nameplate', bx, by,
                0.0, 0.0, w, top_h, geom='rect', fill='#18181B', border_width=0.0, shadow=True,
                text_body={
                    'valign': 'middle', 'wrap': True,
                    'padding': {'left': 12.0, 'top': 4.0, 'right': 12.0, 'bottom': 4.0},
                    'paragraphs': [
                        make_para([make_run(title, max(12.0, title_sz), True, '#D0E516', font)], spaceAfter=2.0),
                        make_para([make_run(subtitle, 9.5, False, '#E2E8F0', font)], spaceAfter=0.0)
                    ]
                }
            ))
            children.append(_make_child_shape(cid, next_idx(), 'shape', 'kpi-cap', bx, by, 0.0, 0.0, 5.0, top_h, geom='rect', fill='#D0E516', border_width=0.0))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'kpi-img-box', bx, by,
                0.0, round(top_h + gap, 2), w, img_h, geom='rect', fill='#FFFFFF', border_color='#27272A', border_width=0.8, border_alpha=0.25, shadow=True
            ))
            children.append(_make_child_image(
                cid, next_idx(), 'image', 'image', bx, by,
                4.0, round(top_h + gap + 4.0, 2), round(w - 8.0, 2), round(img_h - 8.0, 2), img_src
            ))
            box_y = round(top_h + gap * 2 + img_h, 2)
            children.append(_make_child_shape(
                cid, next_idx(), 'metric-box', 'metric-box', bx, by,
                0.0, box_y, w, box_h, geom='rect', fill='#FFFFFF', fill_alpha=0.90,
                border_color='#27272A', border_width=0.9, border_alpha=0.28, shadow=True
            ))
            children.append(_make_child_shape(cid, next_idx(), 'shape', 'kpi-lime-bar', bx, by, 0.0, box_y, 7.0, box_h, geom='rect', fill='#D0E516', border_width=0.0))
            # 右上 4 枚平行四边形装饰纹带（复刻 Slide 7）
            for p_i in range(4):
                children.append(_make_child_shape(
                    cid, next_idx(), 'shape', f'para-tick_{p_i+1}', bx, by,
                    round(w - 64.0 + p_i * 12.0, 2), round(box_y + 10.0, 2), 9.0, 14.0, geom='parallelogram',
                    fill='#D0E516' if p_i < 2 else '#18181B', border_width=0.0, adj=38000
                ))
            mv_sz = 21.0 if len(m_val) <= 9 else (15.5 if len(m_val) <= 18 else 13.0)
            m_paras = [
                make_para([make_run(m_val, mv_sz, True, '#141413', font)], spaceAfter=2.0),
                make_para([make_run(m_lbl, 10.0, True, '#52504C', font)], spaceAfter=5.0)
            ]
            for it in items:
                runs = _split_item_prefix(it, bold_color='#141413', body_color='#2E2D2A', font_sz=9.3, font=font)
                m_paras.append(make_para(runs, spaceAfter=2.5))
            children.append(_make_child_shape(
                cid, next_idx(), 'body', 'kpi-text', bx, by,
                12.0, round(box_y + 4.0, 2), round(w - 20.0, 2), round(box_h - 8.0, 2), geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 6.0, 'top': 4.0, 'right': 6.0, 'bottom': 4.0}, 'paragraphs': m_paras}
            ))
        elif is_editorial:
            # 极简弥散 KPI 卡片：纯白细框 + 顶部四角星名牌 + 深抹茶高对比指标数字
            pass_tok = get_tone('pass', tpl, 'pass')
            children.append(_make_child_shape(
                cid, next_idx(), 'title', 'kpi-nameplate', bx, by,
                0.0, 0.0, w, top_h, geom='roundRect', fill='#FFFFFF', fill_alpha=0.96,
                border_color=pal.get('cardBorder', '#D2D4C8'), border_width=0.95, shadow=True, adj=4000,
                text_body={
                    'valign': 'middle', 'wrap': True,
                    'padding': {'left': 26.0, 'top': 4.0, 'right': 10.0, 'bottom': 4.0},
                    'paragraphs': [
                        make_para([make_run(title, max(12.0, title_sz), True, tpl_primary, font)], spaceAfter=2.0),
                        make_para([make_run(subtitle, 9.5, False, pal.get('mutedColor', '#5E616B'), font)], spaceAfter=0.0)
                    ]
                }
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'kpi-star', bx, by,
                9.0, 14.0, 11.0, 11.0, geom='star4', fill=tpl_accent, border_color=tpl_primary, border_width=0.45
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'shape', 'kpi-img-box', bx, by,
                0.0, round(top_h + gap, 2), w, img_h, geom='roundRect', fill='#FFFFFF',
                border_color=pal.get('cardBorder', '#D2D4C8'), border_width=0.9, adj=4000
            ))
            children.append(_make_child_image(
                cid, next_idx(), 'image', 'image', bx, by,
                4.0, round(top_h + gap + 4.0, 2), round(w - 8.0, 2), round(img_h - 8.0, 2), img_src
            ))
            box_y = round(top_h + gap * 2 + img_h, 2)
            children.append(_make_child_shape(
                cid, next_idx(), 'metric-box', 'metric-box', bx, by,
                0.0, box_y, w, box_h, geom='roundRect', fill='#FFFFFF', fill_alpha=0.96,
                border_color=pal.get('cardBorder', '#D2D4C8'), border_width=0.95, shadow=True, adj=4000
            ))
            children.append(_make_child_shape(
                cid, next_idx(), 'divider', 'kpi-aura-bar', bx, by,
                0.0, box_y, w, 3.5, geom='rect', fill=None, border_width=0.0,
                grad_fill={'angle': 0, 'stops': [
                    {'pos': 0.0, 'color': tpl_accent, 'alpha': 0.95},
                    {'pos': 0.72, 'color': pal.get('cardAltBg', '#E0E0CC'), 'alpha': 0.45},
                    {'pos': 1.0, 'color': '#FFFFFF', 'alpha': 0.0}
                ]}
            ))
            mv_sz = 21.0 if len(m_val) <= 9 else (15.5 if len(m_val) <= 18 else 13.0)
            m_paras = [
                make_para([make_run(m_val, mv_sz, True, pass_tok['title'], font)], spaceAfter=2.0),
                make_para([make_run(m_lbl, 10.0, True, tpl_primary, font)], spaceAfter=5.0)
            ]
            for it in items:
                runs = _split_item_prefix(it, bold_color=tpl_primary, body_color=pal.get('bodyColor', '#2E2D2A'), font_sz=9.3, font=font)
                m_paras.append(make_para(runs, spaceAfter=2.5))
            children.append(_make_child_shape(
                cid, next_idx(), 'body', 'kpi-text', bx, by,
                0.0, round(box_y + 4.0, 2), w, round(max(20.0, box_h - 6.0), 2), geom='rect',
                fill=None, border_width=0.0,
                text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 12.0, 'top': 6.0, 'right': 10.0, 'bottom': 6.0}, 'paragraphs': m_paras}
            ))
        else:
            children.append(_make_child_shape(
                cid, next_idx(), 'title', 'title', bx, by,
                0.0, 0.0, w, top_h, geom='roundRect',
                fill=pal.get('bannerBg', '#EDF2F8'), border_color=tpl_primary, border_width=1.2,
                text_body={
                    'valign': 'middle', 'wrap': True,
                    'padding': {'left': 10.0, 'top': 4.0, 'right': 10.0, 'bottom': 4.0},
                    'paragraphs': [
                        make_para([make_run(title, max(12.0, title_sz), True, tpl_primary, font)], spaceAfter=2.0),
                        make_para([make_run(subtitle, 9.5, False, pal.get('mutedColor', '#64748B'), font)], spaceAfter=0.0)
                    ]
                },
                adj=8000
            ))
            children.append(_make_child_image(cid, next_idx(), 'image', 'image', bx, by, 0.0, round(top_h + gap, 2), w, img_h, img_src))
            mv_sz = 21.0 if len(m_val) <= 9 else (15.5 if len(m_val) <= 18 else 13.0)
            m_paras = [
                make_para([make_run(m_val, mv_sz, True, tpl_accent, font)], spaceAfter=2.0),
                make_para([make_run(m_lbl, 10.5, True, '#1E293B', font)], spaceAfter=6.0)
            ]
            for it in items:
                runs = _split_item_prefix(it, bold_color=tpl_primary, body_color=pal.get('bodyColor', '#334155'), font_sz=9.5, font=font)
                m_paras.append(make_para(runs, spaceAfter=3.0))
            children.append(_make_child_shape(
                cid, next_idx(), 'metric-box', 'metric-box', bx, by,
                0.0, round(top_h + gap * 2 + img_h, 2), w, box_h, geom='roundRect',
                fill='#FFFFFF', border_color=pal.get('cardBorder', '#CBD5E1'), border_width=1.1,
                text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 12.0, 'top': 8.0, 'right': 12.0, 'bottom': 8.0}, 'paragraphs': m_paras},
                adj=8000
            ))
        comp['children'] = children
        return comp

    # -------------------- 12. vertical-stack --------------------
    if ctype == 'vertical-stack':
        title = (content.get('title') or '').strip()
        direction = content.get('direction', 'down')
        layers = content.get('layers') or []
        if not layers:
            return comp
        gap = max(10.0, float(layout.get('itemGap', 14.0)))
        cur_y = 0.0
        if title:
            bar_h = 28.0
            children.append(_make_child_shape(
                cid, next_idx(), 'header-bar', 'header-bar', bx, by,
                0.0, 0.0, w, bar_h, geom='rect' if is_terra else 'roundRect',
                fill='#18181B' if is_terra else tpl_primary, border_width=0.0,
                text_body={
                    'valign': 'middle', 'wrap': True,
                    'padding': {'left': 10.0, 'top': 2.0, 'right': 10.0, 'bottom': 2.0},
                    'paragraphs': [make_para([make_run(title, title_sz, True, '#D0E516' if is_terra else '#FFFFFF', font)], align='center', spaceAfter=0.0)]
                },
                adj=8000
            ))
            cur_y = bar_h + header_gap

        n = len(layers)
        min_need = cur_y + n * 34.0 + max(0, n - 1) * gap
        if h < min_need:
            h = round(min_need, 1)
            comp['h'] = h
        avail_h = max(34.0 * n, h - cur_y)
        layer_h = round((avail_h - max(0, n - 1) * gap) / n, 2)
        badge_w = min(84.0, round(w * 0.16, 1))
        card_x = badge_w + 8.0
        card_w = max(40.0, round(w - card_x, 2))

        for i, layer in enumerate(layers):
            l_tone = str(layer.get('tone') or 'info').lower()
            pal_t = get_tone(l_tone, tpl, 'info')
            tag_txt = str(layer.get('tag', f'L{i + 1}'))
            l_title = str(layer.get('title', ''))
            l_desc = str(layer.get('desc', ''))

            if is_terra:
                is_sem_layer = l_tone in ('pass', 'promoted', 'warn', 'reject', 'rollback', 'neutral', 'baseline')
                cap_c = pal_t.get('stripe') or '#D0E516'
                badge_bg = '#52504C' if l_tone in ('neutral', 'baseline') else '#18181B'
                badge_fg = '#FFFFFF' if l_tone in ('neutral', 'baseline') else (cap_c if l_tone in ('warn', 'reject', 'rollback') else '#D0E516')
                card_bg = pal_t['bg'] if is_sem_layer else '#FFFFFF'
                card_bd = pal_t['border'] if is_sem_layer else '#27272A'
                glow_c = cap_c if is_sem_layer else '#D0E516'
                glow_a = 0.14 if is_sem_layer else 0.20

                children.append(_make_child_shape(
                    cid, next_idx(), 'badge', f'badge_{i+1}', bx, by,
                    0.0, cur_y, badge_w, layer_h, geom='rect', fill=badge_bg, border_width=0.0, shadow=True,
                    text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 4.0, 'top': 2.0, 'right': 4.0, 'bottom': 2.0},
                               'paragraphs': [make_para([make_run(tag_txt, min(title_sz, 12.0), True, badge_fg, font)], align='center', spaceAfter=0.0)]}
                ))
                children.append(_make_child_shape(
                    cid, next_idx(), 'shape', f'badge-cap_{i+1}', bx, by,
                    0.0, cur_y, badge_w, 4.0, geom='rect', fill=cap_c if is_sem_layer else '#D0E516', border_width=0.0
                ))
                children.append(_make_child_shape(
                    cid, next_idx(), 'layer-card', f'layer-card_{i+1}', bx, by,
                    card_x, cur_y, card_w, layer_h, geom='rect', fill=card_bg, fill_alpha=0.92,
                    border_color=card_bd, border_width=0.95, border_alpha=0.45 if is_sem_layer else 0.28, shadow=True
                ))
                if is_sem_layer:
                    children.append(_make_child_shape(
                        cid, next_idx(), 'shape', f'layer-bar_{i+1}', bx, by,
                        card_x, cur_y, 5.0, layer_h, geom='rect', fill=cap_c, border_width=0.0
                    ))
                children.append(_make_child_shape(
                    cid, next_idx(), 'shape', f'layer-glow_{i+1}', bx, by,
                    card_x + (5.0 if is_sem_layer else 0.0), cur_y, round(card_w - (5.0 if is_sem_layer else 0.0), 2), round(layer_h * 0.42, 1), geom='rect',
                    fill=None, border_width=0.0, grad_fill=_terra_glow(glow_c, glow_a, angle=0.0)
                ))
                paras = []
                if l_title:
                    paras.append(make_para([make_run(l_title, max(10.5, title_sz - 0.5), True, pal_t['title'] if is_sem_layer else '#141413', font)], spaceAfter=2.5))
                if l_desc:
                    paras.append(make_para([make_run(l_desc, min(10.0, body_sz), False, pal_t['body'], font)], spaceAfter=0.0))
                children.append(_make_child_shape(
                    cid, next_idx(), 'body', f'layer-text_{i+1}', bx, by,
                    card_x + (8.0 if is_sem_layer else 4.0), cur_y, round(card_w - (12.0 if is_sem_layer else 8.0), 2), layer_h, geom='rect', fill=None, border_width=0.0,
                    text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 8.0, 'top': 4.0, 'right': 8.0, 'bottom': 4.0}, 'paragraphs': paras}
                ))
            else:
                children.append(_make_child_shape(
                    cid, next_idx(), 'badge', f'badge_{i+1}', bx, by,
                    0.0, cur_y, badge_w, layer_h, geom='roundRect',
                    fill=pal_t['badgeBg'], border_color=pal_t['badgeBg'], border_width=0.0,
                    text_body={
                        'valign': 'middle', 'wrap': True,
                        'padding': {'left': 4.0, 'top': 2.0, 'right': 4.0, 'bottom': 2.0},
                        'paragraphs': [make_para([make_run(tag_txt, title_sz, True, pal_t['badgeFg'], font)], align='center', spaceAfter=0.0)]
                    },
                    adj=10000
                ))
                paras = []
                if l_title:
                    paras.append(make_para([make_run(l_title, max(10.0, title_sz - 0.5), True, pal_t['title'], font)], spaceAfter=2.0))
                if l_desc:
                    paras.append(make_para([make_run(l_desc, body_sz, False, pal_t['body'], font)], spaceAfter=0.0))
                if not paras:
                    paras.append(make_para([make_run(' ', body_sz, False, pal_t['body'], font)], spaceAfter=0.0))
                children.append(_make_child_shape(
                    cid, next_idx(), 'layer-card', f'layer-card_{i+1}', bx, by,
                    card_x, cur_y, card_w, layer_h, geom='roundRect',
                    fill=pal_t['bg'], border_color=pal_t['border'], border_width=1.2,
                    text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 10.0, 'top': 4.0, 'right': 10.0, 'bottom': 4.0}, 'paragraphs': paras},
                    adj=8000
                ))

            if i < n - 1:
                conn_h = max(4.0, gap - 4.0)
                children.append(_make_child_shape(
                    cid, next_idx(), 'connector', f'connector_{i+1}', bx, by,
                    round(w / 2.0, 2), round(cur_y + layer_h + 2.0, 2), 0.0, conn_h,
                    geom='line', fill=None, border_color='#18181B' if is_terra else pal_t['border'], border_width=1.6,
                    tail_end='triangle', flip_v=(direction == 'up')
                ))
            cur_y = round(cur_y + layer_h + gap, 2)

        comp['children'] = children
        return comp

    # -------------------- 13. decision-gate --------------------
    if ctype == 'decision-gate':
        branches = content.get('branches') or []
        if not branches:
            return comp
        gate_shape = 'hexagon' if is_terra else (content.get('gateShape') or 'diamond')
        gate_text = content.get('gateText') or '判定条件是否满足？'
        gate_w = round(min(w * 0.84, 540.0), 1) if gate_shape == 'hexagon' else round(min(w * 0.78, 440.0), 1)
        gate_h = 70.0 if gate_shape == 'diamond' else 56.0
        gate_x = round((w - gate_w) / 2.0, 1)
        gate_pad_x = 38.0 if gate_shape == 'diamond' else 48.0
        gate_t_sz = 9.8 if (len(str(gate_text)) > 20 and gate_shape == 'hexagon') else max(10.0, title_sz - 0.5)

        children.append(_make_child_shape(
            cid, next_idx(), 'gate-node', 'gate-node', bx, by,
            gate_x, 0.0, gate_w, gate_h, geom=gate_shape,
            fill='#18181B' if is_terra else pal.get('bannerBg', '#EDF2F8'),
            border_color='#D0E516' if is_terra else tpl_primary, border_width=1.6, shadow=is_terra,
            text_body={
                'valign': 'middle', 'wrap': True,
                'padding': {'left': gate_pad_x, 'top': 5.0, 'right': gate_pad_x, 'bottom': 5.0},
                'paragraphs': [make_para([make_run(gate_text, gate_t_sz, True, '#D0E516' if is_terra else pal.get('titleColor', tpl_primary), font)], align='center', spaceAfter=0.0)]
            },
            adj=12000
        ))

        fork_h = max(24.0, header_gap * 1.8)
        k = len(branches)
        gap = max(8.0, float(layout.get('itemGap', 14.0)))
        bw = round((w - max(0, k - 1) * gap) / k, 2)
        card_top = round(gate_h + fork_h, 2)
        card_h = round(max(82.0, h - card_top), 2)
        if h < card_top + 82.0:
            h = round(card_top + 82.0, 1)
            comp['h'] = h

        top_cx = round(w / 2.0, 2)
        mid_y = round(gate_h + fork_h * 0.45, 2)
        stem_h = round(max(6.0, mid_y - gate_h), 2)
        drop_h = round(max(8.0, card_top - mid_y - 1.0), 2)

        children.append(_make_child_shape(
            cid, next_idx(), 'connector', 'connector_stem', bx, by,
            top_cx, gate_h, 0.0, stem_h, geom='line', border_color='#18181B' if is_terra else tpl_primary, border_width=1.6
        ))

        for i, br in enumerate(branches):
            pal_t = get_tone(br.get('tone'), tpl, 'pass')
            bx_rel = round(i * (bw + gap), 2)
            cx_rel = round(bx_rel + bw / 2.0, 2)
            is_reject = str(br.get('tone', '')).lower() in ('reject', 'rollback')
            dash = 'dash' if is_reject else None

            if abs(cx_rel - top_cx) >= 2.0:
                hb_x = round(min(top_cx, cx_rel), 2)
                hb_w = round(abs(cx_rel - top_cx), 2)
                children.append(_make_child_shape(
                    cid, next_idx(), 'connector', f'connector_bus_{i+1}', bx, by,
                    hb_x, mid_y, hb_w, 0.0, geom='line', border_color=pal_t['border'], border_width=1.5, dash_style=dash
                ))

            children.append(_make_child_shape(
                cid, next_idx(), 'connector', f'connector_drop_{i+1}', bx, by,
                cx_rel, mid_y, 0.0, drop_h, geom='line', border_color=pal_t['border'], border_width=1.5, tail_end='triangle', dash_style=dash
            ))

            badge_h = 24.0
            children.append(_make_child_shape(
                cid, next_idx(), 'badge', f'badge_{i+1}', bx, by,
                bx_rel, card_top, bw, badge_h, geom='rect' if is_terra else 'roundRect',
                fill=pal_t['badgeBg'], border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 6.0, 'top': 1.0, 'right': 6.0, 'bottom': 1.0},
                           'paragraphs': [make_para([make_run(str(br.get('label', f'分支 {i+1}')), max(9.5, body_sz), True, pal_t['badgeFg'], font)], align='center', spaceAfter=0.0)]},
                adj=8000
            ))

            paras = []
            if br.get('title'):
                paras.append(make_para([make_run(str(br['title']), max(10.5, title_sz - 0.5), True, pal_t['title'], font)], spaceAfter=4.0))
            for it in (br.get('items') or []):
                paras.append(make_para([make_run(str(it), max(9.5, body_sz), False, pal_t['body'], font)], spaceAfter=3.0))
            if not paras:
                paras.append(make_para([make_run(' ', body_sz, False, pal_t['body'], font)], spaceAfter=0.0))

            children.append(_make_child_shape(
                cid, next_idx(), 'branch-card', f'branch-card_{i+1}', bx, by,
                bx_rel, round(card_top + badge_h + 3.0, 2), bw, round(card_h - badge_h - 3.0, 2),
                geom='rect' if is_terra else 'roundRect', fill=pal_t['bg'], border_color=pal_t['border'],
                border_width=1.05, border_alpha=0.55 if is_terra else 1.0, dash_style=dash, shadow=is_terra,
                text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 9.0, 'top': 7.0, 'right': 9.0, 'bottom': 6.0}, 'paragraphs': paras},
                adj=8000
            ))

        comp['children'] = children
        return comp

    # -------------------- 14. stage-funnel --------------------
    if ctype == 'stage-funnel':
        stages = content.get('stages') or []
        if not stages:
            return comp
        title = (content.get('title') or '').strip()
        summary = (content.get('summary') or '').strip()
        cur_y = 0.0
        if title:
            children.append(_make_child_shape(
                cid, next_idx(), 'header-bar', 'header-bar', bx, by,
                0.0, 0.0, w, 26.0, geom='rect' if is_terra else 'roundRect',
                fill='#18181B' if is_terra else tpl_primary, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 10.0, 'top': 2.0, 'right': 10.0, 'bottom': 2.0},
                           'paragraphs': [make_para([make_run(title, title_sz, True, '#D0E516' if is_terra else '#FFFFFF', font)], align='center', spaceAfter=0.0)]},
                adj=8000
            ))
            cur_y = 26.0 + header_gap

        sum_h = 28.0 if summary else 0.0
        sum_gap = header_gap if summary else 0.0
        mid_h = max(72.0, h - cur_y - sum_h - sum_gap)
        if h < cur_y + mid_h + sum_h + sum_gap:
            h = round(cur_y + mid_h + sum_h + sum_gap, 1)
            comp['h'] = h

        m = len(stages)
        gap = max(12.0, float(layout.get('itemGap', 18.0)))
        sw = round((w - max(0, m - 1) * gap) / m, 2)
        chev_h = 28.0
        box_y = round(cur_y + chev_h + 4.0, 2)
        box_h = round(max(40.0, mid_h - chev_h - 4.0), 2)

        for i, st in enumerate(stages):
            pal_t = get_tone(st.get('tone'), tpl, 'info')
            sx_rel = round(i * (sw + gap), 2)
            head_txt = f"{st.get('code', '')} {st.get('name', '')}".strip()

            children.append(_make_child_shape(
                cid, next_idx(), 'badge', f'badge_{i+1}', bx, by,
                sx_rel, cur_y, sw, chev_h, geom='chevron',
                fill=pal_t['badgeBg'], border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 16.0, 'top': 2.0, 'right': 14.0, 'bottom': 2.0},
                           'paragraphs': [make_para([make_run(head_txt, max(9.5, body_sz), True, pal_t['badgeFg'], font)], align='center', spaceAfter=0.0)]}
            ))

            paras = []
            if st.get('metric'):
                paras.append(make_para([make_run(str(st['metric']), max(11.0, title_sz - 0.5), True, pal_t['title'], font)], align='center', spaceAfter=4.0))
            if st.get('desc'):
                paras.append(make_para([make_run(str(st['desc']), max(9.3, body_sz - 0.3), False, pal_t['body'], font)], align='left', spaceAfter=0.0))
            if not paras:
                paras.append(make_para([make_run(' ', body_sz, False, pal_t['body'], font)], spaceAfter=0.0))

            if is_terra:
                children.append(_make_child_shape(
                    cid, next_idx(), 'stage-box', f'stage-box_{i+1}', bx, by,
                    sx_rel, box_y, sw, box_h, geom='rect',
                    fill=pal_t['bg'], fill_alpha=0.92, border_color=pal_t['border'], border_width=0.95, border_alpha=0.40, shadow=True,
                    text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 7.0, 'top': 9.0, 'right': 7.0, 'bottom': 6.0}, 'paragraphs': paras}
                ))
                children.append(_make_child_shape(
                    cid, next_idx(), 'shape', f'stage-top-bar_{i+1}', bx, by,
                    sx_rel, box_y, sw, 3.5, geom='rect', fill=pal_t.get('stripe') or pal_t['badgeBg'], border_width=0.0
                ))
            else:
                children.append(_make_child_shape(
                    cid, next_idx(), 'stage-box', f'stage-box_{i+1}', bx, by,
                    sx_rel, box_y, sw, box_h, geom='roundRect',
                    fill=pal_t['bg'], border_color=pal_t['border'], border_width=1.1,
                    text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 7.0, 'top': 6.0, 'right': 7.0, 'bottom': 6.0}, 'paragraphs': paras},
                    adj=8000
                ))

            if i < m - 1:
                children.append(_make_child_shape(
                    cid, next_idx(), 'connector', f'connector_{i+1}', bx, by,
                    round(sx_rel + sw + 2.0, 2), round(box_y + box_h / 2.0, 2),
                    round(max(4.0, gap - 4.0), 2), 0.0, geom='line',
                    border_color='#18181B' if is_terra else tpl_primary, border_width=1.5, tail_end='triangle'
                ))

        if summary:
            children.append(_make_child_shape(
                cid, next_idx(), 'summary-bar', 'summary-bar', bx, by,
                0.0, round(cur_y + mid_h + sum_gap, 2), w, sum_h, geom='rect' if is_terra else 'roundRect',
                fill='#18181B' if is_terra else pal.get('bannerBg', '#EDF2F8'),
                border_color=tpl_primary, border_width=1.1,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 10.0, 'top': 2.0, 'right': 10.0, 'bottom': 2.0},
                           'paragraphs': [make_para([make_run(summary, max(9.0, body_sz), True, '#D0E516' if is_terra else pal.get('titleColor', tpl_primary), font)], align='left', spaceAfter=0.0)]},
                adj=10000
            ))

        comp['children'] = children
        return comp

    # -------------------- 15. iteration-lanes --------------------
    if ctype == 'iteration-lanes':
        lanes = content.get('lanes') or []
        if not lanes:
            return comp
        topology = (content.get('topology') or '').strip()
        topo_h = 28.0 if topology else 0.0
        topo_gap = header_gap if topology else 0.0
        lane_h = round(max(120.0, h - topo_h - topo_gap), 2)
        if h < lane_h + topo_h + topo_gap:
            h = round(lane_h + topo_h + topo_gap, 1)
            comp['h'] = h

        l_cnt = len(lanes)
        gap = max(12.0, float(layout.get('itemGap', 18.0)))
        lw = round((w - max(0, l_cnt - 1) * gap) / l_cnt, 2)

        for i, ln in enumerate(lanes):
            l_tone = str(ln.get('tone') or 'neutral').lower()
            pal_t = get_tone(l_tone, tpl, 'neutral')
            lx_rel = round(i * (lw + gap), 2)
            is_rb_lane = l_tone in ('rollback', 'reject')
            is_pass_lane = l_tone in ('pass', 'promoted')

            paras = []
            if ln.get('title'):
                paras.append(make_para([make_run(str(ln['title']), max(10.5, title_sz - 0.5), True, pal_t['title'], font)], spaceAfter=4.0))
            if ln.get('metric'):
                m_c = '#364204' if (is_terra and is_pass_lane) else pal_t['title']
                paras.append(make_para([make_run(str(ln['metric']), max(10.5, title_sz), True, m_c, font)], spaceAfter=5.0))
            for it in (ln.get('items') or []):
                paras.append(make_para([make_run(str(it), max(9.5, body_sz), False, pal_t['body'], font)], spaceAfter=3.5))
            if ln.get('verdict'):
                paras.append(make_para([make_run(str(ln['verdict']), max(9.5, body_sz), True, pal_t['title'], font)], spaceBefore=4.0, spaceAfter=0.0))
            if not paras:
                paras.append(make_para([make_run(' ', body_sz, False, pal_t['body'], font)], spaceAfter=0.0))

            if is_terra:
                stripe_c = pal_t.get('stripe') or pal_t['badgeBg']
                children.append(_make_child_shape(
                    cid, next_idx(), 'lane-card', f'lane-card_{i+1}', bx, by,
                    lx_rel, 0.0, lw, lane_h, geom='rect',
                    fill=pal_t['bg'], fill_alpha=0.92,
                    border_color=pal_t['border'], border_width=1.0, border_alpha=0.52 if (is_rb_lane or is_pass_lane) else 0.35,
                    dash_style='dash' if is_rb_lane else None, shadow=True,
                    text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 14.0, 'top': 34.0, 'right': 10.0, 'bottom': 6.0}, 'paragraphs': paras}
                ))
                # 左侧 5px 机能竖条
                children.append(_make_child_shape(
                    cid, next_idx(), 'divider', f'lane-stripe_{i+1}', bx, by,
                    lx_rel, 26.0, 5.0, round(max(20.0, lane_h - 26.0), 2), geom='rect',
                    fill=stripe_c, border_width=0.0
                ))
                # 顶部 PRTS 铭牌头：R2 回退用深炭暗绯头配左红信号块；R3 定稿用青柠头配左黑锚块；其余用黑/灰铭牌
                hdr_bg = '#261919' if is_rb_lane else pal_t['badgeBg']
                hdr_fg = '#F5E6E4' if is_rb_lane else pal_t['badgeFg']
                children.append(_make_child_shape(
                    cid, next_idx(), 'badge', f'badge_{i+1}', bx, by,
                    lx_rel, 0.0, lw, 26.0, geom='rect', fill=hdr_bg, border_width=0.0,
                    text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 14.0, 'top': 1.0, 'right': 6.0, 'bottom': 1.0},
                               'paragraphs': [make_para([make_run(str(ln.get('round', f'R{i}')), max(9.5, body_sz), True, hdr_fg, font)], align='center', spaceAfter=0.0)]}
                ))
                if is_rb_lane or is_pass_lane:
                    children.append(_make_child_shape(
                        cid, next_idx(), 'shape', f'badge-anchor_{i+1}', bx, by,
                        lx_rel, 0.0, 10.0, 26.0, geom='rect',
                        fill='#A63429' if is_rb_lane else '#18181B', border_width=0.0
                    ))
            else:
                children.append(_make_child_shape(
                    cid, next_idx(), 'lane-card', f'lane-card_{i+1}', bx, by,
                    lx_rel, 0.0, lw, lane_h, geom='roundRect',
                    fill=pal_t['bg'], border_color=pal_t['border'], border_width=1.2,
                    text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 8.0, 'top': 32.0, 'right': 8.0, 'bottom': 6.0}, 'paragraphs': paras},
                    adj=8000
                ))
                children.append(_make_child_shape(
                    cid, next_idx(), 'badge', f'badge_{i+1}', bx, by,
                    lx_rel, 0.0, lw, 26.0, geom='roundRect',
                    fill=pal_t['badgeBg'], border_width=0.0,
                    text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 6.0, 'top': 1.0, 'right': 6.0, 'bottom': 1.0},
                               'paragraphs': [make_para([make_run(str(ln.get('round', f'R{i}')), max(9.5, body_sz), True, pal_t['badgeFg'], font)], align='center', spaceAfter=0.0)]},
                    adj=8000
                ))

            if i < l_cnt - 1:
                next_tone = str(lanes[i + 1].get('tone', '')).lower()
                is_rb = next_tone in ('rollback', 'reject')
                children.append(_make_child_shape(
                    cid, next_idx(), 'connector', f'connector_{i+1}', bx, by,
                    round(lx_rel + lw + 2.0, 2), round(lane_h / 2.0, 2),
                    round(max(4.0, gap - 4.0), 2), 0.0, geom='line',
                    border_color=('#A63429' if is_terra else '#8C2D3C') if is_rb else ('#18181B' if is_terra else tpl_primary),
                    border_width=1.6, tail_end='triangle', dash_style='dash' if is_rb else None
                ))

        if topology:
            children.append(_make_child_shape(
                cid, next_idx(), 'topology-bar', 'topology-bar', bx, by,
                0.0, round(lane_h + topo_gap, 2), w, topo_h, geom='rect' if is_terra else 'roundRect',
                fill='#18181B' if is_terra else pal.get('bannerBg', '#EDF2F8'),
                border_color=tpl_primary, border_width=1.1,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 10.0, 'top': 2.0, 'right': 10.0, 'bottom': 2.0},
                           'paragraphs': [make_para([make_run(topology, max(9.0, body_sz), True, '#D0E516' if is_terra else pal.get('titleColor', tpl_primary), font)], align='left', spaceAfter=0.0)]},
                adj=10000
            ))

        comp['children'] = children
        return comp

    # -------------------- 16. rule-checklist --------------------
    if ctype == 'rule-checklist':
        rows = content.get('rows') or []
        if not rows:
            return comp
        title = (content.get('title') or '').strip()
        mode = content.get('mode') or 'checklist'
        gap = max(4.0, float(layout.get('itemGap', 6.0)))
        title_h = 24.0 if title else 0.0
        t_gap = header_gap if title else 0.0
        r_cnt = len(rows)
        min_need = py * 2.0 + title_h + t_gap + r_cnt * 28.0 + max(0, r_cnt - 1) * gap
        if h < min_need:
            h = round(min_need, 1)
            comp['h'] = h

        children.append(_make_child_shape(
            cid, next_idx(), 'container', 'container', bx, by,
            0.0, 0.0, w, h, geom='rect' if is_terra else 'roundRect',
            fill='#FFFFFF', fill_alpha=0.90 if is_terra else 1.0,
            border_color='#27272A' if is_terra else pal.get('cardBorder', '#CBD5E1'),
            border_width=1.0 if is_terra else float(style.get('borderWidth') or 1.2),
            border_alpha=0.3 if is_terra else 1.0, shadow=is_terra, adj=8000
        ))
        if is_terra:
            children.append(_make_child_shape(cid, next_idx(), 'divider', 'rule-left-bar', bx, by, 0.0, 0.0, 6.0, h, geom='rect', fill='#18181B', border_width=0.0))

        cur_y = py
        if title:
            children.append(_make_child_shape(
                cid, next_idx(), 'title', 'title', bx, by,
                px, cur_y, max(40.0, w - 2.0 * px), title_h, geom='rect', fill=None, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 0.0, 'top': 0.0, 'right': 0.0, 'bottom': 0.0},
                           'paragraphs': [make_para([make_run(title, title_sz, True, '#141413' if is_terra else (style.get('titleColor') or pal.get('titleColor', tpl_primary)), font)], spaceAfter=0.0)]}
            ))
            cur_y = round(cur_y + title_h + t_gap, 2)

        avail_h = max(28.0 * r_cnt, h - cur_y - py)
        row_h = round((avail_h - max(0, r_cnt - 1) * gap) / r_cnt, 2)

        for i, r in enumerate(rows):
            r_tone = str(r.get('tone') or 'info').lower()
            pal_t = get_tone(r_tone, tpl, 'info')
            is_kv = (mode == 'kv-matrix')
            badge_w = min(98.0, round(w * 0.28, 1)) if is_kv else min(30.0, row_h)
            badge_h = row_h if is_kv else badge_w
            badge_y = round(cur_y + (row_h - badge_h) / 2.0, 2)
            badge_geom = ('plaque' if is_terra else 'roundRect') if is_kv else ('hexagon' if is_terra else 'oval')

            # terra_quest 下“准/PASS”徽章采用曜石黑底+亮青柠字，与“禁(暗绯)/警(黄铜)”形成克制统一工业矩阵
            if is_terra and not is_kv and r_tone in ('pass', 'promoted'):
                b_bg, b_fg = '#18181B', '#D0E516'
            else:
                b_bg, b_fg = pal_t['badgeBg'], pal_t['badgeFg']

            children.append(_make_child_shape(
                cid, next_idx(), 'badge', f'badge_{i+1}', bx, by,
                px, badge_y, badge_w, badge_h, geom=badge_geom,
                fill=b_bg, border_width=0.0,
                text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 3.0, 'top': 1.0, 'right': 3.0, 'bottom': 1.0},
                           'paragraphs': [make_para([make_run(str(r.get('badge', '•')), max(9.5, body_sz), True, b_fg, font)], align='center', spaceAfter=0.0)]},
                adj=10000
            ))

            r_title = str(r.get('title', '')).strip()
            r_desc = str(r.get('desc', '')).strip()
            runs = []
            if r_title:
                runs.append(make_run(f"{r_title}：", max(9.5, body_sz), True, pal_t['title'], font))
            if r_desc or not runs:
                runs.append(make_run(r_desc or ' ', max(9.5, body_sz), False, pal_t['body'] if is_terra else '#334155', font))

            item_x = round(px + badge_w + 8.0, 2)
            item_w = round(max(40.0, w - px - item_x), 2)
            children.append(_make_child_shape(
                cid, next_idx(), 'rule-item', f'rule-item_{i+1}', bx, by,
                item_x, cur_y, item_w, row_h, geom='rect' if is_terra else 'roundRect',
                fill='#F7F5EC' if is_terra else '#FFFFFF',
                border_color='#DCD8CC' if is_terra else '#E2E8F0', border_width=0.9,
                text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 10.0 if is_terra else 8.0, 'top': 3.0, 'right': 8.0, 'bottom': 3.0},
                           'paragraphs': [make_para(runs, spaceAfter=0.0)]},
                adj=8000
            ))
            if is_terra and not is_kv:
                children.append(_make_child_shape(
                    cid, next_idx(), 'divider', f'rule-stripe_{i+1}', bx, by,
                    item_x, cur_y, 3.5, row_h, geom='rect',
                    fill=pal_t.get('stripe') or pal_t['badgeBg'], border_width=0.0
                ))
            cur_y = round(cur_y + row_h + gap, 2)

        comp['children'] = children
        return comp

    # -------------------- 17. process-flow --------------------
    if ctype == 'process-flow':
        items = content.get('items') or []
        if not items:
            return comp
        n = len(items)
        gap = max(14.0, float(layout.get('itemGap', 22.0)))
        step_w = round((w - max(0, n - 1) * gap) / n, 2)
        hl_bg = pal.get('bannerBg', '#EDF2F8')
        norm_bg = pal.get('cardBg', '#F6F8FB')
        norm_border = pal.get('cardBorder', '#94A3B8')

        for i, raw_it in enumerate(items):
            if isinstance(raw_it, dict):
                st = str(raw_it.get('title') or '')
                sd = str(raw_it.get('desc') or '')
            else:
                parts = str(raw_it).split('|', 1)
                if len(parts) == 1 and '\n' in parts[0]:
                    parts = parts[0].split('\n', 1)
                st = parts[0].strip()
                sd = parts[1].strip() if len(parts) > 1 else ''
            sx_rel = round(i * (step_w + gap), 2)

            if is_terra:
                children.append(_make_child_shape(
                    cid, next_idx(), 'step-box', f'step-box_{i+1}', bx, by,
                    sx_rel, 0.0, step_w, h, geom='rect', fill='#FFFFFF', fill_alpha=0.90,
                    border_color='#27272A', border_width=0.9, border_alpha=0.30, shadow=True
                ))
                children.append(_make_child_shape(
                    cid, next_idx(), 'shape', f'step-glow_{i+1}', bx, by,
                    sx_rel, 0.0, step_w, 28.0, geom='rect', fill=None, border_width=0.0, grad_fill=_terra_glow('#D0E516', 0.30, angle=0.0)
                ))
                # 顶部小圆形科技图标徽章
                children.append(_make_child_shape(
                    cid, next_idx(), 'badge', f'step-dot_{i+1}', bx, by,
                    round(sx_rel + 10.0, 2), 8.0, 22.0, 22.0, geom='oval', fill='#18181B', border_color='#D0E516', border_width=1.2
                ))
                lime_icons = _get_icon_paths(tpl, 'lime')
                children.append(_make_child_image(
                    cid, next_idx(), 'image', f'step-ico_{i+1}', bx, by,
                    round(sx_rel + 14.0, 2), 12.0, 14.0, 14.0, lime_icons[i % len(lime_icons)]
                ))
                children.append(_make_child_shape(
                    cid, next_idx(), 'title', f'step-title_{i+1}', bx, by,
                    round(sx_rel + 36.0, 2), 6.0, round(max(40.0, step_w - 44.0), 2), 26.0, geom='rect', fill=None, border_width=0.0,
                    text_body={'valign': 'middle', 'wrap': True, 'padding': {'left': 2, 'top': 0, 'right': 2, 'bottom': 0},
                               'paragraphs': [make_para([make_run(st, min(11.0, max(9.5, title_sz - 1.0)), True, '#141413', font)], spaceAfter=0.0)]}
                ))
                if sd:
                    children.append(_make_child_shape(
                        cid, next_idx(), 'body', f'step-desc_{i+1}', bx, by,
                        round(sx_rel + 10.0, 2), 34.0, round(step_w - 20.0, 2), round(max(30.0, h - 40.0), 2), geom='rect', fill=None, border_width=0.0,
                        text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 0, 'top': 2, 'right': 0, 'bottom': 2},
                                   'paragraphs': [make_para([make_run(sd, min(9.5, body_sz), False, '#2E2D2A', font)], spaceAfter=0.0)]}
                    ))
                if i < n - 1:
                    children.append(_make_child_shape(
                        cid, next_idx(), 'shape', f'step-chev_{i+1}', bx, by,
                        round(sx_rel + step_w + max(2.0, (gap - 12.0) / 2.0), 2), round(h / 2.0 - 9.0, 2), 12.0, 18.0,
                        geom='chevron', fill='#D0E516', border_color='#18181B', border_width=0.8
                    ))
            else:
                is_hl = (i == 0 or i == n - 1) if n >= 3 else (i == n // 2)
                paras = [make_para([make_run(st, max(10.5, title_sz - 1.0), True, tpl_primary if is_hl else pal.get('secondary', '#2B547E'), font)], spaceAfter=5.0)]
                if sd:
                    paras.append(make_para([make_run(sd, max(9.3, body_sz - 0.5), False, pal.get('bodyColor', '#334155'), font)], spaceAfter=0.0))
                children.append(_make_child_shape(
                    cid, next_idx(), 'step-box', f'step-box_{i+1}', bx, by,
                    sx_rel, 0.0, step_w, h, geom='roundRect',
                    fill=hl_bg if is_hl else norm_bg,
                    border_color=tpl_primary if is_hl else norm_border, border_width=1.2,
                    text_body={'valign': 'top', 'wrap': True, 'padding': {'left': 10.0, 'top': 9.0, 'right': 10.0, 'bottom': 9.0}, 'paragraphs': paras},
                    adj=8000
                ))
                if i < n - 1:
                    children.append(_make_child_shape(
                        cid, next_idx(), 'connector', f'connector_{i+1}', bx, by,
                        round(sx_rel + step_w + 2.0, 2), round(h / 2.0, 2),
                        round(max(4.0, gap - 4.0), 2), 0.0, geom='line',
                        border_color=tpl_primary, border_width=1.6, tail_end='triangle'
                    ))
        comp['children'] = children
        return comp

    return comp


def rebuild_component_layout(comp, template=None):
    return compile_component(comp, template=template)


def create_default_component(comp_type, comp_id=None, template_id=None):
    """按指定模板（默认学术深蓝 academic）生成自适应画布尺寸的标准元件初始 JSON。"""
    tpl = get_template(template_id or DEFAULT_TEMPLATE_ID)
    pal = tpl['palette']
    skel = tpl['skeleton']
    cw = float(tpl['canvas'].get('width', 1020.67))
    ch = float(tpl['canvas'].get('height', 680.33))
    mx = float(skel.get('defaultMarginX', 48.0))
    safe_w = round(cw - mx * 2, 2)
    ftr_y = float(skel.get('footerY', ch - 84.0))
    top_y = float(skel.get('contentTopY', 136.0))

    cid = comp_id or f"comp_{uuid.uuid4().hex[:8]}"
    primary = pal['primary']
    title_c = pal['titleColor']
    body_c = pal['bodyColor']
    font = pal.get('fontFamily', '微软雅黑')

    if comp_type == 'slide-header':
        comp = {
            'id': cid, 'type': 'slide-header', 'subType': 'default', 'name': 'slide-header',
            'x': 0.0, 'y': 0.0, 'w': cw, 'h': 120.0,
            'layout': {'paddingX': 10.0, 'paddingY': 8.0, 'headerGap': 4.0, 'itemGap': 4.0, 'lineHeight': 1.25, 'align': 'left', 'valign': 'top'},
            'style': {'fill': pal['bannerBg'], 'borderColor': primary, 'borderWidth': 0.8, 'borderRadius': 10.0, 'titleColor': title_c, 'titleSize': 19.0, 'titleBold': True, 'bodyColor': pal['mutedColor'], 'bodySize': 10.5, 'accentColor': pal['accent'], 'fontFamily': font},
            'content': {'sectionTag': '01 研究模块', 'title': '新建页面主标题', 'subtitle': '在此输入页面副标题与核心论点导语', 'pageNumber': '1 / 1', 'items': []},
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'section-divider':
        comp = {
            'id': cid, 'type': 'section-divider', 'subType': 'declarative', 'name': 'section-divider',
            'x': 0.0, 'y': 0.0, 'w': cw, 'h': ch,
            'layout': {'paddingX': mx, 'paddingY': 20.0, 'headerGap': 8.0, 'itemGap': 8.0, 'lineHeight': 1.2, 'align': 'center', 'valign': 'middle'},
            'style': {'fill': primary, 'borderColor': primary, 'borderWidth': 0.0, 'borderRadius': 0.0, 'titleColor': title_c, 'titleSize': 40.0, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 14.0, 'accentColor': pal['accent'], 'fontFamily': font},
            'content': {'sectionNumber': 'PART 01', 'title': '第一部分：研究方法与架构', 'leftLabel': 'METHODOLOGY', 'rightLabel': 'FRAMEWORK'},
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'milestone-timeline':
        comp = {
            'id': cid, 'type': 'milestone-timeline', 'subType': 'declarative', 'name': 'milestone-timeline',
            'x': mx, 'y': top_y + 10.0, 'w': safe_w, 'h': 320.0,
            'layout': {'paddingX': 12.0, 'paddingY': 10.0, 'headerGap': 8.0, 'itemGap': 22.0, 'lineHeight': 1.25, 'align': 'left', 'valign': 'top'},
            'style': {'fill': pal['cardBg'], 'borderColor': pal['cardBorder'], 'borderWidth': 1.0, 'borderRadius': 8.0, 'titleColor': title_c, 'titleSize': 12.0, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.0, 'accentColor': pal['accent'], 'fontFamily': font},
            'content': {
                'milestones': [
                    {'step': '01', 'tag': 'PHASE A', 'icon': 'flask', 'title': '数据发现与清洗对齐', 'desc': '校验真实底表结构与历史时点快照口径，隔离事后重述干扰'},
                    {'step': '02', 'tag': 'PHASE B', 'icon': 'gear', 'title': '核心算子与约束构建', 'desc': '解耦计算口径与缓冲区机制，支持单变量受控消融验证'},
                    {'step': '03', 'tag': 'PHASE C', 'icon': 'board', 'title': '分歧归因与门禁裁决', 'desc': '横向剥离误差源并纵向定位首处分歧漏斗，严禁盲目调参'},
                    {'step': '04', 'tag': 'PHASE D', 'icon': 'chart', 'title': '样本外收敛与验收交付', 'desc': '跨多期调仓窗口稳定性检验，达成命中率与重合度门禁阈值'}
                ]
            },
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'footer-banner':
        comp = {
            'id': cid, 'type': 'footer-banner', 'subType': 'default', 'name': 'footer-banner',
            'x': mx, 'y': ftr_y, 'w': safe_w, 'h': 44.0,
            'layout': {'paddingX': 12.0, 'paddingY': 8.0, 'headerGap': 4.0, 'itemGap': 4.0, 'lineHeight': 1.2, 'align': 'left', 'valign': 'middle'},
            'style': {'fill': pal['bannerBg'], 'borderColor': pal['bannerBorder'], 'borderWidth': 1.1, 'borderRadius': 10.0, 'titleColor': primary, 'titleSize': 10.5, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.0, 'accentColor': pal['accent'], 'fontFamily': font},
            'content': {'prefix': '结论与启示：', 'title': '结论与启示：', 'subtitle': '在此输入本页核心发现、实证含义或设计边界说明。', 'items': []},
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'data-table':
        comp = {
            'id': cid, 'type': 'data-table', 'subType': 'default', 'name': 'data-table',
            'x': mx, 'y': top_y + 10.0, 'w': round(safe_w * 0.65, 1), 'h': 140.0,
            'layout': {'paddingX': 8.0, 'paddingY': 6.0, 'headerGap': 0.0, 'itemGap': 0.0, 'lineHeight': 1.2, 'align': 'left', 'valign': 'middle'},
            'style': {'fill': '#FFFFFF', 'borderColor': pal['cardBorder'], 'borderWidth': 1.0, 'borderRadius': 0.0, 'titleColor': '#FFFFFF', 'titleSize': 10.5, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.0, 'accentColor': pal['tableHeaderBg'], 'fontFamily': font},
            'content': {
                'title': 'data-table',
                'headers': ['评估维度', '核心指标定义与实验口径', '目标基准'],
                'rows': [
                    ['样本对齐', '统一时点快照校验与异常极值处理口径', '>= 95.0%'],
                    ['统计稳健', '多期样本外交叉验证与参数敏感性边界', '<= 0.05 pp']
                ]
            },
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'process-flow':
        comp = {
            'id': cid, 'type': 'process-flow', 'subType': 'horizontal', 'name': 'process-flow',
            'x': mx, 'y': top_y, 'w': safe_w, 'h': 112.0,
            'layout': {'paddingX': 10.0, 'paddingY': 8.0, 'headerGap': 6.0, 'itemGap': 18.0, 'lineHeight': 1.3, 'align': 'left', 'valign': 'top'},
            'style': {'fill': pal['bannerBg'], 'borderColor': primary, 'borderWidth': 1.2, 'borderRadius': 10.0, 'titleColor': title_c, 'titleSize': 11.5, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.0, 'accentColor': primary, 'fontFamily': font},
            'content': {
                'title': 'process-flow',
                'items': [
                    '1. 问题凝练 | 基于典型事实提出核心假说',
                    '2. 数据建模 | 多源异构样本清洗与口径对齐',
                    '3. 机制检验 | 因果识别与分位数稳健消融',
                    '4. 结论凝练 | 理论边界探讨与实践启示'
                ]
            },
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'tag-badge':
        comp = {
            'id': cid, 'type': 'tag-badge', 'subType': 'pill', 'name': 'tag-badge',
            'x': mx, 'y': top_y + 110.0, 'w': 176.0, 'h': 32.0,
            'layout': {'paddingX': 10.0, 'paddingY': 4.0, 'headerGap': 0.0, 'itemGap': 0.0, 'lineHeight': 1.1, 'align': 'center', 'valign': 'middle'},
            'style': {'fill': primary, 'borderColor': primary, 'borderWidth': 0.0, 'borderRadius': 8.0, 'titleColor': '#FFFFFF', 'titleSize': 11.0, 'titleBold': True, 'bodyColor': '#FFFFFF', 'bodySize': 10.0, 'accentColor': primary, 'fontFamily': font},
            'content': {'title': '核心模块标签', 'subtitle': '', 'items': []},
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'kpi-card':
        comp = {
            'id': cid, 'type': 'kpi-card', 'subType': 'default', 'name': 'kpi-card',
            'x': mx, 'y': top_y, 'w': 300.0, 'h': 420.0,
            'layout': {'paddingX': 12.0, 'paddingY': 10.0, 'headerGap': 6.0, 'itemGap': 6.0, 'lineHeight': 1.3, 'align': 'left', 'valign': 'top'},
            'style': {'fill': '#FFFFFF', 'borderColor': primary, 'borderWidth': 1.2, 'borderRadius': 8.0, 'titleColor': title_c, 'titleSize': 12.5, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.0, 'accentColor': primary, 'fontFamily': font},
            'content': {
                'title': '实验组模型表现 (Model-A)',
                'subtitle': '样本外滚动回测基准',
                'metricValue': '97.7%',
                'metricLabel': '样本外命中率与基准吻合度',
                'image': '/assets/showcase/nav_benchmark.png',
                'items': ['• 覆盖窗口：2018-2025 连续滚动期', '• 拟合误差：年化偏差 <= 0.42%', '核心特征：稳健正则化 + 结构约束']
            },
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'image-frame':
        comp = {
            'id': cid, 'type': 'image-frame', 'subType': 'default', 'name': 'image-frame',
            'x': mx + 20.0, 'y': top_y + 10.0, 'w': 360.0, 'h': 240.0,
            'layout': {'paddingX': 8.0, 'paddingY': 8.0, 'headerGap': 6.0, 'itemGap': 4.0, 'lineHeight': 1.2, 'align': 'center', 'valign': 'middle'},
            'style': {'fill': '#FFFFFF', 'borderColor': pal['cardBorder'], 'borderWidth': 1.0, 'borderRadius': 8.0, 'titleColor': title_c, 'titleSize': 11.0, 'titleBold': True, 'bodyColor': pal['mutedColor'], 'bodySize': 9.5, 'accentColor': primary, 'fontFamily': font},
            'content': {'title': 'image-frame', 'caption': '图 1：多因子机制敏感性与分布对照曲线', 'images': ['/assets/showcase/factor_attribution.png'], 'items': []},
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'toc-list':
        comp = {
            'id': cid, 'type': 'toc-list', 'subType': 'default', 'name': 'toc-list',
            'x': mx + 10.0, 'y': top_y + 10.0, 'w': safe_w - 20.0, 'h': 420.0,
            'layout': {'paddingX': 10.0, 'paddingY': 8.0, 'headerGap': 12.0, 'itemGap': 24.0, 'lineHeight': 1.25, 'align': 'left', 'valign': 'middle'},
            'style': {'fill': primary, 'borderColor': primary, 'borderWidth': 1.0, 'borderRadius': 10.0, 'titleColor': '#1E293B', 'titleSize': 14.5, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.5, 'accentColor': pal['accent'], 'fontFamily': font},
            'content': {
                'title': '目录列表',
                'items': [
                    '01 | 研究背景与核心问题 | 现实痛点凝练、核心假说提出与分析框架界定',
                    '02 | 理论基础与系统设计 | 四层原子化架构栈、门禁约束与识别方法论',
                    '03 | 实证检验与消融评估 | 多阶段归因分析、样本外稳健性与误差边界讨论',
                    '04 | 总结归纳与后续展望 | 核心研究结论、实践应用边界与推进路线图'
                ]
            },
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'cover-divider':
        comp = {
            'id': cid, 'type': 'cover-divider', 'subType': 'cover', 'name': 'cover-divider',
            'x': 0.0, 'y': 0.0, 'w': cw, 'h': ch,
            'layout': {'paddingX': 64.0, 'paddingY': 20.0, 'headerGap': 12.0, 'itemGap': 8.0, 'lineHeight': 1.25, 'align': 'left', 'valign': 'middle'},
            'style': {'fill': primary, 'borderColor': primary, 'borderWidth': 0.0, 'borderRadius': 0.0, 'titleColor': '#FFFFFF', 'titleSize': 27.0, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 12.0, 'accentColor': pal['accent'], 'fontFamily': font},
            'content': {
                'tag': 'ACADEMIC & RESEARCH PRESENTATION',
                'title': '演示文稿核心研究主题',
                'subtitle': '基于元件化结构设计与声明式智能排版引擎的汇报模板',
                'meta': [
                    '汇  报  人：【姓名 / 研究小组】',
                    '所属机构：【院系 / 实验室名称】',
                    '汇报日期：2026 年 11 月'
                ]
            },
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'vertical-stack':
        comp = {
            'id': cid, 'type': 'vertical-stack', 'subType': 'declarative', 'name': 'vertical-stack',
            'x': mx, 'y': top_y, 'w': round(safe_w * 0.48, 1), 'h': 380.0,
            'layout': {'paddingX': 10.0, 'paddingY': 8.0, 'headerGap': 10.0, 'itemGap': 16.0, 'lineHeight': 1.25, 'align': 'left', 'valign': 'middle'},
            'style': {'fill': pal['cardBg'], 'borderColor': primary, 'borderWidth': 1.2, 'borderRadius': 8.0, 'titleColor': title_c, 'titleSize': 12.0, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.0, 'accentColor': primary, 'fontFamily': font},
            'content': {
                'title': '四层原子化构建栈（L1 -> L4）',
                'direction': 'down',
                'layers': [
                    {'tag': 'L1', 'title': '原子数据对齐层', 'desc': '统一时点快照边界与异常值/缺失样本前置清洗口径', 'tone': 'navy'},
                    {'tag': 'L2', 'title': '特征与因子计算层', 'desc': '按固定滚动窗口构建核心指标并执行同口径标准化', 'tone': 'blue'},
                    {'tag': 'L3', 'title': '约束筛选与门禁层', 'desc': '应用缓冲区机制与结构中性硬约束筛选目标样本池', 'tone': 'burgundy'},
                    {'tag': 'L4', 'title': '求解输出与校验层', 'desc': '执行加权求解、边界检查与多期稳健性归因输出', 'tone': 'pass'}
                ]
            },
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'decision-gate':
        comp = {
            'id': cid, 'type': 'decision-gate', 'subType': 'declarative', 'name': 'decision-gate',
            'x': mx, 'y': top_y, 'w': round(safe_w * 0.54, 1), 'h': 300.0,
            'layout': {'paddingX': 10.0, 'paddingY': 8.0, 'headerGap': 16.0, 'itemGap': 14.0, 'lineHeight': 1.25, 'align': 'left', 'valign': 'top'},
            'style': {'fill': pal['bannerBg'], 'borderColor': primary, 'borderWidth': 1.3, 'borderRadius': 8.0, 'titleColor': title_c, 'titleSize': 11.5, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.0, 'accentColor': primary, 'fontFamily': font},
            'content': {
                'gateShape': 'diamond',
                'gateText': '门禁裁决：命中 >= 95% 且未触及约束红线？',
                'branches': [
                    {'label': 'PASS · 晋升发布', 'tone': 'pass', 'title': '锁定当前最优版本', 'items': ['• 命中率 >= 95% 且误差收敛', '• 归档参数并进入终态验收']},
                    {'label': 'WARN · 局部调优', 'tone': 'warn', 'title': '进入单机制消融', 'items': ['• 围绕首处分歧层测试单一规则', '• 保留基准快照便于对照验证']},
                    {'label': 'REJECT · 强制回退', 'tone': 'reject', 'title': '回退至上一锚点', 'items': ['• 核心指标回撤或连续两轮无升', '• 废弃假设并切换下一候选路径']}
                ]
            },
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'stage-funnel':
        comp = {
            'id': cid, 'type': 'stage-funnel', 'subType': 'declarative', 'name': 'stage-funnel',
            'x': mx, 'y': top_y, 'w': safe_w, 'h': 240.0,
            'layout': {'paddingX': 10.0, 'paddingY': 8.0, 'headerGap': 10.0, 'itemGap': 18.0, 'lineHeight': 1.25, 'align': 'left', 'valign': 'top'},
            'style': {'fill': pal['cardBg'], 'borderColor': primary, 'borderWidth': 1.2, 'borderRadius': 8.0, 'titleColor': title_c, 'titleSize': 12.0, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.0, 'accentColor': primary, 'fontFamily': font},
            'content': {
                'title': '首处分歧定位漏斗（S1 -> S5 逐级归因）',
                'stages': [
                    {'code': 'S1', 'name': '数据基准', 'metric': '100% 对齐', 'desc': '检查快照时间与基础口径是否一致', 'tone': 'navy'},
                    {'code': 'S2', 'name': '样本空间', 'metric': '偏差 18 项', 'desc': '核对准入条件与流动性剔除规则', 'tone': 'blue'},
                    {'code': 'S3', 'name': '特征排序', 'metric': '偏差 9 项', 'desc': '对比全样本与分组内部标准化截尾', 'tone': 'warn'},
                    {'code': 'S4', 'name': '约束缓冲', 'metric': '偏差 4 项', 'desc': '检验优先保留区间与切换惩罚阈值', 'tone': 'burgundy'},
                    {'code': 'S5', 'name': '权重求解', 'metric': '重合 97.4%', 'desc': '校验上限约束与二次归一化精度', 'tone': 'pass'}
                ],
                'summary': '定位结论：由上游向下游逐层归因，优先收敛错漏贡献最大的 S2 样本空间口径。'
            },
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'iteration-lanes':
        comp = {
            'id': cid, 'type': 'iteration-lanes', 'subType': 'declarative', 'name': 'iteration-lanes',
            'x': mx, 'y': top_y, 'w': safe_w, 'h': 340.0,
            'layout': {'paddingX': 10.0, 'paddingY': 8.0, 'headerGap': 10.0, 'itemGap': 18.0, 'lineHeight': 1.25, 'align': 'left', 'valign': 'top'},
            'style': {'fill': '#F8FAFC', 'borderColor': '#94A3B8', 'borderWidth': 1.2, 'borderRadius': 8.0, 'titleColor': '#1E293B', 'titleSize': 12.0, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.0, 'accentColor': primary, 'fontFamily': font},
            'content': {
                'lanes': [
                    {'round': 'R0 · 基线', 'tone': 'baseline', 'title': '冷启动默认参数', 'metric': '命中 68 / 100', 'items': ['• 默认周期窗口快照', '• 全局极值截尾标准化', '• 未启用缓冲机制'], 'verdict': '首处分歧：样本池偏差'},
                    {'round': 'R1 · 晋升', 'tone': 'info', 'title': '修正 S2 样本边界', 'metric': '命中 84 / 100 (+16)', 'items': ['• 对齐公告日历边界', '• 引入尾部流动性剔除', '• 冻结下游其余超参数'], 'verdict': '状态：PROMOTED（新锚点）'},
                    {'round': 'R2 · 回退', 'tone': 'rollback', 'title': '盲试放宽约束上限', 'metric': '命中 82 / 100 (-2)', 'items': ['• 上限由 5% 放宽至 8%', '• 触发回退红线（跌 2 项）', '• 权重偏差同步放大'], 'verdict': '状态：REJECT（强制回退 R1）'},
                    {'round': 'R3 · 终态', 'tone': 'pass', 'title': '启用分组中性 + 缓冲', 'metric': '命中 97 / 100 (+13)', 'items': ['• 基于 R1 锚点叠加中性化', '• 启用 20% 优先保留带', '• 权重重合度达 96.4%'], 'verdict': '状态：FINAL（满足验收门禁）'}
                ],
                'topology': '版本演进拓扑：R0 (68) -> R1 (84, 锚点晋升) -> R2 (82, 触发红线回退至 R1) -> R3 (97, 验收交付)'
            },
            'children': []
        }
        return compile_component(comp, tpl)

    if comp_type == 'rule-checklist':
        comp = {
            'id': cid, 'type': 'rule-checklist', 'subType': 'declarative', 'name': 'rule-checklist',
            'x': mx, 'y': top_y, 'w': round(safe_w * 0.50, 1), 'h': 310.0,
            'layout': {'paddingX': 12.0, 'paddingY': 10.0, 'headerGap': 8.0, 'itemGap': 8.0, 'lineHeight': 1.25, 'align': 'left', 'valign': 'middle'},
            'style': {'fill': '#FFFFFF', 'borderColor': pal['cardBorder'], 'borderWidth': 1.2, 'borderRadius': 8.0, 'titleColor': title_c, 'titleSize': 12.5, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.0, 'accentColor': primary, 'fontFamily': font},
            'content': {
                'title': '实验纪律与红线调整边界',
                'mode': 'checklist',
                'rows': [
                    {'badge': '准', 'tone': 'pass', 'title': '单变量受控消融', 'desc': '每次试验仅改动 1 个优先级规则，确保收益可归因'},
                    {'badge': '准', 'tone': 'pass', 'title': '多期样本外交叉验真', 'desc': '至少覆盖最近 3 个连续评估窗口，防止单期过拟合'},
                    {'badge': '警', 'tone': 'warn', 'title': '收益衰减即停阈值', 'desc': '若连续两轮提升低于阈值或误差扩大则切换排错路径'},
                    {'badge': '禁', 'tone': 'reject', 'title': '严禁引入未来信息', 'desc': '禁止使用决策时点之后的观测数据逆向拟合参数'},
                    {'badge': '禁', 'tone': 'reject', 'title': '严禁样本特判硬编码', 'desc': '不得针对个体样本打补丁，规则必须保持通用可解释性'}
                ]
            },
            'children': []
        }
        return compile_component(comp, tpl)

    # Default: info-card
    comp = {
        'id': cid, 'type': 'info-card', 'subType': 'titled-list', 'name': 'info-card',
        'x': mx, 'y': top_y, 'w': 320.0, 'h': 185.0,
        'layout': {'paddingX': 13.0, 'paddingY': 11.0, 'headerGap': 6.0, 'itemGap': 5.0, 'lineHeight': 1.3, 'align': 'left', 'valign': 'top', 'topBar': True},
        'style': {'fill': pal['cardBg'], 'borderColor': pal['cardBorder'], 'borderWidth': 1.0, 'borderRadius': 10.0, 'titleColor': title_c, 'titleSize': 12.0, 'titleBold': True, 'bodyColor': body_c, 'bodySize': 10.0, 'accentColor': primary, 'fontFamily': font},
        'content': {
            'title': '核心研究要点模块',
            'subtitle': '',
            'items': [
                '核心追问：支持自由拖拽与局部空隙分布实时调优',
                '样式联动：支持同类型元件样式跨卡片/跨页面一键同步',
                '智能编译：底层结构化 JSON 面向外部 AI 工具一键生成与导出'
            ]
        },
        'children': []
    }
    return compile_component(comp, tpl)
