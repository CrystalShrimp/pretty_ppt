# Pretty PPT（PPT Component Studio）

**Pretty PPT** 是一款面向人类微调与外部 AI Agent 自动生稿双场景的**元件化演示文稿设计引擎**。底层以标准化的 **15 类可复用组件 + 结构化 Deck JSON** 为核心数据表示，上层提供类 Photoshop 三栏自由拖拽可视化画布、**多风格模板库**、**AI-API 一键生稿接口**以及标准 `.pptx` 双向无损往返编译器。

---

## 核心特性

1. **学术深蓝默认模板（零外部敏感依赖）**
   - 内置默认模板为纯矢量学术深蓝（`#1B365D`）+ 学术酒红（`#7A2048`）风格：包含双段顶栏色带页眉、圆角章节胶囊、带顶部强调条的信息卡片与规范表格。
   - 内置三套公开风格模板（`templates/builtin/`）：`academic`（默认）、`tech_blue`（深海科技蓝）、`emerald_research`（森系智库绿）。
   - 支持本地私有模板目录 `templates/local/`（已加入 `.gitignore`，可安全存放公司或个人私有母版且不会随代码提交到 GitHub）。

2. **15 类标准元件体系与声明式布局编译**
   - **基础展示与信息骨架**：`cover-divider`、`slide-header`、`toc-list`、`tag-badge`、`info-card`、`footer-banner`
   - **数据与图文展示**：`kpi-card`、`data-table`、`image-frame`
   - **复合逻辑架构图（免坐标手算）**：`process-flow`、`vertical-stack`、`decision-gate`、`stage-funnel`、`iteration-lanes`、`rule-checklist`
   - 支持同类元素样式联动（仅当前元件 / 本页同类 / 全篇同类），并带 **PASS / WARN / REJECT 语义状态色护栏**，换肤不破坏逻辑状态色。

3. **外部 AI 工具一键调用接口 (`ai-api`)**
   - 外部 AI / Agent 只需调用 `GET /api/ai/tools` 获取 15 类元件 Schema 与 OpenAI Function Calling 工具规范，再通过 `POST /api/ai/generate` 提交高层语义大纲 JSON，即可由后端智能栅格排版引擎自动分配坐标、套用模板并直接产出 `.pptx`。

4. **PPTX 双向无损往返 & 本地目录批量编辑**
   - 所有导出的形状都会写入轻量 `[PCS:comp_id|comp_type|role]` 标识，重新解析时 100% 还原元件归属，不打散复合图表。
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

项目提供独立渲染脚本 `scripts/render_showcase.py`，可随时按默认 `academic` 或其他指定模板重新渲染覆盖 5 页 15 类标准元件的示范文稿：

```bash
# 使用默认学术模板 (academic) 重渲染并做往返解析验证
python scripts/render_showcase.py

# 使用指定模板（如 tech_blue / emerald_research / 本地私有模板 ID）重渲染到自定义路径
python scripts/render_showcase.py --template tech_blue --out output/showcase_tech_blue.pptx
```

---

## API 接口说明

### 多风格模板库接口

| 方法与路径 | 功能说明 |
| :--- | :--- |
| `GET /api/templates` | 获取全部可用模板列表（包含 `builtin` 公开模板与 `local` 本地私有模板） |
| `GET /api/templates/{template_id}` | 获取单个模板的调色板、背景与骨架配置 |
| `POST /api/templates` | 保存自定义模板到 `templates/local/`（支持传完整配置，或传 `{"fromDeckId": "...", "id": "...", "name": "..."}` 从现有工程一键提取） |
| `DELETE /api/templates/{template_id}` | 删除 `templates/local/` 下的本地自定义模板 |
| `POST /api/decks/{deck_id}/apply-template` | 对指定工程应用新模板（支持 `scope: "deck"` 或 `"slide"`） |

### 外部 AI 一键生成接口 (`ai-api`)

