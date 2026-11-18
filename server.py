import os
import json
import shutil
import hashlib
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from core.schema import COMPONENT_TYPES, create_default_component, rebuild_component_layout
from core.templates import (
    DEFAULT_TEMPLATE_ID,
    TEMPLATES_DIR,
    list_templates,
    get_template,
    save_custom_template,
    delete_custom_template,
    extract_template_from_deck,
    apply_template_to_deck,
)
from core.ai_builder import (
    get_ai_tools_specification,
    build_deck_from_ai_spec,
    render_single_component_from_spec,
)
from core.exporter import export_deck_to_pptx
from core.converter import convert_pptx_to_deck

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DECKS_DIR = os.path.join(BASE_DIR, 'decks')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
CONFIG_FILE = os.path.join(DECKS_DIR, '_workspace_config.json')

os.makedirs(DECKS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app = FastAPI(title="Pretty PPT (PPT Component Studio) API", version="2.0.0")

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/templates", StaticFiles(directory=TEMPLATES_DIR), name="templates")


def load_workspace_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                if cfg.get('folderPath') and os.path.isdir(cfg['folderPath']):
                    return cfg
        except Exception:
            pass
    return {'folderPath': BASE_DIR}


def save_workspace_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def make_deck_id_for_path(pptx_path):
    stem = os.path.splitext(os.path.basename(pptx_path))[0]
    norm_dir = os.path.normcase(os.path.abspath(os.path.dirname(pptx_path)))
    base_norm = os.path.normcase(os.path.abspath(BASE_DIR))
    if norm_dir == base_norm:
        return stem
    short_hash = hashlib.md5(norm_dir.encode('utf-8')).hexdigest()[:6]
    return f"{stem}_{short_hash}"


def scan_folder_pptx(folder_path):
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail=f"目录不存在或不可访问: {folder_path}")
    files = []
    for fname in sorted(os.listdir(folder_path)):
        if fname.lower().endswith('.pptx') and not fname.startswith('~$'):
            full_path = os.path.join(folder_path, fname)
            if not os.path.isfile(full_path):
                continue
            deck_id = make_deck_id_for_path(full_path)
            json_path = os.path.join(DECKS_DIR, f"{deck_id}.json")
            size_kb = round(os.path.getsize(full_path) / 1024.0, 1)
            files.append({
                'fileName': fname,
                'fullPath': full_path,
                'deckId': deck_id,
                'sizeKB': size_kb,
                'sizeKb': size_kb,
                'hasCachedDeck': os.path.exists(json_path)
            })
    return files


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/component-types")
def get_component_types():
    return {"types": COMPONENT_TYPES}


@app.get("/api/components/new/{comp_type}")
def new_component_template(comp_type: str, templateId: str = DEFAULT_TEMPLATE_ID):
    return create_default_component(comp_type, template_id=templateId)


@app.post("/api/components/relayout")
def api_relayout_component(comp: dict = Body(...), templateId: str = None):
    tpl = get_template(templateId) if templateId else None
    return rebuild_component_layout(comp, template=tpl)


# ==================== 1. 多风格模板库接口 ====================
@app.get("/api/templates")
def get_templates_api():
    tpls = list_templates()
    return {
        "defaultTemplateId": DEFAULT_TEMPLATE_ID,
        "templates": tpls
    }


@app.get("/api/templates/{template_id}")
def get_template_detail_api(template_id: str):
    tpl = get_template(template_id)
    return tpl


@app.post("/api/templates")
def create_or_save_template_api(payload: dict = Body(...)):
    from_deck_id = payload.get("fromDeckId")
    if from_deck_id:
        deck = payload.get("deck")
        if not deck:
            fpath = os.path.join(DECKS_DIR, f"{from_deck_id}.json")
            if not os.path.exists(fpath):
                raise HTTPException(status_code=404, detail=f"未找到用于提取模板的工程: {from_deck_id}")
            with open(fpath, 'r', encoding='utf-8') as f:
                deck = json.load(f)
        saved = extract_template_from_deck(
            deck,
            template_id=payload.get("id") or payload.get("name") or f"custom_{from_deck_id}",
            name=payload.get("name") or payload.get("id") or "自定义本地模板",
            description=payload.get("description", "")
        )
        return {"status": "ok", "template": saved}

    saved = save_custom_template(payload)
    return {"status": "ok", "template": saved}


