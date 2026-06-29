/**
 * 故事织机 - 前端 JavaScript
 * API 通过 /api/plug/story_loom/api/ 访问（仅 GET/POST）
 */

const API_BASE = "/api/plug/story_loom/api";

const PAGES = {
  dashboard: { title: '总览', icon: '📊' },
  characters: { title: '角色', icon: '🎭', fields: ['name','aliases','gender','age','personality','appearance','background','goal','abilities','relationships','tags'] },
  locations: { title: '地点', icon: '📍', fields: ['name','description','type','faction','features','tags'] },
  items: { title: '物品', icon: '⚔️', fields: ['name','description','type','holder','location','lore','tags'] },
  factions: { title: '势力', icon: '🏰', fields: ['name','description','leader','members','base','goals','tags'] },
  timeline: { title: '时间线', icon: '📅', fields: ['name','time_point','description','characters','locations','items','importance','tags'] },
  settings: { title: '设定', icon: '📖', fields: ['title','content','category','tags'] },
  inspirations: { title: '灵感', icon: '💡', fields: ['title','content','tags','source','related_settings'] }
};

const FIELD_NAMES = {
  name:'名称',title:'标题',aliases:'别称',age:'年龄',gender:'性别',
  personality:'性格',appearance:'外貌',background:'背景故事',goal:'目标/动机',
  abilities:'能力',relationships:'关系网',tags:'标签',
  description:'描述',type:'类型',faction:'所属势力',features:'特色',
  holder:'持有者',location:'所在地',lore:'传说',
  leader:'首领',members:'成员',base:'根据地',goals:'宗旨',
  time_point:'时间点',characters:'涉及角色',items:'涉及物品',importance:'重要程度',
  content:'内容',category:'分类',source:'来源',related_settings:'关联设定'
};

const FIELD_TYPES = {
  name:'text',title:'text',aliases:'text',age:'text',gender:'select',
  personality:'textarea',appearance:'textarea',background:'textarea',
  goal:'textarea',abilities:'textarea',relationships:'textarea',
  tags:'text',description:'textarea',type:'text',faction:'text',
  features:'textarea',holder:'text',location:'text',lore:'textarea',
  leader:'text',members:'text',base:'text',goals:'textarea',
  time_point:'text',characters:'text',items:'text',importance:'select',
  content:'textarea',category:'text',source:'select',related_settings:'text'
};

const GENDER_OPTIONS = ['','男','女','其他','未知'];
const IMPORTANCE_OPTIONS = ['普通','关键','重要','琐碎'];
const SOURCE_OPTIONS = ['','梦境','阅读','观察','对话','其他','QQ消息','LLM对话'];

let currentPage = 'dashboard';
let editingItem = null;

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
  else await renderListPage(c, page);
}

// ===== API =====
async function apiGet(url) { const r = await fetch(url); return r.json(); }
async function apiPost(url, data) {
  const r = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) });
  return r.json();
}

// ===== 总览 =====
async function renderDashboard(container) {
  container.innerHTML = '<div class="loading">加载中</div>';
  const cols = ['characters','locations','items','factions','timeline','settings','inspirations'];
  const labels = ['角色','地点','物品','势力','事件','设定','灵感'];
  const icons = ['🎭','📍','⚔️','🏰','📅','📖','💡'];
  let stats = {};
  for (const c of cols) { const r = await apiGet(`${API_BASE}/${c}`); stats[c] = r.data ? Object.keys(r.data).length : 0; }
  let html = '<div class="page-header"><h2>📊 总览</h2></div><div class="dashboard-grid">';
  cols.forEach((c,i) => { html += `<div class="stat-card" onclick="navigateTo('${c}')" style="cursor:pointer"><div class="stat-number">${stats[c]}</div><div class="stat-label">${icons[i]} ${labels[i]}</div></div>`; });
  html += '</div>';
  const ir = await apiGet(`${API_BASE}/inspirations`);
  const sorted = Object.entries(ir.data||{}).sort((a,b)=>(b[1].created_at||'').localeCompare(a[1].created_at||'')).slice(0,5);
  if (sorted.length) {
    html += '<h3 style="margin:24px 0 12px">💡 最近的灵感</h3><div class="inspiration-board">';
    for (const [id,insp] of sorted) {
      html += `<div class="inspiration-card" onclick="openEditor('inspirations','${id}')"><div class="card-title">${esc(insp.title||'未命名')}</div><div class="card-body">${esc((insp.content||'').slice(0,100))}</div><div class="card-meta"><span class="inspiration-source">${esc(insp.source||'')}</span><span>${fmtTime(insp.created_at)}</span></div></div>`;
    }
    html += '</div>';
  }
  container.innerHTML = html;
}