| 方法与路径 | 功能说明 |
| :--- | :--- |
| `GET /api/ai/tools` | 获取面向外部 Agent 的自发现规范：模板列表、布局模式、15 类元件 Schema 与 OpenAI `tools` 定义 |
| `POST /api/ai/generate` | **核心一键生稿接口**：传入高层语义 JSON，自动排版、应用模板并导出 `.pptx` |
| `POST /api/ai/render-component` | 编译单个声明式/标准元件 JSON 并返回完整子节点坐标 |
| `POST /api/ai/apply-template` | 对已生成的 `deckId` 切换模板并重新输出 `.pptx` |

#### `POST /api/ai/generate` 请求示例

```bash
curl -X POST http://127.0.0.1:8765/api/ai/generate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "多模态智能体系统研究汇报",
    "templateId": "academic",
    "slides": [
      {
        "layout": "cover",
        "tag": "RESEARCH PRESENTATION",
        "title": "面向复杂工具编排的智能体系统研究",
        "subtitle": "结构化中间表示与确定性视觉编译器",
        "meta": ["汇报团队：AI Systems Lab", "时间：2026 年 11 月"]
      },
      {
        "layout": "toc",
        "sectionTag": "CONTENTS",
        "title": "汇报提纲",
        "items": [
          "01 | 研究背景 | 自由生成排版的对齐与幻觉痛点",
          "02 | 系统设计 | 元件规范 + 自动栅格排版引擎",
          "03 | 消融评估 | 版式一致性与多模板迁移验证"
        ]
      },
      {
        "layout": "top-1-bottom-2",
        "sectionTag": "02 系统设计",
        "title": "三层分离架构与元件化编译流水线",
        "subtitle": "LLM 仅负责内容叙事，几何坐标与样式由确定性引擎统一计算",
        "footer": "核心结论：通过将内容语义与渲染坐标分离，跨页对齐误差降低至零。",
        "components": [
          {
            "type": "process-flow",
            "content": {
              "items": [
                "1. 意图拆解 | 组织结构化大纲",
                "2. 版式推理 | 选择自动栅格模式",
                "3. 元件编译 | 生成标准矢量原语",
                "4. 编译交付 | 导出 .pptx"
              ]
            }
          },
          {
            "type": "info-card",
            "content": {
              "title": "语义输入层规范",
              "items": [
                "免坐标声明：无需输出繁琐像素值",
                "类型约束：覆盖 15 类高频汇报元件"
              ]
            }
          },
          {
            "type": "rule-checklist",
            "content": {
              "title": "质量门禁检查",
              "mode": "checklist",
              "rows": [
                {"badge": "准", "tone": "pass", "title": "页眉对齐", "desc": "双段顶栏与页码自动锁定安全边界"},
                {"badge": "禁", "tone": "reject", "title": "文本溢出", "desc": "自适应分段行高与底部呼吸留白"}
              ]
            }
          }
        ]
      }
    ]
  }'
```

---

## 目录结构

```text
pretty_ppt/
├── assets/showcase/          # 公开示范集图表资源
├── core/
│   ├── ai_builder.py         # 面向外部 AI 的版式分配与一键生稿编译器
│   ├── converter.py          # PPTX -> Deck JSON 双向往返解析器
│   ├── exporter.py           # Deck JSON -> 标准 .pptx 导出器
│   ├── schema.py             # 15 类标准元件声明式编译器与默认模板
│   └── templates.py          # 多风格模板库引擎（内置 + 本地私有）
├── decks/
│   └── component_showcase.json
├── scripts/
│   └── render_showcase.py    # 独立示范集重渲染与往返校验脚本
├── static/                   # Web 前端编辑器 (HTML/CSS/JS)
├── templates/
│   └── builtin/              # 公开内置模板 (academic, tech_blue, emerald_research)
├── component_showcase.pptx   # 默认学术风 15 类元件全景示范集
├── requirements.txt
├── server.py                 # FastAPI 后端服务
├── start.bat / start.ps1
└── .gitignore
```