@app.delete("/api/templates/{template_id}")
def delete_template_api(template_id: str):
    try:
        delete_custom_template(template_id)
        return {"status": "ok", "deleted": template_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/decks/{deck_id}/apply-template")
def apply_template_api(deck_id: str, payload: dict = Body(...)):
    template_id = payload.get("templateId") or DEFAULT_TEMPLATE_ID
    scope = payload.get("scope", "deck")
    slide_index = payload.get("slideIndex")
    deck = payload.get("deck")

    if not deck:
        fpath = os.path.join(DECKS_DIR, f"{deck_id}.json")
        if not os.path.exists(fpath):
            raise HTTPException(status_code=404, detail=f"Deck {deck_id} not found")
        with open(fpath, "r", encoding="utf-8") as f:
            deck = json.load(f)

    updated = apply_template_to_deck(deck, template_id=template_id, scope=scope, slide_index=slide_index)
    if payload.get("save", True):
        save_deck(deck_id, updated)
    return updated


# ==================== 2. 外部 AI 一键生成 PPT 接口 (ai-api) ====================
@app.get("/api/ai/tools")
def ai_tools_spec_api():
    return get_ai_tools_specification()


@app.post("/api/ai/generate")
def ai_generate_ppt_api(payload: dict = Body(...)):
    try:
        deck = build_deck_from_ai_spec(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AI 生稿参数解析失败: {e}")

    deck_id = deck['id']
    save_deck(deck_id, deck)
    json_path = os.path.join(DECKS_DIR, f"{deck_id}.json")

    custom_out = payload.get("outputPath")
    if custom_out:
        out_path = os.path.abspath(custom_out)
    elif payload.get("saveToWorkspace", False):
        cfg = load_workspace_config()
        out_path = os.path.join(cfg['folderPath'], f"{deck_id}.pptx")
    else:
        out_path = os.path.join(OUTPUT_DIR, f"{deck_id}.pptx")

    export_deck_to_pptx(deck, out_path)

    if payload.get("returnFile"):
        encoded_name = quote(os.path.basename(out_path))
        return FileResponse(
            out_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
        )

    return {
        "status": "ok",
        "deckId": deck_id,
        "templateId": deck.get("templateId", DEFAULT_TEMPLATE_ID),
        "slideCount": len(deck.get("slides", [])),
        "componentStats": deck.get("componentStats", {}),
        "jsonPath": json_path,
        "pptxPath": out_path,
        "downloadUrl": f"/api/decks/{quote(deck_id)}/export"
    }


@app.post("/api/ai/render-component")
def ai_render_component_api(payload: dict = Body(...)):
    comp_spec = payload.get("component") or payload
    template_id = payload.get("templateId") or DEFAULT_TEMPLATE_ID
    box = payload.get("box")
    default_box = tuple(box) if isinstance(box, (list, tuple)) and len(box) == 4 else None
    return render_single_component_from_spec(comp_spec, template_id=template_id, default_box=default_box)


@app.post("/api/ai/apply-template")
def ai_apply_template_api(payload: dict = Body(...)):
    deck_id = payload.get("deckId")
    template_id = payload.get("templateId") or DEFAULT_TEMPLATE_ID
    if not deck_id:
        raise HTTPException(status_code=400, detail="缺少必填字段 deckId")
    fpath = os.path.join(DECKS_DIR, f"{deck_id}.json")
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail=f"未找到工程: {deck_id}")
    with open(fpath, "r", encoding="utf-8") as f:
        deck = json.load(f)

    updated = apply_template_to_deck(deck, template_id=template_id, scope="deck")
    save_deck(deck_id, updated)
    out_path = os.path.abspath(payload["outputPath"]) if payload.get("outputPath") else os.path.join(OUTPUT_DIR, f"{deck_id}_{template_id}.pptx")
    export_deck_to_pptx(updated, out_path)
    return {
        "status": "ok",
        "deckId": deck_id,
        "templateId": template_id,
        "slideCount": len(updated.get("slides", [])),
        "pptxPath": out_path
    }


# ==================== 3. 工作区文件夹与工程读写接口 ====================
@app.get("/api/workspace/folder")
def get_workspace_folder():
    cfg = load_workspace_config()
    folder_path = cfg['folderPath']
    files = scan_folder_pptx(folder_path)
    return {
        "folderPath": folder_path,
        "files": files
    }


@app.post("/api/workspace/folder")
def set_workspace_folder(payload: dict = Body(...)):
    folder_path = (payload.get("folderPath") or "").strip().strip('"').strip("'")
    if not folder_path or not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail=f"文件夹路径不存在: {folder_path}")
    folder_path = os.path.abspath(folder_path)
    save_workspace_config({"folderPath": folder_path})
    files = scan_folder_pptx(folder_path)
    return {
        "folderPath": folder_path,
        "files": files
    }


@app.post("/api/workspace/open")
def open_pptx_from_workspace(payload: dict = Body(...)):
    cfg = load_workspace_config()
    folder_path = cfg['folderPath']
    full_path = payload.get("fullPath")
    file_name = payload.get("fileName")
    force_reparse = bool(payload.get("forceReparse", False))

    if not full_path and file_name:
        full_path = os.path.join(folder_path, file_name)
    if not full_path or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail=f"未找到 PPTX 文件: {full_path}")

    deck_id = make_deck_id_for_path(full_path)
    json_path = os.path.join(DECKS_DIR, f"{deck_id}.json")

    if force_reparse or not os.path.exists(json_path):
        deck = convert_pptx_to_deck(
            full_path,
            deck_id,
            os.path.basename(full_path),
            json_path
        )
        deck['deckId'] = deck_id
        deck['sourcePptx'] = os.path.basename(full_path)
        deck['sourceFile'] = full_path
        return deck

    with open(json_path, 'r', encoding='utf-8') as f:
        deck = json.load(f)
    deck['deckId'] = deck_id
    deck['sourcePptx'] = os.path.basename(full_path)
    deck['sourceFile'] = full_path
    return deck


