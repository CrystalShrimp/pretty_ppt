// PPT Component Studio - Frontend Controller

const TYPE_META = {
  'info-card':       { icon: '', label: 'info-card' },
  'slide-header':    { icon: '', label: 'slide-header' },
  'footer-banner':   { icon: '', label: 'footer-banner' },
  'kpi-card':        { icon: '', label: 'kpi-card' },
  'process-flow':    { icon: '', label: 'process-flow' },
  'vertical-stack':  { icon: '', label: 'vertical-stack' },
  'decision-gate':   { icon: '', label: 'decision-gate' },
  'stage-funnel':    { icon: '', label: 'stage-funnel' },
  'iteration-lanes': { icon: '', label: 'iteration-lanes' },
  'rule-checklist':  { icon: '', label: 'rule-checklist' },
  'data-table':      { icon: '', label: 'data-table' },
  'image-frame':     { icon: '', label: 'image-frame' },
  'tag-badge':       { icon: '', label: 'tag-badge' },
  'toc-list':           { icon: '', label: 'toc-list' },
  'cover-divider':      { icon: '', label: 'cover-divider' },
  'section-divider':    { icon: '', label: 'section-divider' },
  'milestone-timeline': { icon: '', label: 'milestone-timeline' }
};

const ROLE_LABELS = {
  'container':       '容器框',
  'title':           '标题',
  'subtitle':        '副标题',
  'body':            '正文列表',
  'page-num':        '页码',
  'step-box':        '步骤节点',
  'step-num':        '序号',
  'connector':       '连接线',
  'metric-box':      '指标面板',
  'image':           '图片',
  'table':           '数据表格',
  'divider':         '分割线',
  'shape':           '图形',
  'header-bar':      '顶栏条',
  'layer-card':      '层级卡片',
  'gate-node':       '判定节点',
  'branch-card':     '分支卡片',
  'stage-box':       '阶段节点',
  'summary-bar':     '总结横条',
  'lane-card':       '演进泳道',
  'topology-bar':    '拓扑汇总',
  'badge':           '语义徽章',
  'rule-item':       '规则条目',
  'trap-card':       '陷阱说明',
  'scenario-banner': '场景横幅',
  'rollback-loop':   '回退回路',
  'arrow-head':      '箭头标记',
  'section-bar':     '分节栏',
  'card':            '卡片'
};

const THEME_PALETTES = {
  academic: { primary: '#1B365D', darkText: '#1B365D', lightBg: '#F4F6F9', altLightBg: '#FDF2F5', border: '#1B365D' },
  orange:   { primary: '#F26B21', darkText: '#D45500', lightBg: '#FFF5EE', altLightBg: '#FFF2E6', border: '#F26B21' },
  blue:     { primary: '#1E6CFF', darkText: '#0F4CD6', lightBg: '#F0F5FF', altLightBg: '#EAF2FF', border: '#1E6CFF' },
  purple:   { primary: '#7B32D9', darkText: '#5B18B2', lightBg: '#F7F0FF', altLightBg: '#F3E8FF', border: '#7B32D9' },
  green:    { primary: '#0D9488', darkText: '#0F766E', lightBg: '#F0FDFA', altLightBg: '#CCFBF1', border: '#0D9488' },
  dark:     { primary: '#B45309', darkText: '#92400E', lightBg: '#FEF3C7', altLightBg: '#FFFBEB', border: '#D97706' }
};

const CARD_PRESETS = {
  'navy-card':     { fill: '#F4F6F9', borderColor: '#1B365D', borderWidth: 1.0, titleColor: '#1B365D', bodyColor: '#334155' },
  'burgundy-card': { fill: '#FDF2F5', borderColor: '#7A2048', borderWidth: 1.0, titleColor: '#7A2048', bodyColor: '#334155' },
  'orange-card':   { fill: '#FFF5EE', borderColor: '#F26B21', borderWidth: 1.3, titleColor: '#D45500', bodyColor: '#333333' },
  'blue-card':     { fill: '#F0F5FF', borderColor: '#1E6CFF', borderWidth: 1.3, titleColor: '#1E6CFF', bodyColor: '#333333' },
  'purple-card':   { fill: '#F7F0FF', borderColor: '#7B32D9', borderWidth: 1.3, titleColor: '#7B32D9', bodyColor: '#333333' },
  'white-card':    { fill: '#FFFFFF', borderColor: '#E2E8F0', borderWidth: 1.0, titleColor: '#1B365D', bodyColor: '#334155' },
  'gray-card':     { fill: '#F8F9FA', borderColor: '#DCDCDC', borderWidth: 1.2, titleColor: '#333333', bodyColor: '#555555' },
  'solid-navy':    { fill: '#1B365D', borderColor: '#1B365D', borderWidth: 1.0, titleColor: '#FFFFFF', bodyColor: '#FFFFFF' },
  'solid-orange':  { fill: '#F26B21', borderColor: '#F26B21', borderWidth: 1.0, titleColor: '#FFFFFF', bodyColor: '#FFFFFF' }
};

const state = {
  folderPath: '',
  folderFiles: [],
  templates: [],
  activeTemplateId: 'academic',
  deckId: 'component_showcase',
  deck: null,
  currentSlideIndex: 0,
  selectedCompId: null,
  selectedChildId: null,   // 若非空，则处于“子元素级微调”模式
  expandedComps: new Set(),
  zoom: 0.85,
  showGrid: false,
  snapToGrid: true,
  syncScope: 'single'      // 'single' | 'slide' | 'deck'
};

// 初始化入口
document.addEventListener('DOMContentLoaded', async () => {
  bindToolbarEvents();
  bindMacroPanelEvents();
  bindMicroPanelEvents();
  await loadTemplates();
  await initWorkspaceFolder();
  fitCanvasToViewport();
});

function showToast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.remove('hidden');
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => el.classList.add('hidden'), 2600);
}

function getCurrentSlide() {
  if (!state.deck || !state.deck.slides.length) return null;
  return state.deck.slides[state.currentSlideIndex] || state.deck.slides[0];
}

function getSelectedComponent() {
  const slide = getCurrentSlide();
  if (!slide || !state.selectedCompId) return null;
  return slide.components.find(c => c.id === state.selectedCompId) || null;
}

function getSelectedChild() {
  const comp = getSelectedComponent();
  if (!comp || !state.selectedChildId) return null;
  return (comp.children || []).find(ch => ch.id === state.selectedChildId) || null;
}

// 获取当前联动模式下受影响的所有目标元件
function getTargetComponentsForSync() {
  const activeComp = getSelectedComponent();
  if (!activeComp) return [];
  const targetType = activeComp.type;

  if (state.syncScope === 'single') {
    return [activeComp];
  }
  if (state.syncScope === 'slide') {
    const slide = getCurrentSlide();
    return slide ? slide.components.filter(c => c.type === targetType) : [activeComp];
  }
  if (state.syncScope === 'deck') {
    const list = [];
    for (const s of (state.deck.slides || [])) {
      for (const c of (s.components || [])) {
        if (c.type === targetType) list.push(c);
      }
    }
    return list;
  }
  return [activeComp];
}

// 加载多风格模板库
async function loadTemplates(selectedId) {
  try {
    const res = await fetch('/api/templates');
    if (!res.ok) return;
    const data = await res.json();
    state.templates = data.templates || [];
    if (selectedId) state.activeTemplateId = selectedId;
    else if (!state.activeTemplateId) state.activeTemplateId = data.defaultTemplateId || 'academic';
    renderTemplateSelect();
  } catch (err) {
    console.warn('加载模板库失败:', err);
  }
}

function renderTemplateSelect() {
  const sel = document.getElementById('templateSelect');
  if (!sel) return;
  sel.innerHTML = '';
  (state.templates || []).forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.id;
    const tag = t.source === 'local' ? '[本地私有] ' : '';
    opt.textContent = `${tag}${t.name || t.id}`;
    if (t.id === state.activeTemplateId) opt.selected = true;
    sel.appendChild(opt);
  });
}

function getActiveTemplate() {
  return (state.templates || []).find(t => t.id === state.activeTemplateId) || state.templates[0] || null;
}

// 初始化工作目录与扫描到的 PPTX 列表
async function initWorkspaceFolder() {
  try {
    const res = await fetch('/api/workspace/folder');
    if (!res.ok) throw new Error('获取默认工作目录失败');
    const data = await res.json();
    state.folderPath = data.folderPath || '';
    state.folderFiles = data.files || [];
    const folderInput = document.getElementById('workspaceFolderInput');
    if (folderInput) folderInput.value = state.folderPath;

    // 优先默认打开公开学术示范集 component_showcase.pptx，否则打开目录第一个文件
    const preferred = state.folderFiles.find(f => f.deckId === 'component_showcase')
      || state.folderFiles[0];
    const targetDeckId = preferred ? preferred.deckId : 'component_showcase';
    populateDeckSelect(state.folderFiles, targetDeckId);
    await openDeckFromFolder(targetDeckId, false);
  } catch (err) {
    console.error(err);
    await loadDeck('component_showcase');
  }
}

// 切换/扫描新文件夹目录
async function scanAndSetFolder(folderPath) {
  const cleanPath = (folderPath || '').trim();
  if (!cleanPath) {
    showToast('请输入有效的文件夹目录路径');
    return;
  }
  try {
    showToast(`正在扫描目录：${cleanPath} ...`);
    const res = await fetch('/api/workspace/folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folderPath: cleanPath })
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `扫描目录失败 (${res.status})`);
    }
    const data = await res.json();
    state.folderPath = data.folderPath;
    state.folderFiles = data.files || [];
    document.getElementById('workspaceFolderInput').value = state.folderPath;

    if (!state.folderFiles.length) {
      populateDeckSelect([], '');
      showToast(`目录 ${state.folderPath} 下未找到 .pptx 文件`);
      return;
    }

    const firstDeckId = state.folderFiles[0].deckId;
    populateDeckSelect(state.folderFiles, firstDeckId);
    await openDeckFromFolder(firstDeckId, false);
    showToast(`已读取目录：共发现 ${state.folderFiles.length} 个 PPTX 文件`);
  } catch (err) {
    console.error(err);
    showToast('读取目录失败：' + err.message);
  }
}

function populateDeckSelect(files, selectedDeckId) {
  const sel = document.getElementById('deckSelect');
  if (!sel) return;
  sel.innerHTML = '';
  if (!files || !files.length) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = '(当前目录无 .pptx 文件)';
    sel.appendChild(opt);
    return;
  }
  files.forEach(f => {
    const opt = document.createElement('option');
    opt.value = f.deckId;
    opt.textContent = `${f.fileName} (${f.sizeKb} KB)`;
    if (f.deckId === selectedDeckId) opt.selected = true;
    sel.appendChild(opt);
  });
}

// 从当前工作目录动态解析并打开任意 PPTX 文件
async function openDeckFromFolder(deckId, forceReparse = false) {
  if (!deckId) return;
  try {
    const fileEntry = state.folderFiles.find(f => f.deckId === deckId);
    const payload = fileEntry
      ? { fileName: fileEntry.fileName, fullPath: fileEntry.fullPath, forceReparse }
      : { fileName: `${deckId}.pptx`, forceReparse };

    showToast(forceReparse ? `正在从原 PPTX 重新解析元件：${deckId}...` : `正在加载 PPT：${deckId}...`);
    const res = await fetch('/api/workspace/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      // 回退到旧接口
      return await loadDeck(deckId);
    }
    state.deck = await res.json();
    state.deckId = state.deck.deckId || deckId;
    if (state.deck.templateId) {
      state.activeTemplateId = state.deck.templateId;
      renderTemplateSelect();
    }
    state.currentSlideIndex = 0;
    const firstSlide = getCurrentSlide();
    state.selectedCompId = firstSlide && firstSlide.components.length ? firstSlide.components[0].id : null;
    state.selectedChildId = null;
    state.expandedComps.clear();
    if (state.selectedCompId) state.expandedComps.add(state.selectedCompId);

    const sel = document.getElementById('deckSelect');
    if (sel) sel.value = state.deckId;
    renderAll();
    fitCanvasToViewport();
    showToast(`已打开：${state.deck.sourcePptx || state.deck.title} (${state.deck.slides.length} 页)`);
  } catch (err) {
    console.error(err);
    showToast('打开 PPT 失败：' + err.message);
  }
}

// 加载工程 (兼容直接按 deckId 读取)
async function loadDeck(deckId) {
  try {
    const res = await fetch(`/api/decks/${encodeURIComponent(deckId)}`);
    if (!res.ok) throw new Error(`加载工程失败: ${res.status}`);
    state.deck = await res.json();
    state.deckId = deckId;
    if (state.deck.templateId) {
      state.activeTemplateId = state.deck.templateId;
      renderTemplateSelect();
    }
    state.currentSlideIndex = 0;
    const firstSlide = getCurrentSlide();
    state.selectedCompId = firstSlide && firstSlide.components.length ? firstSlide.components[0].id : null;
    state.selectedChildId = null;
    state.expandedComps.clear();
    if (state.selectedCompId) state.expandedComps.add(state.selectedCompId);

    document.getElementById('deckSelect').value = deckId;
    renderAll();
    showToast(`已加载工程：${state.deck.title} (${state.deck.slides.length} 页)`);
  } catch (err) {
    console.error(err);
    showToast('加载工程出错：' + err.message);
  }
}

