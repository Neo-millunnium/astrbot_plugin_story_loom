/**
 * 故事织机 - 前端 JavaScript
 */

// ===== API 基础路径 =====
const API_BASE = "/api/plug/story_loom/api";

// ===== 页面配置 =====
const TYPES = {
  character: { label: '角色', icon: '🎭', color: '#3b82f6' },
  location: { label: '地点', icon: '📍', color: '#10b981' },
  item: { label: '物品', icon: '⚔️', color: '#f59e0b' },
  faction: { label: '势力', icon: '🏰', color: '#8b5cf6' },
  event: { label: '事件', icon: '📅', color: '#ef4444' },
  setting: { label: '设定', icon: '📖', color: '#64748b' },
  inspiration: { label: '灵感', icon: '💡', color: '#ec4899' },
};

const FIELDS = {
  character: ['name','aliases','gender','age','personality','appearance','background','goal','abilities','relationships','tags'],
  location: ['name','description','type','faction','features','tags'],
  item: ['name','description','type','holder','location','lore','tags'],
  faction: ['name','description','leader','members','base','goals','tags'],
  event: ['name','time_point','description','characters','locations','items','importance','tags'],
  setting: ['title','content','category','tags'],
  inspiration: ['title','content','tags','source','related_settings'],
};

const LABELS = {
  name:'名称', title:'标题', aliases:'别称', age:'年龄', gender:'性别',
  personality:'性格', appearance:'外貌', background:'背景故事', goal:'目标/动机',
  abilities:'能力', relationships:'关系网', tags:'标签',
  description:'描述', type:'类型', faction:'所属势力', features:'特色',
  holder:'持有者', location:'所在地', lore:'传说',
  leader:'首领', members:'成员', base:'根据地', goals:'宗旨',
  time_point:'时间点', characters:'涉及角色', items:'涉及物品', importance:'重要程度',
  content:'内容', category:'分类', source:'来源', related_settings:'关联设定'
};

const TYPES_SELECT = {
  gender: ['', '男', '女', '其他', '未知'],
  importance: ['普通', '关键', '重要', '琐碎'],
  source: ['', '梦境', '阅读', '观察', '对话', '其他', 'QQ消息', 'LLM对话'],
};

let currentPage = 'dashboard';
let editingItem = null;
let network = null;

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.addEventListener('click', () => navigateTo(el.dataset.page));
  });
  document.getElementById('globalSearch').addEventListener('keydown', e => {
    if (e.key === 'Enter') doGlobalSearch();
  });
  navigateTo('dashboard');
});

async function navigateTo(page) {
  currentPage = page;
  document.querySelectorAll('.nav-item').forEach(el => el.classList.toggle('active', el.dataset.page === page));
  const c = document.getElementById('page-content');
  if (page === 'dashboard') await renderDashboard(c);
  else if (page === 'graph') await renderGraph(c);
  else await renderListPage(c, page);
}

// ===== API 调用 =====
async function apiGet(url) { const r = await fetch(url); return r.json(); }
async function apiPost(url, data) {
  const r = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) });
  return r.json();
}

// ===== 总览页面 =====
async function renderDashboard(container) {
  container.innerHTML = '<div class="loading">加载中</div>';
  const types = Object.keys(TYPES);
  let stats = {};
  for (const t of types) {
    const r = await apiGet(`${API_BASE}/${t}s`);
    stats[t] = r.data ? Object.keys(r.data).length : 0;
  }
  let total = Object.values(stats).reduce((a,b)=>a+b,0);
  let html = `<div class="page-header"><h2>📊 总览</h2></div>
    <div style="margin-bottom:20px">总计 <strong>${total}</strong> 个元素</div>
    <div class="dashboard-grid">`;
  for (const t of types) {
    const cfg = TYPES[t];
    html += `<div class="stat-card" onclick="navigateTo('${t}s')" style="cursor:pointer;border-left:4px solid ${cfg.color}">
      <div class="stat-number" style="color:${cfg.color}">${stats[t]}</div>
      <div class="stat-label">${cfg.icon} ${cfg.label}</div>
    </div>`;
  }
  html += '</div>';

  // 最近灵感
  const ir = await apiGet(`${API_BASE}/inspirations`);
  const sorted = Object.entries(ir.data||{}).sort((a,b)=>(b[1].updated_at||b[1].created_at||'').localeCompare(a[1].updated_at||a[1].created_at||'')).slice(0,5);
  if (sorted.length) {
    html += '<h3 style="margin:24px 0 12px">💡 最近的灵感</h3><div class="inspiration-board">';
    for (const [id, insp] of sorted) {
      html += `<div class="inspiration-card" onclick="openEditor('inspirations','${id}')">
        <div class="card-title">${esc(insp.title||'未命名')}</div>
        <div class="card-body">${esc((insp.content||'').slice(0,100))}</div>
        <div class="card-meta"><span class="inspiration-source">${esc(insp.source||'')}</span><span>${fmtTime(insp.created_at)}</span></div>
      </div>`;
    }
    html += '</div>';
  }
  container.innerHTML = html;
}

