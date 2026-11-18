# Pretty PPT（PPT Component Studio）

**Pretty PPT** 是一款面向人类微调与外部 AI Agent 自动生稿双场景的**元件化演示文稿设计引擎**。底层以标准化的 **17 类可复用组件 + 结构化 Deck JSON** 为核心数据表示，支持**自包含多层级模板包**、**按职能同源设计的语义色令牌 (`palette.semantic`)**、线性渐变光晕、透明度叠加与多边形几何原语，上层提供类 Photoshop 三栏自由拖拽可视化画布、**AI-API 一键生稿接口**以及标准 `.pptx` 双向无损往返编译器。

---

## 核心特性

1. **自包含模板包架构与商用分级隔离 (`templates/`)**
   - 每个模板以自包含文件夹存放（`template.json` + 相对路径 `assets/`），便于整包拷贝与团队分享：
     - `templates/builtin/<id>/`：**公开可商用内置模板**（纯矢量零敏感外部图片依赖：`academic` 默认学术深蓝、`tech_blue` 深海科技蓝、`emerald_research` 森系智库绿）。
     - `templates/local/<id>/`：**本地私有 / 不可商用模板**（已全量列入 `.gitignore`，绝不上传至 GitHub，可安全存放公司母版及个人研究级参考风格包）。
     - `templates/example/`：**通用 PPT 转模板包套件**（含 CLI 脚本 `convert_pptx_to_template.py`、标准示例包 `minimal_slate/` 与 `SKILL.md` Agent 工作流规范）。

2. **17 类标准元件与「按职能同源设计」的有色卡片系统**
   - **基础展示与信息骨架 (7 类)**：`cover-divider`、`section-divider`（穿透高亮带 + 半透明大号序号水印）、`slide-header`、`toc-list`、`tag-badge`、`info-card`、`footer-banner`
   - **数据与图文展示 (4 类)**：`kpi-card`、`data-table`、`image-frame`、`milestone-timeline`（双环序号/科技图标里程碑时间轴）
   - **复合逻辑架构图（6 类，免坐标手算）**：`process-flow`、`vertical-stack`、`decision-gate`、`stage-funnel`、`iteration-lanes`、`rule-checklist`
   - **同源功能色令牌 (`palette.semantic`)**：告别直接叠加大面积高饱和纯红/纯绿导致的撞色违和；所有功能态卡片（`pass` 达标定稿 / `warn` 瓶颈警戒 / `reject` 红线回退 / `info` 常规单元 / `neutral` 客观基线）均以低饱和材质底色 + 窄信号柱/切角铭牌锚块渲染，天然贴合当前模板皮肤色温。

3. **外部 AI 工具一键调用接口 (`ai-api`)**
   - 外部 AI / Agent 只需调用 `GET /api/ai/tools` 获取 17 类元件 Schema 与 OpenAI Function Calling 工具规范，再通过 `POST /api/ai/generate` 提交高层语义大纲 JSON，即可由后端智能栅格排版引擎自动分配坐标、套用模板并直接产出 `.pptx`。

4. **PPTX 双向无损往返 & 本地目录批量编辑**
   - 所有导出形状自动写入轻量 `[PCS:comp_id|comp_type|role]` 标识（页面背景锁死装饰写入 `[PCS:decor|decor|decor]`），支持圆角、多边形、线性渐变 (`gradFill`)、软外阴影 (`outerShdw`)、Alpha 透明度与字间距的双向无损解析与导出。

---

## 快速开始

### 1. 安装依赖与启动编辑器

```bash
pip install -r requirements.txt
python server.py
```

Windows 下也可直接运行 `start.ps1` 或 `start.bat`，启动后浏览器访问 `http://127.0.0.1:8765`。

### 2. 一键重渲染全景示范集 `component_showcase.pptx`

```bash
# 使用默认学术模板 (academic) 重渲染 6 页全 17 类元件示范集并做往返验证
python scripts/render_showcase.py

# 使用通用示例模板包 (minimal_slate) 或其他模板重渲染
python scripts/render_showcase.py --template minimal_slate --out output/showcase_minimal_slate.pptx
```