function renderAll() {
  renderSlideList();
  renderLayerTree();
  renderCanvas();
  renderInspector();
  updateJsonDrawerIfOpen();
}

// ==================== 1. 渲染幻灯片列表 ====================
function renderSlideList() {
  const container = document.getElementById('slideList');
  const slides = (state.deck && state.deck.slides) || [];
  document.getElementById('slideCountBadge').textContent = slides.length;
  container.innerHTML = '';

  slides.forEach((s, idx) => {
    const item = document.createElement('div');
    item.className = 'slide-item' + (idx === state.currentSlideIndex ? ' active' : '');
    item.innerHTML = `
      <span class="slide-num">${String(idx + 1).padStart(2, '0')}</span>
      <span class="slide-title-txt" title="${escapeHtml(s.title || '')}">${escapeHtml(s.title || `第 ${idx + 1} 页`)}</span>
      <span class="slide-comp-cnt">${(s.components || []).length} 元件</span>
    `;
    item.addEventListener('click', () => {
      state.currentSlideIndex = idx;
      const cur = getCurrentSlide();
      state.selectedCompId = cur && cur.components.length ? cur.components[0].id : null;
      state.selectedChildId = null;
      renderAll();
    });
    container.appendChild(item);
  });

  // 同步背景下拉框
  const curSlide = getCurrentSlide();
  if (curSlide) {
    const bgImg = (curSlide.background && curSlide.background.image) || '';
    const sel = document.getElementById('slideBgSelect');
    if (!bgImg) sel.value = 'none';
    else if (bgImg.includes('cover') || bgImg.includes('image2')) sel.value = 'cover';
    else sel.value = 'body';
  }
}

// ==================== 2. 渲染三级操作层级切换树 ====================
function renderLayerTree() {
  const container = document.getElementById('layerTree');
  container.innerHTML = '';
  const slide = getCurrentSlide();
  if (!slide) return;

  const activeComp = getSelectedComponent();
  const activeType = activeComp ? activeComp.type : null;

  slide.components.forEach((comp) => {
    const isCompSelected = comp.id === state.selectedCompId && !state.selectedChildId;
    const isParentOfSub = comp.id === state.selectedCompId && !!state.selectedChildId;
    const isSameTypePeer = state.syncScope !== 'single' && activeType && comp.type === activeType && comp.id !== state.selectedCompId;
    const isExpanded = state.expandedComps.has(comp.id);
    const rawName = comp.name || comp.type;
    const prefix = `${comp.type}:`;
    const shortName = rawName === comp.type
      ? ''
      : (rawName.startsWith(prefix) ? rawName.slice(prefix.length).trim() : rawName);

    const node = document.createElement('div');
    node.className = 'tree-comp-node' +
      ((isCompSelected || isParentOfSub) ? ' selected' : '') +
      (isSameTypePeer ? ' same-type-peer' : '');

    const header = document.createElement('div');
    header.className = 'tree-comp-header';
    header.innerHTML = `
      <span class="tree-toggle" title="展开/折叠元件内子元素">${isExpanded ? '▾' : '▸'}</span>
      <span class="tree-comp-type-badge">${escapeHtml(comp.type)}</span>
      <span class="tree-comp-title" title="${escapeHtml(rawName)}">${escapeHtml(shortName)}</span>
      <span class="tree-comp-type-badge">${ (comp.children || []).length }</span>
    `;

    header.querySelector('.tree-toggle').addEventListener('click', (e) => {
      e.stopPropagation();
      if (state.expandedComps.has(comp.id)) state.expandedComps.delete(comp.id);
      else state.expandedComps.add(comp.id);
      renderLayerTree();
    });

    header.addEventListener('click', () => {
      state.selectedCompId = comp.id;
      state.selectedChildId = null;
      state.expandedComps.add(comp.id);
      renderAll();
    });

    node.appendChild(header);

    if (isExpanded && comp.children && comp.children.length) {
      const chList = document.createElement('div');
      chList.className = 'tree-children-list';
      comp.children.forEach((ch, chIdx) => {
        const chItem = document.createElement('div');
        chItem.className = 'tree-child-item' + (state.selectedChildId === ch.id ? ' selected' : '');
        const rLabel = ROLE_LABELS[ch.role] || ch.rawType || '子项';
        const previewTxt = getChildShortLabel(ch, chIdx);
        chItem.innerHTML = `
          <span style="color:#a855f7;">↳</span>
          <span class="tree-comp-type-badge">${escapeHtml(rLabel)}</span>
          <span class="tree-comp-title">${escapeHtml(previewTxt)}</span>
        `;
        chItem.addEventListener('click', (e) => {
          e.stopPropagation();
          state.selectedCompId = comp.id;
          state.selectedChildId = ch.id;
          renderAll();
        });
        chList.appendChild(chItem);
      });
      node.appendChild(chList);
    }

    container.appendChild(node);
  });
}

function getChildShortLabel(ch, idx) {
  if (ch.rawType === 'image') {
    const parts = (ch.src || '').split('/');
    return parts[parts.length - 1] || `图片 #${idx + 1}`;
  }
  if (ch.rawType === 'table') {
    const r = (ch.rows || []).length;
    const c = r ? ch.rows[0].length : 0;
    return `表格 (${r}×${c})`;
  }
  if (ch.textBody && ch.textBody.paragraphs && ch.textBody.paragraphs.length) {
    const t = ch.textBody.paragraphs.map(p => p.text).join(' ').trim();
    if (t) return t.slice(0, 18);
  }
  return ch.name || `子元素 #${idx + 1}`;
}

// ==================== 3. 同步子元素坐标与渲染中央画布 ====================
function syncChildrenGeometry(comp) {
  const children = comp.children || [];
  if (!children.length) return;
  let maxRW = 0;
  let maxRH = 0;
  for (const ch of children) {
    const rw = (Number(ch.relX) || 0) + (Number(ch.relW) || Number(ch.w) || 0);
    const rh = (Number(ch.relY) || 0) + (Number(ch.relH) || Number(ch.h) || 0);
    if (rw > maxRW) maxRW = rw;
    if (rh > maxRH) maxRH = rh;
  }
  const sx = maxRW > 1 ? comp.w / maxRW : 1;
  const sy = maxRH > 1 ? comp.h / maxRH : 1;
  for (const ch of children) {
    if (ch.relX !== undefined && ch.relY !== undefined) {
      ch.x = +(comp.x + ch.relX * sx).toFixed(2);
      ch.y = +(comp.y + ch.relY * sy).toFixed(2);
      ch.w = +((ch.relW ?? ch.w) * sx).toFixed(2);
      ch.h = +((ch.relH ?? ch.h) * sy).toFixed(2);
    }
  }
}

function recomputeCompBoundsFromChildren(comp) {
  const children = comp.children || [];
  if (!children.length) return;
  const minX = Math.min(...children.map(c => c.x));
  const minY = Math.min(...children.map(c => c.y));
  const maxX = Math.max(...children.map(c => c.x + c.w));
  const maxY = Math.max(...children.map(c => c.y + c.h));
  comp.x = +minX.toFixed(2);
  comp.y = +minY.toFixed(2);
  comp.w = +Math.max(maxX - minX, 4).toFixed(2);
  comp.h = +Math.max(maxY - minY, 4).toFixed(2);
  for (const ch of children) {
    ch.relX = +(ch.x - comp.x).toFixed(2);
    ch.relY = +(ch.y - comp.y).toFixed(2);
    ch.relW = +ch.w.toFixed(2);
    ch.relH = +ch.h.toFixed(2);
  }
}

function hexWithAlpha(hexStr, alphaVal) {
  if (!hexStr || hexStr === 'none') return 'transparent';
  const a = (alphaVal !== undefined && alphaVal !== null) ? Number(alphaVal) : 1.0;
  const h = hexStr.replace('#', '').trim();
  if (h.length === 6) {
    const r = parseInt(h.slice(0, 2), 16);
    const g = parseInt(h.slice(2, 4), 16);
    const b = parseInt(h.slice(4, 6), 16);
    return a >= 0.999 ? `#${h}` : `rgba(${r}, ${g}, ${b}, ${a})`;
  }
  return hexStr;
}

function gradToCss(grad) {
  if (!grad || !grad.stops || !grad.stops.length) return 'none';
  const cssAngle = Math.round(((Number(grad.angle || 0) + 90) % 360));
  const stops = grad.stops.map(s => {
    const pct = Math.round((Number(s.pos || 0) <= 1 ? Number(s.pos || 0) * 100 : Number(s.pos || 0) / 1000));
    return `${hexWithAlpha(s.color, s.alpha)} ${pct}%`;
  }).join(', ');
  return `linear-gradient(${cssAngle}deg, ${stops})`;
}

function renderCanvas() {
  const canvas = document.getElementById('slideCanvas');
  const slide = getCurrentSlide();
  if (!slide) return;

  const cw = (state.deck.canvas && state.deck.canvas.width) || 1020.7;
  const ch = (state.deck.canvas && state.deck.canvas.height) || 680.3;
  canvas.style.width = `${cw}px`;
  canvas.style.height = `${ch}px`;
  canvas.style.transform = `scale(${state.zoom})`;
  canvas.classList.toggle('show-grid', state.showGrid);

  // 背景（支持图片、线性渐变、纯色）
  const bg = slide.background || {};
  if (bg.type === 'image' && bg.image) {
    canvas.style.backgroundImage = `url('${bg.image}')`;
    canvas.style.backgroundColor = bg.color || '#FFFFFF';
  } else if (bg.type === 'gradient' && bg.stops && bg.stops.length) {
    canvas.style.backgroundImage = gradToCss(bg);
    canvas.style.backgroundColor = bg.color || '#F5F1E8';
  } else {
    canvas.style.backgroundImage = 'none';
    canvas.style.backgroundColor = bg.color || '#FFFFFF';
  }

  canvas.innerHTML = '';

  // 渲染底层环境装饰层 (decorations)
  if (slide.decorations && slide.decorations.length) {
    const decorLayer = document.createElement('div');
    decorLayer.className = 'canvas-decor-layer';
    decorLayer.style.cssText = 'position:absolute;inset:0;pointer-events:none;overflow:hidden;z-index:0;';
    const dummyOrigin = { x: 0, y: 0, style: { borderRadius: 0 } };
    slide.decorations.forEach((dec) => {
      const decEl = renderChildDom(dummyOrigin, dec, true);
      decorLayer.appendChild(decEl);
    });
    canvas.appendChild(decorLayer);
  }

  const activeComp = getSelectedComponent();
  const activeType = activeComp ? activeComp.type : null;

  slide.components.forEach((comp) => {
    syncChildrenGeometry(comp);

    const compEl = document.createElement('div');
    const isSelected = comp.id === state.selectedCompId;
    const isSameType = state.syncScope !== 'single' && activeType && comp.type === activeType && comp.id !== state.selectedCompId;

    compEl.className = 'canvas-comp' +
      (isSelected ? ' selected' : '') +
      (isSameType ? ' same-type-highlight' : '');
    compEl.style.left = `${comp.x}px`;
    compEl.style.top = `${comp.y}px`;
    compEl.style.width = `${Math.max(comp.w, 6)}px`;
    compEl.style.height = `${Math.max(comp.h, 6)}px`;
    compEl.dataset.compId = comp.id;

    // 顶部元件类型胶囊 (直接使用纯 type)
    const pill = document.createElement('div');
    pill.className = 'comp-type-pill';
    pill.textContent = comp.type;
    compEl.appendChild(pill);

    // 渲染内部子元素
    (comp.children || []).forEach((child) => {
      const childEl = renderChildDom(comp, child);
      compEl.appendChild(childEl);
    });

    // 若处于元件级选中，添加 8 个缩放控制点
    if (isSelected && !state.selectedChildId) {
      appendResizeHandles(compEl, comp, null);
    }

    // 鼠标按下：选中并拖拽元件
    compEl.addEventListener('mousedown', (e) => {
      if (e.target.classList.contains('resize-handle')) return;
      e.stopPropagation();
      if (state.selectedCompId !== comp.id) {
        state.selectedCompId = comp.id;
        state.selectedChildId = null;
        state.expandedComps.add(comp.id);
        renderAll();
      } else if (state.selectedChildId && !e.target.closest('.sub-selected')) {
        state.selectedChildId = null;
        renderAll();
      }
      startDragElement(e, comp, null);
    });

    canvas.appendChild(compEl);
  });

  // 点击空白画布取消选中
  canvas.onmousedown = (e) => {
    if (e.target === canvas) {
      state.selectedCompId = null;
      state.selectedChildId = null;
      renderAll();
    }
  };

  updateStatusBar();
}