// ===== 关系图谱 =====
async function renderGraph(container) {
  container.innerHTML = `
    <div class="page-header">
      <h2>🕸️ 关系图谱</h2>
      <span style="color:#64748b; font-size:0.875rem">所有元素网状关系展示</span>
    </div>
    <div id="vis-network" class="graph-container"></div>
  `;
  const gdata = await apiGet(`${API_BASE}/graph`);
  if (!gdata.ok || !gdata.data) {
    container.innerHTML += '<p style="color:#64748b; padding:20px">暂无元素</p>';
    return;
  }
  const {nodes, edges} = gdata.data;
  const visNodes = new vis.DataSet(
    nodes.map(n => ({
      id: n.id,
      label: n.label,
      group: n.type,
      color: { background: TYPES[n.type].color, border: TYPES[n.type].color, highlight: { background: TYPES[n.type].color, border: '#000' }}
    }))
  );
  const visEdges = new vis.DataSet(
    edges.map(e => ({
      id: e.id,
      from: e.from,
      to: e.to,
      label: e.label || '',
      value: e.value || 1,
    }))
  );
  const options = {
    nodes: { shape: 'box', font: { color: '#fff', face: 'Segoe UI' } },
    edges: { arrows: { to: { enabled: false } }, color: { color: '#ccc' } },
    physics: { stabilization: true },
    interaction: { tooltipDelay: 300 },
  };
  const containerVis = document.getElementById('vis-network');
  network = new vis.Network(containerVis, {nodes: visNodes, edges: visEdges}, options);
  network.on('click', function (params) {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      const node = nodes.find(n => n.id === nodeId);
      if (node) openEditor(node.type + 's', nodeId);
    }
  });
}

// ===== 列表页面 =====
async function renderListPage(container, collection) {
  const type = collection.replace(/s$/, '');
  const cfg = TYPES[type];
  container.innerHTML = '<div class="loading">加载中</div>';
  const r = await apiGet(`${API_BASE}/${collection}`);
  const items = r.data || {};
  let html = `<div class="page-header">
    <h2>${cfg.icon} ${cfg.label}</h2>
    <button class="btn btn-primary" onclick="openEditor('${collection}')">＋ 新增</button>
  </div>`;
  if (!Object.keys(items).length) {
    html += `<div class="empty-state"><div class="icon">${cfg.icon}</div><p>暂无${cfg.label}</p></div>`;
    container.innerHTML = html;
    return;
  }
  html += '<div class="card-grid">';
  for (const [id,item] of Object.entries(items)) {
    const title = item.name||item.title||'未命名';
    const preview = item.description||item.content||item.background||item.personality||'';
    const tags = item.tags||'';
    html += `<div class="card" onclick="openEditor('${collection}','${id}')" style="border-left:4px solid ${cfg.color}">
      <div class="card-title">${esc(title)}</div>
      <div class="card-body">${esc(preview.slice(0,120))}</div>
      <div class="card-meta">
        ${tags ? `<span class="card-tag">${esc(tags.split(',')[0])}</span>` : ''}
        <span>${fmtTime(item.updated_at||item.created_at)}</span>
      </div>
    </div>`;
  }
  html += '</div>';
  container.innerHTML = html;
}

