"""Two-pane viewer for tracked API conversations."""

from __future__ import annotations

import json


def build_tracking_page(
    api_key_id: str, sessions: list[dict], turns_by_session: dict[str, list[dict]], *, show_feishu_chat_filter: bool = False
) -> str:
    """Render the viewer with server-provided data (no secondary authenticated fetch)."""
    del api_key_id
    visibility_endpoint = "feishu-sessions" if show_feishu_chat_filter else "tracked-sessions"
    payload = json.dumps(
        {"sessions": sessions, "turns_by_session": turns_by_session}, ensure_ascii=False
    ).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

    chat_filter = '<div id="chat-type-filter" class="mt-3 grid grid-cols-3 gap-1 text-xs"><button data-chat-type="all" class="rounded bg-sky-500/20 px-2 py-2 text-sky-200">全部</button><button data-chat-type="p2p" class="rounded bg-slate-800 px-2 py-2">私聊</button><button data-chat-type="group" class="rounded bg-slate-800 px-2 py-2">群聊</button></div>' if show_feishu_chat_filter else ''
    page = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <script src="https://cdn.tailwindcss.com"></script>
  <title>聊天会话跟踪</title>
</head>
<body class="h-screen overflow-hidden bg-slate-950 text-slate-100">
  <div class="flex h-full">
    <aside class="flex w-80 shrink-0 flex-col border-r border-slate-800 bg-slate-900/70">
      <div class="border-b border-slate-800 p-5">
        <a href="/admin" class="text-sm text-sky-300">← 返回 API Key 列表</a>
        <h1 class="mt-4 text-xl font-bold">聊天会话跟踪</h1>
        <input id="search" placeholder="搜索会话" class="mt-4 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-sky-400">
        __CHAT_TYPE_FILTER__
      </div>
      <div id="session-list" class="flex-1 space-y-2 overflow-y-auto p-3"></div>
    </aside>
    <main class="flex min-w-0 flex-1 flex-col bg-slate-950">
      <header class="border-b border-slate-800 px-8 py-5">
        <h2 id="thread-title" class="font-semibold text-slate-200">选择一个会话</h2>
        <p id="thread-meta" class="mt-1 text-xs text-slate-500">在左侧选择会话以查看对话记录</p>
      </header>
      <section id="turns" class="flex-1 space-y-5 overflow-y-auto px-8 py-7"></section>
    </main>
  </div>
  <script id="tracking-payload" type="application/json">__TRACKING_PAYLOAD__</script>
  <script>
    (function () {
      const list = document.getElementById('session-list');
      const search = document.getElementById('search');
      const title = document.getElementById('thread-title');
      const meta = document.getElementById('thread-meta');
      const turnsElement = document.getElementById('turns');
      let selected = '';
      let chatType = 'all';

      function escapeHtml(value) {
        return String(value == null ? '' : value).replace(/[&<>]/g, function (character) {
          return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[character];
        });
      }

      function formatDate(value) {
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? String(value || '') : date.toLocaleString();
      }

      function userText(messages) {
        return (messages || []).filter(function (message) {
          return message.role === 'user';
        }).map(function (message) {
          return message.content || '';
        }).join('\n\n');
      }

      try {
        const payload = JSON.parse(document.getElementById('tracking-payload').textContent);
        const sessions = Array.isArray(payload.sessions) ? payload.sessions : [];
        const turnsBySession = payload.turns_by_session || {};

        function renderList() {
          const keyword = search.value.toLowerCase();
          const matches = sessions.filter(function (item) {
            return String(item.thread_id || '').toLowerCase().includes(keyword) && (chatType === 'all' || item.chat_type === chatType);
          });
          list.innerHTML = matches.map(function (item) {
            const active = item.id === selected;
            return '<div class="group relative rounded-xl border ' +
              (active ? 'border-sky-400 bg-sky-500/10' : 'border-slate-800 bg-slate-950 hover:border-slate-600') + '">' +
              '<button type="button" data-session-id="' + escapeHtml(item.id) + '" class="w-full rounded-xl p-3 pr-16 text-left">' +
              '<p class="truncate font-mono text-sm">' + escapeHtml(item.thread_id) + '</p>' +
              '<p class="mt-2 text-xs text-slate-500">最后使用：' + escapeHtml(formatDate(item.last_used_at)) + '</p>' +
              '</button>' +
              '<label class="absolute right-3 top-3 cursor-pointer" title="' + (item.is_archived ? '已隐藏，点击显示' : '显示中，点击隐藏') + '">' +
              '<input type="checkbox" data-visibility-id="' + escapeHtml(item.id) + '" aria-label="' + (item.is_archived ? '显示会话' : '隐藏会话') + '" class="peer sr-only"' + (item.is_archived ? '' : ' checked') + '>' +
              '<span class="relative block h-6 w-11 rounded-full bg-slate-700 transition-colors duration-200 peer-checked:bg-emerald-500 after:absolute after:left-1 after:top-1 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform after:duration-200 peer-checked:after:translate-x-5"></span></label></div>';
          }).join('');
          list.querySelectorAll('[data-session-id]').forEach(function (button) {
            button.addEventListener('click', function () { selectSession(button.dataset.sessionId); });
          });
          list.querySelectorAll('[data-visibility-id]').forEach(function (control) {
            control.addEventListener('change', function () { toggleVisibility(control.dataset.visibilityId, control.checked); });
          });
          if (!matches.length) {
            list.innerHTML = '<p class="px-3 py-6 text-center text-sm text-slate-500">没有匹配的会话</p>';
          }
        }

        function selectSession(id) {
          selected = id;
          const session = sessions.find(function (item) { return item.id === id; });
          if (!session) return;
          title.textContent = session.thread_id;
          meta.textContent = '最后使用：' + formatDate(session.last_used_at);
          const turns = turnsBySession[id] || [];
          turnsElement.innerHTML = turns.map(function (turn) {
            return '<article class="mx-auto max-w-4xl">' +
              '<p class="mb-3 text-center text-xs text-slate-600">' + escapeHtml(formatDate(turn.created_at)) + '</p>' +
              '<div class="ml-auto max-w-[82%] rounded-2xl rounded-tr-sm bg-sky-500/15 p-4 text-sm">' +
              '<p class="mb-2 text-xs font-semibold text-sky-300">用户指令</p><div class="whitespace-pre-wrap">' + escapeHtml(userText(turn.messages)) + '</div></div>' +
              '<div class="mt-4 max-w-[88%] rounded-2xl rounded-tl-sm bg-emerald-500/15 p-4 text-sm">' +
              '<p class="mb-2 text-xs font-semibold text-emerald-300">AI 回复</p><div class="whitespace-pre-wrap">' + escapeHtml(turn.response || '（本轮未产生回复）') + '</div></div></article>';
          }).join('');
          if (!turns.length) turnsElement.innerHTML = '<p class="pt-24 text-center text-sm text-slate-500">该会话暂时没有已完成的对话记录</p>';
          renderList();
        }

        async function toggleVisibility(id, isVisible) {
          const session = sessions.find(function (item) { return item.id === id; });
          if (!session) return;
          try {
            const response = await fetch('/admin/__VISIBILITY_ENDPOINT__/' + encodeURIComponent(id) + '/visibility', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ is_archived: !isVisible })
            });
            if (!response.ok) throw new Error('Unable to update session visibility');
            session.is_archived = (await response.json()).is_archived;
          } catch (error) {
            renderList();
            window.alert('切换会话显示状态失败，请稍后重试。');
          }
        }

        search.addEventListener('input', renderList);
        document.querySelectorAll('[data-chat-type]').forEach(function (button) {
          button.addEventListener('click', function () { chatType = button.dataset.chatType; document.querySelectorAll('[data-chat-type]').forEach(function (item) { item.className = item.dataset.chatType === chatType ? 'rounded bg-sky-500/20 px-2 py-2 text-sky-200' : 'rounded bg-slate-800 px-2 py-2'; }); renderList(); });
        });
        renderList();
        if (sessions.length) selectSession(sessions[0].id);
      } catch (error) {
        console.error('Unable to render tracked conversations:', error);
        list.innerHTML = '<p class="rounded-lg border border-rose-900 bg-rose-950/30 p-3 text-sm text-rose-300">会话数据无法显示：' + escapeHtml(error.message) + '</p>';
      }
    }());
  </script>
</body>
</html>'''
    return (
        page.replace("__TRACKING_PAYLOAD__", payload)
        .replace("__CHAT_TYPE_FILTER__", chat_filter)
        .replace("__VISIBILITY_ENDPOINT__", visibility_endpoint)
    )