function renderChildDom(comp, ch, isDecor = false) {
  const el = document.createElement('div');
  const isSubSelected = !isDecor && state.selectedCompId === comp.id && state.selectedChildId === ch.id;
  el.className = 'canvas-child' + (isSubSelected ? ' sub-selected' : '');

  const left = ch.x - comp.x;
  const top = ch.y - comp.y;
  el.style.left = `${left}px`;
  el.style.top = `${top}px`;
  el.style.width = `${Math.max(ch.w, 2)}px`;
  el.style.height = `${Math.max(ch.h, 2)}px`;
  if (ch.rotation) {
    el.style.transform = `rotate(${ch.rotation}deg)`;
    el.style.transformOrigin = 'center center';
  }
  if (ch.shadow) {
    el.style.boxShadow = '0 4px 12px rgba(24, 24, 27, 0.10)';
  }

  if (ch.rawType === 'image') {
    const img = document.createElement('img');
    img.src = ch.src || '';
    img.style.width = '100%';
    img.style.height = '100%';
    img.style.objectFit = 'fill';
    if (ch.opacity !== undefined && ch.opacity !== null) {
      img.style.opacity = String(ch.opacity);
    }
    img.draggable = false;
    el.appendChild(img);
  } else if (ch.rawType === 'table') {
    el.appendChild(renderTableDom(ch));
  } else if (ch.geom === 'line' || ch.geom === 'elbowConnector') {
    el.style.overflow = 'visible';
    const w = Math.max(ch.w || 0, 0);
    const h = Math.max(ch.h || 0, 0);
    const padX = w < 2 ? 6 : 0;
    const padY = h < 2 ? 6 : 0;
    const svgW = Math.max(w, 12);
    const svgH = Math.max(h, 12);

    let x1 = padX, x2 = padX + w;
    let y1 = padY, y2 = padY + h;
    if (ch.flipH) [x1, x2] = [x2, x1];
    if (ch.flipV) [y1, y2] = [y2, y1];

    const stroke = hexWithAlpha(ch.borderColor || '#D9D9D9', ch.borderAlpha);
    const sw = Math.max(ch.borderWidth || 1.2, 1);
    const safeId = String(ch.id || Math.random()).replace(/[^a-zA-Z0-9_-]/g, '_');
    const hasHead = ch.headEnd && ch.headEnd !== 'none';
    const hasTail = ch.tailEnd && ch.tailEnd !== 'none';
    const markerId = `arrow_${safeId}`;
    const dashAttr = (ch.dashStyle === 'dot' || ch.dashStyle === 'sysDash')
      ? 'stroke-dasharray="2.5,3"'
      : ((ch.dashStyle && ch.dashStyle !== 'solid') ? 'stroke-dasharray="6,4"' : '');
    const mStart = hasHead ? `marker-start="url(#${markerId})"` : '';
    const mEnd = hasTail ? `marker-end="url(#${markerId})"` : '';
    const defs = (hasHead || hasTail)
      ? `<defs><marker id="${markerId}" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto-start-reverse"><path d="M0,0 L6,3 L0,6 Z" fill="${stroke}" /></marker></defs>`
      : '';

    const shapeEl = ch.geom === 'elbowConnector'
      ? `<path d="M ${x1},${y1} L ${(x1 + x2) / 2},${y1} L ${(x1 + x2) / 2},${y2} L ${x2},${y2}" fill="none" stroke="${stroke}" stroke-width="${sw}" ${dashAttr} ${mStart} ${mEnd} />`
      : `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${sw}" ${dashAttr} ${mStart} ${mEnd} />`;

    el.innerHTML = `
      <svg width="${svgW}" height="${svgH}" style="overflow:visible;position:absolute;left:${-padX}px;top:${-padY}px;pointer-events:none;">
        ${defs}
        ${shapeEl}
      </svg>
    `;
  } else {
    // Shape with fill / gradFill, border, and textBody (支持多边形、梯度渐变与透明度)
    const POLY_GEOMS = new Set(['diamond', 'chevron', 'pentagon', 'hexagon', 'parallelogram', 'triangle', 'rightArrow', 'plaque']);
    const isPoly = POLY_GEOMS.has(ch.geom);
    if (isPoly) {
      const vw = Math.max(ch.w || 40, 10);
      const vh = Math.max(ch.h || 24, 10);
      const sw = ch.borderWidth || 0;
      const stroke = (ch.borderColor && sw > 0) ? hexWithAlpha(ch.borderColor, ch.borderAlpha) : 'none';
      const fill = (ch.fill && ch.fill !== 'none') ? hexWithAlpha(ch.fill, ch.fillAlpha) : 'none';
      const dashAttr = (ch.dashStyle === 'dot' || ch.dashStyle === 'sysDash')
        ? 'stroke-dasharray="2.5,3"'
        : ((ch.dashStyle && ch.dashStyle !== 'solid') ? 'stroke-dasharray="6,4"' : '');
      let pts = '';
      if (ch.geom === 'diamond') {
        pts = `${vw / 2},1 ${vw - 1},${vh / 2} ${vw / 2},${vh - 1} 1,${vh / 2}`;
      } else if (ch.geom === 'chevron') {
        const dx = Math.min(vh * 0.42, vw * 0.28);
        pts = `1,1 ${vw - dx},1 ${vw - 1},${vh / 2} ${vw - dx},${vh - 1} 1,${vh - 1} ${dx},${vh / 2}`;
      } else if (ch.geom === 'pentagon') {
        const dx = Math.min(vh * 0.42, vw * 0.22);
        pts = `1,1 ${vw - dx},1 ${vw - 1},${vh / 2} ${vw - dx},${vh - 1} 1,${vh - 1}`;
      } else if (ch.geom === 'hexagon') {
        const dx = Math.min(vw * 0.25, vh * 0.5);
        pts = `${dx},1 ${vw - dx},1 ${vw - 1},${vh / 2} ${vw - dx},${vh - 1} ${dx},${vh - 1} 1,${vh / 2}`;
      } else if (ch.geom === 'parallelogram') {
        const skew = Math.min(vw * 0.35, vh * 0.55);
        pts = `${skew},1 ${vw - 1},1 ${vw - skew},${vh - 1} 1,${vh - 1}`;
      } else if (ch.geom === 'triangle') {
        pts = `${vw / 2},1 ${vw - 1},${vh - 1} 1,${vh - 1}`;
      } else if (ch.geom === 'rightArrow') {
        const hw = Math.min(vw * 0.45, vh * 0.7);
        const y1 = vh * 0.22, y2 = vh * 0.78;
        pts = `1,${y1} ${vw - hw},${y1} ${vw - hw},1 ${vw - 1},${vh / 2} ${vw - hw},${vh - 1} ${vw - hw},${y2} 1,${y2}`;
      } else if (ch.geom === 'plaque') {
        const c = Math.min(vw, vh) * 0.22;
        pts = `${c},1 ${vw - c},1 ${vw - 1},${c} ${vw - 1},${vh - c} ${vw - c},${vh - 1} ${c},${vh - 1} 1,${vh - c} 1,${c}`;
      }
      const svgBg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svgBg.setAttribute('viewBox', `0 0 ${vw} ${vh}`);
      svgBg.setAttribute('preserveAspectRatio', 'none');
      svgBg.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:0;';
      const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
      poly.setAttribute('points', pts);
      poly.setAttribute('fill', fill);
      poly.setAttribute('stroke', stroke);
      poly.setAttribute('stroke-width', String(sw));
      if (dashAttr) poly.setAttribute('stroke-dasharray', ch.dashStyle === 'dot' || ch.dashStyle === 'sysDash' ? '2.5,3' : '6,4');
      svgBg.appendChild(poly);
      el.appendChild(svgBg);
    } else {
      if (ch.gradFill && ch.gradFill.stops && ch.gradFill.stops.length) {
        el.style.backgroundImage = gradToCss(ch.gradFill);
      } else if (ch.fill && ch.fill !== 'none') {
        el.style.backgroundColor = hexWithAlpha(ch.fill, ch.fillAlpha);
      }
      if (ch.borderColor && (ch.borderWidth || 0) > 0) {
        const bStyle = (ch.dashStyle && ch.dashStyle !== 'solid')
          ? ((ch.dashStyle === 'dot' || ch.dashStyle === 'sysDash') ? 'dotted' : 'dashed')
          : 'solid';
        el.style.border = `${ch.borderWidth}px ${bStyle} ${hexWithAlpha(ch.borderColor, ch.borderAlpha)}`;
      }
      if (ch.geom === 'roundRect') {
        const r = comp.style && comp.style.borderRadius !== undefined ? comp.style.borderRadius : 8;
        el.style.borderRadius = `${r}px`;
      } else if (ch.geom === 'oval' || ch.geom === 'ellipse') {
        el.style.borderRadius = '50%';
      }
    }

    if (ch.textBody && ch.textBody.paragraphs && ch.textBody.paragraphs.length) {
      const tb = ch.textBody;
      const pad = tb.padding || { left: 7.2, top: 3.6, right: 7.2, bottom: 3.6 };
      el.style.padding = `${pad.top ?? 3.6}px ${pad.right ?? 7.2}px ${pad.bottom ?? 3.6}px ${pad.left ?? 7.2}px`;

      if (tb.valign === 'middle') el.style.justifyContent = 'center';
      else if (tb.valign === 'bottom') el.style.justifyContent = 'flex-end';
      else el.style.justifyContent = 'flex-start';

      const lineH = (comp.layout && comp.layout.lineHeight) || 1.3;

      tb.paragraphs.forEach((p) => {
        const pEl = document.createElement('div');
        pEl.style.position = 'relative';
        pEl.style.zIndex = '1';
        pEl.style.textAlign = p.align || 'left';
        pEl.style.lineHeight = String(lineH);
        if (p.spaceBefore) pEl.style.marginTop = `${p.spaceBefore * 1.33}px`;
        if (p.spaceAfter) pEl.style.marginBottom = `${p.spaceAfter * 1.33}px`;
        pEl.style.whiteSpace = tb.wrap === false ? 'nowrap' : 'pre-wrap';
        pEl.style.wordBreak = 'break-word';

        (p.runs || []).forEach((r) => {
          const span = document.createElement('span');
          span.textContent = r.text || '';
          const pt = r.fontSize || 10.5;
          span.style.fontSize = `${(pt * 96 / 72).toFixed(1)}px`;
          if (r.bold) span.style.fontWeight = '700';
          if (r.italic) span.style.fontStyle = 'italic';
          span.style.color = hexWithAlpha(r.color || '#333333', r.alpha);
          if (r.letterSpacing) span.style.letterSpacing = `${r.letterSpacing}pt`;
          if (r.fontFamily) span.style.fontFamily = `"${r.fontFamily}", "Microsoft YaHei", sans-serif`;
          pEl.appendChild(span);
        });
        el.appendChild(pEl);
      });
    }
  }

  if (isDecor) {
    return el;
  }

  // 双击直接进入子元素级微调
  el.addEventListener('dblclick', (e) => {
    e.stopPropagation();
    state.selectedCompId = comp.id;
    state.selectedChildId = ch.id;
    state.expandedComps.add(comp.id);
    renderAll();
  });

  if (isSubSelected) {
    appendResizeHandles(el, comp, ch);
    el.addEventListener('mousedown', (e) => {
      if (e.target.classList.contains('resize-handle')) return;
      e.stopPropagation();
      startDragElement(e, comp, ch);
    });
  }

  return el;
}

function renderTableDom(ch) {
  const tbl = document.createElement('table');
  tbl.className = 'canvas-child-table';
  const rows = ch.rows || [];
  const colWidths = ch.colWidths || [];
  const totalColW = colWidths.reduce((a, b) => a + b, 0) || ch.w || 1;

  if (colWidths.length) {
    const colgroup = document.createElement('colgroup');
    colWidths.forEach(cw => {
      const col = document.createElement('col');
      col.style.width = `${((cw / totalColW) * 100).toFixed(2)}%`;
      colgroup.appendChild(col);
    });
    tbl.appendChild(colgroup);
  }

  const rowHeights = ch.rowHeights || [];
  rows.forEach((r, rIdx) => {
    const tr = document.createElement('tr');
    if (rowHeights[rIdx]) tr.style.height = `${rowHeights[rIdx]}px`;
    r.forEach((cell) => {
      const td = document.createElement('td');
      if (cell.fill) td.style.backgroundColor = cell.fill;
      td.style.color = cell.color || (rIdx === 0 && cell.fill ? '#FFFFFF' : '#333333');
      const pt = cell.fontSize || 10.0;
      td.style.fontSize = `${(pt * 96 / 72).toFixed(1)}px`;
      if (cell.bold || rIdx === 0) td.style.fontWeight = '700';
      td.style.textAlign = cell.align || 'left';
      td.style.verticalAlign = cell.valign || 'middle';
      const pad = cell.padding || { left: 6, top: 3, right: 6, bottom: 3 };
      td.style.padding = `${pad.top ?? 3}px ${pad.right ?? 6}px ${pad.bottom ?? 3}px ${pad.left ?? 6}px`;
      td.textContent = cell.text || '';
      tr.appendChild(td);
    });
    tbl.appendChild(tr);
  });

  return tbl;
}

