import copy
import re
import time
import uuid

from core.schema import (
    COMPONENT_TYPES,
    compile_component,
    create_default_component,
)
from core.templates import get_template, list_templates, DEFAULT_TEMPLATE_ID


LAYOUT_DESCRIPTIONS = {
    'cover': '封面/章节大横幅页（支持直接在 slide 传 title/subtitle/tag/meta 或传入 cover-divider 元件）',
    'toc': '目录页（自动生成顶部页眉 + 居中目录列表元件 toc-list）',
    'single': '单一主体元件占满中间内容安全区',
    '2-col': '左右等宽双栏 (50% / 50%)',
    'left-wide': '左宽右窄双栏 (62% / 38%，适合左图右文或左栈右卡)',
    'right-wide': '左窄右宽双栏 (38% / 62%)',
    '3-col': '三栏等宽并排 (适合 3 张 info-card 或 3 张 kpi-card)',
    'top-bottom': '上下两行排列（若首元件为 process-flow / stage-funnel 则自动给上部紧凑条形高度）',
    'top-1-bottom-2': '上通栏 + 下方两列并排',
    'top-1-bottom-3': '上通栏 + 下方三列并排',
    'grid-2x2': '2x2 四宫格矩阵排布（最多支持 4 个主体元件）',
    'auto': '根据页面元件数量与类型智能推断最合适版式（默认）',
    'free': '使用每个元件显式声明的 x / y / w / h 坐标'
}

AI_COMPONENT_SCHEMAS = {
    'cover-divider': {
        'desc': '封面/章节大色块横幅与汇报人信息区',
        'content': {
            'tag': '顶部标签胶囊文案，例如 RESEARCH REPORT',
            'title': '主标题',
            'subtitle': '副标题或研究副题',
            'meta': ['汇报人：xxx', '所属单位：xxx', '日期：2026 年 11 月']
        }
    },
    'slide-header': {
        'desc': '页面标准页眉组（一般由页面 title/subtitle/sectionTag 自动生成，也可显式覆盖）',
        'content': {
            'sectionTag': '左上角章节胶囊文字，如 01 研究背景',
            'title': '页面主标题',
            'subtitle': '页面核心结论导语',
            'pageNumber': '页码字符串，如 2 / 10'
        }
    },
    'toc-list': {
        'desc': '多章节圆角编号目录列表',
        'content': {
            'items': [
                '01 | 第一章标题 | 章节核心内容概述',
                '02 | 第二章标题 | 方法设计或架构说明'
            ]
        }
    },
    'info-card': {
        'desc': '通用学术信息卡片（圆角容器 + 顶部强调条 + 标题 + 结构化条目）',
        'content': {
            'title': '卡片标题',
            'subtitle': '可选副标题',
            'tone': '可选色调：navy | burgundy | blue | pass | warn | reject | orange',
            'items': ['关键概念：支持自动识别冒号前小标题并加粗', '核心结论：第二条结构化要点']
        }
    },
    'footer-banner': {
        'desc': '底部结论横幅（一般由页面 footer 字段自动生成，也可显式传入）',
        'content': {
            'prefix': '结论前缀：',
            'subtitle': '核心总结文本'
        }
    },
    'kpi-card': {
        'desc': '指标图文展示卡（顶部标题胶囊 + 中部图表 + 底部大字号 KPI 与要点）',
        'content': {
            'title': '组别或实验名称',
            'subtitle': '口径说明',
            'metricValue': '97.7%',
            'metricLabel': '样本外命中率',
            'image': '/assets/showcase/nav_benchmark.png',
            'items': ['• 维度一说明', '• 维度二说明']
        }
    },
    'process-flow': {
        'desc': '横向等距步骤链 + 节点间带箭头连接线',
        'content': {
            'items': ['1. 步骤名称 | 步骤简要描述', '2. 下一步骤 | 描述文本']
        }
    },
    'data-table': {
        'desc': '主题色表头 + 斑马纹数据表格',
        'content': {
            'headers': ['列1', '列2', '列3'],
            'rows': [['A1', '说明1', '95%'], ['A2', '说明2', '98%']],
            'colRatios': [1.2, 2.5, 1.3]
        }
    },
    'image-frame': {
        'desc': '圆角边框图片展示框 + 可选图注',
        'content': {
            'image': '/assets/showcase/factor_attribution.png',
            'caption': '图注说明文本'
        }
    },
    'tag-badge': {
        'desc': '实心标签胶囊或分组标识条',
        'content': {'title': '标签名称', 'tone': 'primary | accent | pass | warn | reject'}
    },
    'vertical-stack': {
        'desc': '纵向分层架构栈 + 层间自动居中箭头',
        'content': {
            'title': '架构栈顶部标题（可选）',
            'direction': 'down | up',
            'layers': [
                {'tag': 'L1', 'title': '层级名', 'desc': '层级职责说明', 'tone': 'navy'}
            ]
        }
    },
    'decision-gate': {
        'desc': '顶部判定节点（菱形/圆角框）+ 正交分叉线 + 状态分支结果卡',
        'content': {
            'gateShape': 'diamond | roundRect',
            'gateText': '核心判断条件？',
            'branches': [
                {'label': 'PASS', 'tone': 'pass', 'title': '通过分支', 'items': ['• 处理动作']}
            ]
        }
    },
    'stage-funnel': {
        'desc': '横向多级筛选与归因漏斗（燕尾箭头头 + 损耗定量框 + 底部汇总横条）',
        'content': {
            'title': '漏斗总标题（可选）',
            'stages': [
                {'code': 'S1', 'name': '阶段名', 'metric': '指标值', 'desc': '归因描述', 'tone': 'navy'}
            ],
            'summary': '漏斗定位总结（可选）'
        }
    },
    'iteration-lanes': {
        'desc': '多轮实验演进泳道（四态头 + 实虚线流转箭头 + 演进拓扑条）',
        'content': {
            'lanes': [
                {'round': 'R0 · 基线', 'tone': 'baseline', 'title': '基线模型', 'metric': '68%', 'items': ['• 特征说明'], 'verdict': '状态裁决'}
            ],
            'topology': '版本演进总结字符串（可选）'
        }
    },
    'rule-checklist': {
        'desc': '带矢量语义徽章的规则清单或键值对参数矩阵',
        'content': {
            'title': '清单标题',
            'mode': 'checklist | kv-matrix',
            'rows': [
                {'badge': '准', 'tone': 'pass', 'title': '规则名', 'desc': '规则详细说明'}
            ]
        }
    }
}


