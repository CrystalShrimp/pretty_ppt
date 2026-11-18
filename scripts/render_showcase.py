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
from core.templates import (
    get_template,
    apply_template_to_deck,
    build_slide_decorations,
    DEFAULT_TEMPLATE_ID,
)
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
    """构建 6 页覆盖全部 17 类标准元件与渐变/透明/多边形原语的公开全景示范集。"""
    tid = template_id or DEFAULT_TEMPLATE_ID
    base_tpl = get_template(DEFAULT_TEMPLATE_ID)
    pal = base_tpl['palette']
    bgs = base_tpl['backgrounds']

    ensure_showcase_assets(primary=pal['primary'], accent=pal['accent'])

    deck = {
        'id': 'component_showcase',
        'title': 'Pretty PPT · 17 类标准元件全景示范集',
        'templateId': base_tpl['id'],
        'sourceFile': os.path.join(BASE_DIR, 'component_showcase.pptx'),
        'canvas': copy.deepcopy(base_tpl['canvas']) | {'gridSize': 8, 'showGrid': False},
        'theme': {
            'name': base_tpl['name'],
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
    s1_cover = create_default_component('cover-divider', comp_id='sc_s1_c1', template_id=base_tpl['id'])
    s1_cover['name'] = 'cover-divider: 17 类标准元件全景示范集'
    s1_cover['content'] = {
        'tag': f"PRETTY PPT · {tid.upper()}",
        'title': '17 类可复用标准元件全景示范集',
        'subtitle': '面向学术汇报、商业展示与外部 AI 一键调度的声明式排版引擎，支持模板级元件重渲染、渐变光晕与 PPTX 无损往返解析。',
        'meta': [
            '默认风格：学术深蓝 (#1B365D) + 学术酒红 (#7A2048) · 纯矢量零敏感依赖',
            '高阶皮肤：新增 terra_quest 16:9 机能工业风与 section-divider / milestone-timeline 元件',
            '工具生态：支持 /api/templates/{id}/render-deck 元件级重渲染与 /api/ai/generate 一键生稿'
        ]
    }
    compile_component(s1_cover, base_tpl)

    deck['slides'].append({
        'id': 'component_showcase_slide_1',
        'index': 1,
        'title': '17 类标准元件全景示范集',
        'background': copy.deepcopy(bgs['cover']),
        'decorations': build_slide_decorations(base_tpl, is_cover=True, slide_idx=1),
        'components': [s1_cover]
    })

    # ---------- 第 2 页：独立章节过渡页 (section-divider) ----------
    s2_sec = create_default_component('section-divider', comp_id='sc_s2_c1', template_id=base_tpl['id'])
    s2_sec['content'] = {
        'sectionNumber': 'PART 01',
        'title': '核心元件谱系与声明式编译范式',
        'leftLabel': 'ARCHITECTURE',
        'rightLabel': '17 COMPONENTS'
    }
    compile_component(s2_sec, base_tpl)

    deck['slides'].append({
        'id': 'component_showcase_slide_2',
        'index': 2,
        'title': 'PART 01 · 核心元件谱系',
        'background': copy.deepcopy(bgs['cover']),
        'decorations': build_slide_decorations(base_tpl, is_section=True, slide_idx=2),
        'components': [s2_sec]
    })

    # ---------- 第 3 页：基础展示与信息组织元件 ----------
    s3_hdr = create_default_component('slide-header', comp_id='sc_s3_c1', template_id=base_tpl['id'])
    s3_hdr['content'] = {
        'sectionTag': '01 基础与信息元件',
        'title': '基础展示与信息组织元件示范（P03）',
        'subtitle': '完整呈现 slide-header / toc-list / tag-badge / info-card / data-table / footer-banner 六类高频元件',
        'pageNumber': '3 / 6'
    }
    compile_component(s3_hdr, base_tpl)

    s3_toc = create_default_component('toc-list', comp_id='sc_s3_c2', template_id=base_tpl['id'])
    s3_toc['x'], s3_toc['y'], s3_toc['w'], s3_toc['h'] = 48.0, 138.0, 446.0, 260.0
    s3_toc['content'] = {
        'title': '目录索引',
        'items': [
            '01 | 封面与章节 | 全幅标题横幅、穿透色带与序号水印',
            '02 | 复合架构图 | 纵向阶梯、决策门禁、筛选漏斗与规则矩阵',
            '03 | 演进泳道图 | 四态语义流转与强制回退保护门禁',
            '04 | 时间轴与原语 | 双环科技图标轴、KPI 图卡与渐变矢量原语'
        ]
    }
    compile_component(s3_toc, base_tpl)

    s3_tag = create_default_component('tag-badge', comp_id='sc_s3_c3', template_id=base_tpl['id'])
    s3_tag['x'], s3_tag['y'], s3_tag['w'], s3_tag['h'] = 516.0, 138.0, 220.0, 30.0
    s3_tag['content'] = {'title': '元件化皮肤编译 · 规范基准', 'tone': 'primary'}
    compile_component(s3_tag, base_tpl)

    s3_info = create_default_component('info-card', comp_id='sc_s3_c4', template_id=base_tpl['id'])
    s3_info['x'], s3_info['y'], s3_info['w'], s3_info['h'] = 516.0, 178.0, 456.0, 220.0
    s3_info['content'] = {
        'title': '学术信息卡片与全皮肤重渲染（info-card）',
        'items': [
            '内容水合：自动还原解析态元件的结构化标题、要点与语义状态色调',
            '跨风格重绘：支持 academic 顶部色条与 terra_quest 左能量条渐变光晕无缝切换',
            '防失真护栏：PASS / WARN / REJECT 红绿琥珀语义色受换肤保护不丢失',
            '画布自适应：3:2 学术版式可按安全区自动映射至 16:9 宽屏演示版式'
        ]
    }
    compile_component(s3_info, base_tpl)

    s3_tbl = create_default_component('data-table', comp_id='sc_s3_c5', template_id=base_tpl['id'])
    s3_tbl['x'], s3_tbl['y'], s3_tbl['w'], s3_tbl['h'] = 48.0, 412.0, 924.67, 166.0
    s3_tbl['content'] = {
        'title': '17 类标准元件与工程能力对照表',
        'headers': ['元件大类', '代表 type 列表', '核心布局能力', '皮肤重渲染特性'],
        'rows': [
            ['信息骨架 (7)', 'cover-divider / section-divider / slide-header / toc-list / info-card / tag-badge / footer-banner', '顶栏铭牌 + 穿透色带 + 光晕卡片', '支持全模板骨架与装饰层切换'],
            ['逻辑架构 (6)', 'vertical-stack / decision-gate / stage-funnel / iteration-lanes / milestone-timeline / rule-checklist', '六边形门禁、双环图标轴、虚线回退', '语义红绿琥珀与品牌皮肤联动'],
            ['数据原语 (4)', 'kpi-card / data-table / image-frame / process-flow', '平行四边形纹带、HUD 取景框、正交连线', '免手算坐标一键导出标准 PPTX']
        ],
        'colRatios': [1.2, 3.1, 2.5, 2.0]
    }
    compile_component(s3_tbl, base_tpl)

    s3_ftr = create_default_component('footer-banner', comp_id='sc_s3_c6', template_id=base_tpl['id'])
    s3_ftr['x'], s3_ftr['y'], s3_ftr['w'], s3_ftr['h'] = 48.0, 594.0, 924.67, 44.0
    s3_ftr['content'] = {
        'prefix': '基础元件小结：',
        'subtitle': '基础骨架与表格元件承担全篇规范导航与数据表达，确保跨页面边距与字体等级完全收敛。'
    }
    compile_component(s3_ftr, base_tpl)

    deck['slides'].append({
        'id': 'component_showcase_slide_3',
        'index': 3,
        'title': '基础展示与信息组织元件示范（P03）',
        'background': copy.deepcopy(bgs['body']),
        'decorations': build_slide_decorations(base_tpl, slide_idx=3),
        'components': [s3_hdr, s3_toc, s3_tag, s3_info, s3_tbl, s3_ftr]
    })

    # ---------- 第 4 页：复合逻辑架构元件 ----------
    s4_hdr = create_default_component('slide-header', comp_id='sc_s4_c1', template_id=base_tpl['id'])
    s4_hdr['content'] = {
        'sectionTag': '02 复合逻辑架构',
        'title': '复合逻辑架构元件示范（P04）',
        'subtitle': '展示 vertical-stack（纵向架构栈）、decision-gate（分支裁决）与 rule-checklist（红线规则清单）的声明式重排能力',
        'pageNumber': '4 / 6'
    }
    compile_component(s4_hdr, base_tpl)

    s4_vs = create_default_component('vertical-stack', comp_id='sc_s4_c2', template_id=base_tpl['id'])
    s4_vs['x'], s4_vs['y'], s4_vs['w'], s4_vs['h'] = 48.0, 138.0, 442.0, 260.0
    compile_component(s4_vs, base_tpl)

    s4_dg = create_default_component('decision-gate', comp_id='sc_s4_c3', template_id=base_tpl['id'])
    s4_dg['x'], s4_dg['y'], s4_dg['w'], s4_dg['h'] = 510.0, 138.0, 462.67, 260.0
    compile_component(s4_dg, base_tpl)

    s4_rc = create_default_component('rule-checklist', comp_id='sc_s4_c4', template_id=base_tpl['id'])
    s4_rc['x'], s4_rc['y'], s4_rc['w'], s4_rc['h'] = 48.0, 412.0, 924.67, 170.0
    s4_rc['content']['rows'] = s4_rc['content']['rows'][:3]
    compile_component(s4_rc, base_tpl)

    s4_ftr = create_default_component('footer-banner', comp_id='sc_s4_c5', template_id=base_tpl['id'])
    s4_ftr['x'], s4_ftr['y'], s4_ftr['w'], s4_ftr['h'] = 48.0, 594.0, 924.67, 44.0
    s4_ftr['content'] = {
        'prefix': '声明式重排特性：',
        'subtitle': '外部 AI 或模板渲染器只需传递结构化层级、分支与规则数据，即可自动生成菱形/六边形门禁与分叉连线。'
    }
    compile_component(s4_ftr, base_tpl)

    deck['slides'].append({
        'id': 'component_showcase_slide_4',
        'index': 4,
        'title': '复合逻辑架构元件示范（P04）',
        'background': copy.deepcopy(bgs['body']),
        'decorations': build_slide_decorations(base_tpl, slide_idx=4),
        'components': [s4_hdr, s4_vs, s4_dg, s4_rc, s4_ftr]
    })

    # ---------- 第 5 页：漏斗与迭代泳道 ----------
    s5_hdr = create_default_component('slide-header', comp_id='sc_s5_c1', template_id=base_tpl['id'])
    s5_hdr['content'] = {
        'sectionTag': '03 漏斗与演进',
        'title': '多阶段归因漏斗与实验演进泳道（P05）',
        'subtitle': '展示 stage-funnel（燕尾漏斗）与 iteration-lanes（四态泳道 + 虚线回退保护）',
        'pageNumber': '5 / 6'
    }
    compile_component(s5_hdr, base_tpl)

    s5_sf = create_default_component('stage-funnel', comp_id='sc_s5_c2', template_id=base_tpl['id'])
    s5_sf['x'], s5_sf['y'], s5_sf['w'], s5_sf['h'] = 48.0, 136.0, 924.67, 210.0
    compile_component(s5_sf, base_tpl)

    s5_il = create_default_component('iteration-lanes', comp_id='sc_s5_c3', template_id=base_tpl['id'])
    s5_il['x'], s5_il['y'], s5_il['w'], s5_il['h'] = 48.0, 358.0, 924.67, 224.0
    compile_component(s5_il, base_tpl)

    s5_ftr = create_default_component('footer-banner', comp_id='sc_s5_c4', template_id=base_tpl['id'])
    s5_ftr['x'], s5_ftr['y'], s5_ftr['w'], s5_ftr['h'] = 48.0, 594.0, 924.67, 44.0
    s5_ftr['content'] = {
        'prefix': '语义防覆盖护栏：',
        'subtitle': 'PASS 绿 / WARN 琥珀 / REJECT 红受主题切换护栏保护，切换任一皮肤均保留实验裁决语义。'
    }
    compile_component(s5_ftr, base_tpl)

    deck['slides'].append({
        'id': 'component_showcase_slide_5',
        'index': 5,
        'title': '多阶段归因漏斗与实验演进泳道（P05）',
        'background': copy.deepcopy(bgs['body']),
        'decorations': build_slide_decorations(base_tpl, slide_idx=5),
        'components': [s5_hdr, s5_sf, s5_il, s5_ftr]
    })

    # ---------- 第 6 页：双环图标时间轴 + KPI + 图框 + 流程链 + 渐变/多边形矢量原语 ----------
    s6_hdr = create_default_component('slide-header', comp_id='sc_s6_c1', template_id=base_tpl['id'])
    s6_hdr['content'] = {
        'sectionTag': '04 时间轴、指标与原语',
        'title': '双环科技时间轴、KPI 展示与新增几何原语示范（P06）',
        'subtitle': '展示 milestone-timeline / kpi-card / image-frame / process-flow / kv-matrix 及 gradFill / hexagon / parallelogram 原语',
        'pageNumber': '6 / 6'
    }
    compile_component(s6_hdr, base_tpl)

    s6_ms = create_default_component('milestone-timeline', comp_id='sc_s6_c2', template_id=base_tpl['id'])
    s6_ms['x'], s6_ms['y'], s6_ms['w'], s6_ms['h'] = 48.0, 134.0, 924.67, 198.0
    compile_component(s6_ms, base_tpl)

    s6_kpi = create_default_component('kpi-card', comp_id='sc_s6_c3', template_id=base_tpl['id'])
    s6_kpi['x'], s6_kpi['y'], s6_kpi['w'], s6_kpi['h'] = 48.0, 344.0, 224.0, 238.0
    s6_kpi['content']['items'] = ['• 滚动期 2018-2025 样本外验真']
    compile_component(s6_kpi, base_tpl)

    s6_img = create_default_component('image-frame', comp_id='sc_s6_c4', template_id=base_tpl['id'])
    s6_img['x'], s6_img['y'], s6_img['w'], s6_img['h'] = 284.0, 344.0, 224.0, 238.0
    s6_img['content'] = {
        'title': 'image-frame',
        'caption': '图 2：各轮次拟合命中率对比',
        'images': ['/assets/showcase/factor_attribution.png']
    }
    compile_component(s6_img, base_tpl)

    s6_pf = create_default_component('process-flow', comp_id='sc_s6_c5', template_id=base_tpl['id'])
    s6_pf['x'], s6_pf['y'], s6_pf['w'], s6_pf['h'] = 520.0, 344.0, 452.67, 102.0
    s6_pf['content'] = {
        'title': 'process-flow',
        'items': ['1. 提取水合 | 还原结构', '2. 皮肤重绘 | 自适应缩放', '3. 编译交付 | 导出PPTX']
    }
    compile_component(s6_pf, base_tpl)

    s6_kv = create_default_component('rule-checklist', comp_id='sc_s6_c6', template_id=base_tpl['id'])
    s6_kv['name'] = 'rule-checklist: kv-matrix'
    s6_kv['x'], s6_kv['y'], s6_kv['w'], s6_kv['h'] = 520.0, 458.0, 220.0, 124.0
    s6_kv['content'] = {
        'title': 'kv-matrix 参数矩阵',
        'mode': 'kv-matrix',
        'rows': [
            {'badge': '快照窗口', 'tone': 'navy', 'title': '时点', 'desc': 'T-10 公告边界'},
            {'badge': '限权规范', 'tone': 'burgundy', 'title': '归一化', 'desc': '5.0% 上限求解'}
        ]
    }
    compile_component(s6_kv, base_tpl)

    # 几何、透明渐变与正交连线原语验证卡
    bx, by, bw, bh = 752.0, 458.0, 220.67, 124.0
    s6_prim = {
        'id': 'sc_s6_c7',
        'type': 'info-card',
        'subType': 'primitives-demo',
        'name': 'info-card: 几何与渐变原语验证',
        'x': bx, 'y': by, 'w': bw, 'h': bh,
        'layout': {'paddingX': 8.0, 'paddingY': 6.0, 'headerGap': 4.0, 'itemGap': 4.0, 'lineHeight': 1.2, 'align': 'left', 'valign': 'middle'},
        'style': {'fill': '#F8FAFC', 'borderColor': pal['cardBorder'], 'borderWidth': 1.1, 'borderRadius': 8.0, 'titleColor': pal['titleColor'], 'titleSize': 10.5, 'titleBold': True, 'bodyColor': pal['bodyColor'], 'bodySize': 9.5, 'accentColor': pal['primary'], 'fontFamily': pal.get('fontFamily', '微软雅黑')},
        'content': {'title': '原语：hex / para / gradFill', 'items': ['六边形、平行四边形、线性渐变与正交折线']},
        'children': [
            _make_child_shape('sc_s6_c7', 1, 'container', 'container', bx, by, 0.0, 0.0, bw, bh,
                              geom='roundRect', fill='#F8FAFC', border_color=pal['cardBorder'], border_width=1.1, adj=8000),
            _make_child_shape('sc_s6_c7', 2, 'shape', 'grad_band', bx, by, 4.0, 4.0, round(bw - 8.0, 2), 26.0,
                              geom='rect', fill=None, border_width=0.0,
                              grad_fill={'angle': 0, 'stops': [{'pos': 0.0, 'color': '#D0E516', 'alpha': 0.45}, {'pos': 1.0, 'color': '#1B365D', 'alpha': 0.0}]}),
            _make_child_shape('sc_s6_c7', 3, 'title', 'hexagon_node', bx, by, 10.0, 14.0, 68.0, 32.0,
                              geom='hexagon', fill=pal['primary'], border_width=0.0,
                              text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 4, 'top': 2, 'right': 4, 'bottom': 2},
                                         'paragraphs': [make_para([make_run('hexagon', 8.5, True, '#FFFFFF')], align='center', spaceAfter=0)]}),
            _make_child_shape('sc_s6_c7', 4, 'shape', 'para_node', bx, by, 92.0, 14.0, 64.0, 24.0,
                              geom='parallelogram', fill=pal['accent'], border_width=0.0, adj=32000,
                              text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 4, 'top': 1, 'right': 4, 'bottom': 1},
                                         'paragraphs': [make_para([make_run('para', 8.5, True, '#FFFFFF')], align='center', spaceAfter=0)]}),
            _make_child_shape('sc_s6_c7', 5, 'body', 'oval_target', bx, by, 134.0, 78.0, 76.0, 30.0,
                              geom='oval', fill='#F0FDF4', border_color='#16A34A', border_width=1.2,
                              text_body={'valign': 'middle', 'wrap': False, 'padding': {'left': 4, 'top': 2, 'right': 4, 'bottom': 2},
                                         'paragraphs': [make_para([make_run('oval 终态', 8.5, True, '#15803D')], align='center', spaceAfter=0)]}),
            _make_child_shape('sc_s6_c7', 6, 'connector', 'elbow_conn', bx, by, 80.0, 30.0, 92.0, 44.0,
                              geom='elbowConnector', fill=None, border_color=pal['primary'], border_width=1.5, tail_end='triangle'),
            _make_child_shape('sc_s6_c7', 7, 'connector', 'flip_dot_conn', bx, by, 14.0, 78.0, 114.0, 26.0,
                              geom='line', fill=None, border_color='#DC2626', border_width=1.4,
                              flip_h=True, flip_v=True, head_end='triangle', tail_end='triangle', dash_style='dot')
        ]
    }

    s6_ftr = create_default_component('footer-banner', comp_id='sc_s6_c8', template_id=base_tpl['id'])
    s6_ftr['x'], s6_ftr['y'], s6_ftr['w'], s6_ftr['h'] = 48.0, 594.0, 924.67, 44.0
    s6_ftr['content'] = {
        'prefix': '全景闭环验收：',
        'subtitle': '6 页示范集覆盖全部 17 类标准元件与渐变/透明/多边形原语，支持任意内置与本地模板一键重渲染。'
    }
    compile_component(s6_ftr, base_tpl)

    deck['slides'].append({
        'id': 'component_showcase_slide_6',
        'index': 6,
        'title': '双环科技时间轴、KPI 展示与新增几何原语示范（P06）',
        'background': copy.deepcopy(bgs['body']),
        'decorations': build_slide_decorations(base_tpl, slide_idx=6),
        'components': [s6_hdr, s6_ms, s6_kpi, s6_img, s6_pf, s6_kv, s6_prim, s6_ftr]
    })

    if tid != DEFAULT_TEMPLATE_ID:
        deck = apply_template_to_deck(deck, tid, scope='deck', rerender_components=True, adapt_canvas=True)
        for slide in deck['slides']:
            for c in slide['components']:
                if c.get('subType') == 'primitives-demo':
                    from core.exporter import sync_component_children_coords
                    c['children'] = sync_component_children_coords(c)
                    bx0, by0 = float(c['x']), float(c['y'])
                    for ch in c['children']:
                        ch['relX'] = round(ch['x'] - bx0, 2)
                        ch['relY'] = round(ch['y'] - by0, 2)
                        ch['relW'] = round(ch['w'], 2)
                        ch['relH'] = round(ch['h'], 2)

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
        print(f"Rendered showcase ({tid}) -> {out_abs} (slides={len(deck['slides'])}, types={len(deck['componentStats'])})")
        return out_abs

    root_pptx = os.path.join(BASE_DIR, 'component_showcase.pptx')
    output_pptx = os.path.join(BASE_DIR, 'output', 'component_showcase.pptx')
    json_path = os.path.join(BASE_DIR, 'decks', 'component_showcase.json')

    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)

    export_deck_to_pptx(deck, root_pptx)
    export_deck_to_pptx(deck, output_pptx)

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