### 3. 从任意外部 PPTX 一键提取并生成自包含模板包

```bash
python templates/example/convert_pptx_to_template.py \
  --pptx "path/to/reference.pptx" \
  --id custom_theme \
  --name "自定义参考主题" \
  --tier local
```

工具会自动解析画布尺寸、安全边距、背景渐变/图片、色频统计与媒体分拣，在 `templates/local/custom_theme/` 下生成 `template.json`、`assets/` 及 `analysis_report.json`，具体调优细则与 17 类元件设计规范见 `templates/example/SKILL.md`。

---

## API 接口说明

### 多风格模板库与元件渲染接口

| 方法与路径 | 功能说明 |
| :--- | :--- |
| `GET /api/templates` | 获取全部可用模板包列表（自动发现 `builtin/<id>/` 与 `local/<id>/`） |
| `GET /api/templates/{template_id}` | 获取单个模板包的画布、调色板、功能语义色 (`semantic`) 与资产配置 |
| `POST /api/templates` | 保存自定义模板包到 `templates/local/<id>/`（支持直接传配置或传 `fromDeckId` 提取） |
| `DELETE /api/templates/{template_id}` | 删除 `templates/local/<id>/` 下的本地模板包 |
| `POST /api/templates/{template_id}/render-component` | **元件级重渲染接口**：对单个元件执行内容水合与指定模板皮肤重构 |
| `POST /api/templates/{template_id}/render-deck` | **全篇模板渲染与画布自适应接口**：执行画布缩放、底层装饰生成与全元件皮肤重绘 |
| `POST /api/decks/{deck_id}/apply-template` | 对指定工程应用新模板（支持 `scope: "deck"` / `"slide"`、`rerenderComponents`、`adaptCanvas`） |

### 外部 AI 一键生成接口 (`ai-api`)

| 方法与路径 | 功能说明 |
| :--- | :--- |
| `GET /api/ai/tools` | 获取面向外部 Agent 的自发现规范：模板列表、布局模式（含 `section` 章节页）、17 类元件 Schema 与 OpenAI `tools` 定义 |
| `POST /api/ai/generate` | **核心一键生稿接口**：传入高层语义 JSON，自动排版、应用模板并导出 `.pptx` |
| `POST /api/ai/render-component` | 编译单个声明式/标准元件 JSON 并返回完整子节点坐标 |
| `POST /api/ai/apply-template` | 对已生成的 `deckId` 切换模板、重绘全篇元件并重新输出 `.pptx` |

---

## 目录结构

```text
pretty_ppt/
├── assets/showcase/                  # 公开示范集图表资源
├── core/
│   ├── ai_builder.py                 # 面向外部 AI 的版式分配与一键生稿编译器
│   ├── converter.py                  # PPTX -> Deck JSON 双向往返解析器
│   ├── exporter.py                   # Deck JSON -> 标准 .pptx 导出器
│   ├── preview.py                    # 纯 Python Pillow 高清幻灯片预览渲染器
│   ├── schema.py                     # 17 类标准元件声明式编译器与功能语义皮肤逻辑
│   └── templates.py                  # 自包含模板包加载、相对资产解析、水合与跨画布自适应引擎
├── decks/
│   └── component_showcase.json
├── scripts/
│   └── render_showcase.py            # 独立示范集重渲染与往返校验脚本
├── static/                           # Web 前端编辑器 (HTML/CSS/JS)
├── templates/
│   ├── builtin/                      # 公开可商用内置模板包 (academic, tech_blue, emerald_research)
│   │   ├── academic/template.json
│   │   ├── tech_blue/template.json
│   │   └── emerald_research/template.json
│   ├── local/                        # 本地私有/不可商用模板包 (.gitignore 忽略)
│   └── example/                      # 通用 PPT 转模板包工具与文档
│       ├── SKILL.md
│       ├── convert_pptx_to_template.py
│       └── minimal_slate/            # 标准 16:9 示例模板包 (template.json + assets/)
├── component_showcase.pptx           # 默认学术风 17 类元件全景示范集
├── requirements.txt
├── server.py                         # FastAPI 后端服务
├── start.bat / start.ps1
└── .gitignore
```