def sanitize_deck_id(raw_id, fallback_title=None):
    base = str(raw_id or fallback_title or '').strip()
    cleaned = re.sub(r'[\\/:*?"<>|\r\n\t]+', '_', base).strip(' ._')
    if not cleaned:
        return f"ai_deck_{int(time.time())}"
    return cleaned[:64]


def get_ai_tools_specification():
    """返回外部 AI / Agent 自发现所需的规范、可用模板、版式清单与 OpenAI Tools Schema。"""
    tpls = [
        {
            'id': t['id'],
            'name': t['name'],
            'description': t.get('description', ''),
            'source': t.get('source', 'builtin'),
            'isDefault': bool(t.get('isDefault', False)),
            'primaryColor': t.get('palette', {}).get('primary')
        }
        for t in list_templates()
    ]

    openai_tools = [
        {
            'type': 'function',
            'function': {
                'name': 'list_ppt_templates',
                'description': '获取当前 Pretty PPT 可用的演示文稿视觉模板列表与 15 类标准元件规范。',
                'parameters': {'type': 'object', 'properties': {}, 'required': []}
            }
        },
        {
            'type': 'function',
            'function': {
                'name': 'generate_ppt_deck',
                'description': '根据高层结构化大纲 JSON 一键自动排版、编译 15 类元件并导出标准 .pptx 文件（外部 AI 无需手动计算 x/y/w/h 像素坐标）。',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'deckId': {'type': 'string', 'description': '可选输出文件标识，留空则由标题自动生成'},
                        'title': {'type': 'string', 'description': 'PPT 文档总标题'},
                        'templateId': {'type': 'string', 'description': '模板 ID，默认 academic（学术深蓝）；可选 tech_blue、emerald_research 或本地模板'},
                        'slides': {
                            'type': 'array',
                            'description': '逐页定义列表',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'layout': {'type': 'string', 'enum': list(LAYOUT_DESCRIPTIONS.keys())},
                                    'sectionTag': {'type': 'string', 'description': '页眉章节胶囊标签'},
                                    'title': {'type': 'string', 'description': '本页主标题'},
                                    'subtitle': {'type': 'string', 'description': '本页副标题或核心结论'},
                                    'footer': {'type': 'string', 'description': '可选底部结论横幅文本（如 "结论：..."）'},
                                    'components': {
                                        'type': 'array',
                                        'description': '主体元件数组（每个元素含 type 与 content）',
                                        'items': {
                                            'type': 'object',
                                            'properties': {
                                                'type': {'type': 'string', 'enum': [c['type'] for c in COMPONENT_TYPES]},
                                                'name': {'type': 'string'},
                                                'content': {'type': 'object'},
                                                'layout': {'type': 'object'},
                                                'style': {'type': 'object'}
                                            },
                                            'required': ['type', 'content']
                                        }
                                    }
                                },
                                'required': ['title']
                            }
                        }
                    },
                    'required': ['title', 'slides']
                }
            }
        },
        {
            'type': 'function',
            'function': {
                'name': 'apply_ppt_template',
                'description': '将已生成的 Deck 一键切换至另一视觉模板并重新编译导出 PPTX。',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'deckId': {'type': 'string', 'description': '工程 ID'},
                        'templateId': {'type': 'string', 'description': '目标模板 ID'}
                    },
                    'required': ['deckId', 'templateId']
                }
            }
        }
    ]

    return {
        'service': 'Pretty PPT AI-API',
        'version': '1.0.0',
        'defaultTemplateId': DEFAULT_TEMPLATE_ID,
        'endpoints': {
            'listTools': 'GET /api/ai/tools',
            'generateDeck': 'POST /api/ai/generate',
            'renderComponent': 'POST /api/ai/render-component',
            'applyTemplate': 'POST /api/ai/apply-template',
            'listTemplates': 'GET /api/templates'
        },
        'templates': tpls,
        'layouts': LAYOUT_DESCRIPTIONS,
        'componentSchemas': AI_COMPONENT_SCHEMAS,
        'openaiTools': openai_tools,
        'exampleGeneratePayload': {
            'title': '人工智能代理系统架构汇报',
            'templateId': DEFAULT_TEMPLATE_ID,
            'slides': [
                {
                    'layout': 'cover',
                    'tag': 'TECHNICAL REPORT',
                    'title': '自动化工具调用与声明式 PPT 生成系统',
                    'subtitle': '基于 15 类标准元件规范的 AI 原生排版工作流',
                    'meta': ['汇报人：Research Team', '时间：2026 年 11 月']
                },
                {
                    'layout': 'toc',
                    'sectionTag': 'CONTENTS',
                    'title': '汇报提纲',
                    'subtitle': '围绕核心架构、元件规范与评测结果展开',
                    'items': [
                        '01 | 设计动机 | 为何需要元件级中间表示',
                        '02 | 系统架构 | 四层构建栈与声明式布局编译',
                        '03 | 实证评测 | 往返一致性与模板迁移实验'
                    ]
                },
                {
                    'layout': 'top-1-bottom-2',
                    'sectionTag': '02 系统架构',
                    'title': '核心编译流水线与分歧管控机制',
                    'subtitle': 'LLM 仅输出语义内容，几何坐标系交由确定性编译器计算',
                    'footer': '结论：通过将内容生成与版式计算解耦，大幅降低大模型排版错位率。',
                    'components': [
                        {
                            'type': 'process-flow',
                            'content': {
                                'items': ['1. 语义生成 | 输出高层 JSON', '2. 栅格分配 | 确定性坐标求解', '3. 元件编译 | 生成矢量原语', '4. 导出交付 | 编译标准 PPTX']
                            }
                        },
                        {
                            'type': 'info-card',
                            'content': {
                                'title': '结构化语义输入优势',
                                'items': ['免坐标手算：AI 专注叙事逻辑与指标', '样式严格一致：自动对齐页边距与字号']
                            }
                        },
                        {
                            'type': 'info-card',
                            'content': {
                                'title': '可控二次微调能力',
                                'tone': 'burgundy',
                                'items': ['画布微调：生成后支持拖拽改距', '无损往返：导出后仍可二次解析修改']
                            }
                        }
                    ]
                }
            ]
        }
    }