// ==================== 4. 拖拽与 8 点缩放交互 ====================
function appendResizeHandles(containerEl, comp, subChild) {
  const dirs = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
  dirs.forEach(dir => {
    const h = document.createElement('div');
    h.className = `resize-handle handle-${dir}`;
    h.addEventListener('mousedown', (e) => {
      e.stopPropagation();
      startResizeElement(e, comp, subChild, dir);
    });
    containerEl.appendChild(h);
  });
}

function startDragElement(e, comp, subChild) {
  const startMouseX = e.clientX;
  const startMouseY = e.clientY;
  const target = subChild || comp;
  const origX = target.x;
  const origY = target.y;

  const onMove = (ev) => {
    const dx = (ev.clientX - startMouseX) / state.zoom;
    const dy = (ev.clientY - startMouseY) / state.zoom;
    let nx = origX + dx;
    let ny = origY + dy;
    if (state.snapToGrid) {
      nx = Math.round(nx / 4) * 4;
      ny = Math.round(ny / 4) * 4;
    }
    target.x = +nx.toFixed(1);
    target.y = +ny.toFixed(1);

    if (subChild) {
      subChild.relX = +(subChild.x - comp.x).toFixed(2);
      subChild.relY = +(subChild.y - comp.y).toFixed(2);
    } else {
      syncChildrenGeometry(comp);
    }
    renderCanvas();
    updateCoordInputs(target);
  };

  const onUp = () => {
    window.removeEventListener('mousemove', onMove);
    window.removeEventListener('mouseup', onUp);
    updateJsonDrawerIfOpen();
  };

  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);
}

function startResizeElement(e, comp, subChild, dir) {
  const startMouseX = e.clientX;
  const startMouseY = e.clientY;
  const target = subChild || comp;
  const orig = { x: target.x, y: target.y, w: target.w, h: target.h };

  const onMove = (ev) => {
    const dx = (ev.clientX - startMouseX) / state.zoom;
    const dy = (ev.clientY - startMouseY) / state.zoom;
    let { x, y, w, h } = orig;

    if (dir.includes('e')) w = Math.max(16, orig.w + dx);
    if (dir.includes('s')) h = Math.max(12, orig.h + dy);
    if (dir.includes('w')) {
      const nw = Math.max(16, orig.w - dx);
      x = orig.x + (orig.w - nw);
      w = nw;
    }
    if (dir.includes('n')) {
      const nh = Math.max(12, orig.h - dy);
      y = orig.y + (orig.h - nh);
      h = nh;
    }

    if (state.snapToGrid) {
      x = Math.round(x / 2) * 2;
      y = Math.round(y / 2) * 2;
      w = Math.round(w / 2) * 2;
      h = Math.round(h / 2) * 2;
    }

    target.x = +x.toFixed(1);
    target.y = +y.toFixed(1);
    target.w = +w.toFixed(1);
    target.h = +h.toFixed(1);

    if (subChild) {
      subChild.relX = +(subChild.x - comp.x).toFixed(2);
      subChild.relY = +(subChild.y - comp.y).toFixed(2);
      subChild.relW = +subChild.w.toFixed(2);
      subChild.relH = +subChild.h.toFixed(2);
    } else {
      syncChildrenGeometry(comp);
    }
    renderCanvas();
    updateCoordInputs(target);
  };

  const onUp = () => {
    window.removeEventListener('mousemove', onMove);
    window.removeEventListener('mouseup', onUp);
    updateJsonDrawerIfOpen();
  };

  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);
}

// ==================== 5. 局部元件细节调优面板渲染与联动 ====================
function renderInspector() {
  const comp = getSelectedComponent();
  const subChild = getSelectedChild();
  const panel = document.getElementById('inspectorContent');
  if (!comp) {
    panel.style.opacity = '0.5';
    panel.style.pointerEvents = 'none';
    return;
  }
  panel.style.opacity = '1';
  panel.style.pointerEvents = 'auto';

  // 同类数量统计
  const slideSameCount = getCurrentSlide().components.filter(c => c.type === comp.type).length;
  let deckSameCount = 0;
  state.deck.slides.forEach(s => {
    deckSameCount += s.components.filter(c => c.type === comp.type).length;
  });
  document.getElementById('sameTypeCountBadge').textContent =
    `本页同类: ${slideSameCount} | 全篇同类: ${deckSameCount}`;

  // 层级标识
  const levelTag = document.getElementById('inspectorLevelTag');
  if (subChild) {
    levelTag.textContent = `子元素级: ${ROLE_LABELS[subChild.role] || subChild.rawType}`;
    levelTag.style.background = 'rgba(168, 85, 247, 0.25)';
    levelTag.style.color = '#e9d5ff';
  } else {
    levelTag.textContent = '元件级 (整体)';
    levelTag.style.background = 'rgba(43, 127, 255, 0.2)';
    levelTag.style.color = '#7ab3ff';
  }

  document.getElementById('propCompName').value = comp.name || '';
  document.getElementById('propCompType').value = comp.type || 'info-card';

  const targetGeom = subChild || comp;
  updateCoordInputs(targetGeom);

  // 空隙分布滑块
  const layout = comp.layout || {};
  setSliderValue('propPaddingX', 'valPaddingX', layout.paddingX ?? 10, ' px');
  setSliderValue('propPaddingY', 'valPaddingY', layout.paddingY ?? 8, ' px');
  setSliderValue('propHeaderGap', 'valHeaderGap', layout.headerGap ?? 6, ' px');
  setSliderValue('propItemGap', 'valItemGap', layout.itemGap ?? 5, ' px');
  setSliderValue('propLineHeight', 'valLineHeight', layout.lineHeight ?? 1.3, '');
  document.getElementById('propAlign').value = layout.align || 'left';
  document.getElementById('propValign').value = layout.valign || 'top';

  // 外观与文字样式
  const st = comp.style || {};
  const fillVal = subChild ? subChild.fill : st.fill;
  const borderVal = subChild ? subChild.borderColor : st.borderColor;
  const bwVal = subChild ? (subChild.borderWidth ?? 0) : (st.borderWidth ?? 1.2);

  setColorInput('propFillColor', 'propFillHex', fillVal);
  setColorInput('propBorderColor', 'propBorderHex', borderVal);
  document.getElementById('propBorderWidth').value = bwVal;
  document.getElementById('propBorderRadius').value = st.borderRadius ?? 8;

  setColorInput('propTitleColor', 'propTitleHex', st.titleColor || '#333333');
  document.getElementById('propTitleSize').value = st.titleSize || 12;
  setColorInput('propBodyColor', 'propBodyHex', st.bodyColor || '#333333');
  document.getElementById('propBodySize').value = st.bodySize || 10;

  // 渲染元件内内容编辑器
  renderContentEditor(comp, subChild);
}

function updateCoordInputs(target) {
  document.getElementById('propX').value = Math.round(target.x * 10) / 10;
  document.getElementById('propY').value = Math.round(target.y * 10) / 10;
  document.getElementById('propW').value = Math.round(target.w * 10) / 10;
  document.getElementById('propH').value = Math.round(target.h * 10) / 10;
}

function setSliderValue(sliderId, labelId, val, unit) {
  const el = document.getElementById(sliderId);
  const lb = document.getElementById(labelId);
  if (el) el.value = val;
  if (lb) lb.textContent = `${val}${unit}`;
}

function setColorInput(pickerId, hexId, hexVal) {
  const picker = document.getElementById(pickerId);
  const hex = document.getElementById(hexId);
  if (hexVal && /^#[0-9A-Fa-f]{6}$/.test(hexVal)) {
    picker.value = hexVal;
    hex.value = hexVal.toUpperCase();
  } else {
    picker.value = '#FFFFFF';
    hex.value = '';
  }
}

// ==================== 6. 元件内空隙分布重算引擎 (Internal Spacing Reflow) ====================
function applySpacingToComp(comp, key, val) {
  comp.layout = comp.layout || {};
  comp.layout[key] = val;
  const children = comp.children || [];
  const textChildren = children.filter(c => c.rawType === 'shape' && c.textBody && c.textBody.paragraphs && c.textBody.paragraphs.length);

  if (key === 'paddingX' || key === 'paddingY') {
    const px = comp.layout.paddingX ?? 10;
    const py = comp.layout.paddingY ?? 8;

    // 情况1：单框卡片（容器本身带多段文本）
    if (children.length === 1 && children[0].textBody) {
      children[0].textBody.padding = { left: px, right: px, top: py, bottom: py };
    } else {
      // 情况2：外框容器 + 内部独立标题/正文/图片子元素
      const container = children.find(c => c.role === 'container');
      for (const ch of children) {
        if (ch === container) continue;
        if (ch.role === 'title' || ch.role === 'body' || ch.role === 'subtitle') {
          if (key === 'paddingX') {
            ch.relX = px;
            ch.relW = Math.max(20, comp.w - px * 2);
          }
          if (key === 'paddingY' && ch.role === 'title') {
            const oldY = ch.relY;
            ch.relY = py;
            const dy = py - oldY;
            // 下方 body 跟随平移
            children.filter(b => b.role === 'body' || b.role === 'subtitle').forEach(b => {
              b.relY = Math.max(0, +(b.relY + dy).toFixed(1));
            });
          }
        } else if (comp.type === 'image-frame' && ch.rawType === 'image' && container) {
          ch.relX = px;
          ch.relY = py;
          ch.relW = Math.max(20, comp.w - px * 2);
          ch.relH = Math.max(20, comp.h - py * 2);
        }
      }
    }
    syncChildrenGeometry(comp);
  }

  if (key === 'headerGap') {
    if (textChildren.length === 1) {
      const paras = textChildren[0].textBody.paragraphs;
      if (paras.length > 0) paras[0].spaceAfter = val;
    } else if (textChildren.length >= 2) {
      const sorted = [...textChildren].sort((a, b) => a.relY - b.relY);
      const titleCh = sorted[0];
      const bodyCh = sorted[1];
      bodyCh.relY = +(titleCh.relY + titleCh.relH + val).toFixed(1);
      syncChildrenGeometry(comp);
    }
  }

  if (key === 'itemGap') {
    if (comp.type === 'process-flow') {
      // 横向流程链：调节步骤节点之间的水平间距并重排连接线
      const steps = children.filter(c => c.role !== 'connector').sort((a, b) => a.relX - b.relX);
      const conns = children.filter(c => c.role === 'connector').sort((a, b) => a.relX - b.relX);
      if (steps.length >= 2) {
        let curX = 0;
        steps.forEach((st, idx) => {
          st.relX = +curX.toFixed(1);
          if (idx < conns.length) {
            conns[idx].relX = +(curX + st.relW + 2).toFixed(1);
            conns[idx].relW = Math.max(4, val - 4);
          }
          curX += st.relW + val;
        });
        comp.w = +(curX - val).toFixed(1);
        syncChildrenGeometry(comp);
      }
    } else if (comp.type === 'kpi-card' && children.length >= 3) {
      // KPI 展示卡：调节上中下三块之间的垂直间距
      const sorted = [...children].sort((a, b) => a.relY - b.relY);
      let curY = 0;
      sorted.forEach((ch) => {
        ch.relY = +curY.toFixed(1);
        curY += ch.relH + val;
      });
      comp.h = +(curY - val).toFixed(1);
      syncChildrenGeometry(comp);
    } else if (comp.type === 'vertical-stack') {
      // 纵向架构栈：调节各层之间的垂直间距（兼容已有子元素，不覆盖文案）
      const header = children.find(c => c.role === 'header-bar' || c.role === 'section-bar');
      const layers = children.filter(c => c.role === 'layer-card').sort((a, b) => a.relY - b.relY);
      const badges = children.filter(c => c.role === 'badge').sort((a, b) => a.relY - b.relY);
      const conns = children.filter(c => c.role === 'connector').sort((a, b) => a.relY - b.relY);
      if (layers.length >= 2) {
        let curY = header ? (header.relY + header.relH + (comp.layout.headerGap ?? 10)) : 0;
        layers.forEach((lay, idx) => {
          lay.relY = +curY.toFixed(1);
          if (badges[idx]) badges[idx].relY = +curY.toFixed(1);
          if (idx < conns.length) {
            conns[idx].relY = +(curY + lay.relH + 2).toFixed(1);
            conns[idx].relH = Math.max(4, val - 4);
          }
          curY += lay.relH + val;
        });
        comp.h = +(curY - val).toFixed(1);
        syncChildrenGeometry(comp);
      }
    } else if (comp.type === 'stage-funnel' || comp.type === 'iteration-lanes') {
      // 横向漏斗或演进泳道：调节列间距与箭头长度
      const colRole = comp.type === 'stage-funnel' ? 'stage-box' : 'lane-card';
      const cols = children.filter(c => c.role === colRole).sort((a, b) => a.relX - b.relX);
      const badges = children.filter(c => c.role === 'badge').sort((a, b) => a.relX - b.relX);
      const conns = children.filter(c => c.role === 'connector').sort((a, b) => a.relX - b.relX);
      if (cols.length >= 2) {
        let curX = 0;
        cols.forEach((col, idx) => {
          col.relX = +curX.toFixed(1);
          if (badges[idx]) badges[idx].relX = +curX.toFixed(1);
          if (idx < conns.length) {
            conns[idx].relX = +(curX + col.relW + 2).toFixed(1);
            conns[idx].relW = Math.max(4, val - 4);
          }
          curX += col.relW + val;
        });
        const newW = +(curX - val).toFixed(1);
        children.filter(c => c.role === 'header-bar' || c.role === 'summary-bar' || c.role === 'topology-bar')
          .forEach(bar => { bar.relW = newW; });
        comp.w = newW;
        syncChildrenGeometry(comp);
      }
    } else if (comp.type === 'rule-checklist') {
      const rules = children.filter(c => c.role === 'rule-item').sort((a, b) => a.relY - b.relY);
      const badges = children.filter(c => c.role === 'badge').sort((a, b) => a.relY - b.relY);
      if (rules.length >= 2) {
        let curY = rules[0].relY;
        rules.forEach((r, idx) => {
          const oldMid = r.relY + r.relH / 2;
          r.relY = +curY.toFixed(1);
          if (badges[idx]) {
            const bOffset = badges[idx].relY - oldMid;
            badges[idx].relY = +(curY + r.relH / 2 + bOffset).toFixed(1);
          }
          curY += r.relH + val;
        });
        const py = comp.layout.paddingY ?? 10;
        comp.h = +(curY - val + py).toFixed(1);
        const container = children.find(c => c.role === 'container');
        if (container) container.relH = comp.h;
        syncChildrenGeometry(comp);
      }
    } else {
      // 普通卡片/列表：调节各条目段落之间的段后距 spaceAfter
      textChildren.forEach(tc => {
        const paras = tc.textBody.paragraphs;
        paras.forEach((p, idx) => {
          if (paras.length === 1 || idx >= 1) {
            p.spaceAfter = val;
          }
        });
      });
    }
  }

  if (key === 'align') {
    textChildren.forEach(tc => {
      tc.textBody.paragraphs.forEach(p => { p.align = val; });
    });
  }

  if (key === 'valign') {
    textChildren.forEach(tc => {
      tc.textBody.valign = val;
    });
  }
}

