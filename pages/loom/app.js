/**
 * 故事织机 - 前端 JavaScript
 * 通过 AstrBot Plugin Page 机制访问，API 路径为 /story_loom/api/...
 */

// ===== API 基础路径 =====
const API_BASE = '/story_loom/api';

// ===== 页面配置 =====
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
  name: '名称', title: '标题', aliases: '别称', age: '年龄', gender: '性别',
  personality: '性格', appearance: '外貌', background: '背景故事', goal: '目标/动机',
  abilities: '能力', relationships: '关系网', tags: '标签',
  description: '描述', type: '类型', faction: '所属势力', features: '特色',
  holder: '持有者', location: '所在地', lore: '传说',
  leader: '首领', members: '成员', base: '根据地', goals: '宗旨',
  time_point: '时间点', characters: '涉及角色', items: '涉及物品', importance: '重要程度',
  content: '内容', category: '分类', source: '来源', related_settings: '关联设定'
};

const FIELD_TYPES = {
  name: 'text', title: 'text', aliases: 'text', age: 'text', gender: 'select',
  personality: 'textarea', appearance: 'textarea', background: 'textarea',
  goal: 'textarea', abilities: 'textarea', relationships: 'textarea',
  tags: 'text', description: 'textarea', type: 'text', faction: 'text',
  features: 'textarea', holder: 'text', location: 'text', lore: 'textarea',
  leader: 'text', members: 'text', base: 'text', goals: 'textarea',
  time_point: 'text', characters: 'text', items: 'text', importance: 'select',
  content: 'textarea', category: 'text', source: 'select', related_settings: 'text'
};

const GENDER_OPTIONS = ['', '男', '女', '其他', '未知'];
const IMPORTANCE_OPTIONS = ['普通', '关键', '重要', '琐碎'];
const SOURCE_OPTIONS = ['', '梦境', '阅读', '观察', '对话', '其他', 'QQ消息', 'LLM对话'];

let currentPage = 'dashboard';
let editingItem = null;

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => navigateTo(item.dataset.page));
  });
  document.getElementById('globalSearch').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doGlobalSearch();
  });
  navigateTo('dashboard');
});

async function navigateTo(page) {
  currentPage = page;
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.page === page);
  });
  const content = document.getElementById('page-content');
  if (page === 'dashboard') await renderDashboard(content);
  else await renderListPage(content, page);
}

// ===== API 调用 =====
async function apiGet(collection, id = null) {
  const url = id ? `${API_BASE}/${collection}/${id}` : `${API_BASE}/${collection}`;
  const res = await fetch(url);
  return res.json();
}

