---
name: pptx-to-pretty-template
description: >
  将任意外部参考 .pptx 演示文稿解包、提取配色/背景/静态图标素材，并重构为 Pretty PPT
  自包含标准模板包（template.json + assets/）的工作流与视觉设计规范。包含通用提取 CLI
  工具、功能有色卡片（Semantic Cards）同源配色原则及 17 类元件皮肤验收清单。
---

# 从参考 PPTX 构建 Pretty PPT 自包含模板包

本技能指导 Agent 与开发者如何将外部精美 PPT（如商业模板、游戏终端 UI 风格或机构研报母版）高效沉淀为 **Pretty PPT** 可复用的自包含模板包，确保“模板元数据 + 静态资源 + 功能语义色 + 17 类元件皮肤”高度内聚且严格遵守商用授权边界。

---

## 一、自包含模板包目录与分级合规规范

每个模板以独立文件夹存放，`template.json` 内所有本地资源均使用相对路径 `"assets/..."`（严禁写死 `/templates/builtin/...` 等跨目录绝对路径），方便整包复制、分享与迁移：

```text
templates/
├── builtin/                        # 公开可商用内置模板（随公开代码库发布）
│   └── <template_id>/
│       ├── template.json
│       └── assets/                   # 仅限 100% 原创矢量/代码生成安全素材
├── local/                          # 本地私有 & 不可商用模板（已加入 .gitignore，永不上传）
│   └── <template_id>/
│       ├── template.json             # 标注 "commercial": false
│       └── assets/                   # 提取自外部母版/企业的图片与图标
└── example/                        # 本转换工具、示例标准包与 Skill 文档
    ├── SKILL.md
    ├── convert_pptx_to_template.py
    └── minimal_slate/                # 可运行的 16:9 最小自包含模板范本
        ├── template.json
        └── assets/corner_grid.png
```

> [!CAUTION]
> **商用分级红线**：凡提取自第三方公开演示文稿、影视游戏素材或公司内部母版的模板，**必须归档到 `templates/local/<id>/`** 并保持 `"commercial": false`，绝不可放入 `templates/builtin/`。

---

## 二、标准转化工作流（4 步闭环）

### 第 1 步：运行通用转换脚本提取骨架与素材

在项目根目录运行 `templates/example/convert_pptx_to_template.py`：

```bash
python templates/example/convert_pptx_to_template.py \
  --pptx "path/to/reference.pptx" \
  --id my_theme_id \
  --name "自定义主题展示名" \
  --tier local
```

脚本将自动完成：
1. 读取 `presentation.xml` 获取精准画布尺寸（如 16:9 `1280×720` 或 3:2）并推断页边距 (`defaultMarginX`)、正文区起止纵坐标 (`contentTopY`, `footerY`)；
2. **全通道色彩识别**：同时统计 `theme1.xml`、`solidFill`、`<a:gradFill>` 全部色标色值及 `<a:schemeClr>` 主题色映射，识别纯渐变主导主题的高频主/辅渐变色对 (`topGradientPairs`) 并生成同源五态 `palette.semantic`；
3. **伪背景检测、资产瘦身与跨页透明装饰识别**：若页面 `<p:bg>` 为空且底层存在覆盖 `>=92%` 画布的 `<p:pic>` / `<p:sp>` 全幅图层，自动提取为 `backgrounds.cover` / `body`，对超 1920px 大图执行 LANCZOS 压测瘦身；并识别跨页高频透明底纹 (`recurring-decor`) 生成推荐 `decorations`；
4. **商业字体安全回退**：检测 `.fntdata` 内嵌字库及第三方商业艺术字体（如字魂/汉仪/方正等），在 `analysis_report.json` 记录告警并将 `palette.fontFamily` 回退至跨平台安全通用字体 `'微软雅黑'`；
5. 输出 `<id>/template.json` 与 `<id>/analysis_report.json`。

### 第 2 步：人工 / Agent 审查与静态资产提纯