// ==================== 7. 元件外观与文字样式同步引擎 ====================
function applyStyleToComp(comp, subChild, prop, val) {
  comp.style = comp.style || {};
  comp.style[prop] = val;

  if (subChild && state.syncScope === 'single') {
    // 仅针对当前选中的单个子元素微调
    if (prop === 'fill') subChild.fill = val;
    if (prop === 'borderColor') subChild.borderColor = val;
    if (prop === 'borderWidth') subChild.borderWidth = val;
    if ((prop === 'titleColor' || prop === 'bodyColor') && subChild.textBody) {
      subChild.textBody.paragraphs.forEach(p => p.runs.forEach(r => { r.color = val; }));
    }
    if ((prop === 'titleSize' || prop === 'bodySize') && subChild.textBody) {
      subChild.textBody.paragraphs.forEach(p => p.runs.forEach(r => { r.fontSize = val; }));
    }
    return;
  }

  const children = comp.children || [];
  const container = children.find(c => c.role === 'container') ||
                    children.find(c => c.rawType === 'shape' && (c.fill || c.borderColor) && c.geom !== 'line');

  if (prop === 'fill') {
    if (container) container.fill = val;
    else if (children[0] && children[0].rawType === 'shape') children[0].fill = val;
  }
  if (prop === 'borderColor') {
    if (container) container.borderColor = val;
    else if (children[0] && children[0].rawType === 'shape') children[0].borderColor = val;
  }
  if (prop === 'borderWidth') {
    if (container) container.borderWidth = val;
    else if (children[0] && children[0].rawType === 'shape') children[0].borderWidth = val;
  }

  // 表格样式同步
  if (comp.type === 'data-table') {
    const tbl = children.find(c => c.rawType === 'table');
    if (tbl && tbl.rows && tbl.rows.length) {
      if (prop === 'fill') {
        tbl.rows[0].forEach(cell => { cell.fill = val; });
      }
      if (prop === 'titleColor') {
        tbl.rows[0].forEach(cell => { cell.color = val; });
      }
      if (prop === 'titleSize') {
        tbl.rows[0].forEach(cell => { cell.fontSize = val; });
      }
      if (prop === 'bodyColor') {
        tbl.rows.slice(1).forEach(r => r.forEach(cell => { cell.color = val; }));
      }
      if (prop === 'bodySize') {
        tbl.rows.slice(1).forEach(r => r.forEach(cell => { cell.fontSize = val; }));
      }
    }
    return;
  }

  // 文本标题与正文颜色/字号同步
  const textShapes = children.filter(c => c.rawType === 'shape' && c.textBody && c.textBody.paragraphs && c.textBody.paragraphs.length);
  if (textShapes.length === 1) {
    const paras = textShapes[0].textBody.paragraphs;
    if (paras.length > 0) {
      if (prop === 'titleColor') paras[0].runs.forEach(r => { r.color = val; });
      if (prop === 'titleSize') paras[0].runs.forEach(r => { r.fontSize = val; });
    }
    if (paras.length > 1) {
      paras.slice(1).forEach(p => {
        if (prop === 'bodyColor') p.runs.forEach(r => { r.color = val; });
        if (prop === 'bodySize') p.runs.forEach(r => { r.fontSize = val; });
      });
    }
  } else if (textShapes.length >= 2) {
    const sorted = [...textShapes].sort((a, b) => a.relY - b.relY);
    const first = sorted[0];
    if (prop === 'titleColor') first.textBody.paragraphs.forEach(p => p.runs.forEach(r => { r.color = val; }));
    if (prop === 'titleSize') first.textBody.paragraphs.forEach(p => p.runs.forEach(r => { r.fontSize = val; }));
    sorted.slice(1).forEach(sh => {
      if (sh.role === 'page-num') return;
      if (prop === 'bodyColor') sh.textBody.paragraphs.forEach(p => p.runs.forEach(r => { r.color = val; }));
      if (prop === 'bodySize') sh.textBody.paragraphs.forEach(p => p.runs.forEach(r => { r.fontSize = val; }));
    });
  }
}

// ==================== 8. 元件内元素内容编辑器 ====================
const DECLARATIVE_ARRAY_KEYS = {
  'vertical-stack':     { key: 'layers',   label: '层',   sample: (n) => ({ tag: `L${n}`, title: `新增第 ${n} 层`, desc: '在此输入该层规则定义与处理口径', tone: 'blue' }) },
  'decision-gate':      { key: 'branches', label: '分支', sample: (n) => ({ label: `分支 ${n}`, tone: 'warn', title: '新增裁决分支', items: ['• 说明判定触发条件', '• 说明对应处置动作'] }) },
  'stage-funnel':       { key: 'stages',   label: '阶段', sample: (n) => ({ code: `S${n}`, name: `阶段${n}`, metric: '待核验', desc: '输入该漏斗阶段核验指标', tone: 'blue' }) },
  'iteration-lanes':    { key: 'lanes',    label: '轮次', sample: (n) => ({ round: `R${n - 1} · 实验`, tone: 'promoted', title: `第 ${n} 轮实验`, metric: '命中率待测', items: ['• 单机制改动点', '• 核心指标变化'], verdict: '状态：待验证' }) },
  'rule-checklist':     { key: 'rows',     label: '条目', sample: (n) => ({ badge: '准', tone: 'pass', title: `新增规则 ${n}`, desc: '输入约束或参数配置说明' }) },
  'milestone-timeline': { key: 'milestones', label: '里程碑', sample: (n) => ({ step: `0${n}`, tag: 'STAGE', title: `里程碑节点 ${n}`, desc: '描述该阶段核心进展与量化成果', icon: 'board' }) },
  'process-flow':       { key: 'items',    label: '步骤', sample: (n) => `${n}. 新增步骤 | 描述核心处理环节` }
};

