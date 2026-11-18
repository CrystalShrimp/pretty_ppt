import argparse
import copy
import json
import math
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PIL import Image, ImageDraw, ImageFont
from core.schema import (
    compile_component,
    create_default_component,
    make_para,
    make_run,
    _make_child_shape,
)
from core.templates import get_template, apply_template_to_deck, DEFAULT_TEMPLATE_ID
from core.exporter import export_deck_to_pptx
from core.converter import convert_pptx_to_deck


SHOWCASE_ASSETS_DIR = os.path.join(BASE_DIR, 'assets', 'showcase')


def _load_pil_font(size):
    candidates = [
        r'C:\Windows\Fonts\msyh.ttc',
        r'C:\Windows\Fonts\segoeui.ttf',
        r'C:\Windows\Fonts\arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def ensure_showcase_assets(primary='#1B365D', accent='#7A2048'):
    """生成两张干净、无外部敏感依赖的高清示范科研图表到 assets/showcase/。"""
    os.makedirs(SHOWCASE_ASSETS_DIR, exist_ok=True)
    f_title = _load_pil_font(34)
    f_axis = _load_pil_font(22)
    f_leg = _load_pil_font(22)

    # 1. nav_benchmark.png: 累计净值 vs 误差跟踪轨迹（2x 超采样抗锯齿缩放）
    p1 = os.path.join(SHOWCASE_ASSETS_DIR, 'nav_benchmark.png')
    W, H = 1600, 960
    img1 = Image.new('RGB', (W, H), '#FFFFFF')
    d1 = ImageDraw.Draw(img1)
    d1.text((W // 2 - 280, 26), 'Benchmark Curve vs Model Trajectory', fill='#1E293B', font=f_title)

    mx0, my0, mx1, my1 = 120, 95, 1520, 620
    d1.rectangle([mx0, my0, mx1, my1], outline='#94A3B8', width=2)
    for k in range(1, 5):
        gy = my0 + int((my1 - my0) * k / 5)
        d1.line([(mx0, gy), (mx1, gy)], fill='#E2E8F0', width=2)
    for k in range(1, 6):
        gx = mx0 + int((mx1 - mx0) * k / 6)
        d1.line([(gx, my0), (gx, my1)], fill='#E2E8F0', width=2)

    pts_bench = []
    pts_model = []
    n_pts = 48
    for i in range(n_pts):
        t = i / (n_pts - 1)
        x = mx0 + int((mx1 - mx0) * t)
        val_b = 1.0 + 0.14 * t + 0.018 * math.sin(t * 14.0) + 0.009 * math.cos(t * 25.0)
        val_m = val_b + 0.0022 * math.sin(t * 19.0)
        y_b = my1 - int((val_b - 0.98) / 0.19 * (my1 - my0 - 30)) - 15
        y_m = my1 - int((val_m - 0.98) / 0.19 * (my1 - my0 - 30)) - 15
        pts_bench.append((x, y_b))
        pts_model.append((x, y_m))

    d1.line(pts_bench, fill='#334155', width=6)
    d1.line(pts_model, fill=accent, width=4)

    # 下方误差带子图
    sy0, sy1 = 665, 880
    d1.rectangle([mx0, sy0, mx1, sy1], outline='#94A3B8', width=2)
    mid_y = (sy0 + sy1) // 2
    d1.line([(mx0, mid_y), (mx1, mid_y)], fill='#CBD5E1', width=2)
    pts_err = []
    for i in range(n_pts):
        t = i / (n_pts - 1)
        x = mx0 + int((mx1 - mx0) * t)
        err = 0.45 * math.sin(t * 19.0) + 0.25 * math.cos(t * 9.0)
        y = mid_y - int(err * 55)
        pts_err.append((x, y))
    d1.line(pts_err, fill=primary, width=4)

    d1.rectangle([150, 120, 560, 210], fill='#F8FAFC', outline='#CBD5E1', width=2)
    d1.line([(170, 148), (230, 148)], fill='#334155', width=6)
    d1.text((248, 134), 'Reference Benchmark', fill='#1E293B', font=f_leg)
    d1.line([(170, 184), (230, 184)], fill=accent, width=5)
    d1.text((248, 170), 'Component Model Fit', fill=accent, font=f_leg)
    d1.text((42, my0 + 10), '1.16', fill='#475569', font=f_axis)
    d1.text((42, my1 - 30), '1.00', fill='#475569', font=f_axis)
    d1.text((mx0 + 10, sy1 + 14), 'T0', fill='#475569', font=f_axis)
    d1.text((mx1 - 70, sy1 + 14), 'T+48M', fill='#475569', font=f_axis)
    img1.resize((1200, 720), Image.LANCZOS).save(p1)

    # 2. factor_attribution.png: 柱状分布 + 双轴趋势对比图
    p2 = os.path.join(SHOWCASE_ASSETS_DIR, 'factor_attribution.png')
    img2 = Image.new('RGB', (W, H), '#FFFFFF')
    d2 = ImageDraw.Draw(img2)
    d2.text((W // 2 - 260, 26), 'Layer Attribution & Out-of-Sample Hit Rate', fill='#1E293B', font=f_title)
    bx0, by0, bx1, by1 = 120, 100, 1500, 860
    d2.rectangle([bx0, by0, bx1, by1], outline='#94A3B8', width=2)
    for k in range(1, 5):
        gy = by0 + int((by1 - by0) * k / 5)
        d2.line([(bx0, gy), (bx1, gy)], fill='#E2E8F0', width=2)

    bars = [0.42, 0.56, 0.68, 0.74, 0.83, 0.89, 0.94, 0.97]
    bar_w = 88
    step = (bx1 - bx0 - 100) // len(bars)
    line_pts = []
    for idx_b, val in enumerate(bars):
        cx = bx0 + 85 + idx_b * step
        bh = int(val * (by1 - by0 - 80))
        d2.rectangle([cx - bar_w // 2, by1 - bh, cx + bar_w // 2, by1 - 2], fill=primary if idx_b < 6 else accent)
        line_pts.append((cx, by1 - bh - 18))
        d2.text((cx - 18, by1 + 14), f"R{idx_b}", fill='#475569', font=f_axis)

    d2.line(line_pts, fill='#0D9488', width=5)
    for px_c, py_c in line_pts:
        d2.ellipse([px_c - 9, py_c - 9, px_c + 9, py_c + 9], fill='#0D9488', outline='#FFFFFF', width=2)

    d2.rectangle([150, 128, 600, 200], fill='#F8FAFC', outline='#CBD5E1', width=2)
    d2.rectangle([170, 152, 210, 178], fill=primary)
    d2.text((226, 150), 'Stage Hit Rate (L1-L4)', fill='#1E293B', font=f_leg)
    img2.resize((1200, 720), Image.LANCZOS).save(p2)

    return p1, p2


def build_showcase_deck(template_id=None):
    """构建 5 页覆盖全部 15 类标准元件与矢量原语的公开全景示范集。"""
    tid = template_id or DEFAULT_TEMPLATE_ID
    tpl = get_template(tid)
    pal = tpl['palette']
    bgs = tpl['backgrounds']

    ensure_showcase_assets(primary=pal['primary'], accent=pal['accent'])

    deck = {
        'id': 'component_showcase',
        'title': 'Pretty PPT · 15 类标准元件全景示范集',
        'templateId': tpl['id'],
        'sourceFile': os.path.join(BASE_DIR, 'component_showcase.pptx'),
        'canvas': copy.deepcopy(tpl['canvas']) | {'gridSize': 8, 'showGrid': False},
        'theme': {
            'name': tpl['name'],
            'primaryColor': pal['primary'],
            'secondaryColor': pal['secondary'],
            'accentColor': pal['accent'],
            'textColor': pal['bodyColor'],
            'mutedColor': pal['mutedColor'],
            'fontFamily': pal.get('fontFamily', '微软雅黑')
        },
        'componentStats': {},
        'slides': []
    }

    # ---------- 第 1 页：封面页 (cover-divider) ----------
    s1_cover = create_default_component('cover-divider', comp_id='sc_s1_c1', template_id=tpl['id'])
    s1_cover['name'] = 'cover-divider: 15 类标准元件全景示范集'
    s1_cover['content'] = {
        'tag': f"PRETTY PPT · {tpl['id'].upper()}",
        'title': '15 类可复用标准元件全景示范集',
        'subtitle': '面向学术汇报与外部 AI 工具调用的声明式排版架构，支持自由拖拽、局部间距微调、多风格模板一键切换与 PPTX 100% 无损往返解析。',
        'meta': [
            '默认风格：学术深蓝 (#1B365D) + 学术酒红 (#7A2048) · 纯矢量零敏感依赖',
            '元件体系：基础展示 (5 类) + 复合架构 (5 类) + 多媒体/原语 (5 类)',
            '工具生态：支持 /api/templates 多模板管理与 /api/ai/generate 一键生稿'
        ]
    }
    compile_component(s1_cover, tpl)

    deck['slides'].append({
        'id': 'component_showcase_slide_1',
        'index': 1,
        'title': '15 类标准元件全景示范集',
        'background': copy.deepcopy(bgs['cover']),
        'components': [s1_cover]
    })

    # ---------- 第 2 页：基础展示与信息组织元件 (slide-header, toc-list, tag-badge, info-card, data-table, footer-banner) ----------
    s2_hdr = create_default_component('slide-header', comp_id='sc_s2_c1', template_id=tpl['id'])
    s2_hdr['content'] = {
        'sectionTag': '01 基础与信息元件',
        'title': '基础展示与信息组织元件示范（P02）',
        'subtitle': '完整呈现 slide-header / toc-list / tag-badge / info-card / data-table / footer-banner 六类高频元件',
        'pageNumber': '2 / 5'
    }
    compile_component(s2_hdr, tpl)

    s2_toc = create_default_component('toc-list', comp_id='sc_s2_c2', template_id=tpl['id'])
    s2_toc['x'], s2_toc['y'], s2_toc['w'], s2_toc['h'] = 48.0, 138.0, 446.0, 260.0
    s2_toc['content'] = {
        'title': '目录索引',
        'items': [
            '01 | 封面与页眉 | 统一导航栏、章节胶囊与页码基准',
            '02 | 复合架构图 | 纵向阶梯、决策门禁、筛选漏斗',
            '03 | 演进与规则 | 多轮迭代泳道、红线规则清单矩阵',
            '04 | 图表与原语 | KPI 图卡、流程链与正交折线原语'
        ]
    }
    compile_component(s2_toc, tpl)

    s2_tag = create_default_component('tag-badge', comp_id='sc_s2_c3', template_id=tpl['id'])
    s2_tag['x'], s2_tag['y'], s2_tag['w'], s2_tag['h'] = 516.0, 138.0, 200.0, 30.0
    s2_tag['content'] = {'title': '学术深蓝 · 标准卡片规范', 'tone': 'primary'}
    compile_component(s2_tag, tpl)

    s2_info = create_default_component('info-card', comp_id='sc_s2_c4', template_id=tpl['id'])
    s2_info['x'], s2_info['y'], s2_info['w'], s2_info['h'] = 516.0, 178.0, 456.0, 220.0
    s2_info['content'] = {
        'title': '学术信息卡片设计规范（info-card）',
        'items': [
            '语义纯化：全部采用标准化 type 与结构化 content 驱动编译器',
            '顶部色条：默认学术风格启用 3.5px 顶栏强调条并自动区分主/辅色',
            '多模板切换：一键套用 academic / tech_blue / emerald 或本地私有模板',
            '同类联动：支持单元件、本页同类、全篇同类实时同步 Padding 与字体'
        ]
    }
    compile_component(s2_info, tpl)

    s2_tbl = create_default_component('data-table', comp_id='sc_s2_c5', template_id=tpl['id'])
    s2_tbl['x'], s2_tbl['y'], s2_tbl['w'], s2_tbl['h'] = 48.0, 412.0, 924.67, 166.0
    s2_tbl['content'] = {
        'title': '标准元件能力与工程特性对照',
        'headers': ['元件大类', '代表 type 列表', '核心布局能力', 'AI-API 友好度'],
        'rows': [
            ['信息骨架类', 'slide-header / cover-divider / toc-list / info-card', '顶栏双色带 + 卡片强调条 + 自适应分段', '自动填充坐标与字号'],
            ['逻辑架构类', 'vertical-stack / decision-gate / stage-funnel / iteration-lanes', '菱形分叉、燕尾漏斗、虚线回退自动连接', '传声明式 JSON 即出图'],
            ['数据原语类', 'kpi-card / data-table / image-frame / rule-checklist / process-flow', '表格斑马纹、高清内嵌图表与正交折线', '支持模板级一键换肤']
        ],
        'colRatios': [1.3, 3.0, 2.7, 1.8]
    }
    compile_component(s2_tbl, tpl)

    s2_ftr = create_default_component('footer-banner', comp_id='sc_s2_c6', template_id=tpl['id'])
    s2_ftr['x'], s2_ftr['y'], s2_ftr['w'], s2_ftr['h'] = 48.0, 594.0, 924.67, 44.0
    s2_ftr['content'] = {
        'prefix': '基础元件小结：',
        'subtitle': '基础类元件承担约 75% 常见科研汇报页面骨架，保证全篇页眉对齐与信息密度可控。'
    }
    compile_component(s2_ftr, tpl)

    deck['slides'].append({
        'id': 'component_showcase_slide_2',
        'index': 2,
        'title': '基础展示与信息组织元件示范（P02）',
        'background': copy.deepcopy(bgs['body']),
        'components': [s2_hdr, s2_toc, s2_tag, s2_info, s2_tbl, s2_ftr]
    })

    # ---------- 第 3 页：复合逻辑架构元件 (vertical-stack, decision-gate, rule-checklist) ----------
    s3_hdr = create_default_component('slide-header', comp_id='sc_s3_c1', template_id=tpl['id'])
    s3_hdr['content'] = {
        'sectionTag': '02 复合逻辑架构',
        'title': '复合逻辑架构元件示范（P03）',
        'subtitle': '展示 vertical-stack（纵向架构栈）、decision-gate（分支裁决）与 rule-checklist（红线规则清单）的声明式重排能力',
        'pageNumber': '3 / 5'
    }
    compile_component(s3_hdr, tpl)

    s3_vs = create_default_component('vertical-stack', comp_id='sc_s3_c2', template_id=tpl['id'])
    s3_vs['x'], s3_vs['y'], s3_vs['w'], s3_vs['h'] = 48.0, 138.0, 442.0, 260.0
    compile_component(s3_vs, tpl)

    s3_dg = create_default_component('decision-gate', comp_id='sc_s3_c3', template_id=tpl['id'])
    s3_dg['x'], s3_dg['y'], s3_dg['w'], s3_dg['h'] = 510.0, 138.0, 462.67, 260.0
    compile_component(s3_dg, tpl)

    s3_rc = create_default_component('rule-checklist', comp_id='sc_s3_c4', template_id=tpl['id'])
    s3_rc['x'], s3_rc['y'], s3_rc['w'], s3_rc['h'] = 48.0, 412.0, 924.67, 170.0
    s3_rc['content']['rows'] = s3_rc['content']['rows'][:3]
    compile_component(s3_rc, tpl)

    s3_ftr = create_default_component('footer-banner', comp_id='sc_s3_c5', template_id=tpl['id'])
    s3_ftr['x'], s3_ftr['y'], s3_ftr['w'], s3_ftr['h'] = 48.0, 594.0, 924.67, 44.0
    s3_ftr['content'] = {
        'prefix': '声明式重排特性：',
        'subtitle': '外部 AI 或前端只需传递结构化分支/层级数据，布局引擎自动计算菱形分叉线、胶囊徽章与间距。'
    }
    compile_component(s3_ftr, tpl)

    deck['slides'].append({
        'id': 'component_showcase_slide_3',
        'index': 3,
        'title': '复合逻辑架构元件示范（P03）',
        'background': copy.deepcopy(bgs['body']),
        'components': [s3_hdr, s3_vs, s3_dg, s3_rc, s3_ftr]
    })

    # ---------- 第 4 页：漏斗与迭代泳道 (stage-funnel, iteration-lanes) ----------
    s4_hdr = create_default_component('slide-header', comp_id='sc_s4_c1', template_id=tpl['id'])
    s4_hdr['content'] = {
        'sectionTag': '03 漏斗与演进',
        'title': '多阶段归因漏斗与实验演进泳道（P04）',
        'subtitle': '展示 stage-funnel（燕尾漏斗）与 iteration-lanes（四态泳道 + 虚线回退保护）',
        'pageNumber': '4 / 5'
    }
    compile_component(s4_hdr, tpl)

    s4_sf = create_default_component('stage-funnel', comp_id='sc_s4_c2', template_id=tpl['id'])
    s4_sf['x'], s4_sf['y'], s4_sf['w'], s4_sf['h'] = 48.0, 136.0, 924.67, 210.0
    compile_component(s4_sf, tpl)

    s4_il = create_default_component('iteration-lanes', comp_id='sc_s4_c3', template_id=tpl['id'])
    s4_il['x'], s4_il['y'], s4_il['w'], s4_il['h'] = 48.0, 358.0, 924.67, 224.0
    compile_component(s4_il, tpl)

    s4_ftr = create_default_component('footer-banner', comp_id='sc_s4_c4', template_id=tpl['id'])
    s4_ftr['x'], s4_ftr['y'], s4_ftr['w'], s4_ftr['h'] = 48.0, 594.0, 924.67, 44.0
    s4_ftr['content'] = {
        'prefix': '语义防覆盖护栏：',
        'subtitle': 'PASS 绿 / WARN 琥珀 / REJECT 红受主题切换护栏保护，确保全局换肤不破坏实验裁决语义。'
    }
    compile_component(s4_ftr, tpl)

    deck['slides'].append({
        'id': 'component_showcase_slide_4',
        'index': 4,
        'title': '多阶段归因漏斗与实验演进泳道（P04）',
        'background': copy.deepcopy(bgs['body']),
        'components': [s4_hdr, s4_sf, s4_il, s4_ftr]
    })

    # ---------- 第 5 页：多媒体、KPI与矢量几何连线原语 (process-flow, kpi-card, image-frame, rule-checklist kv-matrix, primitives-demo) ----------
    s5_hdr = create_default_component('slide-header', comp_id='sc_s5_c1', template_id=tpl['id'])
    s5_hdr['content'] = {
        'sectionTag': '04 指标与矢量原语',
        'title': '多媒体、KPI 展示与几何连线原语示范（P05）',
        'subtitle': '展示 process-flow / kpi-card / image-frame / kv-matrix 及 pentagon / oval / elbowConnector / flip 原语',
        'pageNumber': '5 / 5'
    }
    compile_component(s5_hdr, tpl)

    s5_pf = create_default_component('process-flow', comp_id='sc_s5_c2', template_id=tpl['id'])
    s5_pf['x'], s5_pf['y'], s5_pf['w'], s5_pf['h'] = 48.0, 134.0, 924.67, 94.0
    compile_component(s5_pf, tpl)

    s5_kpi = create_default_component('kpi-card', comp_id='sc_s5_c3', template_id=tpl['id'])
    s5_kpi['x'], s5_kpi['y'], s5_kpi['w'], s5_kpi['h'] = 48.0, 240.0, 294.0, 342.0
    compile_component(s5_kpi, tpl)

    s5_img = create_default_component('image-frame', comp_id='sc_s5_c4', template_id=tpl['id'])
    s5_img['x'], s5_img['y'], s5_img['w'], s5_img['h'] = 356.0, 240.0, 304.0, 342.0
    s5_img['content'] = {
        'title': 'image-frame',
        'caption': '图 2：多轮迭代命中率归因分布',
        'images': ['/assets/showcase/factor_attribution.png']
    }
    compile_component(s5_img, tpl)

    s5_kv = create_default_component('rule-checklist', comp_id='sc_s5_c5', template_id=tpl['id'])
    s5_kv['name'] = 'rule-checklist: kv-matrix'
    s5_kv['x'], s5_kv['y'], s5_kv['w'], s5_kv['h'] = 674.0, 240.0, 298.67, 210.0
    s5_kv['content'] = {
        'title': 'rule-checklist (kv-matrix)',
        'mode': 'kv-matrix',
        'rows': [
            {'badge': '快照窗口', 'tone': 'navy', 'title': '时点', 'desc': 'T-10 公告边界对齐'},
            {'badge': '标准截尾', 'tone': 'blue', 'title': '去极值', 'desc': '组内 MAD 3x 截尾'},
            {'badge': '上限约束', 'tone': 'burgundy', 'title': '归一化', 'desc': '5.0% 封顶二次求解'}
        ]
    }
    compile_component(s5_kv, tpl)

    # 几何连线原语验证卡（自定义子形状组合）
    bx, by, bw, bh = 674.0, 462.0, 298.67, 120.0
    s5_prim = {
        'id': 'sc_s5_c6',
        'type': 'info-card',
        'subType': 'primitives-demo',
        'name': 'info-card: 几何与连线原语验证',
        'x': bx, 'y': by, 'w': bw, 'h': bh,
        'layout': {'paddingX': 8.0, 'paddingY': 6.0, 'headerGap': 4.0, 'itemGap': 4.0, 'lineHeight': 1.2, 'align': 'left', 'valign': 'middle'},
        'style': {'fill': '#F8FAFC', 'borderColor': pal['cardBorder'], 'borderWidth': 1.1, 'borderRadius': 8.0, 'titleColor': pal['titleColor'], 'titleSize': 10.5, 'titleBold': True, 'bodyColor': pal['bodyColor'], 'bodySize': 9.5, 'accentColor': pal['primary'], 'fontFamily': pal.get('fontFamily', '微软雅黑')},
        'content': {'title': '原语：pentagon / elbow / flip', 'items': ['正交折线与反向虚线双端箭头']},
        'children': [
            _make_child_shape('sc_s5_c6', 1, 'container', 'container', bx, by, 0.0, 0.0, bw, bh,
                              geom='roundRect', fill='#F8FAFC', border_color=pal['cardBorder'], border_width=1.1, adj=8000),
            _make_child_shape('sc_s5_c6', 2, 'title', 'pentagon_node', bx, by, 10.0, 14.0, 100.0, 32.0,
                              geom='pentagon', fill=pal['primary'], border_color=pal['primary'], border_width=0.0,
                              text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 6, 'top': 2, 'right': 10, 'bottom': 2},
                                         'paragraphs': [make_para([make_run('pentagon', 9.5, True, '#FFFFFF')], align='center', spaceAfter=0)]}),
            _make_child_shape('sc_s5_c6', 3, 'body', 'oval_target', bx, by, 194.0, 74.0, 92.0, 32.0,
                              geom='oval', fill='#F0FDF4', border_color='#16A34A', border_width=1.2,
                              text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 4, 'top': 2, 'right': 4, 'bottom': 2},
                                         'paragraphs': [make_para([make_run('oval 终态', 9.5, True, '#15803D')], align='center', spaceAfter=0)]}),
            _make_child_shape('sc_s5_c6', 4, 'connector', 'elbow_conn', bx, by, 112.0, 30.0, 128.0, 40.0,
                              geom='elbowConnector', fill=None, border_color=pal['primary'], border_width=1.6, tail_end='triangle'),
            _make_child_shape('sc_s5_c6', 5, 'connector', 'flip_dot_conn', bx, by, 18.0, 74.0, 170.0, 26.0,
                              geom='line', fill=None, border_color='#DC2626', border_width=1.5,
                              flip_h=True, flip_v=True, head_end='triangle', tail_end='triangle', dash_style='dot')
        ]
    }

    s5_ftr = create_default_component('footer-banner', comp_id='sc_s5_c7', template_id=tpl['id'])
    s5_ftr['x'], s5_ftr['y'], s5_ftr['w'], s5_ftr['h'] = 48.0, 594.0, 924.67, 44.0
    s5_ftr['content'] = {
        'prefix': '全景闭环验收：',
        'subtitle': '5 页示范集覆盖全部 15 类标准元件与矢量几何原语，默认使用无敏学术风格并支持往返无损解析。'
    }
    compile_component(s5_ftr, tpl)

    deck['slides'].append({
        'id': 'component_showcase_slide_5',
        'index': 5,
        'title': '多媒体、KPI 展示与几何连线原语示范（P05）',
        'background': copy.deepcopy(bgs['body']),
        'components': [s5_hdr, s5_pf, s5_kpi, s5_img, s5_kv, s5_prim, s5_ftr]
    })

    # 统计组件数量
    stats = {}
    for s in deck['slides']:
        for c in s['components']:
            t = c.get('type', 'info-card')
            stats[t] = stats.get(t, 0) + 1
    deck['componentStats'] = stats
    return deck


def render_showcase(template_id=None, out_pptx=None):
    tid = template_id or DEFAULT_TEMPLATE_ID
    deck = build_showcase_deck(tid)

    if out_pptx:
        out_abs = os.path.abspath(out_pptx)
        export_deck_to_pptx(deck, out_abs)
        print(f"Rendered showcase ({tid}) -> {out_abs}")
        return out_abs

    root_pptx = os.path.join(BASE_DIR, 'component_showcase.pptx')
    output_pptx = os.path.join(BASE_DIR, 'output', 'component_showcase.pptx')
    json_path = os.path.join(BASE_DIR, 'decks', 'component_showcase.json')

    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)

    export_deck_to_pptx(deck, root_pptx)
    export_deck_to_pptx(deck, output_pptx)

    # 往返解析验证
    verify_json = os.path.join(BASE_DIR, 'output', '_verify_showcase_roundtrip.json')
    parsed = convert_pptx_to_deck(root_pptx, 'component_showcase', 'component_showcase.pptx', verify_json)
    if os.path.exists(verify_json):
        os.remove(verify_json)

    print(f"Showcase rendered successfully! template={tid}, slides={len(parsed['slides'])}, types={len(deck['componentStats'])}")
    print("Component stats:", json.dumps(deck['componentStats'], ensure_ascii=True))
    return root_pptx


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Render component_showcase.pptx with a chosen template.')
    parser.add_argument('--template', '-t', default=DEFAULT_TEMPLATE_ID, help='Template ID (default: academic)')
    parser.add_argument('--out', '-o', default=None, help='Optional custom output .pptx path')
    args = parser.parse_args()
    render_showcase(template_id=args.template, out_pptx=args.out)