async function apiPost(collection, data) {
  const res = await fetch(`${API_BASE}/${collection}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

async function apiPut(collection, id, data) {
  const res = await fetch(`${API_BASE}/${collection}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

async function apiDelete(collection, id) {
  const res = await fetch(`${API_BASE}/${collection}/${id}`, { method: 'DELETE' });
  return res.json();
}

// ===== 总览页面 =====
async function renderDashboard(container) {
  container.innerHTML = '<div class="loading">加载中</div>';
  const collections = ['characters','locations','items','factions','timeline','settings','inspirations'];
  const labels = ['角色','地点','物品','势力','事件','设定','灵感'];
  const icons = ['🎭','📍','⚔️','🏰','📅','📖','💡'];

  let stats = {};
  for (const coll of collections) {
    const res = await apiGet(coll);
    stats[coll] = res.data ? Object.keys(res.data).length : 0;
  }

  let html = `<div class="page-header"><h2>📊 总览</h2></div><div class="dashboard-grid">`;
  collections.forEach((coll, i) => {
    html += `<div class="stat-card" onclick="navigateTo('${coll}')" style="cursor:pointer">
      <div class="stat-number">${stats[coll]}</div>
      <div class="stat-label">${icons[i]} ${labels[i]}</div>
    </div>`;
  });
  html += '</div>';

  // 最近灵感
  const inspRes = await apiGet('inspirations');
  const inspirations = inspRes.data || {};
  const sorted = Object.entries(inspirations)
    .sort((a, b) => (b[1].created_at || '').localeCompare(a[1].created_at || ''))
    .slice(0, 5);

  if (sorted.length > 0) {
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

// ===== 列表页面 =====
async function renderListPage(container, collection) {
  const config = PAGES[collection];
  container.innerHTML = '<div class="loading">加载中</div>';
  const res = await apiGet(collection);
  const items = res.data || {};

  let html = `<div class="page-header">
    <h2>${config.icon} ${config.title}</h2>
    <button class="btn btn-primary" onclick="openEditor('${collection}')">＋ 新增</button>
  </div>`;

  if (Object.keys(items).length === 0) {
    html += `<div class="empty-state"><div class="icon">${config.icon}</div><p>暂无${config.title}</p></div>`;
    container.innerHTML = html;
    return;
  }

  html += '<div class="card-grid">';
  for (const [id, item] of Object.entries(items)) {
    const title = item.name || item.title || '未命名';
    const preview = item.description || item.content || item.background || item.personality || '';
    const tags = item.tags || '';
    html += `<div class="card" onclick="openEditor('${collection}','${id}')">
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
  editingItem = { collection, id };
  const config = PAGES[collection];

  // 如果是编辑，先获取数据
  if (id) {
    apiGet(collection, id).then(res => {
      const item = res.data || {};
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
    const label = FIELD_NAMES[field] || field;
    const type = FIELD_TYPES[field] || 'text';
    const value = item[field] || '';

    if (type === 'textarea') {
      html += `<div class="form-group"><label>${label}</label><textarea name="${field}" rows="3">${esc(value)}</textarea></div>`;
    } else if (type === 'select') {
      let options = [];
      if (field === 'gender') options = GENDER_OPTIONS;
      else if (field === 'importance') options = IMPORTANCE_OPTIONS;
      else if (field === 'source') options = SOURCE_OPTIONS;
      let selectHtml = `<select name="${field}">`;
      for (const opt of options) {
        selectHtml += `<option value="${opt}" ${value===opt?'selected':''}>${opt||'(空)'}</option>`;
      }
      selectHtml += '</select>';
      html += `<div class="form-group"><label>${label}</label>${selectHtml}</div>`;
    } else {
      html += `<div class="form-group"><label>${label}</label><input type="text" name="${field}" value="${esc(value)}" /></div>`;
    }
  }
  document.getElementById('modalBody').innerHTML = html;
}

function closeModal() {
  document.getElementById('modal').classList.add('hidden');
  editingItem = null;
}

async function saveModal() {
  const { collection, id } = editingItem;
  const inputs = document.querySelectorAll('#modalBody input, #modalBody textarea, #modalBody select');
  const data = {};
  inputs.forEach(input => { data[input.name] = input.value; });
  try {
    if (id) await apiPut(collection, id, data);
    else await apiPost(collection, data);
    closeModal();
    navigateTo(currentPage);
  } catch (e) {
    alert('保存失败: ' + e.message);
  }
}

async function deleteCurrentItem() {
  if (!editingItem || !editingItem.id) return;
  if (!confirm('确定要删除吗？此操作不可撤销。')) return;
  try {
    await apiDelete(editingItem.collection, editingItem.id);
    closeModal();
    navigateTo(currentPage);
  } catch (e) {
    alert('删除失败: ' + e.message);
  }
}

// ===== 搜索 =====
async function doGlobalSearch() {
  const keyword = document.getElementById('globalSearch').value.trim();
  if (!keyword) return;
  const content = document.getElementById('page-content');
  content.innerHTML = '<div class="loading">搜索中</div>';

  const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(keyword)}`);
  const result = await res.json();

  if (!result.ok || !result.data || Object.keys(result.data).length === 0) {
    content.innerHTML = `<div class="page-header"><h2>🔍 搜索结果</h2></div>
      <div class="empty-state"><div class="icon">🔍</div><p>未找到与「${esc(keyword)}」相关的内容</p></div>`;
    return;
  }

  const nameMap = {
    characters: '🎭 角色', locations: '📍 地点', items: '⚔️ 物品',
    factions: '🏰 势力', timeline: '📅 事件', settings: '📖 设定', inspirations: '💡 灵感'
  };

  let html = `<div class="page-header"><h2>🔍 搜索「${esc(keyword)}」</h2></div>`;
  for (const [coll, items] of Object.entries(result.data)) {
    html += `<div class="search-section"><h3>${nameMap[coll]||coll} (${Object.keys(items).length})</h3>`;
    for (const [id, item] of Object.entries(items)) {
      const title = item.name || item.title || '未命名';
      html += `<div class="search-item" onclick="openEditor('${coll}','${id}')">${esc(title)}</div>`;
    }
    html += '</div>';
  }
  content.innerHTML = html;
}

// ===== 工具函数 =====
function esc(str) { if (!str) return ''; return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function fmtTime(iso) { if (!iso) return ''; try { const d=new Date(iso); return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`; } catch { return iso.slice(0,10); } }