async function relayoutDeclarativeComp(comp) {
  try {
    const res = await fetch(`/api/components/relayout?templateId=${encodeURIComponent(state.activeTemplateId || 'academic')}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(comp)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const updated = await res.json();
    comp.children = updated.children || comp.children;
    comp.h = updated.h ?? comp.h;
    comp.w = updated.w ?? comp.w;
    state.selectedChildId = null;
    renderAll();
    showToast(`已重排 ${comp.type} 内部布局`);
  } catch (err) {
    showToast('重排失败：' + err.message);
  }
}

function renderContentEditor(comp, subChild) {
  const container = document.getElementById('contentEditorContainer');
  container.innerHTML = '';

  // 0A. 声明式多节点元件：增删阶段/分支/条目 + 重排
  const declCfg = DECLARATIVE_ARRAY_KEYS[comp.type];
  if (!subChild && declCfg && comp.content && Array.isArray(comp.content[declCfg.key]) && comp.content[declCfg.key].length > 0 && (comp.subType === 'declarative' || comp.type === 'process-flow')) {
    const arr = comp.content[declCfg.key];
    const bar = document.createElement('div');
    bar.className = 'inline-control';
    bar.style.marginBottom = '4px';
    bar.innerHTML = `
      <button class="mini-btn mini-btn-primary" id="btnDeclAdd">+ 新增${declCfg.label}</button>
      <button class="mini-btn mini-btn-danger" id="btnDeclDel">− 删除末${declCfg.label}</button>
      <button class="mini-btn" id="btnDeclRelayout" title="按当前外框与间距重排子元素">↻ 重排</button>
    `;
    bar.querySelector('#btnDeclAdd').addEventListener('click', () => {
      arr.push(declCfg.sample(arr.length + 1));
      relayoutDeclarativeComp(comp);
    });
    bar.querySelector('#btnDeclDel').addEventListener('click', () => {
      if (arr.length <= 1) {
        showToast(`至少保留 1 个${declCfg.label}`);
        return;
      }
      arr.pop();
      relayoutDeclarativeComp(comp);
    });
    bar.querySelector('#btnDeclRelayout').addEventListener('click', () => {
      relayoutDeclarativeComp(comp);
    });
    container.appendChild(bar);
  }

  // 0B. 子元素级几何/连线原语控制器
  if (subChild && subChild.rawType === 'shape') {
    const isConn = (subChild.geom === 'line' || subChild.geom === 'elbowConnector');
    const primBox = document.createElement('div');
    primBox.className = 'form-row';
    primBox.style.background = '#1d1f26';
    primBox.style.padding = '7px';
    primBox.style.borderRadius = '5px';
    if (isConn) {
      primBox.innerHTML = `
        <label>连接线原语属性 (line / elbowConnector / dash / arrow)</label>
        <div class="inline-control" style="flex-wrap:wrap;gap:5px;">
          <select id="subConnGeom" class="half-select" style="width:48%;">
            <option value="line" ${subChild.geom === 'line' ? 'selected' : ''}>直线 (line)</option>
            <option value="elbowConnector" ${subChild.geom === 'elbowConnector' ? 'selected' : ''}>正交折线 (elbow)</option>
          </select>
          <select id="subConnDash" class="half-select" style="width:48%;">
            <option value="solid" ${!subChild.dashStyle || subChild.dashStyle === 'solid' ? 'selected' : ''}>实线 (solid)</option>
            <option value="dash" ${subChild.dashStyle === 'dash' ? 'selected' : ''}>虚线 (dash)</option>
            <option value="dot" ${subChild.dashStyle === 'dot' ? 'selected' : ''}>点线 (dot)</option>
          </select>
          <select id="subConnHead" class="half-select" style="width:48%;">
            <option value="" ${!subChild.headEnd ? 'selected' : ''}>起点：无箭头</option>
            <option value="triangle" ${subChild.headEnd === 'triangle' ? 'selected' : ''}>起点：实心箭头</option>
          </select>
          <select id="subConnTail" class="half-select" style="width:48%;">
            <option value="" ${!subChild.tailEnd ? 'selected' : ''}>终点：无箭头</option>
            <option value="triangle" ${subChild.tailEnd === 'triangle' ? 'selected' : ''}>终点：实心箭头</option>
          </select>
          <label class="tb-checkbox"><input type="checkbox" id="subConnFlipH" ${subChild.flipH ? 'checked' : ''}/> 水平翻转(flipH)</label>
          <label class="tb-checkbox"><input type="checkbox" id="subConnFlipV" ${subChild.flipV ? 'checked' : ''}/> 垂直翻转(flipV)</label>
        </div>
      `;
      primBox.querySelector('#subConnGeom').addEventListener('change', (e) => { subChild.geom = e.target.value; renderCanvas(); });
      primBox.querySelector('#subConnDash').addEventListener('change', (e) => { subChild.dashStyle = e.target.value === 'solid' ? null : e.target.value; renderCanvas(); });
      primBox.querySelector('#subConnHead').addEventListener('change', (e) => { subChild.headEnd = e.target.value || null; renderCanvas(); });
      primBox.querySelector('#subConnTail').addEventListener('change', (e) => { subChild.tailEnd = e.target.value || null; renderCanvas(); });
      primBox.querySelector('#subConnFlipH').addEventListener('change', (e) => { subChild.flipH = e.target.checked; renderCanvas(); });
      primBox.querySelector('#subConnFlipV').addEventListener('change', (e) => { subChild.flipV = e.target.checked; renderCanvas(); });
    } else {
      const geoms = ['rect', 'roundRect', 'plaque', 'hexagon', 'parallelogram', 'diamond', 'chevron', 'pentagon', 'triangle', 'rightArrow', 'oval'];
      primBox.innerHTML = `
        <label>几何形状类型 (geom)</label>
        <select id="subShapeGeom" class="full-select">
          ${geoms.map(g => `<option value="${g}" ${subChild.geom === g ? 'selected' : ''}>${g}</option>`).join('')}
        </select>
      `;
      primBox.querySelector('#subShapeGeom').addEventListener('change', (e) => {
        subChild.geom = e.target.value;
        renderCanvas();
      });
    }
    container.appendChild(primBox);
  }

  // 若选中了特定子元素，只编辑该子元素
  const targetChildren = subChild ? [subChild] : (comp.children || []);

  // 1. 表格编辑器
  const tblChild = targetChildren.find(c => c.rawType === 'table');
  if (tblChild && tblChild.rows) {
    const actionRow = document.createElement('div');
    actionRow.className = 'inline-control';
    actionRow.innerHTML = `
      <button class="mini-btn" id="btnTblAddRow">+ 新增数据行</button>
      <button class="mini-btn mini-btn-danger" id="btnTblDelRow">− 删除末行</button>
    `;
    container.appendChild(actionRow);

    const grid = document.createElement('div');
    grid.className = 'table-editor-grid';
    tblChild.rows.forEach((row, rIdx) => {
      const rEl = document.createElement('div');
      rEl.className = 'table-editor-row' + (rIdx === 0 ? ' is-header' : '');
      row.forEach((cell) => {
        const inp = document.createElement('input');
        inp.type = 'text';
        inp.value = cell.text || '';
        inp.addEventListener('input', () => {
          cell.text = inp.value;
          cell.textBody = null; // 使用更新后的文本导出
          syncTableContentSummary(comp, tblChild);
          renderCanvas();
        });
        rEl.appendChild(inp);
      });
      grid.appendChild(rEl);
    });
    container.appendChild(grid);

    actionRow.querySelector('#btnTblAddRow').addEventListener('click', () => {
      const lastRow = tblChild.rows[tblChild.rows.length - 1] || [];
      const newRow = lastRow.map(c => ({ ...c, text: '新单元格数据', textBody: null }));
      tblChild.rows.push(newRow);
      if (tblChild.rowHeights && tblChild.rowHeights.length) {
        tblChild.rowHeights.push(tblChild.rowHeights[tblChild.rowHeights.length - 1]);
      }
      syncTableContentSummary(comp, tblChild);
      renderCanvas();
      renderContentEditor(comp, subChild);
    });

    actionRow.querySelector('#btnTblDelRow').addEventListener('click', () => {
      if (tblChild.rows.length > 2) {
        tblChild.rows.pop();
        if (tblChild.rowHeights && tblChild.rowHeights.length > 2) tblChild.rowHeights.pop();
        syncTableContentSummary(comp, tblChild);
        renderCanvas();
        renderContentEditor(comp, subChild);
      }
    });
  }

  // 2. 图片路径编辑器
  const imgChildren = targetChildren.filter(c => c.rawType === 'image');
  imgChildren.forEach((imgCh, idx) => {
    const row = document.createElement('div');
    row.className = 'form-row';
    row.innerHTML = `<label>内嵌图片 #${idx + 1} 路径 (src)</label>`;
    const inp = document.createElement('input');
    inp.type = 'text';
    inp.className = 'full-input';
    inp.value = imgCh.src || '';
    inp.addEventListener('change', () => {
      imgCh.src = inp.value.trim();
      renderCanvas();
    });
    row.appendChild(inp);
    container.appendChild(row);
  });

  // 3. 文本与段落条目编辑器
  const textChildren = targetChildren.filter(c => c.rawType === 'shape' && c.textBody && c.textBody.paragraphs && c.textBody.paragraphs.length);
  textChildren.forEach((tCh) => {
    const paras = tCh.textBody.paragraphs;
    const roleTitle = ROLE_LABELS[tCh.role] || tCh.name || '文本块';

    const header = document.createElement('div');
    header.style.display = 'flex';
    header.style.justifyContent = 'space-between';
    header.style.alignItems = 'center';
    header.style.marginTop = '4px';
    header.innerHTML = `
      <span style="font-size:11px;color:#ff985c;font-weight:600;">▪ ${escapeHtml(roleTitle)} (${paras.length} 段)</span>
      <button class="mini-btn" title="在此文本块末尾新增一段">+ 加段落</button>
    `;
    header.querySelector('button').addEventListener('click', () => {
      const lastP = paras[paras.length - 1];
      const baseRun = (lastP && lastP.runs && lastP.runs[0]) || { fontSize: 10, bold: false, color: '#333333', fontFamily: '微软雅黑' };
      paras.push({
        align: lastP ? lastP.align : 'left',
        spaceBefore: 0,
        spaceAfter: comp.layout?.itemGap ?? 4,
        runs: [{ ...baseRun, text: '• 新增条目内容' }],
        text: '• 新增条目内容'
      });
      syncTextContentSummary(comp);
      renderCanvas();
      renderContentEditor(comp, subChild);
    });
    container.appendChild(header);

    paras.forEach((p, pIdx) => {
      const itemRow = document.createElement('div');
      itemRow.className = 'item-edit-row';
      const ta = document.createElement('textarea');
      ta.value = p.runs ? p.runs.map(r => r.text).join('') : (p.text || '');
      ta.rows = ta.value.length > 36 ? 2 : 1;

      ta.addEventListener('input', () => {
        const newText = ta.value;
        p.text = newText;
        if (p.runs && p.runs.length > 1 && newText.includes('\n')) {
          const nlIdx = newText.indexOf('\n');
          const pre = newText.slice(0, nlIdx);
          const rest = newText.slice(nlIdx);
          p.runs[0].text = pre;
          p.runs[1].text = rest;
          p.runs = p.runs.slice(0, 2);
        } else if (p.runs && p.runs.length > 1 && newText.includes('：')) {
          const [pre, rest] = newText.split(/：(.*)/s);
          p.runs[0].text = pre + '：';
          p.runs[1].text = rest || '';
          p.runs = p.runs.slice(0, 2);
        } else if (p.runs && p.runs.length) {
          p.runs = [{ ...p.runs[0], text: newText }];
        } else {
          p.runs = [{ text: newText, fontSize: 10.5, bold: false, color: '#333333', fontFamily: '微软雅黑' }];
        }
        syncTextContentSummary(comp);
        renderCanvas();
      });

      itemRow.appendChild(ta);

      if (paras.length > 1) {
        const delBtn = document.createElement('button');
        delBtn.className = 'mini-btn mini-btn-danger';
        delBtn.textContent = '×';
        delBtn.title = '删除该段落';
        delBtn.addEventListener('click', () => {
          paras.splice(pIdx, 1);
          syncTextContentSummary(comp);
          renderCanvas();
          renderContentEditor(comp, subChild);
        });
        itemRow.appendChild(delBtn);
      }

      container.appendChild(itemRow);
    });
  });
}

function syncTableContentSummary(comp, tblChild) {
  if (!tblChild.rows || !tblChild.rows.length) return;
  comp.content = comp.content || {};
  comp.content.headers = tblChild.rows[0].map(c => c.text);
  comp.content.rows = tblChild.rows.slice(1).map(r => r.map(c => c.text));
}

function syncTextContentSummary(comp) {
  const textShapes = (comp.children || []).filter(c => c.rawType === 'shape' && c.textBody && c.textBody.paragraphs && c.textBody.paragraphs.length);
  if (!textShapes.length) return;
  comp.content = comp.content || {};
  const firstP = textShapes[0].textBody.paragraphs[0];
  if (firstP) {
    comp.content.title = firstP.text;
    if (comp.type === 'slide-header') {
      const slide = getCurrentSlide();
      if (slide) {
        slide.title = firstP.text;
        renderSlideList();
      }
    }
  }
}