// ===== 列表 =====
async function renderListPage(container, collection) {
  const config = PAGES[collection];
  container.innerHTML = '<div class="loading">加载中</div>';
  const r = await apiGet(`${API_BASE}/${collection}`);
  const items = r.data || {};
  let html = `<div class="page-header"><h2>${config.icon} ${config.title}</h2><button class="btn btn-primary" onclick="openEditor('${collection}')">＋ 新增</button></div>`;
  if (!Object.keys(items).length) {
    html += `<div class="empty-state"><div class="icon">${config.icon}</div><p>暂无${config.title}</p></div>`;
    container.innerHTML = html; return;
  }
  html += '<div class="card-grid">';
  for (const [id,item] of Object.entries(items)) {
    const title = item.name||item.title||'未命名';
    const preview = item.description||item.content||item.background||item.personality||'';
    const tags = item.tags||'';
    html += `<div class="card" onclick="openEditor('${collection}','${id}')"><div class="card-title">${esc(title)}</div><div class="card-body">${esc(preview.slice(0,120))}</div><div class="card-meta">${tags?`<span class="card-tag">${esc(tags.split(',')[0])}</span>`:''}<span>${fmtTime(item.updated_at||item.created_at)}</span></div></div>`;
  }
  html += '</div>';
  container.innerHTML = html;
}

// ===== 编辑器 =====
function openEditor(collection, id) {
  editingItem = { collection, id };
  const config = PAGES[collection];
  if (id) {
    apiGet(`${API_BASE}/${collection}/${id}`).then(res => {
      const item = res.data||{};
      document.getElementById('modalTitle').textContent = `编辑${config.title}`;
      renderForm(config, item);
      document.getElementById('deleteBtn').style.display = 'inline-block';
      document.getElementById('modal').classList.remove('hidden');
    });
  } else {
    document.getElementById('modalTitle').textContent = `新增${config.title}`;
    renderForm(config, {});
    document.getElementById('deleteBtn').style.display = 'none';
    document.getElementById('modal').classList.remove('hidden');
  }
}

function renderForm(config, item) {
  let html = '';
  for (const field of config.fields) {
    const label = FIELD_NAMES[field]||field;
    const type = FIELD_TYPES[field]||'text';
    const value = item[field]||'';
    if (type === 'textarea') {
      html += `<div class="form-group"><label>${label}</label><textarea name="${field}" rows="3">${esc(value)}</textarea></div>`;
    } else if (type === 'select') {
      let opts = []; if (field==='gender') opts=GENDER_OPTIONS; else if (field==='importance') opts=IMPORTANCE_OPTIONS; else if (field==='source') opts=SOURCE_OPTIONS;
      let s = `<select name="${field}">`; for (const o of opts) s+=`<option value="${o}" ${value===o?'selected':''}>${o||'(空)'}</option>`; s+='</select>';
      html += `<div class="form-group"><label>${label}</label>${s}</div>`;
    } else {
      html += `<div class="form-group"><label>${label}</label><input type="text" name="${field}" value="${esc(value)}" /></div>`;
    }
  }
  document.getElementById('modalBody').innerHTML = html;
}

function closeModal() { document.getElementById('modal').classList.add('hidden'); editingItem=null; }

async function saveModal() {
  const { collection, id } = editingItem;
  const inputs = document.querySelectorAll('#modalBody input, #modalBody textarea, #modalBody select');
  const data = { _collection: collection };
  if (id) data._id = id;
  inputs.forEach(i => { data[i.name] = i.value; });
  try {
    await apiPost(`${API_BASE}/save`, data);
    closeModal();
    navigateTo(currentPage);
  } catch(e) { alert('保存失败: '+e.message); }
}

async function deleteCurrentItem() {
  if (!editingItem||!editingItem.id) return;
  if (!confirm('确定删除？不可撤销。')) return;
  try {
    await apiPost(`${API_BASE}/delete`, { _collection: editingItem.collection, _id: editingItem.id });
    closeModal();
    navigateTo(currentPage);
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
    c.innerHTML = `<div class="page-header"><h2>🔍 搜索结果</h2></div><div class="empty-state"><div class="icon">🔍</div><p>未找到与「${esc(kw)}」相关的内容</p></div>`; return;
  }
  const nm = { characters:'🎭 角色', locations:'📍 地点', items:'⚔️ 物品', factions:'🏰 势力', timeline:'📅 事件', settings:'📖 设定', inspirations:'💡 灵感' };
  let html = `<div class="page-header"><h2>🔍 搜索「${esc(kw)}」</h2></div>`;
  for (const [coll,items] of Object.entries(r.data)) {
    html += `<div class="search-section"><h3>${nm[coll]||coll} (${Object.keys(items).length})</h3>`;
    for (const [id,item] of Object.entries(items)) {
      const t = item.name||item.title||'未命名';
      html += `<div class="search-item" onclick="openEditor('${coll}','${id}')">${esc(t)}</div>`;
    }
    html += '</div>';
  }
  c.innerHTML = html;
}

function esc(s) { if(!s)return ''; return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function fmtTime(iso) { if(!iso)return ''; try{const d=new Date(iso);return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`;}catch{return iso.slice(0,10);} }