def _compute_slots(layout_mode, comp_specs, bx, by, bw, bh):
    """根据版式模式为 body_specs 列表分配不重叠的安全矩形槽位 [(x, y, w, h), ...]。"""
    n = len(comp_specs)
    if n == 0:
        return []

    gap_x = 18.0
    gap_y = 14.0
    mode = (layout_mode or 'auto').lower().strip()

    if mode == 'auto':
        first_type = comp_specs[0].get('type', 'info-card') if n > 0 else ''
        if n == 1:
            mode = 'single'
        elif n == 2 and first_type in ('process-flow', 'stage-funnel', 'tag-badge'):
            mode = 'top-bottom'
        elif n == 2:
            mode = '2-col'
        elif n == 3 and first_type in ('process-flow', 'stage-funnel', 'tag-badge'):
            mode = 'top-1-bottom-2'
        elif n == 3:
            mode = '3-col'
        elif n == 4 and first_type in ('process-flow', 'stage-funnel'):
            mode = 'top-1-bottom-3'
        elif n == 4:
            mode = 'grid-2x2'
        else:
            mode = 'grid-2x2'

    if mode == 'free':
        slots = []
        for idx_c, cs in enumerate(comp_specs):
            slots.append((
                float(cs.get('x', bx + (idx_c % 2) * 300)),
                float(cs.get('y', by)),
                float(cs.get('w', 420.0)),
                float(cs.get('h', 240.0))
            ))
        return slots

    if mode == 'single':
        return [(bx, by, bw, bh)] + [(bx, by, bw, bh) for _ in range(n - 1)]

    if mode in ('2-col', 'left-wide', 'right-wide'):
        ratio = 0.5 if mode == '2-col' else (0.62 if mode == 'left-wide' else 0.38)
        w1 = round((bw - gap_x) * ratio, 2)
        w2 = round(bw - gap_x - w1, 2)
        res = [(bx, by, w1, bh), (round(bx + w1 + gap_x, 2), by, w2, bh)]
        while len(res) < n:
            res.append(res[-1])
        return res[:n]

    if mode == '3-col':
        cw = round((bw - gap_x * 2) / 3.0, 2)
        res = [(round(bx + i * (cw + gap_x), 2), by, cw, bh) for i in range(n)]
        return res

    if mode == 'top-bottom':
        first_t = comp_specs[0].get('type', '')
        top_h = 104.0 if first_t == 'process-flow' else (36.0 if first_t == 'tag-badge' else (210.0 if first_t == 'stage-funnel' else round((bh - gap_y) * 0.45, 2)))
        top_h = min(top_h, round(bh * 0.65, 2))
        bot_h = round(max(80.0, bh - top_h - gap_y), 2)
        res = [(bx, by, bw, top_h), (bx, round(by + top_h + gap_y, 2), bw, bot_h)]
        while len(res) < n:
            res.append(res[-1])
        return res[:n]

    if mode in ('top-1-bottom-2', 'top-1-bottom-3'):
        cols = 2 if mode == 'top-1-bottom-2' else 3
        first_t = comp_specs[0].get('type', '')
        top_h = 104.0 if first_t == 'process-flow' else (34.0 if first_t == 'tag-badge' else round((bh - gap_y) * 0.36, 2))
        bot_y = round(by + top_h + gap_y, 2)
        bot_h = round(max(100.0, bh - top_h - gap_y), 2)
        col_w = round((bw - gap_x * (cols - 1)) / cols, 2)
        res = [(bx, by, bw, top_h)]
        for i in range(n - 1):
            col_i = i % cols
            res.append((round(bx + col_i * (col_w + gap_x), 2), bot_y, col_w, bot_h))
        return res

    # grid-2x2 或多行自动网格
    cols = 2 if n <= 4 else 3
    rows_n = max(1, (n + cols - 1) // cols)
    cell_w = round((bw - gap_x * (cols - 1)) / cols, 2)
    cell_h = round((bh - gap_y * (rows_n - 1)) / rows_n, 2)
    res = []
    for i in range(n):
        r_i = i // cols
        c_i = i % cols
        # 若最后一行只剩 1 个元素且不满行，使其横跨整行
        if r_i == rows_n - 1 and (n % cols == 1) and n > 2:
            res.append((bx, round(by + r_i * (cell_h + gap_y), 2), bw, cell_h))
        else:
            res.append((round(bx + c_i * (cell_w + gap_x), 2), round(by + r_i * (cell_h + gap_y), 2), cell_w, cell_h))
    return res


def render_single_component_from_spec(comp_spec, template_id=None, default_box=None):
    """编译单个外部 AI/Agent 传入的元件规范字典为完整 Component JSON。"""
    tpl = get_template(template_id or DEFAULT_TEMPLATE_ID)
    ctype = comp_spec.get('type', 'info-card')
    cid = comp_spec.get('id') or f"ai_{uuid.uuid4().hex[:8]}"
    comp = create_default_component(ctype, comp_id=cid, template_id=tpl['id'])

    if default_box:
        bx, by, bw, bh = default_box
        comp['x'], comp['y'], comp['w'], comp['h'] = bx, by, bw, bh
    for k in ('x', 'y', 'w', 'h'):
        if comp_spec.get(k) is not None:
            comp[k] = float(comp_spec[k])

    if comp_spec.get('name'):
        comp['name'] = str(comp_spec['name'])
    if comp_spec.get('subType'):
        comp['subType'] = str(comp_spec['subType'])

    if isinstance(comp_spec.get('layout'), dict):
        comp['layout'] = {**comp.get('layout', {}), **comp_spec['layout']}
    if isinstance(comp_spec.get('style'), dict):
        comp['style'] = {**comp.get('style', {}), **comp_spec['style']}
    if isinstance(comp_spec.get('content'), dict):
        comp['content'] = copy.deepcopy(comp_spec['content'])

    return compile_component(comp, tpl)


def build_deck_from_ai_spec(spec):
    """将高层语义 AI-API JSON 请求编译为完整可渲染与可导出的 Deck JSON。"""
    tpl_id = spec.get('templateId') or DEFAULT_TEMPLATE_ID
    tpl = get_template(tpl_id)
    pal = tpl['palette']
    bgs = tpl['backgrounds']
    skel = tpl['skeleton']

    title = str(spec.get('title') or 'AI 生成演示文稿').strip()
    deck_id = sanitize_deck_id(spec.get('deckId'), fallback_title=title)
    slides_spec = spec.get('slides') or []
    if not slides_spec:
        raise ValueError('slides 数组不能为空，至少需要 1 页幻灯片定义')

    canvas_w = float(tpl['canvas'].get('width', 1020.67))
    canvas_h = float(tpl['canvas'].get('height', 680.33))
    margin_x = float(skel.get('defaultMarginX', 48.0))
    safe_w = round(canvas_w - margin_x * 2, 2)
    content_top = float(skel.get('contentTopY', 134.0))
    footer_y = float(skel.get('footerY', 596.0))

    deck = {
        'id': deck_id,
        'title': title,
        'templateId': tpl['id'],
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

    total_slides = len(slides_spec)
    for s_idx, s_spec in enumerate(slides_spec, start=1):
        layout_mode = str(s_spec.get('layout') or 'auto').lower().strip()
        raw_comps = copy.deepcopy(s_spec.get('components') or [])
        s_title = str(s_spec.get('title') or f'第 {s_idx} 页')
        s_subtitle = str(s_spec.get('subtitle') or '')
        s_sec = str(s_spec.get('sectionTag') or s_spec.get('tag') or '').strip()

        slide_comps = []

        # 1. 封面 / 章节大横幅页
        is_explicit_cover = (layout_mode == 'cover') or any(c.get('type') == 'cover-divider' for c in raw_comps)
        if is_explicit_cover:
            cov_spec = next((c for c in raw_comps if c.get('type') == 'cover-divider'), None)
            if not cov_spec:
                cov_spec = {
                    'type': 'cover-divider',
                    'content': {
                        'tag': s_spec.get('tag') or s_sec or 'PRESENTATION',
                        'title': s_title,
                        'subtitle': s_subtitle,
                        'meta': s_spec.get('meta') or s_spec.get('items') or []
                    }
                }
            cov_comp = render_single_component_from_spec(cov_spec, template_id=tpl['id'])
            cov_comp['id'] = f"{deck_id}_s{s_idx}_c1"
            compile_component(cov_comp, tpl)
            slide_comps.append(cov_comp)
            bg_obj = copy.deepcopy(bgs['cover'])
        else:
            bg_obj = copy.deepcopy(bgs['body'])
            # 2. 顶部页眉处理
            hdr_spec = next((c for c in raw_comps if c.get('type') == 'slide-header'), None)
            if not hdr_spec:
                hdr_spec = {
                    'type': 'slide-header',
                    'content': {
                        'sectionTag': s_sec,
                        'title': s_title,
                        'subtitle': s_subtitle,
                        'pageNumber': f"{s_idx} / {total_slides}"
                    }
                }
            hdr_comp = render_single_component_from_spec(hdr_spec, template_id=tpl['id'])
            hdr_comp['id'] = f"{deck_id}_s{s_idx}_hdr"
            compile_component(hdr_comp, tpl)
            slide_comps.append(hdr_comp)

            # 3. 底部横幅处理
            ftr_comp = None
            ftr_spec = next((c for c in raw_comps if c.get('type') == 'footer-banner'), None)
            raw_footer = s_spec.get('footer')
            if ftr_spec:
                ftr_comp = render_single_component_from_spec(ftr_spec, template_id=tpl['id'], default_box=(margin_x, footer_y, safe_w, 44.0))
            elif raw_footer:
                if isinstance(raw_footer, dict):
                    f_pref = raw_footer.get('prefix') or '核心结论：'
                    f_sub = raw_footer.get('subtitle') or raw_footer.get('text') or ''
                else:
                    txt_f = str(raw_footer)
                    if '：' in txt_f:
                        p0, p1 = txt_f.split('：', 1)
                        f_pref, f_sub = p0 + '：', p1
                    else:
                        f_pref, f_sub = '总结与启示：', txt_f
                ftr_comp = render_single_component_from_spec({
                    'type': 'footer-banner',
                    'content': {'prefix': f_pref, 'subtitle': f_sub}
                }, template_id=tpl['id'], default_box=(margin_x, footer_y, safe_w, 44.0))

            # 4. 目录或中间内容区主体元件
            body_specs = [c for c in raw_comps if c.get('type') not in ('slide-header', 'footer-banner', 'cover-divider')]
            if layout_mode == 'toc' and not body_specs:
                toc_items = s_spec.get('items') or []
                body_specs = [{'type': 'toc-list', 'content': {'title': s_title, 'items': toc_items}}]
                layout_mode = 'single'

            content_bottom = (footer_y - 12.0) if ftr_comp else (canvas_h - 38.0)
            content_h = round(max(120.0, content_bottom - content_top), 2)
            slots = _compute_slots(layout_mode, body_specs, margin_x, content_top, safe_w, content_h)

            for c_i, (b_spec, slot) in enumerate(zip(body_specs, slots), start=1):
                # 双栏/三栏同质 info-card 自动交替主辅色以增强对比层次（除非用户显式指定 tone/style）
                b_copy = copy.deepcopy(b_spec)
                b_content = b_copy.setdefault('content', {})
                if b_copy.get('type') == 'info-card' and not b_content.get('tone') and not b_copy.get('style'):
                    if len(body_specs) >= 2 and c_i == len(body_specs):
                        b_content['tone'] = 'burgundy' if tpl['id'] == 'academic' else None
                comp = render_single_component_from_spec(b_copy, template_id=tpl['id'], default_box=slot)
                comp['id'] = f"{deck_id}_s{s_idx}_c{c_i}"
                compile_component(comp, tpl)
                slide_comps.append(comp)

            if ftr_comp:
                ftr_comp['id'] = f"{deck_id}_s{s_idx}_ftr"
                compile_component(ftr_comp, tpl)
                slide_comps.append(ftr_comp)

        deck['slides'].append({
            'id': f"{deck_id}_slide_{s_idx}",
            'index': s_idx,
            'title': s_title,
            'background': bg_obj,
            'components': slide_comps
        })

    stats = {}
    for s in deck['slides']:
        for c in s['components']:
            t = c.get('type', 'info-card')
            stats[t] = stats.get(t, 0) + 1
    deck['componentStats'] = stats
    return deck