@app.get("/api/decks")
def list_decks():
    items = []
    for fname in sorted(os.listdir(DECKS_DIR)):
        if fname.endswith(".json") and not fname.startswith("_"):
            fpath = os.path.join(DECKS_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    d = json.load(f)
                items.append({
                    "id": d.get("id", fname[:-5]),
                    "title": d.get("title", fname[:-5]),
                    "templateId": d.get("templateId", DEFAULT_TEMPLATE_ID),
                    "sourceFile": d.get("sourceFile"),
                    "slideCount": len(d.get("slides", [])),
                    "componentStats": d.get("componentStats", {})
                })
            except Exception as e:
                print(f"Error reading {fname}: {e}")
    return {"decks": items}


@app.get("/api/decks/{deck_id}")
def get_deck(deck_id: str):
    fpath = os.path.join(DECKS_DIR, f"{deck_id}.json")
    if not os.path.exists(fpath):
        cfg = load_workspace_config()
        candidate = os.path.join(cfg['folderPath'], f"{deck_id}.pptx")
        if os.path.isfile(candidate):
            return convert_pptx_to_deck(candidate, deck_id, f"{deck_id}.pptx", fpath)
        raise HTTPException(status_code=404, detail=f"Deck {deck_id} not found")
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)


@app.put("/api/decks/{deck_id}")
def save_deck(deck_id: str, deck: dict = Body(...)):
    fpath = os.path.join(DECKS_DIR, f"{deck_id}.json")
    stats = {}
    for s in deck.get("slides", []):
        for c in s.get("components", []):
            t = c.get("type", "info-card")
            stats[t] = stats.get(t, 0) + 1
    deck["componentStats"] = stats
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
    return {"status": "ok", "deckId": deck_id, "componentStats": stats}


@app.post("/api/decks/{deck_id}/reset")
def reset_deck(deck_id: str):
    fpath = os.path.join(DECKS_DIR, f"{deck_id}.json")
    source_file = None
    if os.path.exists(fpath):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                source_file = json.load(f).get('sourceFile')
        except Exception:
            pass
    if not source_file or not os.path.isfile(source_file):
        cfg = load_workspace_config()
        candidate = os.path.join(cfg['folderPath'], f"{deck_id}.pptx")
        if os.path.isfile(candidate):
            source_file = candidate
        else:
            candidate2 = os.path.join(BASE_DIR, f"{deck_id}.pptx")
            if os.path.isfile(candidate2):
                source_file = candidate2

    if not source_file or not os.path.isfile(source_file):
        raise HTTPException(status_code=404, detail=f"未找到原始 PPTX 文件以重置: {deck_id}")

    deck = convert_pptx_to_deck(
        source_file,
        deck_id,
        os.path.basename(source_file),
        fpath
    )
    return deck


@app.post("/api/decks/{deck_id}/save-pptx")
def save_deck_to_folder_pptx(deck_id: str, payload: dict = Body(...)):
    deck = payload.get("deck") or payload
    mode = payload.get("mode", "overwrite")

    save_deck(deck_id, deck)

    source_file = deck.get("sourceFile")
    if not source_file:
        cfg = load_workspace_config()
        source_file = os.path.join(cfg['folderPath'], f"{deck_id}.pptx")

    repro_path = os.path.join(OUTPUT_DIR, f"reproduced_{deck_id}.pptx")
    export_deck_to_pptx(deck, repro_path)

    target_path = repro_path
    if source_file and os.path.isdir(os.path.dirname(source_file)):
        if mode == "overwrite":
            backup_path = os.path.join(OUTPUT_DIR, f"backup_{os.path.basename(source_file)}")
            if os.path.isfile(source_file) and not os.path.exists(backup_path):
                shutil.copy2(source_file, backup_path)
            target_path = source_file
            export_deck_to_pptx(deck, target_path)
        elif mode == "copy":
            stem, ext = os.path.splitext(source_file)
            target_path = f"{stem}_edited{ext}"
            export_deck_to_pptx(deck, target_path)

    return {
        "status": "ok",
        "savedPptxPath": target_path,
        "reproducedPath": repro_path
    }


@app.post("/api/decks/{deck_id}/export")
def export_deck(deck_id: str, payload: dict = Body(default=None)):
    if payload and "slides" in payload:
        deck = payload
        save_deck(deck_id, deck)
    else:
        fpath = os.path.join(DECKS_DIR, f"{deck_id}.json")
        if not os.path.exists(fpath):
            raise HTTPException(status_code=404, detail=f"Deck {deck_id} not found")
        with open(fpath, "r", encoding="utf-8") as f:
            deck = json.load(f)

    out_filename = f"reproduced_{deck_id}.pptx"
    out_path = os.path.join(OUTPUT_DIR, out_filename)
    export_deck_to_pptx(deck, out_path)
    encoded_name = quote(out_filename)
    return FileResponse(
        out_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
