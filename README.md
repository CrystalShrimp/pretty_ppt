# Pretty PPT（PPT Component Studio）

**Pretty PPT** 是一款面向人类微调与外部 AI Agent 自动生稿双场景的**元件化演示文稿设计引擎**。底层以标准化的 **17 类可复用组件 + 结构化 Deck JSON** 为核心数据表示，支持**元件级皮肤/骨架重渲染**、线性渐变光晕、透明度叠加与多边形几何原语，上层提供类 Photoshop 三栏自由拖拽可视化画布、**多风格模板库**、**AI-API 一键生稿接口**以及标准 `.pptx` 双向无损往返编译器。

---

## 核心特性

1. **学术深蓝默认模板（零外部敏感依赖）与多风格皮肤库**
   - 内置默认模板为纯矢量学术深蓝（`#1B365D`）+ 学术酒红（`#7A2048`）风格：包含双段顶栏色带页眉、圆角章节胶囊、带顶部强调条的信息卡片与规范表格。
   - 内置四套公开风格模板（`templates/builtin/`）：
     - `academic`（默认 · 3:2 学术深蓝）
     - `terra_quest`（16:9 宽屏 · 灵感源自机能工业终端美学：暖米白纸感渐变基底 `#FBF7EF -> #E3DED3`、曜石黑铭牌头 `#18181B`、荧光青柠 `#D0E516` 能量条与线性渐变光晕、双环科技图标、六边形蜂巢装饰与等高线 HUD 底层装饰）
     - `tech_blue`（深海科技蓝）
     - `emerald_research`（森系智库绿）
   - 支持本地私有模板目录 `templates/local/`（已加入 `.gitignore`，可安全存放公司或个人私有母版且不会随代码提交到 GitHub）。

2. **17 类标准元件体系与模板级真实重渲染**
   - **基础展示与信息骨架 (7 类)**：`cover-divider`、`section-divider`（新增穿透色带与序号水印章节页）、`slide-header`、`toc-list`、`tag-badge`、`info-card`、`footer-banner`
   - **数据与图文展示 (4 类)**：`kpi-card`、`data-table`、`image-frame`、`milestone-timeline`（新增双环科技图标里程碑时间轴）
   - **复合逻辑架构图（6 类，免坐标手算）**：`process-flow`、`vertical-stack`、`decision-gate`、`stage-funnel`、`iteration-lanes`、`rule-checklist`
   - **真正的元件级重渲染（Content Hydration + Skin Recompilation）**：对任何 PPTX 解析出的历史元件执行模板切换时，先无损水合结构化内容，再由目标模板的编译器重绘皮肤形状、渐变光晕、图标徽章并按新画布比例（如 3:2 -> 16:9）重算安全区坐标，同时严格保留 **PASS / WARN / REJECT 语义状态色护栏**。

3. **外部 AI 工具一键调用接口 (`ai-api`)**
   - 外部 AI / Agent 只需调用 `GET /api/ai/tools` 获取 17 类元件 Schema 与 OpenAI Function Calling 工具规范，再通过 `POST /api/ai/generate` 提交高层语义大纲 JSON，即可由后端智能栅格排版引擎自动分配坐标、套用模板并直接产出 `.pptx`。

4. **PPTX 双向无损往返 & 本地目录批量编辑**
   - 所有导出的形状都会写入轻量 `[PCS:comp_id|comp_type|role]` 标识（页面背景锁死装饰写入 `[PCS:decor|decor|decor]`），支持圆角、多边形、线性渐变 (`gradFill`)、软外阴影 (`outerShdw`)、Alpha 透明度与字间距的双向无损解析与导出。
   - 支持在顶部工作栏指定任意本地文件夹路径，扫描编辑任意 `.pptx` 并保存写回或另存副本。

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动可视化编辑器

- **Windows CMD**：双击或运行 `start.bat`
- **Windows PowerShell**：运行 `./start.ps1`
- **通用终端**：

```bash
python server.py
```

启动后在浏览器访问：`http://127.0.0.1:8765`

### 3. 一键重渲染全景示范集 `component_showcase.pptx`

项目提供独立渲染脚本 `scripts/render_showcase.py`，可随时按默认 `academic` 或其他指定模板重新渲染覆盖 6 页 17 类标准元件的示范文稿：

```bash
# 使用默认学术模板 (academic) 重渲染并做往返解析验证
python scripts/render_showcase.py

# 使用 16:9 机能工业风模板 (terra_quest) 或其他模板重渲染
python scripts/render_showcase.py --template terra_quest --out output/showcase_terra_quest.pptx
```

---

## API 接口说明

### 多风格模板库与元件渲染接口

| 方法与路径 | 功能说明 |
| :--- | :--- |
| `GET /api/templates` | 获取全部可用模板列表（包含 `builtin` 公开模板与 `local` 本地私有模板） |
| `GET /api/templates/{template_id}` | 获取单个模板的画布、调色板、渐变背景与骨架配置 |
| `POST /api/templates` | 保存自定义模板到 `templates/local/`（支持传完整配置，或传 `{"fromDeckId": "...", "id": "...", "name": "..."}` 从现有工程一键提取） |
| `DELETE /api/templates/{template_id}` | 删除 `templates/local/` 下的本地自定义模板 |
| `POST /api/templates/{template_id}/render-component` | **元件级重渲染接口**：接收单个 Component JSON（含 PPTX 解析态元件），执行水合与指定模板皮肤重构 |
| `POST /api/templates/{template_id}/render-deck` | **全篇模板渲染与画布自适应接口**：执行画布缩放、页面装饰生成、全元件皮肤重绘及可选 `.pptx` 导出 |
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
├── assets/showcase/          # 公开示范集图表资源
├── core/
│   ├── ai_builder.py         # 面向外部 AI 的版式分配与一键生稿编译器
│   ├── converter.py          # PPTX -> Deck JSON 双向往返解析器
│   ├── exporter.py           # Deck JSON -> 标准 .pptx 导出器（含渐变/透明/多边形/阴影原语）
│   ├── preview.py            # 纯 Python Pillow 高清幻灯片预览 PNG 渲染器
│   ├── schema.py             # 17 类标准元件声明式编译器与多皮肤渲染逻辑
│   └── templates.py          # 多风格模板库、内容水合与跨画布自适应重渲染引擎
├── decks/
│   └── component_showcase.json
├── scripts/
│   └── render_showcase.py    # 独立示范集重渲染与往返校验脚本
├── static/                   # Web 前端编辑器 (HTML/CSS/JS)
├── templates/
│   └── builtin/              # 公开内置模板及公共静态几何/图标素材 (academic, terra_quest, tech_blue, emerald_research)
├── component_showcase.pptx   # 默认学术风 17 类元件全景示范集
├── requirements.txt
├── server.py                 # FastAPI 后端服务
├── start.bat / start.ps1
└── .gitignore
```