打开生成的 `analysis_report.json` 与 `assets/` 目录进行三项清洗：
1. **删除干扰图片**：移除单页人物立绘、水印、乐谱/特定剧情插图或带有版权 Logo 的 `media_*` 文件（本引擎不关注 PPT 原动画帧）；
2. **图标归一化**：筛选出 3~4 枚通用小图标（如实验瓶、齿轮、看板、折线图），使用 Pillow 重着色为与 `palette.primary` 及 `palette.accent` 匹配的双色 PNG（如深炭黑与高亮强调色）；
3. **声明 `decorations` 层**：在 `template.json` 的 `"decorations": {"cover": [...], "body": [...]}` 中配置底层锁定装饰（注意正文页背景装饰图 `opacity` 建议控制在 `0.12 ~ 0.22`，避免遮挡文字）。

### 第 3 步：功能有色卡片（Semantic Cards）同源设计规范

**禁止直接套用刺眼的外来高饱和纯绿 `#16A34A` / 纯红 `#DC2626` / 亮橙 `#F26B21`！** 每一类有色卡片都应根据其**业务功能职责**在 `palette.semantic` 中采用“同源材质底色 + 克制信号条”表达：

| 语义角色 | 典型功能承担（如 P10 / P16 / P18 / P20 / P22） | 视觉构建原则 |
| :--- | :--- | :--- |
| **`pass`** | 达标终态、锚点晋升 (`PROMOTED`/`FINAL`)、`准` 准入条 | 在亮黄/深黑主题下用主题高亮色作小面积徽章或左能量条；卡片主体保持柔和象牙/浅灰绿材质底，标题用低明度深橄榄/深翠，绝不大面积铺翠绿背景 |
| **`warn`** | 关键瓶颈层、警戒阈值 (`WARN`)、`警` 提醒条 | 采用同色温的**黄铜琥珀/赭石金**作为小徽章或顶部 3.5px 细眉，底色微调为暖砂/浅米黄 |
| **`reject`** | 禁令 (`禁`)、强制回退条件 (`REJECT`)、已证伪红线 | 采用沉稳**暗绯/酒红/锈铁红**作左信号柱、六边形小徽章或虚线边框，卡片底用极低饱和暖岩/灰粉底（明度 > 93%），严禁整块大红/艳粉糊底 |
| **`info`** | 普通分类子卡、标准步骤、常规分组信息 | 严格跟随模板 `primary` + `cardBg`（如深黑头+白卡），即使同一页多卡并列也不要各自涂成红蓝绿紫 |
| **`neutral`** | 冷启动基线 (`R0`)、不可控客观边界 (`L5`) | 中性炭灰/石板灰头配低饱和浅灰底 |

### 第 4 步：接入定制皮肤与双端目视验收

1. 若该模板需深度定制复杂元件几何（如六边形门禁 `hexagon`、倾斜纹带 `parallelogram`、双环科技图标 `milestone-timeline`），可在 `skeleton.skin` 命名专属皮肤并在 `core/schema.py` 的 `compile_component` 中按 `palette.semantic` 与 `_get_asset_base(tpl)` 编写渲染分支；若只需通用卡片+渐变背景+底层装饰，`template.json` 已开箱即用。
2. 运行预览渲染脚本验证效果：

```bash
python -c "
import json
from core.templates import apply_template_to_deck
from core.preview import render_deck_previews
deck = json.load(open('decks/component_showcase.json', encoding='utf-8'))
rendered = apply_template_to_deck(deck, template_id='my_theme_id')
render_deck_previews(rendered, [1, 2, 3, 4, 5, 6], 'output/preview_my_theme', scale=1.2)
"
```

用图像查看工具逐页检查文字对比度、渐变遮罩透明度、箭头连通性与页底留白，必要时调优 `template.json` 中的 `palette.semantic` 与 `skeleton` 安全边界，直至零重叠、零撞色、导出 `.pptx` 在 PowerPoint 中 100% 正常打开。
