document.addEventListener('DOMContentLoaded', () => {
  // Automatically clean up any leftover legacy query parameters from the browser address bar
  if (window.location.search) {
    window.history.replaceState({}, document.title, window.location.pathname);
  }

  const chatForm = document.getElementById('chatForm');
  const endpointInput = document.getElementById('endpointInput');
  const scenarioInput = document.getElementById('scenarioInput');
  const sendBtn = document.getElementById('sendBtn');
  const chatStream = document.getElementById('chatStream');

  const historyDrawer = document.getElementById('historyDrawer');
  const toggleHistoryBtn = document.getElementById('toggleHistoryBtn');
  const closeHistoryBtn = document.getElementById('closeHistoryBtn');
  const historyContainer = document.getElementById('historyContainer');

  let activeRawDataStore = {};

  // Global Event Delegation for Sample Presets (Works infinitely for all static & dynamic buttons)
  document.addEventListener('click', (e) => {
    const presetBtn = e.target.closest('.sample-preset');
    if (presetBtn) {
      const url = presetBtn.getAttribute('data-url');
      const desc = presetBtn.getAttribute('data-desc');
      if (url) endpointInput.value = url;
      if (desc) scenarioInput.value = desc;
      scenarioInput.focus();
    }
  });

  // History Drawer Toggle
  if (toggleHistoryBtn) {
    toggleHistoryBtn.addEventListener('click', () => {
      historyDrawer.classList.remove('hidden');
      loadHistory();
    });
  }

  if (closeHistoryBtn) {
    closeHistoryBtn.addEventListener('click', () => {
      historyDrawer.classList.add('hidden');
    });
  }

  // Handle Chat Form Submit (Supports Unlimited Continuous Test Runs)
  if (chatForm) {
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const targetUrl = endpointInput.value.trim();
      const scenarioDesc = scenarioInput.value.trim();

      if (!targetUrl) {
        alert('Silakan masukkan Target Endpoint API.');
        return;
      }

      if (!scenarioDesc) {
        alert('Silakan masukkan deskripsi skenario pengujian.');
        return;
      }

      // 1. Append User Chat Message Bubble to Stream
      appendUserMessage(targetUrl, scenarioDesc);

      // 2. Append Agent Loading/Typing Bubble
      const loadingBubbleId = appendAgentLoadingMessage();

      // Disable send button temporarily during execution
      sendBtn.disabled = true;
      sendBtn.classList.add('opacity-75');

      const payload = {
        target_endpoint: targetUrl,
        scenario_description: scenarioDesc
      };

      try {
        const response = await fetch('/api/v1/test-integration', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          throw new Error(`Server status ${response.status}`);
        }

        const data = await response.json();
        
        // Remove loading indicator & append Agent Response Bubble
        removeMessage(loadingBubbleId);
        appendAgentResponseMessage(data);

        // Focus back on scenario input for convenient next trial
        scenarioInput.focus();

      } catch (err) {
        console.error('Integration test error:', err);
        removeMessage(loadingBubbleId);
        appendAgentErrorMessage('Terjadi kesalahan saat memproses pengujian integrasi. Silakan periksa kembali URL endpoint.');
      } finally {
        // Re-enable send button so user can perform unlimited subsequent tests!
        sendBtn.disabled = false;
        sendBtn.classList.remove('opacity-75');
      }
    });
  }

  // Append User Chat Bubble
  function appendUserMessage(url, desc) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble-user flex justify-end gap-3';
    bubble.innerHTML = `
      <div class="bg-brand-600 text-white rounded-2xl p-4 shadow-sm max-w-2xl text-xs sm:text-sm space-y-1.5">
        <div class="flex items-center gap-2 font-mono text-blue-100 font-bold border-b border-white/20 pb-1">
          <i class="fa-solid fa-terminal text-blue-200"></i>
          <span>${escapeHtml(url)}</span>
        </div>
        <p class="font-medium text-white">${escapeHtml(desc)}</p>
      </div>
      <div class="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs shrink-0 font-bold shadow-xs">
        <i class="fa-solid fa-user"></i>
      </div>
    `;
    chatStream.appendChild(bubble);
    scrollToBottom();
  }

  // Append Agent Loading Indicator
  function appendAgentLoadingMessage() {
    const id = `loading_${Date.now()}`;
    const bubble = document.createElement('div');
    bubble.id = id;
    bubble.className = 'chat-bubble-agent flex gap-3 max-w-3xl';
    bubble.innerHTML = `
      <div class="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center text-sm shrink-0 font-bold shadow-xs">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div class="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs text-xs text-slate-600 space-y-2">
        <div class="flex items-center gap-2 font-bold text-slate-800">
          <div class="w-3 h-3 border-2 border-brand-600 border-t-transparent rounded-full animate-spin"></div>
          <span>Micro-Agents Sedang Mengeksekusi Testing...</span>
        </div>
        <div class="text-[11px] text-slate-500 space-y-0.5 pl-5">
          <p>✓ Agent 1: Membangkitkan 3 variasi test payload</p>
          <p>✓ Agent 2: Mengeksekusi HTTP async & mengukur latensi ms</p>
          <p class="animate-pulse font-semibold text-brand-600">⏳ Agent 3: Evaluasi skor & sintesis laporan Markdown via Gemini AI...</p>
        </div>
      </div>
    `;
    chatStream.appendChild(bubble);
    scrollToBottom();
    return id;
  }

  // Append Agent Response Chat Bubble
  function appendAgentResponseMessage(data) {
    const { agent_logs, llm_evaluation, local_files, saved_id, created_at } = data;
    const score = llm_evaluation.integration_health_score;

    const dataKey = `res_${Date.now()}_${saved_id || 'id'}`;
    activeRawDataStore[dataKey] = data;

    let badgeColor = 'bg-emerald-100 text-emerald-800 border-emerald-300';
    let badgeText = 'EXCELLENT';
    if (score < 85 && score >= 60) {
      badgeColor = 'bg-amber-100 text-amber-900 border-amber-300';
      badgeText = 'NEEDS ATTENTION';
    } else if (score < 60) {
      badgeColor = 'bg-rose-100 text-rose-800 border-rose-300';
      badgeText = 'CRITICAL RISK';
    }

    // Build Execution Rows
    let executionRowsHtml = '';
    agent_logs.execution_results.forEach(res => {
      const statusBadge = res.is_success 
        ? '<span class="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] rounded font-bold">LULUS</span>'
        : '<span class="px-2 py-0.5 bg-rose-100 text-rose-800 text-[10px] rounded font-bold">GAGAL</span>';
      executionRowsHtml += `
        <tr>
          <td class="p-2 font-semibold text-slate-800">${escapeHtml(res.case_type)}</td>
          <td class="p-2 font-mono font-bold">${res.status_code}</td>
          <td class="p-2 font-mono text-slate-600">${res.latency_ms} ms</td>
          <td class="p-2">${statusBadge}</td>
        </tr>
      `;
    });

    // Parse Markdown Report string via Marked.js
    let markdownHtml = '';
    if (window.marked && llm_evaluation.report_md) {
      markdownHtml = window.marked.parse(llm_evaluation.report_md);
    } else {
      markdownHtml = `<p>${escapeHtml(llm_evaluation.summary)}</p>`;
    }

    const localJsonPath = local_files?.json_filepath || 'app/output/raw_json/test_run_...json';
    const localMdPath = local_files?.md_filepath || 'app/output/reports/test_report_...md';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble-agent flex gap-3 max-w-4xl';
    bubble.innerHTML = `
      <div class="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center text-sm shrink-0 font-bold shadow-xs">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div class="space-y-4 bg-white border border-slate-200 rounded-2xl p-5 shadow-xs text-xs sm:text-sm text-slate-800 flex-1">
        
        <!-- Header Health Score & Time -->
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold text-slate-500">Skor Kesehatan:</span>
            <span class="text-xl font-extrabold text-brand-700">${score}%</span>
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${badgeColor}">${badgeText}</span>
          </div>
          <span class="text-[11px] text-slate-400 font-medium">${created_at || 'Baru Saja'}</span>
        </div>

        <!-- Local Files Saved Alert -->
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs space-y-1 font-mono text-slate-700">
          <p class="font-bold text-brand-800 font-sans flex items-center gap-1.5">
            <i class="fa-solid fa-folder-check text-emerald-600"></i> Local File Output Tersimpan Otomatis:
          </p>
          <p class="text-[11px] text-slate-600 truncate"><span class="text-slate-400">JSON:</span> ${escapeHtml(localJsonPath)}</p>
          <p class="text-[11px] text-slate-600 truncate"><span class="text-slate-400">Report:</span> ${escapeHtml(localMdPath)}</p>
        </div>

        <!-- Execution Table (Agent 1 & 2) -->
        <div class="space-y-2">
          <h5 class="font-bold text-xs text-slate-700 flex items-center gap-1.5">
            <i class="fa-solid fa-microchip text-brand-600"></i> Hasil Eksekusi Test Cases (Agent 1 & 2)
          </h5>
          <div class="overflow-x-auto border border-slate-200 rounded-xl">
            <table class="w-full text-left text-xs">
              <thead class="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th class="p-2">Test Case</th>
                  <th class="p-2">Status</th>
                  <th class="p-2">Latensi</th>
                  <th class="p-2">Hasil</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                ${executionRowsHtml}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Markdown Visual Report (Agent 3 - Gemini AI) -->
        <div class="markdown-body border-t border-slate-100 pt-3">
          ${markdownHtml}
        </div>

        <!-- Action Download JSON -->
        <div class="border-t border-slate-100 pt-3 flex justify-end">
          <button 
            type="button" 
            class="download-json-action px-3.5 py-2 bg-slate-900 hover:bg-black text-white text-xs font-bold rounded-xl shadow-xs transition flex items-center gap-1.5"
            data-key="${dataKey}"
          >
            <i class="fa-solid fa-file-arrow-down text-brand-400"></i>
            <span>📥 Download Output JSON</span>
          </button>
        </div>

      </div>
    `;

    chatStream.appendChild(bubble);

    // Attach Download JSON Click Listener
    bubble.querySelector('.download-json-action').addEventListener('click', (e) => {
      const key = e.currentTarget.getAttribute('data-key');
      const rawData = activeRawDataStore[key];
      if (rawData) {
        triggerJsonDownload(rawData);
      }
    });

    scrollToBottom();
  }

  function appendAgentErrorMessage(msg) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble-agent flex gap-3 max-w-3xl';
    bubble.innerHTML = `
      <div class="w-8 h-8 rounded-full bg-rose-600 text-white flex items-center justify-center text-sm shrink-0 font-bold shadow-xs">
        <i class="fa-solid fa-triangle-exclamation"></i>
      </div>
      <div class="bg-rose-50 border border-rose-200 rounded-2xl p-4 shadow-xs text-xs text-rose-800 font-medium">
        ${escapeHtml(msg)}
      </div>
    `;
    chatStream.appendChild(bubble);
    scrollToBottom();
  }

  function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function scrollToBottom() {
    chatStream.scrollTop = chatStream.scrollHeight;
  }

  function triggerJsonDownload(data) {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const todayDate = new Date().toISOString().split('T')[0];
    const link = document.createElement('a');
    link.href = url;
    link.download = `integration_test_${todayDate}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  // Load History from MongoDB Atlas
  async function loadHistory() {
    historyContainer.innerHTML = '<p class="text-xs text-slate-400 py-4 text-center">Memuat riwayat pengujian...</p>';
    try {
      const res = await fetch('/api/v1/history?limit=10');
      if (!res.ok) throw new Error('Gagal mengambil riwayat');

      const result = await res.json();
      const items = result.data || [];

      if (items.length === 0) {
        historyContainer.innerHTML = '<p class="text-xs text-slate-400 py-4 text-center">Belum ada riwayat pengujian tersimpan.</p>';
        return;
      }

      historyContainer.innerHTML = '';
      items.forEach(item => {
        const evalData = item.llm_evaluation || {};
        const reqData = item.request_payload || item.payload || {};
        const score = evalData.integration_health_score || 0;

        const card = document.createElement('div');
        card.className = 'history-card bg-white border border-slate-200 rounded-xl p-3.5 space-y-1.5 shadow-xs cursor-pointer text-xs';
        card.innerHTML = `
          <div class="flex items-center justify-between text-[11px] text-slate-500 border-b border-slate-100 pb-1.5">
            <span class="font-bold text-slate-800"><i class="fa-regular fa-calendar-check mr-1 text-brand-600"></i>${item.created_at || 'Pengujian'}</span>
            <span class="font-bold px-2 py-0.5 bg-blue-50 text-brand-700 rounded-full text-[10px] border border-blue-200">Skor: ${score}%</span>
          </div>
          <h5 class="font-mono font-bold text-slate-900 truncate">${escapeHtml(reqData.target_endpoint || 'API Endpoint')}</h5>
          <p class="text-slate-600 line-clamp-2">${escapeHtml(evalData.summary || reqData.scenario_description || '')}</p>
        `;

        card.addEventListener('click', () => {
          historyDrawer.classList.add('hidden');
          appendAgentResponseMessage(item);
        });

        historyContainer.appendChild(card);
      });

    } catch (e) {
      console.error('History load error:', e);
      historyContainer.innerHTML = '<p class="text-xs text-rose-500 py-4 text-center">Gagal memuat riwayat.</p>';
    }
  }

  // Utility
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