// ==================== 9. 绑定顶部与两侧面板事件 ====================
function bindToolbarEvents() {
  // 工作目录读取与回车触发
  const folderInput = document.getElementById('workspaceFolderInput');
  const btnScan = document.getElementById('btnScanFolder');
  if (btnScan && folderInput) {
    btnScan.addEventListener('click', () => scanAndSetFolder(folderInput.value));
    folderInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') scanAndSetFolder(folderInput.value);
    });
  }

  document.getElementById('deckSelect').addEventListener('change', (e) => {
    openDeckFromFolder(e.target.value, false);
  });

  document.getElementById('btnResetDeck').addEventListener('click', async () => {
    if (!confirm(`确定要从目录内原始 ${state.deckId}.pptx 重新解析并恢复初始元件状态吗？`)) return;
    await openDeckFromFolder(state.deckId, true);
  });

  // 新建 15 类元件（自动遵循当前激活模板风格）
  document.getElementById('btnAddComponent').addEventListener('click', async () => {
    const compType = document.getElementById('newCompTypeSelect').value;
    const tplParam = encodeURIComponent(state.activeTemplateId || 'academic');
    const res = await fetch(`/api/components/new/${compType}?templateId=${tplParam}`);
    if (!res.ok) return;
    const newComp = await res.json();
    const slide = getCurrentSlide();
    if (!slide) return;
    // 稍微偏移避免完全重叠
    const offset = (slide.components.length % 5) * 16;
    newComp.x = +(newComp.x + offset).toFixed(1);
    newComp.y = +(newComp.y + offset).toFixed(1);
    syncChildrenGeometry(newComp);
    slide.components.push(newComp);
    state.selectedCompId = newComp.id;
    state.selectedChildId = null;
    state.expandedComps.add(newComp.id);
    renderAll();
    showToast(`已新建元件：${newComp.name}`);
  });

  // 缩放与网格
  document.getElementById('btnZoomOut').addEventListener('click', () => setZoom(state.zoom - 0.1));
  document.getElementById('btnZoomIn').addEventListener('click', () => setZoom(state.zoom + 0.1));
  document.getElementById('btnZoomFit').addEventListener('click', fitCanvasToViewport);

  document.getElementById('chkGrid').addEventListener('change', (e) => {
    state.showGrid = e.target.checked;
    renderCanvas();
  });
  document.getElementById('chkSnap').addEventListener('change', (e) => {
    state.snapToGrid = e.target.checked;
  });

  // 左右栏互换
  document.getElementById('btnSwapPanels').addEventListener('click', () => {
    document.getElementById('workspace').classList.toggle('swapped');
    showToast('已互换左右两栏面板位置');
  });

  // Agent JSON 抽屉
  document.getElementById('btnToggleJson').addEventListener('click', () => {
    const drawer = document.getElementById('jsonDrawer');
    drawer.classList.toggle('hidden');
    updateJsonDrawerIfOpen();
  });
  document.getElementById('btnCloseJson').addEventListener('click', () => {
    document.getElementById('jsonDrawer').classList.add('hidden');
  });
  document.getElementById('jsonTargetSelect').addEventListener('change', updateJsonDrawerIfOpen);
  document.getElementById('btnApplyJson').addEventListener('click', applyJsonFromDrawer);

  // 保存并写回目录原 PPTX / 另存副本 / 浏览器下载 PPTX
  document.getElementById('btnSaveDeck').addEventListener('click', async () => {
    showToast(`正在保存并将修改写回 ${state.deckId}.pptx ...`);
    const res = await fetch(`/api/decks/${encodeURIComponent(state.deckId)}/save-pptx`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ deck: state.deck, mode: 'overwrite' })
    });
    if (res.ok) {
      const info = await res.json();
      showToast(`已保存并写回：${info.savedPptxPath} (原文件已自动备份)`);
    } else {
      showToast('保存写回失败');
    }
  });

  const btnSaveCopy = document.getElementById('btnSaveCopy');
  if (btnSaveCopy) {
    btnSaveCopy.addEventListener('click', async () => {
      showToast(`正在生成副本 ${state.deckId}_edited.pptx ...`);
      const res = await fetch(`/api/decks/${encodeURIComponent(state.deckId)}/save-pptx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ deck: state.deck, mode: 'copy' })
      });
      if (res.ok) {
        const info = await res.json();
        showToast(`已另存副本至：${info.savedPptxPath}`);
        // 刷新当前目录文件下拉框
        if (state.folderPath) {
          const fRes = await fetch('/api/workspace/folder');
          if (fRes.ok) {
            const fData = await fRes.json();
            state.folderFiles = fData.files || [];
            populateDeckSelect(state.folderFiles, state.deckId);
          }
        }
      } else {
        showToast('另存副本失败');
      }
    });
  }

  document.getElementById('btnExportPptx').addEventListener('click', async () => {
    showToast('正在通过 python-pptx 编译生成标准 .pptx 文件...');
    const res = await fetch(`/api/decks/${encodeURIComponent(state.deckId)}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.deck)
    });
    if (!res.ok) {
      showToast('导出失败');
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `reproduced_${state.deckId}.pptx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast(`已成功下载 reproduced_${state.deckId}.pptx`);
  });
}

function bindMacroPanelEvents() {
  // 页面增删复制（使用当前激活模板背景与元件风格）
  document.getElementById('btnAddSlide').addEventListener('click', async () => {
    const tplParam = encodeURIComponent(state.activeTemplateId || 'academic');
    const hdrRes = await fetch(`/api/components/new/slide-header?templateId=${tplParam}`);
    const cardRes = await fetch(`/api/components/new/info-card?templateId=${tplParam}`);
    const ftrRes = await fetch(`/api/components/new/footer-banner?templateId=${tplParam}`);
    const hdr = await hdrRes.json();
    const card = await cardRes.json();
    const ftr = await ftrRes.json();
    const newIdx = state.deck.slides.length + 1;
    if (hdr.content) {
      hdr.content.pageNumber = `${newIdx} / ${newIdx}`;
      const pNumCh = (hdr.children || []).find(ch => ch.role === 'page-num');
      if (pNumCh?.textBody?.paragraphs?.[0]?.runs?.[0]) {
        pNumCh.textBody.paragraphs[0].runs[0].text = `${newIdx} / ${newIdx}`;
        pNumCh.textBody.paragraphs[0].text = `${newIdx} / ${newIdx}`;
      }
    }
    const tpl = getActiveTemplate();
    const bodyBg = (tpl && tpl.backgrounds && tpl.backgrounds.body)
      ? JSON.parse(JSON.stringify(tpl.backgrounds.body))
      : { type: 'color', color: '#FFFFFF', image: null };
    const newSlide = {
      id: `${state.deckId}_slide_${Date.now()}`,
      index: newIdx,
      title: `新建页面 ${newIdx}`,
      background: bodyBg,
      components: [hdr, card, ftr]
    };
    state.deck.slides.splice(state.currentSlideIndex + 1, 0, newSlide);
    state.currentSlideIndex += 1;
    state.selectedCompId = card.id;
    state.selectedChildId = null;
    renderAll();
    showToast('已新建标准幻灯片页面');
  });

  document.getElementById('btnDupSlide').addEventListener('click', () => {
    const cur = getCurrentSlide();
    if (!cur) return;
    const copy = JSON.parse(JSON.stringify(cur));
    copy.id = `${state.deckId}_slide_${Date.now()}`;
    copy.title = `${cur.title} (副本)`;
    copy.components.forEach((c, idx) => {
      c.id = `comp_${Date.now()}_${idx}`;
      (c.children || []).forEach((ch, ci) => { ch.id = `${c.id}_ch${ci + 1}`; });
    });
    state.deck.slides.splice(state.currentSlideIndex + 1, 0, copy);
    state.currentSlideIndex += 1;
    renderAll();
    showToast('已复制当前页面');
  });

  document.getElementById('btnDelSlide').addEventListener('click', () => {
    if (state.deck.slides.length <= 1) {
      showToast('至少保留一页幻灯片');
      return;
    }
    state.deck.slides.splice(state.currentSlideIndex, 1);
    state.currentSlideIndex = Math.max(0, state.currentSlideIndex - 1);
    state.selectedCompId = getCurrentSlide()?.components[0]?.id || null;
    state.selectedChildId = null;
    renderAll();
    showToast('已删除页面');
  });

  // 层级上下移动与删除元件
  document.getElementById('btnLayerUp').addEventListener('click', () => moveCompLayer(-1));
  document.getElementById('btnLayerDown').addEventListener('click', () => moveCompLayer(1));
  document.getElementById('btnDelComp').addEventListener('click', deleteSelectedElement);

  // 宏观页面对齐与等距分布
  document.querySelectorAll('.align-btn').forEach(btn => {
    btn.addEventListener('click', () => applyMacroAlignment(btn.dataset.align));
  });

  document.getElementById('btnApplyMarginX').addEventListener('click', () => {
    const margin = Number(document.getElementById('macroMarginX').value) || 50;
    const slide = getCurrentSlide();
    if (!slide) return;
    const cw = state.deck.canvas?.width || 1020.7;
    slide.components.forEach(c => {
      if (c.x < 85 && c.w > 750) {
        c.x = margin;
        c.w = +(cw - margin * 2).toFixed(1);
        syncChildrenGeometry(c);
      }
    });
    renderAll();
    showToast(`已将全宽元件左右页边距统一规整为 ${margin}px`);
  });

  // 多风格模板库：套用模板 & 将当前工程存为自定义模板
  const btnApplyTpl = document.getElementById('btnApplyTemplate');
  if (btnApplyTpl) {
    btnApplyTpl.addEventListener('click', async () => {
      const tplId = document.getElementById('templateSelect').value || 'academic';
      const scope = document.getElementById('themeScopeSelect').value || 'deck';
      state.activeTemplateId = tplId;
      showToast(`正在套用模板 [${tplId}] (${scope === 'deck' ? '全文档' : '当前页'})...`);
      const res = await fetch(`/api/decks/${encodeURIComponent(state.deckId)}/apply-template`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          templateId: tplId,
          scope,
          slideIndex: state.currentSlideIndex,
          deck: state.deck,
          save: false
        })
      });
      if (!res.ok) {
        showToast('套用模板失败');
        return;
      }
      state.deck = await res.json();
      renderAll();
      showToast(`已成功套用模板：${tplId}`);
    });
  }

  const btnSaveTpl = document.getElementById('btnSaveTemplate');
  if (btnSaveTpl) {
    btnSaveTpl.addEventListener('click', async () => {
      const tplName = prompt('请输入要保存为本地自定义模板的名称：', `${state.deck?.title || '自定义'} 模板`);
      if (!tplName || !tplName.trim()) return;
      const tplId = prompt('请输入英文模板 ID (仅限字母/数字/下划线)：', `custom_${Date.now().toString(36)}`);
      if (!tplId || !tplId.trim()) return;
      const res = await fetch('/api/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fromDeckId: state.deckId,
          deck: state.deck,
          id: tplId.trim(),
          name: tplName.trim(),
          description: `从工程 ${state.deckId} 提取的本地自定义模板`
        })
      });
      if (res.ok) {
        const data = await res.json();
        await loadTemplates(data.template.id);
        showToast(`已沉淀本地模板：${data.template.name} (${data.template.id})`);
      } else {
        showToast('保存自定义模板失败');
      }
    });
  }

  // 宏观主题色切换
  document.querySelectorAll('.theme-swatch').forEach(btn => {
    btn.addEventListener('click', () => {
      const themeKey = btn.dataset.theme;
      const scope = document.getElementById('themeScopeSelect').value;
      applyMacroThemePalette(themeKey, scope);
    });
  });

  // 页面背景底图切换（读取当前激活模板底图或置为纯白）
  document.getElementById('slideBgSelect').addEventListener('change', (e) => {
    const slide = getCurrentSlide();
    if (!slide) return;
    const val = e.target.value;
    const tpl = getActiveTemplate();
    if (val === 'cover' && tpl?.backgrounds?.cover) {
      slide.background = JSON.parse(JSON.stringify(tpl.backgrounds.cover));
    } else if (val === 'body' && tpl?.backgrounds?.body) {
      slide.background = JSON.parse(JSON.stringify(tpl.backgrounds.body));
    } else {
      slide.background = { type: 'color', color: '#FFFFFF', image: null };
    }
    renderCanvas();
    showToast('已切换当前页背景配置');
  });

  // 宏观全页字号缩放
  document.getElementById('btnMacroFontDec').addEventListener('click', () => scaleSlideFonts(-1));
  document.getElementById('btnMacroFontInc').addEventListener('click', () => scaleSlideFonts(1));
}

function bindMicroPanelEvents() {
  // 同类元素样式同步范围切换
  document.querySelectorAll('input[name="syncScope"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      state.syncScope = e.target.value;
      renderLayerTree();
      renderCanvas();
      updateStatusBar();
    });
  });

  // 元件名称与类型修改
  document.getElementById('propCompName').addEventListener('input', (e) => {
    const comp = getSelectedComponent();
    if (!comp) return;
    comp.name = e.target.value;
    renderLayerTree();
  });

  document.getElementById('propCompType').addEventListener('change', (e) => {
    const comp = getSelectedComponent();
    if (!comp) return;
    comp.type = e.target.value;
    renderAll();
    showToast(`已将元件类型调整为：${e.target.value}`);
  });

  // 快速卡片样式预设
  document.querySelectorAll('.preset-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const preset = CARD_PRESETS[btn.dataset.preset];
      if (!preset) return;
      const targets = getTargetComponentsForSync();
      targets.forEach(c => {
        Object.entries(preset).forEach(([k, v]) => applyStyleToComp(c, null, k, v));
      });
      renderCanvas();
      renderInspector();
      showToast(`已应用样式预设到 ${targets.length} 个同类元件`);
    });
  });

  // 坐标与宽高输入
  ['X', 'Y', 'W', 'H'].forEach(axis => {
    document.getElementById(`prop${axis}`).addEventListener('change', (e) => {
      const comp = getSelectedComponent();
      if (!comp) return;
      const subChild = getSelectedChild();
      const target = subChild || comp;
      const key = axis.toLowerCase();
      target[key] = Number(e.target.value) || 0;
      if (subChild) {
        subChild.relX = +(subChild.x - comp.x).toFixed(2);
        subChild.relY = +(subChild.y - comp.y).toFixed(2);
        subChild.relW = +subChild.w.toFixed(2);
        subChild.relH = +subChild.h.toFixed(2);
      } else {
        syncChildrenGeometry(comp);
      }
      renderCanvas();
    });
  });

  // 元件内空隙分布滑块
  const spacingBindings = [
    { id: 'propPaddingX', valId: 'valPaddingX', key: 'paddingX', unit: ' px' },
    { id: 'propPaddingY', valId: 'valPaddingY', key: 'paddingY', unit: ' px' },
    { id: 'propHeaderGap', valId: 'valHeaderGap', key: 'headerGap', unit: ' px' },
    { id: 'propItemGap', valId: 'valItemGap', key: 'itemGap', unit: ' px' },
    { id: 'propLineHeight', valId: 'valLineHeight', key: 'lineHeight', unit: '' }
  ];
  spacingBindings.forEach(({ id, valId, key, unit }) => {
    const el = document.getElementById(id);
    el.addEventListener('input', () => {
      const v = Number(el.value);
      document.getElementById(valId).textContent = `${v}${unit}`;
      const targets = getTargetComponentsForSync();
      targets.forEach(c => applySpacingToComp(c, key, v));
      renderCanvas();
    });
  });

  document.getElementById('propAlign').addEventListener('change', (e) => {
    const targets = getTargetComponentsForSync();
    targets.forEach(c => applySpacingToComp(c, 'align', e.target.value));
    renderCanvas();
  });
  document.getElementById('propValign').addEventListener('change', (e) => {
    const targets = getTargetComponentsForSync();
    targets.forEach(c => applySpacingToComp(c, 'valign', e.target.value));
    renderCanvas();
  });

  // 颜色与字号绑定
  bindColorPair('propFillColor', 'propFillHex', 'fill');
  bindColorPair('propBorderColor', 'propBorderHex', 'borderColor');
  bindColorPair('propTitleColor', 'propTitleHex', 'titleColor');
  bindColorPair('propBodyColor', 'propBodyHex', 'bodyColor');

  ['BorderWidth', 'BorderRadius', 'TitleSize', 'BodySize'].forEach(field => {
    const propKey = field.charAt(0).toLowerCase() + field.slice(1);
    document.getElementById(`prop${field}`).addEventListener('input', (e) => {
      const v = Number(e.target.value);
      const subChild = getSelectedChild();
      const targets = getTargetComponentsForSync();
      targets.forEach(c => applyStyleToComp(c, subChild, propKey, v));
      renderCanvas();
    });
  });
}

function bindColorPair(pickerId, hexId, styleProp) {
  const picker = document.getElementById(pickerId);
  const hex = document.getElementById(hexId);
  const apply = (val) => {
    const subChild = getSelectedChild();
    const targets = getTargetComponentsForSync();
    targets.forEach(c => applyStyleToComp(c, subChild, styleProp, val));
    renderCanvas();
  };
  picker.addEventListener('input', () => {
    hex.value = picker.value.toUpperCase();
    apply(picker.value.toUpperCase());
  });
  hex.addEventListener('change', () => {
    const v = hex.value.trim();
    if (!v) {
      apply(null);
    } else if (/^#[0-9A-Fa-f]{6}$/.test(v)) {
      picker.value = v;
      apply(v.toUpperCase());
    }
  });
}

// ==================== 10. 宏观排版、主题与辅助工具 ====================
function applyMacroAlignment(mode) {
  const slide = getCurrentSlide();
  if (!slide) return;
  const comp = getSelectedComponent();
  const cw = state.deck.canvas?.width || 1020.7;
  const ch = state.deck.canvas?.height || 680.3;
  const safeMarginX = 49.9;

  if (mode === 'distribute-h' || mode === 'distribute-v') {
    // 筛选本页除页眉与底部横幅外的主体元件进行等距分布
    const bodyComps = slide.components.filter(c => c.type !== 'slide-header' && c.type !== 'footer-banner');
    if (bodyComps.length < 2) {
      showToast('当前页主体元件少于 2 个，无需等距分布');
      return;
    }
    if (mode === 'distribute-h') {
      bodyComps.sort((a, b) => a.x - b.x);
      const minX = bodyComps[0].x;
      const maxRight = Math.max(...bodyComps.map(c => c.x + c.w));
      const totalW = bodyComps.reduce((s, c) => s + c.w, 0);
      const gap = (maxRight - minX - totalW) / (bodyComps.length - 1);
      let curX = minX;
      bodyComps.forEach(c => {
        c.x = +curX.toFixed(1);
        syncChildrenGeometry(c);
        curX += c.w + gap;
      });
      showToast(`已完成 ${bodyComps.length} 个元件水平等距分布 (间距 ${gap.toFixed(1)}px)`);
    } else {
      bodyComps.sort((a, b) => a.y - b.y);
      const minY = bodyComps[0].y;
      const maxBottom = Math.max(...bodyComps.map(c => c.y + c.h));
      const totalH = bodyComps.reduce((s, c) => s + c.h, 0);
      const gap = (maxBottom - minY - totalH) / (bodyComps.length - 1);
      let curY = minY;
      bodyComps.forEach(c => {
        c.y = +curY.toFixed(1);
        syncChildrenGeometry(c);
        curY += c.h + gap;
      });
      showToast(`已完成 ${bodyComps.length} 个元件垂直等距分布 (间距 ${gap.toFixed(1)}px)`);
    }
    renderAll();
    return;
  }

  if (!comp) {
    showToast('请先在画布选中一个元件');
    return;
  }
  if (mode === 'left') comp.x = safeMarginX;
  if (mode === 'center-h') comp.x = +((cw - comp.w) / 2).toFixed(1);
  if (mode === 'right') comp.x = +(cw - safeMarginX - comp.w).toFixed(1);
  if (mode === 'top') comp.y = 144.0;
  if (mode === 'center-v') comp.y = +((ch - comp.h) / 2).toFixed(1);
  if (mode === 'bottom') comp.y = +(574.1 - comp.h).toFixed(1);

  syncChildrenGeometry(comp);
  renderAll();
}

function applyMacroThemePalette(themeKey, scope) {
  const pal = THEME_PALETTES[themeKey];
  if (!pal) return;
  const targetSlides = scope === 'deck' ? state.deck.slides : [getCurrentSlide()];
  const brandOldColors = new Set(['#1B365D', '#7A2048', '#2B5B84', '#F26B21', '#F26421', '#1E6CFF', '#7B32D9', '#0D9488', '#B45309', '#D97706']);
  const darkTextOld = new Set(['#1B365D', '#7A2048', '#D45500', '#DB5312', '#0F4CD6', '#5B18B2', '#0F766E', '#92400E']);
  const lightBgOld = new Set(['#F4F6F9', '#FDF2F5', '#FFF5EE', '#FFF2E6', '#FFF7F0', '#FFF7ED', '#FFF4EB', '#F0F5FF', '#EAF2FF', '#F7FBFF', '#F7F0FF', '#F3E8FF', '#F0FDFA', '#CCFBF1', '#FEF3C7', '#FFFBEB']);
  // 语义状态色护栏：保护 PASS 绿 / WARN 琥珀 / REJECT 红不被主题色替换
  const semanticProtected = new Set(['#16A34A', '#F0FDF4', '#15803D', '#2E7D32', '#F1F8F4', '#D97706', '#FFFBEB', '#B45309', '#DC2626', '#FEF2F2', '#B91C1C', '#C62828', '#FFF3F3']);

  targetSlides.forEach(s => {
    if (!s) return;
    s.components.forEach(c => {
      if (c.style) {
        if (brandOldColors.has((c.style.borderColor || '').toUpperCase())) c.style.borderColor = pal.border;
        if (brandOldColors.has((c.style.fill || '').toUpperCase())) c.style.fill = pal.primary;
        else if (lightBgOld.has((c.style.fill || '').toUpperCase())) c.style.fill = pal.lightBg;
        if (darkTextOld.has((c.style.titleColor || '').toUpperCase()) || brandOldColors.has((c.style.titleColor || '').toUpperCase())) {
          c.style.titleColor = pal.darkText;
        }
      }
      (c.children || []).forEach(ch => {
        if (ch.rawType === 'shape') {
          const f = (ch.fill || '').toUpperCase();
          const bc = (ch.borderColor || '').toUpperCase();
          if (!semanticProtected.has(f)) {
            if (brandOldColors.has(f)) ch.fill = pal.primary;
            else if (lightBgOld.has(f)) ch.fill = pal.lightBg;
          }
          if (!semanticProtected.has(bc) && brandOldColors.has(bc)) ch.borderColor = pal.border;
          if (ch.textBody && ch.textBody.paragraphs) {
            ch.textBody.paragraphs.forEach(p => {
              (p.runs || []).forEach(r => {
                const rc = (r.color || '').toUpperCase();
                if (semanticProtected.has(rc)) return;
                if (brandOldColors.has(rc)) r.color = pal.primary;
                else if (darkTextOld.has(rc)) r.color = pal.darkText;
              });
            });
          }
        } else if (ch.rawType === 'table' && ch.rows && ch.rows.length) {
          ch.rows[0].forEach(cell => {
            if (cell.fill) cell.fill = pal.primary;
          });
        }
      });
    });
  });

  renderAll();
  showToast(`已应用【${themeKey}】主题色板 (${scope === 'deck' ? '全文档' : '当前页'})`);
}

function scaleSlideFonts(deltaPt) {
  const slide = getCurrentSlide();
  if (!slide) return;
  slide.components.forEach(c => {
    if (c.style) {
      if (c.style.titleSize) c.style.titleSize = Math.max(8, +(c.style.titleSize + deltaPt).toFixed(1));
      if (c.style.bodySize) c.style.bodySize = Math.max(8, +(c.style.bodySize + deltaPt).toFixed(1));
    }
    (c.children || []).forEach(ch => {
      if (ch.textBody && ch.textBody.paragraphs) {
        ch.textBody.paragraphs.forEach(p => {
          (p.runs || []).forEach(r => {
            r.fontSize = Math.max(7, +((r.fontSize || 10) + deltaPt).toFixed(1));
          });
        });
      } else if (ch.rawType === 'table' && ch.rows) {
        ch.rows.forEach(row => row.forEach(cell => {
          cell.fontSize = Math.max(7, +((cell.fontSize || 10) + deltaPt).toFixed(1));
          cell.textBody = null;
        }));
      }
    });
  });
  renderAll();
  showToast(`当前页全部文字已 ${deltaPt > 0 ? '放大' : '缩小'} ${Math.abs(deltaPt)}pt`);
}

function moveCompLayer(dir) {
  const slide = getCurrentSlide();
  if (!slide || !state.selectedCompId) return;
  const idx = slide.components.findIndex(c => c.id === state.selectedCompId);
  if (idx < 0) return;
  const targetIdx = idx + dir;
  if (targetIdx < 0 || targetIdx >= slide.components.length) return;
  const [item] = slide.components.splice(idx, 1);
  slide.components.splice(targetIdx, 0, item);
  renderAll();
}

function deleteSelectedElement() {
  const slide = getCurrentSlide();
  const comp = getSelectedComponent();
  if (!slide || !comp) return;
  if (state.selectedChildId && comp.children.length > 1) {
    comp.children = comp.children.filter(ch => ch.id !== state.selectedChildId);
    state.selectedChildId = null;
    recomputeCompBoundsFromChildren(comp);
    renderAll();
    showToast('已删除元件内选中的子元素');
    return;
  }
  slide.components = slide.components.filter(c => c.id !== comp.id);
  state.selectedCompId = slide.components[0]?.id || null;
  state.selectedChildId = null;
  renderAll();
  showToast('已删除选中元件');
}

function setZoom(z) {
  state.zoom = Math.min(1.6, Math.max(0.4, +z.toFixed(2)));
  document.getElementById('zoomLabel').textContent = `${Math.round(state.zoom * 100)}%`;
  renderCanvas();
}

function fitCanvasToViewport() {
  const scroll = document.getElementById('canvasScroll');
  if (!scroll) return;
  const vw = scroll.clientWidth - 64;
  const vh = scroll.clientHeight - 64;
  const cw = state.deck?.canvas?.width || 1020.7;
  const ch = state.deck?.canvas?.height || 680.3;
  const scale = Math.min(vw / cw, vh / ch, 1.15);
  setZoom(Math.max(0.5, scale));
}

function updateStatusBar() {
  const slides = state.deck?.slides || [];
  document.getElementById('statusSlideInfo').textContent =
    `第 ${state.currentSlideIndex + 1} / ${slides.length} 页`;

  const comp = getSelectedComponent();
  const sub = getSelectedChild();
  const selInfo = document.getElementById('statusSelectionInfo');
  if (!comp) {
    selInfo.textContent = '未选中元件（点击画布任意元件可拖拽、缩放或调优）';
  } else if (sub) {
    selInfo.textContent = `当前选中：[子元素级] ${comp.name} → ${ROLE_LABELS[sub.role] || sub.rawType} (${sub.w}×${sub.h})`;
  } else {
    selInfo.textContent = `当前选中：[元件级] ${comp.name} [${comp.type}] (${comp.w}×${comp.h})`;
  }

  const badge = document.getElementById('statusSyncBadge');
  if (state.syncScope === 'single') {
    badge.className = 'sync-badge sync-single';
    badge.textContent = '样式作用范围：🎯 仅当前元件';
  } else if (state.syncScope === 'slide') {
    badge.className = 'sync-badge sync-slide';
    badge.textContent = '样式作用范围：📄 本页同类元件联动';
  } else {
    badge.className = 'sync-badge sync-deck';
    badge.textContent = '样式作用范围：🌐 全文档同类元件联动';
  }
}

function updateJsonDrawerIfOpen() {
  const drawer = document.getElementById('jsonDrawer');
  if (drawer.classList.contains('hidden')) return;
  const target = document.getElementById('jsonTargetSelect').value;
  const ta = document.getElementById('jsonEditor');
  if (target === 'component') {
    const comp = getSelectedComponent();
    ta.value = comp ? JSON.stringify(comp, null, 2) : '// 当前未选中元件';
  } else {
    const slide = getCurrentSlide();
    ta.value = slide ? JSON.stringify(slide, null, 2) : '// 无幻灯片数据';
  }
}

function applyJsonFromDrawer() {
  const target = document.getElementById('jsonTargetSelect').value;
  const ta = document.getElementById('jsonEditor');
  try {
    const parsed = JSON.parse(ta.value);
    const slide = getCurrentSlide();
    if (target === 'component' && slide && state.selectedCompId) {
      const idx = slide.components.findIndex(c => c.id === state.selectedCompId);
      if (idx >= 0) {
        slide.components[idx] = parsed;
        state.selectedCompId = parsed.id;
      }
    } else if (target === 'slide' && state.deck) {
      state.deck.slides[state.currentSlideIndex] = parsed;
    }
    renderAll();
    showToast('已将 Agent JSON 修改实时应用到画布！');
  } catch (err) {
    alert('JSON 格式有误：' + err.message);
  }
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