// ===== 编辑器弹窗 =====
function openEditor(collection, id = null) {
  const type = collection.replace(/s$/, '');
  editingItem = { collection, id, type };
  const cfg = TYPES[type];

  if (id) {
    apiGet(`${API_BASE}/${collection}/${id}`).then(res => {
      const item = res.data || {};
      document.getElementById('modalTitle').textContent = `编辑${cfg.label}`;
      renderForm(type, item);
      document.getElementById('deleteBtn').style.display = 'inline-block';
      document.getElementById('modal').classList.remove('hidden');
    });
  } else {
    document.getElementById('modalTitle').textContent = `新增${cfg.label}`;
    renderForm(type, {});
    document.getElementById('deleteBtn').style.display = 'none';
    document.getElementById('modal').classList.remove('hidden');
  }
}

function renderForm(type, item) {
  let html = '';
  for (const field of FIELDS[type]) {
    const label = LABELS[field] || field;
    if (field in TYPES_SELECT) {
      let opts = TYPES_SELECT[field];
      let select = `<select name="${field}">`;
      for (const o of opts) {
        select += `<option value="${o}" ${item[field]===o?'selected':''}>${o||'(空)'}</option>`;
      }
      select += '</select>';
      html += `<div class="form-group"><label>${label}</label>${select}</div>`;
    } else if (['description','content','background','personality'].includes(field)) {
      html += `<div class="form-group"><label>${label}</label><textarea name="${field}" rows="4">${esc(item[field]||'')}</textarea></div>`;
    } else {
      html += `<div class="form-group"><label>${label}</label><input type="text" name="${field}" value="${esc(item[field]||'')}" /></div>`;
    }
  }
  document.getElementById('modalBody').innerHTML = html;
}

function closeModal() { document.getElementById('modal').classList.add('hidden'); editingItem=null; }

async function saveModal() {
  const { collection, id, type } = editingItem;
  const inputs = document.querySelectorAll('#modalBody input, #modalBody textarea, #modalBody select');
  const data = { _collection: collection };
  if (id) data._id = id;
  inputs.forEach(i => { data[i.name] = i.value; });
  try {
    await apiPost(`${API_BASE}/save`, data);
    closeModal();
    if (currentPage === 'graph') renderGraph(document.getElementById('page-content'));
    else navigateTo(currentPage);
  } catch(e) { alert('保存失败: '+e.message); }
}

async function deleteCurrentItem() {
  if (!editingItem||!editingItem.id) return;
  if (!confirm('确定删除？此操作不可撤销。')) return;
  try {
    await apiPost(`${API_BASE}/delete`, { _collection: editingItem.collection, _id: editingItem.id });
    closeModal();
    if (currentPage === 'graph') renderGraph(document.getElementById('page-content'));
    else navigateTo(currentPage);
  } catch(e) { alert('删除失败: '+e.message); }
}

// ===== 搜索 =====
async function doGlobalSearch() {
  const kw = document.getElementById('globalSearch').value.trim();
  if (!kw) return;
  const c = document.getElementById('page-content');
  c.innerHTML = '<div class="loading">搜索中</div>';
  const r = await apiGet(`${API_BASE}/search?q=${encodeURIComponent(kw)}`);
  if (!r.ok||!r.data||!Object.keys(r.data).length) {
    c.innerHTML = `<div class="page-header"><h2>🔍 搜索结果</h2></div>
      <div class="empty-state"><div class="icon">🔍</div><p>未找到与「${esc(kw)}」相关的内容</p></div>`;
    return;
  }
  let html = `<div class="page-header"><h2>🔍 搜索「${esc(kw)}」</h2></div>`;
  for (const [coll, items] of Object.entries(r.data)) {
    const type = coll.replace(/s$/, '');
    const cfg = TYPES[type];
    html += `<div class="search-section"><h3>${cfg.icon} ${cfg.label} (${Object.keys(items).length})</h3>`;
    for (const [id,item] of Object.entries(items)) {
      const title = item.name||item.title||'未命名';
      html += `<div class="search-item" onclick="openEditor('${coll}','${id}')">${esc(title)}</div>`;
    }
    html += '</div>';
  }
  c.innerHTML = html;
}

// ===== 工具函数 =====
function esc(s) { if (!s) return ''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function fmtTime(iso) { if (!iso) return ''; try { const d=new Date(iso); return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`; } catch { return iso.slice(0,10); } }
