const fileInput = document.getElementById('fileInput');
const uploadDrop = document.getElementById('uploadDrop');
const uploadBtn = document.getElementById('uploadBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const refreshBtn = document.getElementById('refreshBtn');
const docList = document.getElementById('docList');
const historyList = document.getElementById('historyList');
const pageTitle = document.getElementById('pageTitle');
const healthText = document.getElementById('healthText');
const chatInner = document.getElementById('chatInner');
const emptyState = document.getElementById('emptyState');
const summaryBtn = document.getElementById('summaryBtn');
const questionInput = document.getElementById('questionInput');
const askBtn = document.getElementById('askBtn');
const statusText = document.getElementById('statusText');
const docFilterPill = document.getElementById('docFilterPill');
const docFilterText = document.getElementById('docFilterText');
const clearDocFilterBtn = document.getElementById('clearDocFilterBtn');

let documents = [];
let selectedDocumentId = '';

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function setStatus(text = '') {
  statusText.textContent = text;
}

function getSelectedDocument() {
  return documents.find((doc) => doc.id === selectedDocumentId) || null;
}

function updateHeader() {
  const selected = getSelectedDocument();
  pageTitle.textContent = selected ? selected.file_name : '新建对话';
  if (selected) {
    docFilterPill.classList.remove('hidden');
    docFilterText.textContent = `当前文档：${selected.file_name}`;
  } else {
    docFilterPill.classList.add('hidden');
    docFilterText.textContent = '';
  }
}

function updateUploadPreview() {
  const file = fileInput.files?.[0];
  if (!file) {
    uploadDrop.classList.remove('has-file');
    uploadDrop.innerHTML = `
      <div>
        <strong>上传 PDF / Markdown</strong>
        选择文件后点击“处理文档”
      </div>
    `;
    return;
  }

  uploadDrop.classList.add('has-file');
  uploadDrop.innerHTML = `
    <div>
      <strong>${escapeHtml(file.name)}</strong>
      ${escapeHtml(file.type || 'PDF / Markdown')}
    </div>
  `;
}

function autoResizeTextarea() {
  questionInput.style.height = '0px';
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 220)}px`;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error?.message || data?.detail || data?.message || '请求失败');
  }
  return data;
}

function clearChatUI() {
  chatInner.innerHTML = `
    <div class="empty-state" id="emptyState">
      上传文档后开始提问。<br>
      如果左侧选中了文档，本轮提问会优先在当前文档内回答。
    </div>
  `;
}

function renderDocuments() {
  docList.innerHTML = '';

  if (!documents.length) {
    docList.innerHTML = '<div class="item-meta">当前没有文档</div>';
    updateHeader();
    return;
  }

  documents.forEach((doc) => {
    const item = document.createElement('div');
    item.className = `doc-item${doc.id === selectedDocumentId ? ' active' : ''}`;
    item.innerHTML = `
      <div class="item-title">${escapeHtml(doc.file_name)}</div>
      <div class="item-meta">${doc.chunks} 个文档块</div>
      <button class="doc-delete" type="button" data-doc-id="${escapeHtml(doc.id)}" title="删除文档">×</button>
    `;
    item.addEventListener('click', () => {
      selectedDocumentId = doc.id;
      renderDocuments();
    });

    const deleteBtn = item.querySelector('.doc-delete');
    deleteBtn.addEventListener('click', async (event) => {
      event.stopPropagation();
      selectedDocumentId = doc.id;
      renderDocuments();
      try {
        await deleteSelectedDocument();
      } catch (error) {
        setStatus(error.message);
      }
    });

    docList.appendChild(item);
  });

  updateHeader();
}

function renderHistory(history) {
  historyList.innerHTML = '';
  if (!history.length) {
    historyList.innerHTML = '<div class="item-meta">暂无历史记录</div>';
    return;
  }

  history
    .slice(-10)
    .forEach((entry) => {
      const item = document.createElement('div');
      item.className = 'history-item';
      item.innerHTML = `
        <div class="item-title">${escapeHtml(entry.content).slice(0, 36) || '空消息'}</div>
        <div class="item-meta">${escapeHtml(entry.role)} · ${escapeHtml(entry.timestamp || '')}</div>
      `;
      historyList.appendChild(item);
    });
}

function appendMessage(role, text, citations = []) {
  const currentEmpty = document.getElementById('emptyState');
  if (currentEmpty) {
    currentEmpty.remove();
  }

  const message = document.createElement('div');
  message.className = `message ${role}`;
  message.innerHTML = `
    <div class="message-meta">
      <div class="avatar">${role === 'user' ? 'U' : 'AI'}</div>
      <div>${role === 'user' ? '你' : 'RAG 助手'}</div>
    </div>
    <div class="bubble">${escapeHtml(text)}</div>
  `;

  if (citations.length) {
    const citationsWrap = document.createElement('div');
    citationsWrap.className = 'citations';
    const citationList = document.createElement('div');
    citationList.className = 'citation-list';

    const toggle = document.createElement('button');
    toggle.className = 'citation-toggle';
    toggle.type = 'button';
    toggle.textContent = `引用文档 (${citations.length})`;
    toggle.addEventListener('click', () => {
      citationList.classList.toggle('open');
      toggle.textContent = citationList.classList.contains('open')
        ? `隐藏引用 (${citations.length})`
        : `引用文档 (${citations.length})`;
    });

    citationsWrap.appendChild(toggle);

    citations.forEach((citation) => {
      const item = document.createElement('div');
      item.className = 'citation';
      item.innerHTML = `
        <div class="citation-title">${escapeHtml(citation.source)}</div>
        <div class="citation-meta">页码: ${escapeHtml(citation.page)} · 分数: ${escapeHtml(citation.score)}</div>
        <div>${escapeHtml(citation.text)}</div>
      `;
      citationList.appendChild(item);
    });

    citationsWrap.appendChild(citationList);
    message.appendChild(citationsWrap);
  }

  chatInner.appendChild(message);
  chatInner.parentElement.scrollTop = chatInner.parentElement.scrollHeight;
}

async function loadHealth() {
  try {
    const health = await fetchJson('/api/v1/health');
    healthText.textContent = `状态: ${health.status} · 文档块: ${health.document_count} · 文档数: ${health.saved_documents}`;
  } catch (error) {
    healthText.textContent = error.message;
  }
}

async function loadDocuments() {
  const data = await fetchJson('/api/v1/documents');
  documents = data.documents || [];
  if (!documents.find((doc) => doc.id === selectedDocumentId)) {
    selectedDocumentId = '';
  }
  renderDocuments();
}

async function loadHistory() {
  try {
    const data = await fetchJson('/api/v1/chat/all');
    renderHistory(data.history || []);
  } catch (error) {
    historyList.innerHTML = `<div class="item-meta">${escapeHtml(error.message)}</div>`;
  }
}

async function uploadDocument() {
  const file = fileInput.files?.[0];
  if (!file) {
    setStatus('请先选择文件。');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  setStatus('上传处理中...');
  const response = await fetch('/api/v1/upload', { method: 'POST', body: formData });
  const data = await response.json();
  if (!response.ok || !data.success) {
    throw new Error(data?.message || data?.error?.message || '上传失败');
  }

  selectedDocumentId = data.document_id || selectedDocumentId;
  await Promise.all([loadDocuments(), loadHealth()]);
  setStatus(data.message || '上传成功');
}

async function askQuestion() {
  const question = questionInput.value.trim();
  if (!question) {
    setStatus('请输入问题。');
    return;
  }

  appendMessage('user', question);
  questionInput.value = '';
  autoResizeTextarea();
  setStatus('思考中...');

  const payload = { question };
  if (selectedDocumentId) {
    payload.document_id = selectedDocumentId;
  }

  const result = await fetchJson('/api/v1/ask', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  appendMessage('assistant', result.answer || '没有返回内容', result.citations || []);
  setStatus('');
  await loadHistory();
}

async function summarizeSelectedDocument() {
  const selected = getSelectedDocument();
  if (!selected) {
    setStatus('请先在左侧选择一份文档。');
    return;
  }

  setStatus('总结文档中...');
  const result = await fetchJson(`/api/v1/documents/${selected.id}/summary`);
  appendMessage('assistant', result.answer || '没有返回内容', result.citations || []);
  setStatus('');
  await loadHistory();
}

async function deleteSelectedDocument() {
  const selected = getSelectedDocument();
  if (!selected) {
    setStatus('请先在左侧选择一份文档。');
    return;
  }

  setStatus('删除文档中...');
  const result = await fetchJson(`/api/v1/documents/${selected.id}`, { method: 'DELETE' });
  selectedDocumentId = '';
  clearChatUI();
  await Promise.all([loadDocuments(), loadHealth(), loadHistory()]);
  setStatus(result.message || '删除成功');
}

async function clearChatHistory() {
  await fetchJson('/api/v1/chat', { method: 'DELETE' });
  clearChatUI();
  await loadHistory();
  setStatus('聊天记录已清空。');
}

fileInput.addEventListener('change', updateUploadPreview);
questionInput.addEventListener('input', autoResizeTextarea);
questionInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    askQuestion().catch((error) => setStatus(error.message));
  }
});

uploadBtn.addEventListener('click', () => uploadDocument().catch((error) => setStatus(error.message)));
clearChatBtn.addEventListener('click', () => clearChatHistory().catch((error) => setStatus(error.message)));
refreshBtn.addEventListener('click', () => {
  Promise.all([loadDocuments(), loadHistory(), loadHealth()]).catch((error) => setStatus(error.message));
});
summaryBtn.addEventListener('click', () => summarizeSelectedDocument().catch((error) => setStatus(error.message)));
askBtn.addEventListener('click', () => askQuestion().catch((error) => setStatus(error.message)));
clearDocFilterBtn.addEventListener('click', () => {
  selectedDocumentId = '';
  renderDocuments();
});

updateUploadPreview();
autoResizeTextarea();
Promise.all([loadDocuments(), loadHistory(), loadHealth()]).catch((error) => setStatus(error.message));
