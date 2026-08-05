"""Tailwind-powered, same-origin administration dashboard."""

ADMIN_PAGE = r'''<!doctype html>
<html lang="zh-CN" class="bg-slate-950 [scrollbar-gutter:stable]">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Deep Agents · 管理后台</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>tailwind.config={theme:{extend:{colors:{ink:'#0f172a',brand:'#22c55e'}}}}</script>
</head>
<body class="min-h-screen bg-slate-950 text-slate-100 antialiased">
  <div class="mx-auto flex min-h-screen max-w-[1600px]">
    <aside class="hidden w-64 shrink-0 border-r border-slate-800 bg-slate-950 p-5 lg:block">
      <div class="mb-10 flex items-center gap-3"><div class="grid h-10 w-10 place-items-center rounded-xl bg-emerald-400 text-lg font-black text-slate-950">D</div><div><p class="font-semibold">Deep Agents</p><p class="text-xs text-slate-500">控制台 · Debug</p></div></div>
      <nav class="space-y-1" id="nav">
        <button data-view="overview" class="nav-btn w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium">概览</button>
        <button data-view="mcp" class="nav-btn w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium">MCP 服务与工具</button>
        <button data-view="roles" class="nav-btn w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium">角色与授权</button>
        <button data-view="keys" class="nav-btn w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium">API Keys</button>
      </nav>
    </aside>
    <main class="min-w-0 flex-1 p-5 sm:p-8">
      <header class="mb-8 flex flex-wrap items-center justify-between gap-4"><div><p class="text-sm font-medium text-emerald-400">DEVELOPMENT CONSOLE</p><h1 class="mt-1 text-2xl font-bold tracking-tight sm:text-3xl" id="page-title">平台概览</h1></div></header>

      <section data-panel="overview" class="panel space-y-6">
        <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <article class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><p class="text-sm text-slate-400">已登记 MCP 服务</p><p class="mt-3 text-3xl font-bold" id="stat-servers">—</p><p class="mt-2 text-xs text-slate-500">工具通过服务同步写入目录</p></article>
          <article class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><p class="text-sm text-slate-400">可用工具</p><p class="mt-3 text-3xl font-bold" id="stat-tools">—</p><p class="mt-2 text-xs text-slate-500">MCP 与 Deep Agents 内置工具</p></article>
          <article class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><p class="text-sm text-slate-400">启用角色</p><p class="mt-3 text-3xl font-bold" id="stat-roles">—</p><p class="mt-2 text-xs text-slate-500">角色决定工具可见范围</p></article>
          <article class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><p class="text-sm text-slate-400">启用 API Key</p><p class="mt-3 text-3xl font-bold" id="stat-keys">—</p><p class="mt-2 text-xs text-slate-500">明文 Key 不会保存到数据库</p></article>
        </div>
      </section>

      <section data-panel="mcp" class="panel hidden space-y-6">
        <div class="grid gap-6 xl:grid-cols-[380px_1fr]"><form id="server-form" class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><h2 class="text-lg font-semibold">登记 MCP 服务</h2><p class="mt-1 text-sm text-slate-400">工具名由同步功能发现</p><label class="mt-5 block text-sm text-slate-300">服务名称<input required name="name" pattern="[A-Za-z0-9_-]+" placeholder="knowledge-bases" class="field mt-2"></label><label class="mt-4 block text-sm text-slate-300">MCP 地址<input required name="url" type="url" placeholder="http://127.0.0.1:8001/mcp" class="field mt-2"></label><label class="mt-4 block text-sm text-slate-300">说明（可选）<textarea name="description" rows="3" class="field mt-2" placeholder="财务、业务和人事知识库"></textarea></label><button class="primary-btn mt-5 w-full">登记服务</button></form>
          <div><div class="mb-3 flex items-end justify-between"><div><h2 class="text-lg font-semibold">服务列表</h2><p class="text-sm text-slate-400">同步会使用 API 签发的短期内部 JWT 调用 tools/list。</p></div></div><div id="server-list" class="grid gap-3"></div></div></div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><div class="flex items-center justify-between"><div><h2 class="text-lg font-semibold">已发现工具目录</h2><p class="mt-1 text-sm text-slate-400">只有这里出现的工具，才能被角色授权。</p></div><span id="tool-count" class="rounded-full bg-slate-800 px-3 py-1 text-sm text-slate-300">0 个工具</span></div><div id="tool-list" class="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3"></div></div>
      </section>

      <section data-panel="roles" class="panel hidden space-y-6">
        <div class="grid gap-6 xl:grid-cols-[380px_1fr]"><form id="role-form" class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><h2 class="text-lg font-semibold">创建角色</h2><p class="mt-1 text-sm text-slate-400">例如 finance_reader、hr_reader。</p><label class="mt-5 block text-sm text-slate-300">角色名<input required name="name" pattern="[A-Za-z0-9_-]+" class="field mt-2" placeholder="finance_reader"></label><label class="mt-4 block text-sm text-slate-300">说明<textarea name="description" rows="3" class="field mt-2" placeholder="可查询财务知识库"></textarea></label><button class="primary-btn mt-5 w-full">创建角色</button></form>
          <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><h2 class="text-lg font-semibold">给角色分配工具</h2><p class="mt-1 text-sm text-slate-400">保存后，绑定该角色的 API Key 会获得这些 MCP 或 Deep Agents 内置工具。</p><select id="role-select" class="field mt-5"></select><div id="role-tools" class="mt-4 grid gap-3 sm:grid-cols-2"></div><button id="save-role-tools" class="primary-btn mt-5">保存工具授权</button></div></div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><h2 class="text-lg font-semibold">角色一览</h2><div id="role-list" class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3"></div></div>
      </section>

      <section data-panel="keys" class="panel hidden space-y-6">
        <div class="grid gap-6 xl:grid-cols-[420px_1fr]"><form id="key-form" class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><h2 class="text-lg font-semibold">新建 API Key</h2><p class="mt-1 text-sm text-slate-400">Key 一旦离开此页面，就只能禁用或重新创建。</p><label class="mt-5 block text-sm text-slate-300">Key 名称<input required name="name" class="field mt-2" placeholder="财务知识库测试 Key"></label><label class="mt-4 block text-sm text-slate-300">文件权限<select name="file_access" class="field mt-2"><option value="none">none · 不允许文件访问</option><option value="read_only">read_only · 只读</option><option value="read_write">read_write · 读写</option></select></label><p class="mt-4 text-sm text-slate-300">绑定角色</p><div id="key-roles" class="mt-2 space-y-2"></div><button class="primary-btn mt-5 w-full">创建并显示 Key</button></form>
          <div class="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-5"><h2 class="text-lg font-semibold text-emerald-300">新 Key</h2><p class="mt-1 text-sm text-slate-400">请复制到安全的密码管理器妥善保管。</p><div id="new-key" class="mt-6 rounded-xl border border-dashed border-emerald-500/30 bg-slate-950 p-4 font-mono text-sm break-all text-emerald-200">尚未创建 API Key</div><button id="copy-key" class="mt-4 rounded-lg border border-emerald-500/40 px-3 py-2 text-sm font-medium text-emerald-300 hover:bg-emerald-500/10">复制 Key</button></div></div>
        <div class="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60"><div class="border-b border-slate-800 px-5 py-4"><h2 class="text-lg font-semibold">API Key 列表</h2></div><div class="overflow-x-auto"><table class="w-full min-w-[720px] text-left text-sm"><thead class="bg-slate-900 text-xs uppercase tracking-wide text-slate-500"><tr><th class="px-5 py-3">名称</th><th class="px-5 py-3">前缀</th><th class="px-5 py-3">权限</th><th class="px-5 py-3">状态</th><th class="px-5 py-3">创建时间</th><th class="px-5 py-3"></th></tr></thead><tbody id="key-list" class="divide-y divide-slate-800"></tbody></table></div></div>
      </section>
    </main>
  </div>
  <div id="toast" class="fixed bottom-5 right-5 hidden max-w-md rounded-xl border px-4 py-3 text-sm shadow-2xl"></div>
  <dialog id="edit-key-dialog" class="w-[min(94vw,500px)] rounded-2xl border border-slate-700 bg-slate-900 p-0 text-slate-100 shadow-2xl backdrop:bg-slate-950/80">
    <form id="edit-key-form" class="p-6"><div class="flex items-start justify-between gap-4"><div><h2 class="text-xl font-semibold">编辑 API Key</h2><p id="edit-key-name" class="mt-1 text-sm text-slate-400"></p></div><button type="button" onclick="$('#edit-key-dialog').close()" class="text-xl text-slate-400 hover:text-white">×</button></div><input id="edit-key-id" type="hidden"><label class="mt-5 block text-sm text-slate-300">文件权限<select id="edit-key-file-access" class="field mt-2"><option value="none">none · 不允许文件访问</option><option value="read_only">read_only · 只读</option><option value="read_write">read_write · 读写</option></select></label><p class="mt-5 text-sm text-slate-300">绑定角色</p><div id="edit-key-roles" class="mt-2 max-h-56 space-y-2 overflow-y-auto"></div><div class="mt-6 flex justify-end gap-3"><button type="button" onclick="$('#edit-key-dialog').close()" class="rounded-lg border border-slate-700 px-4 py-2.5 text-sm text-slate-300 hover:bg-slate-800">取消</button><button class="primary-btn">保存更改</button></div></form>
  </dialog>
  <style type="text/tailwindcss">@layer components {.field{@apply w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20}.primary-btn{@apply rounded-lg bg-emerald-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50}.nav-btn{@apply box-border min-h-11 text-slate-400 transition-colors hover:bg-slate-900 hover:text-white}.nav-btn.active{@apply bg-emerald-400 text-slate-950 hover:bg-emerald-300}}</style>
  <script>
    const state={roles:[],servers:[],tools:[],keys:[],newKey:''};
    const titles={overview:'平台概览',mcp:'MCP 服务与工具',roles:'角色与授权',keys:'API Keys'};
    const $=s=>document.querySelector(s); const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
    async function api(path,options={}){const response=await fetch('/admin'+path,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});if(!response.ok){let message='请求失败';const body=await response.text();if(body){try{const data=JSON.parse(body);const detail=data.detail;if(Array.isArray(detail))message=detail.map(item=>item.msg||item.message||JSON.stringify(item)).join('；');else message=detail||message}catch{message=body}}throw Error(message)}return response.status===204?null:response.json()}
    function toast(message,kind='ok'){const el=$('#toast');el.textContent=message;el.className=`fixed bottom-5 right-5 max-w-md rounded-xl border px-4 py-3 text-sm shadow-2xl ${kind==='ok'?'border-emerald-500/40 bg-emerald-950 text-emerald-200':'border-rose-500/40 bg-rose-950 text-rose-200'}`;setTimeout(()=>el.classList.add('hidden'),3500)}
    function toolOrigin(tool){return tool.source==='builtin'?'Deep Agents 内置工具':(state.servers.find(s=>s.id===tool.server_id)?.name||'未知 MCP 服务')}
    function render(){
      $('#stat-servers').textContent=state.servers.length;$('#stat-tools').textContent=state.tools.length;$('#stat-roles').textContent=state.roles.length;$('#stat-keys').textContent=state.keys.filter(k=>k.is_active).length;
      $('#server-list').innerHTML=state.servers.length?state.servers.map(s=>`<article class="rounded-xl border ${s.is_active?'border-slate-800 bg-slate-900':'border-slate-800/60 bg-slate-950/60'} p-4"><div class="flex flex-wrap items-start justify-between gap-3"><div><div class="flex items-center gap-2"><h3 class="font-semibold">${esc(s.name)}</h3><span class="rounded-full px-2 py-0.5 text-xs ${s.is_active?'bg-emerald-500/15 text-emerald-300':'bg-slate-700 text-slate-400'}">${s.is_active?'运行中':'已关闭'}</span></div><p class="mt-1 break-all font-mono text-xs text-slate-500">${esc(s.url)}</p><p class="mt-2 text-sm text-slate-400">${esc(s.description||'暂无说明')}</p></div><div class="flex flex-wrap gap-2"><button onclick="syncServer('${s.id}',this)" ${s.is_active?'':'disabled'} class="rounded-lg border border-emerald-500/40 px-3 py-2 text-sm text-emerald-300 hover:bg-emerald-500/10 disabled:cursor-not-allowed disabled:opacity-30">同步</button><button onclick="editServer('${s.id}')" class="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800">编辑</button><button onclick="setServerState('${s.id}',${!s.is_active})" class="rounded-lg border border-amber-500/35 px-3 py-2 text-sm text-amber-300 hover:bg-amber-500/10">${s.is_active?'关闭':'启用'}</button><button onclick="deleteServer('${s.id}')" class="rounded-lg border border-rose-500/35 px-3 py-2 text-sm text-rose-300 hover:bg-rose-500/10">删除</button></div></div></article>`).join(''):'<p class="rounded-xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-500">还没有登记 MCP 服务。</p>';
      $('#tool-count').textContent=`${state.tools.length} 个工具`;$('#tool-list').innerHTML=state.tools.length?state.tools.map(t=>`<article class="rounded-xl border border-slate-800 bg-slate-950 p-4"><p class="text-xs text-emerald-400">${esc(toolOrigin(t))}</p><h3 class="mt-1 font-mono text-sm font-semibold">${esc(t.name)}</h3><p class="mt-2 text-sm text-slate-400">${esc(t.description||'暂无描述')}</p></article>`).join(''):'<p class="col-span-full rounded-xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-500">Deep Agents 内置工具会自动出现；MCP 工具在服务同步后出现。</p>';
      $('#role-select').innerHTML=state.roles.length?state.roles.map(r=>`<option value="${r.id}">${esc(r.name)}</option>`).join(''):'<option value="">请先创建角色</option>';
      renderRoleTools();$('#role-list').innerHTML=state.roles.length?state.roles.map(r=>`<article class="rounded-xl border border-slate-800 bg-slate-950 p-4"><div class="flex items-center justify-between gap-2"><h3 class="font-semibold">${esc(r.name)}</h3><span class="rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-400">${r.tool_ids.length} 个工具</span></div><p class="mt-2 min-h-10 text-sm text-slate-400">${esc(r.description||'暂无说明')}</p></article>`).join(''):'<p class="col-span-full rounded-xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-500">尚未创建角色。</p>';
      $('#key-roles').innerHTML=state.roles.length?state.roles.map(r=>`<label class="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm hover:border-slate-600"><input type="checkbox" value="${r.id}" class="h-4 w-4 accent-emerald-400"><span>${esc(r.name)}</span></label>`).join(''):'<p class="text-sm text-amber-300">请先在“角色与授权”中创建角色。</p>';
      $('#key-list').innerHTML=state.keys.length?state.keys.map(k=>`<tr class="${k.is_active?'':'opacity-60'}"><td class="px-5 py-4 font-medium">${esc(k.name)}</td><td class="px-5 py-4 font-mono text-xs text-slate-400">${esc(k.api_key||k.key_prefix+'…')}</td><td class="px-5 py-4 text-slate-300">${esc(k.file_access)}</td><td class="px-5 py-4"><span class="rounded-full px-2.5 py-1 text-xs font-medium ${k.is_active?'bg-emerald-500/15 text-emerald-300':'bg-slate-700 text-slate-400'}">${k.is_active?'启用':'已禁用'}</span></td><td class="px-5 py-4 text-slate-400">${new Date(k.created_at).toLocaleString()}</td><td class="px-5 py-4"><div class="flex gap-3"><button onclick="navigator.clipboard.writeText('${k.api_key||''}').then(()=>toast('API Key 已复制'))" ${k.api_key?'':'disabled'} class="text-sm text-emerald-300 hover:text-emerald-200 disabled:opacity-40">复制</button><button onclick="openKeyEditor('${k.id}')" class="text-sm text-sky-300 hover:text-sky-200">编辑</button>${k.is_active?`<button onclick="setKeyState('${k.id}',false)" class="text-sm text-amber-300 hover:text-amber-200">禁用</button>`:`<button onclick="setKeyState('${k.id}',true)" class="text-sm text-emerald-300 hover:text-emerald-200">启用</button>`}<button onclick="deleteKey('${k.id}')" class="text-sm text-rose-300 hover:text-rose-200">删除</button></div></td></tr>`).join(''):'<tr><td colspan="6" class="px-5 py-10 text-center text-slate-500">尚未创建 API Key。</td></tr>';
    }
    function renderRoleTools(){const role=state.roles.find(r=>r.id===$('#role-select').value)||state.roles[0];if(role&&$('#role-select').value!==role.id)$('#role-select').value=role.id;$('#role-tools').innerHTML=state.tools.length?state.tools.map(t=>`<label class="flex cursor-pointer gap-3 rounded-xl border border-slate-800 bg-slate-950 p-3 hover:border-slate-600"><input class="mt-0.5 h-4 w-4 accent-emerald-400" type="checkbox" value="${t.id}" ${role?.tool_ids.includes(t.id)?'checked':''}><span><span class="block font-mono text-sm">${esc(t.name)}</span><span class="mt-1 block text-xs text-slate-500">${esc(toolOrigin(t))}</span></span></label>`).join(''):'<p class="text-sm text-amber-300">暂时没有可授权工具。</p>'}
    async function loadAll(){try{const [roles,servers,tools,keys]=await Promise.all([api('/roles'),api('/mcp-servers'),api('/mcp-tools'),api('/api-keys')]);Object.assign(state,{roles,servers,tools,keys});render()}catch(e){toast(e.message,'error')}}
    async function syncServer(id,button){try{if(button){button.disabled=true;button.textContent='同步中…'}const tools=await api(`/mcp-servers/${id}/sync-tools`,{method:'POST'});toast(`已同步 ${tools.length} 个工具`);await loadAll()}catch(e){toast(e.message,'error')}finally{if(button){button.disabled=false;button.textContent='同步工具'}}}
    async function editServer(id){const s=state.servers.find(x=>x.id===id);if(!s)return;const name=prompt('服务名称',s.name);if(name===null)return;const url=prompt('MCP 地址',s.url);if(url===null)return;const description=prompt('说明（可留空）',s.description||'');if(description===null)return;try{await api(`/mcp-servers/${id}`,{method:'PATCH',body:JSON.stringify({name,url,description:description||null})});toast('MCP 服务已更新');await loadAll()}catch(e){toast(e.message,'error')}}
    async function setServerState(id,enable){const action=enable?'启用':'关闭';if(!confirm(`${action}此 MCP 服务？${enable?'':'关闭后它将立刻从有效工具授权中排除。'}`))return;try{await api(`/mcp-servers/${id}/${enable?'enable':'disable'}`,{method:'POST'});toast(`MCP 服务已${action}`);await loadAll()}catch(e){toast(e.message,'error')}}
    async function deleteServer(id){if(!confirm('永久删除此 MCP 服务及其工具目录？关联角色将失去这些工具授权，此操作不可恢复。'))return;try{await api(`/mcp-servers/${id}`,{method:'DELETE'});toast('MCP 服务已删除');await loadAll()}catch(e){toast(e.message,'error')}}
    async function setKeyState(id,enable){const action=enable?'启用':'禁用';if(!confirm(`${action}此 API Key？`))return;try{await api(`/api-keys/${id}/${enable?'enable':'disable'}`,{method:'POST'});toast(`API Key 已${action}`);await loadAll()}catch(e){toast(e.message,'error')}}
    async function deleteKey(id){if(!confirm('永久删除此 API Key？删除后不能恢复，也不能找回明文。'))return;try{await api(`/api-keys/${id}`,{method:'DELETE'});toast('API Key 已删除');await loadAll()}catch(e){toast(e.message,'error')}}
    function openKeyEditor(id){const key=state.keys.find(k=>k.id===id);if(!key)return;$('#edit-key-id').value=id;$('#edit-key-name').textContent=`${key.name} · ${key.key_prefix}…`;$('#edit-key-file-access').value=key.file_access;const tracking=confirm('是否启用该 Key 的聊天内容跟踪？\n确定=启用，取消=关闭');key._trackingChoice=tracking;$('#edit-key-roles').innerHTML=state.roles.length?state.roles.map(r=>`<label class="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm hover:border-slate-600"><input type="checkbox" value="${r.id}" class="h-4 w-4 accent-emerald-400" ${key.role_ids.includes(r.id)?'checked':''}><span>${esc(r.name)}</span></label>`).join(''):'<p class="text-sm text-amber-300">没有可用角色。</p>';$('#edit-key-dialog').showModal()}
    $('#server-form').onsubmit=async e=>{e.preventDefault();const f=new FormData(e.target);try{const server=await api('/mcp-servers',{method:'POST',body:JSON.stringify(Object.fromEntries(f))});state.servers=[...state.servers,server];render();e.target.reset();toast('MCP 服务已登记，正在同步工具…');await syncServer(server.id)}catch(err){toast(err.message,'error')}};
    $('#role-form').onsubmit=async e=>{e.preventDefault();const f=new FormData(e.target);const payload=Object.fromEntries(f);const normalizedName=String(payload.name||'').trim().toLocaleLowerCase();if(state.roles.some(role=>role.name.toLocaleLowerCase()===normalizedName)){toast('角色名称已存在，不能重复创建','error');return}try{await api('/roles',{method:'POST',body:JSON.stringify(payload)});e.target.reset();document.querySelector('#role-create-dialog')?.close();toast('角色已创建');await loadAll()}catch(err){toast(err.message,'error')}};
    $('#role-select').onchange=renderRoleTools;$('#save-role-tools').onclick=async()=>{const id=$('#role-select').value;if(!id)return toast('请先创建角色','error');try{const tool_ids=[...document.querySelectorAll('#role-tools input:checked')].map(x=>x.value);await api(`/roles/${id}/tools`,{method:'PUT',body:JSON.stringify({tool_ids})});toast('工具授权已保存');await loadAll()}catch(e){toast(e.message,'error')}};
    $('#key-form').onsubmit=async e=>{e.preventDefault();const f=new FormData(e.target);const role_ids=[...document.querySelectorAll('#key-roles input:checked')].map(x=>x.value);try{const result=await api('/api-keys',{method:'POST',body:JSON.stringify({name:f.get('name'),file_access:f.get('file_access'),role_ids})});state.newKey=result.api_key;$('#new-key').textContent=result.api_key;e.target.reset();toast('新 API Key 已创建，请立即复制');await loadAll()}catch(err){toast(err.message,'error')}};
    $('#edit-key-form').onsubmit=async e=>{e.preventDefault();const id=$('#edit-key-id').value;const key=state.keys.find(k=>k.id===id);const role_ids=[...document.querySelectorAll('#edit-key-roles input:checked')].map(x=>x.value);try{await api(`/api-keys/${id}`,{method:'PATCH',body:JSON.stringify({file_access:$('#edit-key-file-access').value,role_ids,chat_tracking:key?key._trackingChoice:false})});$('#edit-key-dialog').close();toast('API Key 授权已更新');await loadAll()}catch(err){toast(err.message,'error')}};
    $('#copy-key').onclick=async()=>{if(!state.newKey)return toast('还没有可复制的新 Key','error');await navigator.clipboard.writeText(state.newKey);toast('已复制到剪贴板')};
    document.querySelectorAll('.nav-btn').forEach(button=>button.onclick=()=>{const view=button.dataset.view;document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('hidden',p.dataset.panel!==view));document.querySelectorAll('.nav-btn').forEach(b=>b.classList.toggle('active',b===button));$('#page-title').textContent=titles[view]});
    document.querySelector('[data-view="overview"]').classList.add('active');loadAll();
  </script>
</body></html>'''

# Keep the original dashboard markup compact while adding the tracking controls
# as a final same-origin enhancement.
ADMIN_PAGE += r'''<script>
(() => {
  const originalRender = render;
  function roleSummary(ids) { return ids.map(id => state.roles.find(r => r.id === id)?.name).filter(Boolean).join(', ') || '无角色'; }
  function drawKeyRows() {
    const body = document.querySelector('#key-list'); if (!body) return;
    body.innerHTML = state.keys.map(key => {
      const roles = roleSummary(key.role_ids);
      const shown = roles.length > 20 ? roles.slice(0, 20) + '…' : roles;
      const storedKey = key.api_key || null;
      return `<tr class="${key.is_active ? '' : 'opacity-60'}"><td class="px-5 py-4 font-medium">${esc(key.name)}</td><td class="px-5 py-4 font-mono text-xs text-slate-400">${esc(storedKey || key.key_prefix + '…')}</td><td class="px-5 py-4"><span title="${esc(roles)}" class="inline-block max-w-40 truncate rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-300">${esc(shown)}</span></td><td class="px-5 py-4 text-slate-300">${esc(key.file_access)}</td><td class="px-5 py-4"><span class="rounded-full px-2 py-1 text-xs ${key.chat_tracking ? 'bg-sky-500/15 text-sky-300' : 'bg-slate-700 text-slate-400'}">${key.chat_tracking ? '已跟踪' : '未跟踪'}</span></td><td class="px-5 py-4"><div class="flex gap-3"><button onclick="navigator.clipboard.writeText('${storedKey || ''}').then(()=>toast('API Key 已复制'))" ${storedKey ? '' : 'disabled'} class="text-sm text-emerald-300 disabled:opacity-40">复制</button><button onclick="openKeyEditor('${key.id}')" class="text-sm text-sky-300">编辑</button>${key.chat_tracking ? `<a href="/admin/api-keys/${key.id}/sessions/view" class="text-sm text-violet-300">会话</a>` : ''}${key.is_active ? `<button onclick="setKeyState('${key.id}',false)" class="text-sm text-amber-300">禁用</button>` : `<button onclick="setKeyState('${key.id}',true)" class="text-sm text-emerald-300">启用</button>`}<button onclick="deleteKey('${key.id}')" class="text-sm text-rose-300">删除</button></div></td></tr>`;
    }).join('');
  }
  render = () => { originalRender(); document.querySelector('#key-tracking-row')?.remove(); document.querySelector('#key-roles')?.insertAdjacentHTML('beforebegin', '<label id="key-tracking-row" class="mb-4 flex cursor-pointer items-center justify-between text-sm"><span class="font-semibold">跟踪聊天内容</span><input id="key-chat-tracking" type="checkbox" class="peer sr-only"><span class="h-6 w-11 rounded-full bg-slate-700 transition peer-checked:bg-emerald-500 after:ml-1 after:mt-1 after:block after:h-4 after:w-4 after:rounded-full after:bg-white after:transition peer-checked:after:translate-x-5"></span></label>'); drawKeyRows(); };
  document.querySelector('#key-form').onsubmit = async event => { event.preventDefault(); const form = new FormData(event.target); const role_ids = [...document.querySelectorAll('#key-roles input:checked')].map(x => x.value); try { const result = await api('/api-keys', {method:'POST', body:JSON.stringify({name:form.get('name'), file_access:form.get('file_access'), role_ids, chat_tracking:document.querySelector('#key-chat-tracking').checked})}); state.newKey=result.api_key; document.querySelector('#new-key').textContent=result.api_key; event.target.reset(); await loadAll(); } catch (error) { toast(error.message,'error'); } };
  document.querySelector('#edit-key-form').onsubmit = async event => { event.preventDefault(); const id=document.querySelector('#edit-key-id').value; const role_ids=[...document.querySelectorAll('#edit-key-roles input:checked')].map(x=>x.value); try { await api(`/api-keys/${id}`,{method:'PATCH',body:JSON.stringify({file_access:document.querySelector('#edit-key-file-access').value,role_ids})}); document.querySelector('#edit-key-dialog').close(); await loadAll(); } catch(error) { toast(error.message,'error'); } };
})();
</script>'''


# Must be last: the older console incrementally rebinds the Key editor.
ADMIN_PAGE += r'''<script>
(() => {
  const priorOpenKeyEditor = window.openKeyEditor;
  window.openKeyEditor = id => {
    priorOpenKeyEditor(id);
    const key = state.keys.find(item => item.id === id); if (!key) return;
    document.querySelector('#edit-key-output-schema-row')?.remove();
    const roles = document.querySelector('#edit-key-roles');
    roles.insertAdjacentHTML('beforebegin', `<label id="edit-key-output-schema-row" class="mb-5 block text-sm text-slate-300">最终输出 JSON Schema（留空则不限制）<textarea id="edit-key-output-schema" rows="10" spellcheck="false" class="field mt-2 font-mono text-xs" placeholder='{"type":"object","required":["items"],"properties":{"items":{"type":"array"}},"additionalProperties":false}'></textarea><span class="mt-2 block text-xs text-slate-500">启用后，服务端会校验最终回答；回答必须是纯 JSON，不能带 Markdown 或说明文字。</span></label>`);
    document.querySelector('#edit-key-output-schema').value = key.output_schema ? JSON.stringify(key.output_schema, null, 2) : '';
  };
  document.querySelector('#edit-key-form').onsubmit = async event => {
    event.preventDefault();
    const id = document.querySelector('#edit-key-id').value;
    const role_ids = [...document.querySelectorAll('#edit-key-roles input:checked')].map(node => node.value);
    const rawSchema = document.querySelector('#edit-key-output-schema')?.value.trim() || '';
    let output_schema = null;
    try { output_schema = rawSchema ? JSON.parse(rawSchema) : null; }
    catch (_) { toast('最终输出规则不是合法 JSON', 'error'); return; }
    if (rawSchema && (Array.isArray(output_schema) || typeof output_schema !== 'object')) { toast('JSON Schema 必须是对象', 'error'); return; }
    try {
      await api(`/api-keys/${id}`, {method:'PATCH', body:JSON.stringify({
        name:document.querySelector('#edit-key-display-name').value.trim(),
        file_access:document.querySelector('#edit-key-file-access').value,
        role_ids,
        chat_tracking:document.querySelector('#edit-key-chat-tracking').checked,
        prompt_template_id:document.querySelector('#edit-key-prompt-template')?.value || null,
        output_schema,
      })});
      document.querySelector('#edit-key-dialog').close(); await loadAll(); toast('API Key 配置已保存');
    } catch(error) { toast(error.message, 'error'); }
  };
})();
</script>'''


ADMIN_PAGE += r'''<script>
(() => {
  const nav=document.querySelector('#nav'), main=document.querySelector('main'); if(!nav||!main)return;
  const button=document.createElement('button'); button.type='button'; button.dataset.view='feishu-applications'; button.className='nav-btn w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium'; button.textContent='飞书应用管理';
  const usersButton=nav.querySelector('[data-view="feishu"]'); usersButton?.insertAdjacentElement('beforebegin',button)||nav.appendChild(button);
  const panel=document.createElement('section'); panel.dataset.panel='feishu-applications'; panel.className='panel hidden space-y-6';
  panel.innerHTML=`<div class="flex items-start justify-between gap-4"><div><h2 class="text-xl font-semibold">飞书应用管理</h2><p class="mt-2 text-sm text-slate-400">应用与平台 Key 绑定；连接管理 Worker 会自动按此处的启停状态维护长连接。</p></div><button id="create-feishu-app" class="primary-btn">新增飞书应用</button></div><div id="feishu-application-list" class="grid gap-4 md:grid-cols-2"></div>`; main.appendChild(panel);
  const dialog=document.createElement('dialog'); dialog.className='w-[min(94vw,620px)] rounded-2xl border border-slate-700 bg-slate-900 p-0 text-slate-100'; dialog.innerHTML=`<form id="feishu-app-form" class="space-y-4 p-6"><div class="flex justify-between"><h2 class="text-xl font-semibold">新增飞书应用</h2><button type="button" onclick="this.closest('dialog').close()">×</button></div><label class="block text-sm">应用名称<input id="feishu-app-name" required maxlength="120" class="field mt-2" placeholder="财务助手"></label><label class="block text-sm">飞书 App ID<input id="feishu-app-id" required maxlength="128" class="field mt-2" placeholder="cli_xxx"></label><label class="block text-sm">飞书 App Secret<textarea id="feishu-app-secret" required maxlength="2048" rows="3" class="field mt-2" placeholder="仅加密保存，创建后不再回显"></textarea></label><label class="block text-sm">平台 API Key<select id="feishu-app-key" required class="field mt-2"></select></label><div class="flex justify-end gap-3"><button type="button" onclick="this.closest('dialog').close()" class="rounded-lg border border-slate-700 px-4 py-2">取消</button><button class="primary-btn">保存应用</button></div></form>`; document.body.appendChild(dialog);
  let applications=[];
  const status=(item)=>item.connection_status==='running'?'bg-emerald-500/15 text-emerald-300':item.connection_status==='error'?'bg-rose-500/15 text-rose-300':'bg-slate-700 text-slate-300';
  function draw(){const host=document.querySelector('#feishu-application-list');host.innerHTML=applications.length?applications.map(item=>`<article class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><div class="flex items-start justify-between gap-3"><div><h3 class="font-semibold">${esc(item.name)}</h3><p class="mt-1 font-mono text-xs text-emerald-300">${esc(item.app_id)}</p></div><span class="rounded-full px-2 py-1 text-xs ${status(item)}">${esc(item.connection_status)}</span></div><p class="mt-3 text-sm text-slate-400">平台 Key：${esc(item.api_key_name)}</p><p class="mt-1 text-xs text-slate-500">期望状态：${esc(item.desired_state)}${item.last_error?' · '+esc(item.last_error):''}</p><div class="mt-4 flex gap-2"><button data-app-action="start" data-app-id="${item.id}" class="rounded-lg border border-emerald-500/40 px-3 py-2 text-sm text-emerald-300">启动</button><button data-app-action="stop" data-app-id="${item.id}" class="rounded-lg border border-amber-500/40 px-3 py-2 text-sm text-amber-300">停止</button><button data-app-action="restart" data-app-id="${item.id}" class="rounded-lg border border-sky-500/40 px-3 py-2 text-sm text-sky-300">重启</button></div></article>`).join(''):'<p class="rounded-xl border border-dashed border-slate-700 p-8 text-center text-sm text-slate-500">尚未登记飞书应用。</p>';host.querySelectorAll('[data-app-action]').forEach(node=>node.onclick=async()=>{try{await api(`/feishu-applications/${node.dataset.appId}/${node.dataset.appAction}`,{method:'POST'});await load();toast('飞书应用状态已更新')}catch(e){toast(e.message,'error')}})}
  async function load(){applications=await api('/feishu-applications');draw()}
  document.querySelector('#create-feishu-app').onclick=()=>{document.querySelector('#feishu-app-key').innerHTML=(state.keys||[]).filter(key=>key.is_active).map(key=>`<option value="${key.id}">${esc(key.name)}</option>`).join('')||'<option value="">暂无启用 Key</option>';dialog.showModal()};
  document.querySelector('#feishu-app-form').onsubmit=async event=>{event.preventDefault();try{await api('/feishu-applications',{method:'POST',body:JSON.stringify({name:document.querySelector('#feishu-app-name').value.trim(),app_id:document.querySelector('#feishu-app-id').value.trim(),app_secret:document.querySelector('#feishu-app-secret').value.trim(),api_key_id:document.querySelector('#feishu-app-key').value})});event.target.reset();dialog.close();await load();toast('飞书应用已创建')}catch(e){toast(e.message,'error')}};
  button.onclick=async()=>{document.querySelectorAll('.panel').forEach(item=>item.classList.toggle('hidden',item!==panel));document.querySelectorAll('.nav-btn').forEach(item=>item.classList.toggle('active',item===button));document.querySelector('#page-title').textContent='飞书应用管理';try{await load()}catch(e){toast(e.message,'error')}};
  setTimeout(()=>nav.querySelector('[data-view="feishu"]')?.insertAdjacentElement('beforebegin',button),0);
})();
</script>'''

# This must be the final page enhancement so it owns the Key form handlers.
ADMIN_PAGE += r'''<script>
(() => {
  const options = selected => `<option value="">不绑定模板（仅全局规则）</option>${(state.promptTemplates || []).filter(item => item.is_active || item.id === selected).map(item => `<option value="${item.id}" ${item.id === selected ? 'selected' : ''}>${esc(item.name)}${item.is_active ? '' : '（已停用）'}</option>`).join('')}`;
  const ensure = () => {
    const createAnchor = document.querySelector('#key-roles');
    if (createAnchor && !document.querySelector('#key-prompt-template')) (createAnchor.previousElementSibling || createAnchor).insertAdjacentHTML('beforebegin', '<label class="mb-4 block text-sm text-slate-300">提示词模板<select id="key-prompt-template" class="field mt-2"></select></label>');
    const createSelect = document.querySelector('#key-prompt-template'); if (createSelect) createSelect.innerHTML = options(createSelect.value || null);
    const editAnchor = document.querySelector('#edit-key-roles');
    if (editAnchor && !document.querySelector('#edit-key-prompt-template')) (editAnchor.previousElementSibling || editAnchor).insertAdjacentHTML('beforebegin', '<label class="mb-5 block text-sm text-slate-300">提示词模板<select id="edit-key-prompt-template" class="field mt-2"></select></label>');
  };
  const render = window.render;
  window.render = () => { render(); ensure(); };
  const openKeyEditor = window.openKeyEditor;
  window.openKeyEditor = id => { openKeyEditor(id); ensure(); const key = state.keys.find(item => item.id === id); const select = document.querySelector('#edit-key-prompt-template'); if (select) select.innerHTML = options(key?.prompt_template_id || null); };
  document.querySelector('#key-form').onsubmit = async event => { event.preventDefault(); const form = new FormData(event.target); const role_ids = [...document.querySelectorAll('#key-roles input:checked')].map(item => item.value); try { const result = await api('/api-keys', {method:'POST', body:JSON.stringify({name:form.get('name'), file_access:form.get('file_access'), role_ids, chat_tracking:false, prompt_template_id:document.querySelector('#key-prompt-template')?.value || null})}); state.newKey=result.api_key; document.querySelector('#new-key').textContent=result.api_key; event.target.reset(); await loadAll(); } catch(error) { toast(error.message,'error'); } };
  document.querySelector('#edit-key-form').onsubmit = async event => { event.preventDefault(); const id=document.querySelector('#edit-key-id').value; const role_ids=[...document.querySelectorAll('#edit-key-roles input:checked')].map(item=>item.value); try { await api(`/api-keys/${id}`, {method:'PATCH', body:JSON.stringify({file_access:document.querySelector('#edit-key-file-access').value, role_ids, chat_tracking:document.querySelector('#edit-key-chat-tracking').checked, prompt_template_id:document.querySelector('#edit-key-prompt-template')?.value || null})}); document.querySelector('#edit-key-dialog').close(); await loadAll(); } catch(error) { toast(error.message,'error'); } };
  ensure();
})();
</script>'''

# Keep template assignment wired after all legacy Key-editor enhancements.
ADMIN_PAGE += r'''<script>
(() => {
  const templateOptions = selected => `<option value="">不绑定模板（仅全局规则）</option>${(state.promptTemplates || []).filter(item => item.is_active || item.id === selected).map(item => `<option value="${item.id}" ${item.id === selected ? 'selected' : ''}>${esc(item.name)}${item.is_active ? '' : '（已停用）'}</option>`).join('')}`;
  const addTemplateFields = () => {
    const createAnchor = document.querySelector('#key-roles');
    if (createAnchor && !document.querySelector('#key-prompt-template')) (createAnchor.previousElementSibling || createAnchor).insertAdjacentHTML('beforebegin', '<label class="mb-4 block text-sm text-slate-300">提示词模板<select id="key-prompt-template" class="field mt-2"></select></label>');
    const createSelect = document.querySelector('#key-prompt-template'); if (createSelect) createSelect.innerHTML = templateOptions(createSelect.value || null);
    const editAnchor = document.querySelector('#edit-key-roles');
    if (editAnchor && !document.querySelector('#edit-key-prompt-template')) (editAnchor.previousElementSibling || editAnchor).insertAdjacentHTML('beforebegin', '<label class="mb-5 block text-sm text-slate-300">提示词模板<select id="edit-key-prompt-template" class="field mt-2"></select></label>');
  };
  const baseRender = window.render;
  window.render = () => { baseRender(); addTemplateFields(); };
  const baseOpen = window.openKeyEditor;
  window.openKeyEditor = id => { baseOpen(id); addTemplateFields(); const key = state.keys.find(item => item.id === id); const select = document.querySelector('#edit-key-prompt-template'); if (select) select.innerHTML = templateOptions(key?.prompt_template_id || null); };
  document.querySelector('#key-form').onsubmit = async event => { event.preventDefault(); const form = new FormData(event.target); const role_ids = [...document.querySelectorAll('#key-roles input:checked')].map(item => item.value); try { const result = await api('/api-keys', {method:'POST', body:JSON.stringify({name:form.get('name'), file_access:form.get('file_access'), role_ids, chat_tracking:false, prompt_template_id:document.querySelector('#key-prompt-template')?.value || null})}); state.newKey = result.api_key; document.querySelector('#new-key').textContent = result.api_key; event.target.reset(); await loadAll(); } catch (error) { toast(error.message, 'error'); } };
  document.querySelector('#edit-key-form').onsubmit = async event => { event.preventDefault(); const id = document.querySelector('#edit-key-id').value; const role_ids = [...document.querySelectorAll('#edit-key-roles input:checked')].map(item => item.value); try { await api(`/api-keys/${id}`, {method:'PATCH', body:JSON.stringify({file_access:document.querySelector('#edit-key-file-access').value, role_ids, chat_tracking:document.querySelector('#edit-key-chat-tracking').checked, prompt_template_id:document.querySelector('#edit-key-prompt-template')?.value || null})}); document.querySelector('#edit-key-dialog').close(); await loadAll(); } catch (error) { toast(error.message, 'error'); } };
  addTemplateFields();
})();
</script>'''

# Add edit controls to dynamically rendered Feishu application cards.
ADMIN_PAGE += r'''<script>
(() => {
  const dialog=document.createElement('dialog'); dialog.id='edit-feishu-application-dialog'; dialog.className='w-[min(94vw,620px)] rounded-2xl border border-slate-700 bg-slate-900 p-6 text-slate-100';
  dialog.innerHTML='<form id="edit-feishu-application-form" class="space-y-4"><div class="flex justify-between"><h2 class="text-xl font-semibold">编辑飞书应用</h2><button type="button" onclick="this.closest(\'dialog\').close()">×</button></div><label class="block text-sm">应用名称<input id="edit-feishu-app-name" required class="field mt-2"></label><label class="block text-sm">飞书 App ID<input id="edit-feishu-app-id" required class="field mt-2"></label><label class="block text-sm">平台 API Key<select id="edit-feishu-app-key" class="field mt-2"></select></label><label class="block text-sm">更新 App Secret（留空则不变）<textarea id="edit-feishu-app-secret" rows="3" class="field mt-2"></textarea></label><div class="flex justify-end gap-3"><button type="button" onclick="this.closest(\'dialog\').close()" class="rounded-lg border border-slate-700 px-4 py-2">取消</button><button class="primary-btn">保存配置</button></div></form>'; document.body.appendChild(dialog);
  async function edit(id){const apps=await api('/feishu-applications');const app=apps.find(item=>item.id===id);if(!app)return;dialog.dataset.id=id;document.querySelector('#edit-feishu-app-name').value=app.name;document.querySelector('#edit-feishu-app-id').value=app.app_id;document.querySelector('#edit-feishu-app-secret').value='';document.querySelector('#edit-feishu-app-key').innerHTML=(state.keys||[]).filter(key=>key.is_active||key.id===app.api_key_id).map(key=>`<option value="${key.id}" ${key.id===app.api_key_id?'selected':''}>${esc(key.name)}</option>`).join('');dialog.showModal()}
  dialog.querySelector('form').onsubmit=async event=>{event.preventDefault();const id=dialog.dataset.id;const secret=document.querySelector('#edit-feishu-app-secret').value.trim();try{await api(`/feishu-applications/${id}`,{method:'PATCH',body:JSON.stringify({name:document.querySelector('#edit-feishu-app-name').value.trim(),app_id:document.querySelector('#edit-feishu-app-id').value.trim(),api_key_id:document.querySelector('#edit-feishu-app-key').value,app_secret:secret||null})});dialog.close();document.querySelector('[data-view="feishu-applications"]')?.click();toast('飞书应用已更新')}catch(e){toast(e.message,'error')}};
  const attach=()=>{const labels={stopped:'已停止',starting:'启动中',running:'已启动',stopping:'停止中',error:'启动失败'};document.querySelectorAll('#feishu-application-list article span').forEach(node=>{const raw=node.textContent.trim();if(labels[raw])node.textContent=labels[raw]});document.querySelectorAll('[data-app-action="start"]').forEach(start=>{const actions=start.parentElement;if(actions.querySelector('[data-app-edit]'))return;const editButton=document.createElement('button');editButton.type='button';editButton.dataset.appEdit=start.dataset.appId;editButton.className='rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200';editButton.textContent='编辑配置';editButton.onclick=()=>edit(editButton.dataset.appEdit);actions.prepend(editButton)})};
  new MutationObserver(attach).observe(document.body,{childList:true,subtree:true}); setTimeout(attach,0);
})();
</script>'''

# Keep the Key creation guidance focused on templates and RBAC rather than
# the legacy one-time-key warning.
ADMIN_PAGE += r'''<script>
setTimeout(() => {
  const form = document.querySelector('#key-form');
  const description = form?.querySelector('h2')?.nextElementSibling;
  if (description) description.textContent = '提示词模板确定 AI 的工作方式；角色控制 Tool 与 Skill 的访问权限。';
  form?.querySelectorAll('#key-prompt-template + span').forEach(item => item.remove());
}, 0);
</script>'''

# Prompt templates are managed independently from permissions, then assigned
# to API keys.  This final enhancement also keeps the existing compact page
# markup backwards-compatible.
ADMIN_PAGE += r'''<script>
(() => {
  state.promptTemplates = [];
  const previousLoadAll = window.loadAll;
  window.loadAll = async () => {
    await previousLoadAll();
    try { state.promptTemplates = await api('/prompt-templates'); window.render(); }
    catch (error) { toast(error.message, 'error'); }
  };
  const nav = document.querySelector('#nav'), main = document.querySelector('main');
  const button = document.createElement('button');
  button.type = 'button'; button.dataset.view = 'prompts';
  button.className = 'nav-btn w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium'; button.textContent = '提示词管理';
  const keyButton = nav.querySelector('[data-view="keys"]');
  keyButton?.insertAdjacentElement('beforebegin', button) || nav.appendChild(button);
  // The static API Key navigation is available after the base page loads;
  // keep prompt management immediately ahead of it.
  setTimeout(() => nav.querySelector('[data-view="keys"]')?.insertAdjacentElement('beforebegin', button), 0);
  const panel = document.createElement('section'); panel.dataset.panel = 'prompts'; panel.className = 'panel hidden space-y-6';
  panel.innerHTML = `<div class="flex flex-wrap items-start justify-between gap-4"><div><h2 class="text-xl font-semibold">提示词模板</h2><p class="mt-2 text-sm text-slate-400">模板定义 AI 的工作方式；Tool 和 Skill 权限仍由 API Key 的角色决定。</p></div><button id="create-prompt-template" class="primary-btn">新建模板</button></div><div id="prompt-template-list" class="grid gap-4 md:grid-cols-2 xl:grid-cols-3"></div>`;
  main.appendChild(panel);
  const dialog = document.createElement('dialog'); dialog.id = 'prompt-template-dialog';
  dialog.className = 'w-[min(94vw,760px)] rounded-2xl border border-slate-700 bg-slate-900 p-0 text-slate-100 shadow-2xl backdrop:bg-slate-950/80';
  dialog.innerHTML = `<form id="prompt-template-form" class="space-y-4 p-6"><div class="flex items-start justify-between gap-4"><div><h2 id="prompt-template-dialog-title" class="text-xl font-semibold">新建提示词模板</h2><p class="mt-1 text-sm text-slate-400">全局平台规则会自动叠加在模板之前。</p></div><button type="button" onclick="document.querySelector('#prompt-template-dialog').close()" class="text-xl text-slate-400 hover:text-white">×</button></div><label class="block text-sm">模板名称<input id="prompt-template-name" required maxlength="120" class="field mt-2" placeholder="企业知识助手"></label><label class="block text-sm">模板标识<input id="prompt-template-slug" required maxlength="100" pattern="[A-Za-z0-9_-]+" class="field mt-2" placeholder="knowledge_assistant"></label><label class="block text-sm">说明<textarea id="prompt-template-description" maxlength="2000" rows="2" class="field mt-2" placeholder="适用场景和管理员说明"></textarea></label><label class="block text-sm">系统提示词<textarea id="prompt-template-content" required maxlength="16000" rows="12" class="field mt-2 font-mono" placeholder="定义角色、流程、回答风格和输出格式"></textarea></label><label class="flex items-center gap-2 text-sm"><input id="prompt-template-active" type="checkbox" checked> 启用此模板</label><div class="flex justify-end gap-3"><button type="button" onclick="document.querySelector('#prompt-template-dialog').close()" class="rounded-lg border border-slate-700 px-4 py-2">取消</button><button class="primary-btn">保存模板</button></div></form>`;
  document.body.appendChild(dialog);
  const templateOptions = (selected = null) => `<option value="">不绑定模板（仅全局规则）</option>${state.promptTemplates.filter(item => item.is_active || item.id === selected).map(item => `<option value="${item.id}" ${item.id === selected ? 'selected' : ''}>${esc(item.name)}${item.is_active ? '' : '（已停用）'}</option>`).join('')}`;
  function ensureKeyTemplateFields() {
    const createAnchor = document.querySelector('#key-roles');
    if (createAnchor && !document.querySelector('#key-prompt-template')) (createAnchor.previousElementSibling || createAnchor).insertAdjacentHTML('beforebegin', `<label class="mb-4 block text-sm text-slate-300">提示词模板<select id="key-prompt-template" class="field mt-2">${templateOptions()}</select></label>`);
    const editAnchor = document.querySelector('#edit-key-roles');
    if (editAnchor && !document.querySelector('#edit-key-prompt-template')) (editAnchor.previousElementSibling || editAnchor).insertAdjacentHTML('beforebegin', `<label class="mb-5 block text-sm text-slate-300">提示词模板<select id="edit-key-prompt-template" class="field mt-2"></select></label>`);
    const createSelect = document.querySelector('#key-prompt-template'); if (createSelect) createSelect.innerHTML = templateOptions(createSelect.value || null);
  }
  function drawTemplates() {
    const host = document.querySelector('#prompt-template-list'); if (!host) return;
    host.innerHTML = state.promptTemplates.length ? state.promptTemplates.map(template => `<article class="rounded-2xl border ${template.is_active ? 'border-slate-800 bg-slate-900/60' : 'border-slate-800/70 bg-slate-950/60'} p-5"><div class="flex items-start justify-between gap-3"><div><h3 class="font-semibold">${esc(template.name)}</h3><p class="mt-1 font-mono text-xs text-emerald-300">${esc(template.slug)}</p></div><span class="rounded-full px-2 py-1 text-xs ${template.is_active ? 'bg-emerald-500/15 text-emerald-300' : 'bg-slate-700 text-slate-400'}">${template.is_active ? '已启用' : '已停用'}</span></div><p class="mt-3 min-h-10 text-sm text-slate-400">${esc(template.description || '暂无说明')}</p><div class="mt-4 flex items-center justify-between text-xs text-slate-500"><span>已绑定 ${template.api_key_count} 个 Key</span><span>v${template.version}</span></div><button data-prompt-edit="${template.id}" class="mt-4 rounded-lg border border-slate-700 px-3 py-2 text-sm text-sky-300 hover:border-sky-400">编辑模板</button></article>`).join('') : '<p class="rounded-xl border border-dashed border-slate-700 p-8 text-center text-sm text-slate-500">尚未创建提示词模板。</p>';
    host.querySelectorAll('[data-prompt-edit]').forEach(item => item.onclick = () => openTemplate(item.dataset.promptEdit));
  }
  function openTemplate(id = null) {
    const template = state.promptTemplates.find(item => item.id === id);
    dialog.dataset.templateId = template?.id || '';
    document.querySelector('#prompt-template-dialog-title').textContent = template ? '编辑提示词模板' : '新建提示词模板';
    document.querySelector('#prompt-template-name').value = template?.name || '';
    document.querySelector('#prompt-template-slug').value = template?.slug || '';
    document.querySelector('#prompt-template-description').value = template?.description || '';
    document.querySelector('#prompt-template-content').value = template?.system_prompt || '';
    document.querySelector('#prompt-template-active').checked = template?.is_active ?? true;
    dialog.showModal();
  }
  document.querySelector('#create-prompt-template').onclick = () => openTemplate();
  document.querySelector('#prompt-template-form').onsubmit = async event => { event.preventDefault(); const id = dialog.dataset.templateId; const payload = {name:document.querySelector('#prompt-template-name').value.trim(), slug:document.querySelector('#prompt-template-slug').value.trim(), description:document.querySelector('#prompt-template-description').value.trim() || null, system_prompt:document.querySelector('#prompt-template-content').value.trim(), is_active:document.querySelector('#prompt-template-active').checked}; try { await api(id ? `/prompt-templates/${id}` : '/prompt-templates', {method:id ? 'PATCH' : 'POST', body:JSON.stringify(payload)}); dialog.close(); await loadAll(); toast('提示词模板已保存'); } catch (error) { toast(error.message, 'error'); } };
  const priorRender = window.render;
  window.render = () => { priorRender(); ensureKeyTemplateFields(); drawTemplates(); };
  const priorOpenKeyEditor = window.openKeyEditor;
  window.openKeyEditor = id => { priorOpenKeyEditor(id); ensureKeyTemplateFields(); const key = state.keys.find(item => item.id === id); const select = document.querySelector('#edit-key-prompt-template'); if (select) select.innerHTML = templateOptions(key?.prompt_template_id || null); };
  document.querySelector('#key-form').onsubmit = async event => { event.preventDefault(); const form = new FormData(event.target); const role_ids = [...document.querySelectorAll('#key-roles input:checked')].map(item => item.value); try { const result = await api('/api-keys', {method:'POST', body:JSON.stringify({name:form.get('name'), file_access:form.get('file_access'), role_ids, chat_tracking:false, prompt_template_id:document.querySelector('#key-prompt-template')?.value || null})}); state.newKey = result.api_key; document.querySelector('#new-key').textContent = result.api_key; event.target.reset(); await loadAll(); } catch (error) { toast(error.message, 'error'); } };
  document.querySelector('#edit-key-form').onsubmit = async event => { event.preventDefault(); const id = document.querySelector('#edit-key-id').value; const role_ids = [...document.querySelectorAll('#edit-key-roles input:checked')].map(item => item.value); try { await api(`/api-keys/${id}`, {method:'PATCH', body:JSON.stringify({file_access:document.querySelector('#edit-key-file-access').value, role_ids, chat_tracking:document.querySelector('#edit-key-chat-tracking').checked, prompt_template_id:document.querySelector('#edit-key-prompt-template')?.value || null})}); document.querySelector('#edit-key-dialog').close(); await loadAll(); } catch (error) { toast(error.message, 'error'); } };
  button.onclick = () => { document.querySelectorAll('.panel').forEach(item => item.classList.toggle('hidden', item !== panel)); document.querySelectorAll('.nav-btn').forEach(item => item.classList.toggle('active', item === button)); document.querySelector('#page-title').textContent = '提示词管理'; drawTemplates(); };
  loadAll();
})();
</script>'''

# Skill catalog and grants are kept separate from tools: skills change the
# agent's instructions/resources, while tools perform external actions.
ADMIN_PAGE += r'''<script>
(() => {
  state.skills = [];
  const originalLoadAll = window.loadAll;
  window.loadAll = async () => {
    await originalLoadAll();
    try { state.skills = await api('/skills'); window.render(); }
    catch (error) { toast(error.message, 'error'); }
  };
  const nav = document.querySelector('#nav'), main = document.querySelector('main');
  const button = document.createElement('button');
  button.type = 'button'; button.dataset.view = 'skills'; button.className = 'nav-btn w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium'; button.textContent = 'Skill 管理';
  // Keep Skill management directly below the related MCP service entry.
  const mcpNavButton = nav.querySelector('[data-view="mcp"]');
  mcpNavButton?.insertAdjacentElement('afterend', button) || nav.appendChild(button);
  const panel = document.createElement('section');
  panel.dataset.panel = 'skills'; panel.className = 'panel hidden space-y-6';
  panel.innerHTML = `<div class="grid gap-6 xl:grid-cols-[380px_1fr]"><div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><h2 class="text-lg font-semibold">刷新 Skill 目录</h2><p class="mt-1 text-sm text-slate-400">扫描 AGENT_SKILLS_DIR 下所有 SKILL.md。文件系统是唯一事实来源；已删除目录会在刷新后从可用列表移除。</p><button id="sync-skills" class="primary-btn mt-5 w-full">刷新 Skill 目录</button></div><div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><h2 class="text-lg font-semibold">已发现 Skill</h2><div id="skill-list" class="mt-4 grid gap-3 sm:grid-cols-2"></div></div></div>`;
  main.appendChild(panel);
  function drawSkills() { const target = document.querySelector('#skill-list'); if (!target) return; target.innerHTML = state.skills.length ? state.skills.map(skill => `<article class="rounded-xl border border-slate-800 bg-slate-950 p-4"><h3 class="font-mono font-semibold">${esc(skill.name)}</h3><p class="mt-1 text-xs text-emerald-300">${esc(skill.path)}</p><p class="mt-2 text-sm text-slate-400">${esc(skill.description || '暂无说明')}</p></article>`).join('') : '<p class="text-sm text-slate-500">尚未登记 Skill。</p>'; }
  const baseRender = window.render;
  window.render = () => {
    baseRender(); drawSkills();
    const box = document.querySelector('#role-tools'); if (!box) return;
    document.querySelector('#role-skills')?.closest('.mt-6')?.remove();
    box.insertAdjacentHTML('afterend', '<div class="mt-6 border-t border-slate-800 pt-5"><h3 class="font-semibold">给角色分配 Skill</h3><p class="mt-1 text-sm text-slate-400">Skill 仅提供流程和资料，不直接授予 Tool 权限。</p><div id="role-skills" class="mt-4 grid gap-3 sm:grid-cols-2"></div><button id="save-role-skills" class="primary-btn mt-5">保存 Skill 授权</button></div>');
    const select = document.querySelector('#role-select');
    const drawRoleSkills = () => { const role = state.roles.find(item => item.id === select.value) || state.roles[0]; document.querySelector('#role-skills').innerHTML = state.skills.map(skill => `<label class="flex cursor-pointer gap-3 rounded-xl border border-slate-800 bg-slate-950 p-3"><input type="checkbox" value="${skill.id}" ${(role?.skill_ids || []).includes(skill.id) ? 'checked' : ''}><span><span class="block font-mono text-sm">${esc(skill.name)}</span><span class="mt-1 block text-xs text-slate-500">${esc(skill.path)}</span></span></label>`).join('') || '<p class="text-sm text-slate-500">暂无已登记 Skill。</p>'; };
    select.addEventListener('change', drawRoleSkills); drawRoleSkills();
    document.querySelector('#save-role-skills').onclick = async () => { try { const skill_ids = [...document.querySelectorAll('#role-skills input:checked')].map(item => item.value); await api(`/roles/${select.value}/skills`, {method:'PUT', body:JSON.stringify({skill_ids})}); toast('Skill 授权已保存'); await loadAll(); } catch (error) { toast(error.message, 'error'); } };
  };
  document.querySelector('#sync-skills').onclick = async () => { try { const skills = await api('/skills/sync', {method:'POST'}); state.skills = skills; window.render(); toast(`已发现 ${skills.length} 个 Skill`); } catch (error) { toast(error.message, 'error'); } };
  button.onclick = () => { document.querySelectorAll('.panel').forEach(item => item.classList.toggle('hidden', item !== panel)); document.querySelectorAll('.nav-btn').forEach(item => item.classList.toggle('active', item === button)); document.querySelector('#page-title').textContent = 'Skill 管理'; drawSkills(); };
  loadAll();
})();
</script>'''

# Role authoring is a selection-first flow: create, choose a role, then edit
# its Tool and Skill grants side by side.
ADMIN_PAGE += r'''<script>
(() => {
  let selectedRoleId = null;
  const priorRender = window.render;
  const labelList = (ids, collection) => ids.map(id => collection.find(item => item.id === id)?.name).filter(Boolean);
  function selectRole(roleId) {
    selectedRoleId = roleId;
    const select = document.querySelector('#role-select');
    if (select) { select.value = roleId; if (typeof window.renderRoleTools === 'function') window.renderRoleTools(); }
    drawRoleCards(); updateAssignmentHeading();
  }
  function openRoleEditor(roleId) {
    const role = state.roles.find(item => item.id === roleId); if (!role) return;
    let dialog = document.querySelector('#role-edit-dialog');
    if (!dialog) {
      dialog = document.createElement('dialog'); dialog.id = 'role-edit-dialog'; dialog.className = 'w-[min(94vw,560px)] rounded-2xl border border-slate-700 bg-slate-900 p-0 text-slate-100 shadow-2xl backdrop:bg-slate-950/80';
      dialog.innerHTML = '<form id="role-edit-form" class="space-y-4 p-6"><div class="flex items-start justify-between gap-4"><div><h2 class="text-xl font-semibold">编辑角色</h2><p class="mt-1 text-sm text-slate-400">修改名称、说明和启用状态。</p></div><button type="button" onclick="document.querySelector(\'#role-edit-dialog\').close()" class="text-xl text-slate-400 hover:text-white">×</button></div><label class="block text-sm">角色名<input id="role-edit-name" required pattern="[A-Za-z0-9_-]+" class="field mt-2"></label><label class="block text-sm">说明<textarea id="role-edit-description" rows="3" class="field mt-2"></textarea></label><fieldset class="flex gap-5 text-sm"><legend class="mb-2">状态</legend><label><input type="radio" name="role-edit-active" value="true"> 启用</label><label><input type="radio" name="role-edit-active" value="false"> 停用</label></fieldset><button class="primary-btn w-full">保存角色</button></form>';
      document.body.appendChild(dialog);
      dialog.querySelector('#role-edit-form').onsubmit = async event => { event.preventDefault(); const id = dialog.dataset.roleId; const name = document.querySelector('#role-edit-name').value.trim(); if (state.roles.some(item => item.id !== id && item.name.toLocaleLowerCase() === name.toLocaleLowerCase())) return toast('角色名称已存在，不能重复创建', 'error'); try { await api(`/roles/${id}`, {method:'PATCH', body:JSON.stringify({name, description:document.querySelector('#role-edit-description').value || null, is_active:document.querySelector('input[name="role-edit-active"]:checked').value === 'true'})}); dialog.close(); toast('角色已更新'); await loadAll(); } catch (error) { toast(error.message, 'error'); } };
    }
    dialog.dataset.roleId = role.id; document.querySelector('#role-edit-name').value = role.name; document.querySelector('#role-edit-description').value = role.description || ''; document.querySelector(`input[name="role-edit-active"][value="${role.is_active ? 'true' : 'false'}"]`).checked = true; dialog.showModal();
  }
  function drawRoleCards() {
    const list = document.querySelector('#role-list'); if (!list) return;
    if (!selectedRoleId || !state.roles.some(role => role.id === selectedRoleId)) selectedRoleId = state.roles[0]?.id || null;
    list.className = 'mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3';
    list.innerHTML = state.roles.length ? state.roles.map(role => {
      const tools = labelList(role.tool_ids || [], state.tools || []), skills = labelList(role.skill_ids || [], state.skills || []);
      const title = `工具：${tools.join('、') || '无'}\nSkill：${skills.join('、') || '无'}`;
      const isDisabled = !role.is_active;
      const cardTone = role.id === selectedRoleId
        ? 'border-emerald-400 bg-emerald-400/10'
        : isDisabled
          ? 'border-slate-700/80 bg-gradient-to-br from-slate-900/70 to-slate-950 hover:border-slate-600'
          : 'border-slate-800 bg-slate-950 hover:border-slate-600';
      const grantTone = isDisabled ? 'bg-slate-800/80 text-slate-400' : 'bg-sky-500/15 text-sky-200';
      const skillTone = isDisabled ? 'bg-slate-800/80 text-slate-400' : 'bg-violet-500/15 text-violet-200';
      const statusBadge = isDisabled
        ? '<span class="inline-flex shrink-0 items-center gap-1 rounded-full border border-slate-600 bg-slate-800 px-2 py-1 text-xs font-medium text-slate-300"><span class="h-1.5 w-1.5 rounded-full bg-slate-500"></span>已停用</span>'
        : '<span class="inline-flex shrink-0 items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2 py-1 text-xs font-medium text-emerald-300"><span class="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>已启用</span>';
      const statusHint = isDisabled ? '该角色暂不参与授权计算' : '该角色正在参与授权计算';
      return `<button type="button" data-role-card="${role.id}" title="${esc(title)}" class="rounded-xl border p-4 text-left transition ${cardTone}"><div class="flex items-center justify-between gap-3"><div class="flex min-w-0 items-center gap-2"><h3 class="truncate font-semibold ${isDisabled ? 'text-slate-300' : ''}">${esc(role.name)}</h3>${statusBadge}</div></div><p class="mt-2 min-h-10 text-sm ${isDisabled ? 'text-slate-500' : 'text-slate-400'}">${esc(role.description || '暂无说明')}</p><p class="mt-2 text-xs ${isDisabled ? 'text-slate-500' : 'text-emerald-300/80'}">${statusHint}</p><div class="mt-4 flex gap-2"><span title="${esc(tools.join('、') || '无工具')}" class="rounded-full px-2 py-1 text-xs ${grantTone}">${tools.length} Tool</span><span title="${esc(skills.join('、') || '无 Skill')}" class="rounded-full px-2 py-1 text-xs ${skillTone}">${skills.length} Skill</span></div></button>`;
    }).join('') : '<p class="text-sm text-slate-500">先在上方创建角色。</p>';
    list.querySelectorAll('[data-role-card]').forEach(card => { card.onclick = () => selectRole(card.dataset.roleCard); const role = state.roles.find(item => item.id === card.dataset.roleCard); const header = card.firstElementChild; const edit = document.createElement('button'); edit.type = 'button'; edit.textContent = '编辑'; edit.className = `shrink-0 rounded border px-2 py-1 text-xs transition ${role.is_active ? 'border-slate-700 text-slate-300 hover:border-emerald-400 hover:text-emerald-200' : 'border-slate-700/80 text-slate-400 hover:border-slate-500 hover:text-slate-200'}`; edit.onclick = event => { event.stopPropagation(); openRoleEditor(role.id); }; header.appendChild(edit); });
  }
  function updateAssignmentHeading() {
    const role = state.roles.find(item => item.id === selectedRoleId);
    const heading = document.querySelector('#role-assignment-heading');
    const help = document.querySelector('#role-assignment-help');
    if (heading) heading.textContent = role ? `配置角色：${role.name}` : '选择一个角色';
    if (help) help.textContent = role ? '分别保存 Tool 与 Skill 授权。' : '请先创建并选择一个角色。';
  }
  function arrangeRolePage() {
    const panel = document.querySelector('[data-panel="roles"]');
    const form = document.querySelector('#role-form');
    const list = document.querySelector('#role-list');
    const allocation = document.querySelector('#role-tools')?.closest('.rounded-2xl');
    if (!panel || !form || !list || !allocation) return;
    if (!selectedRoleId || !state.roles.some(role => role.id === selectedRoleId)) selectedRoleId = state.roles[0]?.id || null;
    const legacyListHost = list.parentElement;
    const formHost = document.querySelector('#role-create-host') || Object.assign(document.createElement('div'), {id: 'role-create-host', className: 'rounded-2xl border border-slate-800 bg-slate-900/60 p-5'});
    const listHost = document.querySelector('#role-list-host') || Object.assign(document.createElement('div'), {id: 'role-list-host', className: 'rounded-2xl border border-slate-800 bg-slate-900/60 p-5'});
    // The original page placed form and grants in a two-column wrapper. Move
    // the grants out of that wrapper before laying out this selection-first UI;
    // otherwise the grants inherit a narrow left column on wide screens.
    const legacyGrid = allocation.parentElement;
    if (legacyGrid !== panel) {
      panel.appendChild(allocation);
      if (!legacyGrid.children.length) legacyGrid.remove();
    }
    if (!formHost.parentElement) panel.prepend(formHost);
    panel.prepend(formHost);
    panel.insertBefore(listHost, allocation);
    if (legacyGrid !== panel && !legacyGrid.children.length) legacyGrid.remove();
    if (legacyListHost && legacyListHost !== listHost && !legacyListHost.contains(list)) legacyListHost.remove();
    let dialog = document.querySelector('#role-create-dialog');
    if (!dialog) {
      formHost.innerHTML = '<div class="flex items-center justify-between gap-4"><div><h2 class="text-lg font-semibold">角色</h2><p class="mt-1 text-sm text-slate-400">创建后即可配置 Tool 与 Skill。</p></div><button id="open-role-create" type="button" class="primary-btn">创建角色</button></div>';
      dialog = document.createElement('dialog'); dialog.id = 'role-create-dialog'; dialog.className = 'w-[min(94vw,560px)] rounded-2xl border border-slate-700 bg-slate-900 p-0 text-slate-100 shadow-2xl backdrop:bg-slate-950/80';
      form.className = 'space-y-4 p-6'; dialog.appendChild(form); document.body.appendChild(dialog);
      document.querySelector('#open-role-create').onclick = () => dialog.showModal();
      form.insertAdjacentHTML('afterbegin', '<div class="flex items-start justify-between gap-4"><div><h2 class="text-xl font-semibold">创建角色</h2><p class="mt-1 text-sm text-slate-400">填写角色名称和说明。</p></div><button type="button" onclick="document.querySelector(\'#role-create-dialog\').close()" class="text-xl text-slate-400 hover:text-white">×</button></div>');
      form.querySelectorAll('h2:not(:first-child), p:not(:first-child)').forEach(item => item.remove());
      form.querySelector('.primary-btn').insertAdjacentHTML('beforebegin', '<fieldset class="flex gap-5 text-sm"><legend class="mb-2">状态</legend><label><input type="radio" name="is_active" value="true" checked> 启用</label><label><input type="radio" name="is_active" value="false"> 停用</label></fieldset>');
    }
    if (legacyGrid !== panel && !legacyGrid.children.length) legacyGrid.remove();
    listHost.innerHTML = '<div class="flex items-center justify-between"><div><h2 class="text-lg font-semibold">角色一览</h2><p class="mt-1 text-sm text-slate-400">悬停查看已分配的具体 Tool 与 Skill；点击角色开始配置。</p></div></div>';
    listHost.appendChild(list);
    if (legacyListHost && legacyListHost !== listHost && !legacyListHost.contains(list)) legacyListHost.remove();
    allocation.querySelector('h2')?.remove(); allocation.querySelector('p')?.remove();
    allocation.querySelector('#role-select')?.classList.add('hidden');
    let heading = allocation.querySelector('#role-assignment-heading');
    if (!heading) { heading = document.createElement('h2'); heading.id = 'role-assignment-heading'; heading.className = 'text-lg font-semibold'; allocation.prepend(heading); }
    let help = allocation.querySelector('#role-assignment-help');
    if (!help) { help = document.createElement('p'); help.id = 'role-assignment-help'; help.className = 'mt-1 text-sm text-slate-400'; heading.after(help); }
    let columns = allocation.querySelector('#role-assignment-columns');
    if (!columns) { columns = document.createElement('div'); columns.id = 'role-assignment-columns'; columns.className = 'mt-5 grid gap-6 xl:grid-cols-2'; allocation.appendChild(columns); }
    let toolColumn = columns.querySelector('#role-tool-column');
    if (!toolColumn) { toolColumn = document.createElement('section'); toolColumn.id = 'role-tool-column'; toolColumn.className = 'rounded-xl border border-slate-800 bg-slate-950/50 p-4'; toolColumn.innerHTML = '<h3 class="font-semibold">Tool 授权</h3><p class="mt-1 text-sm text-slate-400">允许角色调用的 MCP 与内置工具。</p>'; columns.appendChild(toolColumn); }
    let skillColumn = columns.querySelector('#role-skill-column');
    if (!skillColumn) { skillColumn = document.createElement('section'); skillColumn.id = 'role-skill-column'; skillColumn.className = 'rounded-xl border border-slate-800 bg-slate-950/50 p-4'; skillColumn.innerHTML = '<h3 class="font-semibold">Skill 授权</h3><p class="mt-1 text-sm text-slate-400">提供流程、资料和模板，不直接授予系统动作。</p>'; columns.appendChild(skillColumn); }
    toolColumn.appendChild(document.querySelector('#role-tools'));
    toolColumn.appendChild(document.querySelector('#save-role-tools'));
    document.querySelector('#role-tools').className = 'mt-4 grid gap-3';
    document.querySelectorAll('#role-skills').forEach(box => box.closest('.mt-6')?.remove() || box.remove());
    document.querySelectorAll('#save-role-skills').forEach(button => button.remove());
    const selected = state.roles.find(role => role.id === selectedRoleId) || state.roles[0];
    const assigned = new Set(selected?.skill_ids || []);
    skillColumn.innerHTML = '<h3 class="font-semibold">Skill 授权</h3><p class="mt-1 text-sm text-slate-400">提供流程、资料和模板，不直接授予系统动作。</p>' + (state.skills?.length ? `<div id="clean-role-skills" class="mt-4 grid gap-3">${state.skills.map(skill => `<label class="flex cursor-pointer gap-3 rounded-xl border border-slate-800 bg-slate-900 p-3"><input type="checkbox" value="${skill.id}" ${assigned.has(skill.id) ? 'checked' : ''}><span><span class="block font-mono text-sm">${esc(skill.name)}</span><span class="mt-1 block text-xs text-slate-500">${esc(skill.path)}</span></span></label>`).join('')}</div><button id="save-clean-role-skills" class="primary-btn mt-5">保存 Skill 授权</button>` : '<p class="mt-4 text-sm text-slate-500">暂无已发现 Skill。</p>');
    skillColumn.querySelector('#save-clean-role-skills')?.addEventListener('click', async () => { try { const skill_ids = [...skillColumn.querySelectorAll('#clean-role-skills input:checked')].map(item => item.value); await api(`/roles/${selectedRoleId}/skills`, {method:'PUT', body:JSON.stringify({skill_ids})}); toast('Skill 授权已保存'); await loadAll(); } catch (error) { toast(error.message, 'error'); } });
    updateAssignmentHeading(); drawRoleCards();
  }
  window.render = () => { priorRender(); arrangeRolePage(); };
  setTimeout(() => { arrangeRolePage(); drawRoleCards(); }, 0);
})();
</script>'''

ADMIN_PAGE += r'''<script>
(() => {
  const nav = document.querySelector('#nav');
  const main = document.querySelector('main');
  if (!nav || !main || document.querySelector('[data-panel="feishu"]')) return;
  const button = document.createElement('button');
  button.type = 'button'; button.dataset.view = 'feishu';
  button.className = 'nav-btn w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium';
  button.textContent = '飞书用户管理'; nav.appendChild(button);
  const panel = document.createElement('section');
  panel.dataset.panel = 'feishu'; panel.className = 'panel hidden space-y-6';
  panel.innerHTML = `<div><h2 class="text-xl font-semibold">飞书用户管理</h2><p class="mt-2 text-sm text-slate-400">角色授权可叠加用户额外工具和 Skill。</p></div><div class="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60"><table class="w-full min-w-[960px] text-left text-sm"><thead class="bg-slate-900 text-slate-400"><tr><th class="px-5 py-3">飞书用户</th><th>角色</th><th>额外工具</th><th>最终工具</th><th>会话</th><th>状态</th><th>操作</th></tr></thead><tbody id="feishu-user-rows" class="divide-y divide-slate-800"></tbody></table></div><dialog id="feishu-user-dialog" class="w-[min(94vw,680px)] rounded-2xl border border-slate-700 bg-slate-900 p-6 text-slate-100"><h3 id="feishu-user-name" class="text-xl font-semibold"></h3><p id="feishu-user-openid" class="mt-1 text-xs text-slate-400"></p><p class="mt-5 text-sm">额外角色</p><div id="feishu-user-roles" class="mt-2 grid gap-2 sm:grid-cols-2"></div><p class="mt-5 text-sm">额外工具</p><div id="feishu-user-tools" class="mt-2 grid gap-2 sm:grid-cols-2"></div><p class="mt-5 text-sm">额外 Skill</p><div id="feishu-user-skills" class="mt-2 grid gap-2 sm:grid-cols-2"></div><label class="mt-5 flex gap-2"><input id="feishu-user-active" type="checkbox"> 启用该用户</label><div class="mt-6 flex justify-end gap-3"><button onclick="document.querySelector('#feishu-user-dialog').close()" class="rounded-lg border border-slate-700 px-4 py-2">取消</button><button id="save-feishu-user" class="primary-btn">保存</button></div></dialog>`;
  main.appendChild(panel);
  const applicationFilter=document.createElement('div'); applicationFilter.className='flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-4'; applicationFilter.innerHTML='<label for="feishu-application-filter" class="text-sm font-semibold">飞书应用</label><select id="feishu-application-filter" class="field max-w-sm"></select><span id="feishu-application-hint" class="text-xs text-slate-400"></span>'; panel.querySelector('.overflow-x-auto').before(applicationFilter);
  let feishuUsers = [], feishuApplications = [], selectedFeishuApplicationId = '', editingUser = null;
  applicationFilter.querySelector('#feishu-application-filter').onchange = async event => { selectedFeishuApplicationId = event.target.value; try { await loadFeishuUsers(); } catch (error) { toast(error.message, 'error'); } };
  const chip = name => `<span title="${esc(name)}" class="mr-1 inline-block max-w-36 truncate rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-300">${esc(name)}</span>`;
  async function loadFeishuUsers() {
    feishuApplications = await api('/feishu-applications');
    if (!feishuApplications.some(app => app.id === selectedFeishuApplicationId)) selectedFeishuApplicationId = feishuApplications[0]?.id || '';
    const select = document.querySelector('#feishu-application-filter');
    select.innerHTML = feishuApplications.map(app => `<option value="${app.id}">${esc(app.name)} · ${esc(app.api_key_name)}</option>`).join(''); select.value = selectedFeishuApplicationId;
    document.querySelector('#feishu-application-hint').textContent = feishuApplications.length ? '仅显示当前应用的用户、会话与权限。' : '请先创建飞书应用。';
    const users = selectedFeishuApplicationId ? await api('/feishu-users?application_id=' + encodeURIComponent(selectedFeishuApplicationId)) : []; feishuUsers = users;
    const rows = document.querySelector('#feishu-user-rows');
    rows.innerHTML = users.length ? users.map(user => {
      const roles = user.role_ids.map(id => state.roles.find(role => role.id === id)?.name).filter(Boolean);
      const extras = user.extra_tool_ids.map(id => state.tools.find(tool => tool.id === id)?.name).filter(Boolean);
      return `<tr><td class="px-5 py-4"><p class="font-semibold">${esc(user.display_name)}</p><p class="mt-1 font-mono text-xs text-slate-500">${esc(user.open_id)}</p></td><td>${roles.map(chip).join('') || '—'}</td><td>${extras.map(chip).join('') || '—'}</td><td>${user.effective_tools.map(tool => chip(tool.name)).join('') || '—'}</td><td><a class="text-sky-300 hover:text-sky-200" href="/admin/feishu-users/${user.id}/sessions/view">${user.session_count} 个会话</a></td><td><span class="rounded-full px-2 py-1 text-xs ${user.is_active ? 'bg-emerald-500/15 text-emerald-300' : 'bg-slate-700 text-slate-400'}">${user.is_active ? '启用' : '禁用'}</span></td><td><button data-feishu-edit="${user.id}" class="text-sky-300 hover:text-sky-200">编辑</button></td></tr>`;
    }).join('') : '<tr><td colspan="7" class="px-5 py-12 text-center text-slate-500">飞书用户发送第一条消息后会自动出现在这里。</td></tr>';
    const header = panel.querySelector('thead tr');
    if (header && !header.querySelector('[data-feishu-keys-header]')) header.children[header.children.length - 1].insertAdjacentHTML('beforebegin', '<th data-feishu-keys-header>已配置 Key</th>');
    rows.querySelectorAll('tr').forEach((row, index) => { const user = users[index]; if (!user || row.querySelector('[data-feishu-keys-cell]')) return; const keys = (user.key_profiles || []).map(profile => chip(profile.api_key_name)).join('') || '—'; row.children[row.children.length - 1].insertAdjacentHTML('beforebegin', `<td data-feishu-keys-cell>${keys}</td>`); });
    rows.querySelectorAll('[data-feishu-edit]').forEach(element => element.onclick = () => editFeishuUser(element.dataset.feishuEdit));
  }
  function editFeishuUser(id) {
    editingUser = feishuUsers.find(user => user.id === id); if (!editingUser) return;
    document.querySelector('#feishu-user-name').textContent = editingUser.display_name;
    document.querySelector('#feishu-user-openid').textContent = `${editingUser.application_name} · ${editingUser.open_id}`;
    document.querySelector('#feishu-user-active').checked = editingUser.is_active;
    document.querySelector('#feishu-user-roles').innerHTML = state.roles.map(role => `<label><input type="checkbox" value="${role.id}" ${editingUser.role_ids.includes(role.id) ? 'checked' : ''}> ${esc(role.name)}</label>`).join('');
    document.querySelector('#feishu-user-tools').innerHTML = state.tools.map(tool => `<label><input type="checkbox" value="${tool.id}" ${editingUser.extra_tool_ids.includes(tool.id) ? 'checked' : ''}> ${esc(tool.name)}</label>`).join('');
    document.querySelector('#feishu-user-skills').innerHTML = (state.skills || []).map(skill => `<label><input type="checkbox" value="${skill.id}" ${(editingUser.extra_skill_ids || []).includes(skill.id) ? 'checked' : ''}> ${esc(skill.name)}</label>`).join('') || '<span class="text-sm text-slate-500">暂无已登记 Skill</span>';
    document.querySelector('#feishu-user-key-profiles')?.remove();
    const configured = new Map((editingUser.key_profiles || []).map(profile => [profile.api_key_id, profile]));
    // Only the API Key bound to this user's Feishu application is relevant.
    const originalKeys = state.keys;
    const boundApplication = feishuApplications.find(app => app.id === editingUser.application_id);
    state.keys = (state.keys || []).filter(key => key.is_active && key.id === boundApplication?.api_key_id);
    document.querySelector('#feishu-user-skills').insertAdjacentHTML('afterend', `<div id="feishu-user-key-profiles" class="mt-5"><p class="text-sm">按 Key 的个性化提示词</p><p class="mt-1 text-xs text-slate-500">仅影响当前 Key 的回答偏好，不会改变 Tool 或 Skill 权限。</p><div class="mt-3 space-y-3">${(state.keys || []).filter(key => key.is_active).map(key => { const profile = configured.get(key.id); return `<label class="block rounded-xl border border-slate-700 bg-slate-950 p-3"><span class="flex items-center gap-2"><input data-key-profile-enabled="${key.id}" type="checkbox" ${profile ? 'checked' : ''}><span class="font-medium">${esc(key.name)}</span><span class="text-xs text-slate-500">${esc(key.prompt_template_name || '仅全局规则')}</span></span><textarea data-key-profile-prompt="${key.id}" maxlength="4000" rows="3" class="field mt-3" placeholder="该用户在此 Key 下的工作偏好">${esc(profile?.prompt_profile || '')}</textarea></label>`; }).join('') || '<p class="text-sm text-slate-500">暂无可配置的启用 Key。</p>'}</div></div>`);
    document.querySelector('#feishu-user-dialog').showModal();
    state.keys = originalKeys;
  }
  document.querySelector('#save-feishu-user').onclick = async () => {
    if (!editingUser) return;
    const checked = selector => [...document.querySelectorAll(selector + ' input:checked')].map(item => item.value);
    const key_profiles = [...document.querySelectorAll('[data-key-profile-enabled]:checked')].map(input => ({api_key_id:input.dataset.keyProfileEnabled, is_active:true, prompt_profile:document.querySelector(`[data-key-profile-prompt="${input.dataset.keyProfileEnabled}"]`).value.trim() || null}));
    try { await api(`/feishu-users/${editingUser.id}`, {method:'PUT', body:JSON.stringify({role_ids:checked('#feishu-user-roles'), extra_tool_ids:checked('#feishu-user-tools'), extra_skill_ids:checked('#feishu-user-skills'), key_profiles, is_active:document.querySelector('#feishu-user-active').checked})}); document.querySelector('#feishu-user-dialog').close(); await loadFeishuUsers(); toast('飞书用户权限已保存'); } catch (error) { toast(error.message, 'error'); }
  };
  button.onclick = async () => { document.querySelectorAll('.panel').forEach(item => item.classList.toggle('hidden', item !== panel)); document.querySelectorAll('.nav-btn').forEach(item => item.classList.toggle('active', item === button)); document.querySelector('#page-title').textContent = '飞书用户管理'; try { await loadFeishuUsers(); } catch (error) { toast(error.message, 'error'); } };
})();
</script>'''


# Final interaction rules: tracking is configured only in the edit dialog.
ADMIN_PAGE += r'''<script>
(() => {
  const enhancedRender = window.render;
  window.render = () => { enhancedRender(); document.querySelector('#key-tracking-row')?.remove(); };
  window.openKeyEditor = id => {
    const key = state.keys.find(item => item.id === id); if (!key) return;
    document.querySelector('#edit-key-id').value = id;
    document.querySelector('#edit-key-name').textContent = key.name + ' · ' + key.key_prefix + '…';
    document.querySelector('#edit-key-display-name-field')?.remove();
    document.querySelector('#edit-key-file-access').closest('label').insertAdjacentHTML('beforebegin', '<label id="edit-key-display-name-field" class="mb-5 block text-sm text-slate-300">Key 名称<input id="edit-key-display-name" required maxlength="120" class="field mt-2"></label>');
    document.querySelector('#edit-key-display-name').value = key.name;
    document.querySelector('#edit-key-file-access').value = key.file_access;
    document.querySelector('#edit-key-tracking-row')?.remove();
    document.querySelector('#edit-key-file-access').closest('label').insertAdjacentHTML('beforebegin', '<label id="edit-key-tracking-row" class="mb-5 flex cursor-pointer items-center justify-between text-sm"><span class="font-semibold">跟踪聊天内容</span><input id="edit-key-chat-tracking" type="checkbox" class="peer sr-only"><span class="h-6 w-11 rounded-full bg-slate-700 transition peer-checked:bg-emerald-500 after:ml-1 after:mt-1 after:block after:h-4 after:w-4 after:rounded-full after:bg-white after:transition peer-checked:after:translate-x-5"></span></label>');
    document.querySelector('#edit-key-chat-tracking').checked = Boolean(key.chat_tracking);
    const promptTemplate = document.querySelector('#edit-key-prompt-template');
    if (promptTemplate) promptTemplate.innerHTML = `<option value="">不绑定模板（仅全局规则）</option>${(state.promptTemplates || []).filter(item => item.is_active || item.id === key.prompt_template_id).map(item => `<option value="${item.id}" ${item.id === key.prompt_template_id ? 'selected' : ''}>${esc(item.name)}${item.is_active ? '' : '（已停用）'}</option>`).join('')}`;
    document.querySelector('#edit-key-roles').innerHTML = state.roles.map(role => `<label class="flex gap-3"><input type="checkbox" value="${role.id}" ${key.role_ids.includes(role.id) ? 'checked' : ''}><span>${esc(role.name)}</span></label>`).join('');
    document.querySelector('#edit-key-dialog').showModal();
  };
  document.querySelector('#key-form').onsubmit = async event => { event.preventDefault(); const form=new FormData(event.target); const role_ids=[...document.querySelectorAll('#key-roles input:checked')].map(node=>node.value); try { const result=await api('/api-keys',{method:'POST',body:JSON.stringify({name:form.get('name'),file_access:form.get('file_access'),role_ids,chat_tracking:false,prompt_template_id:document.querySelector('#key-prompt-template')?.value || null})}); state.newKey=result.api_key; document.querySelector('#new-key').textContent=result.api_key; event.target.reset(); await loadAll(); } catch(error) { toast(error.message,'error'); } };
  document.querySelector('#edit-key-form').onsubmit = async event => { event.preventDefault(); const id=document.querySelector('#edit-key-id').value; const role_ids=[...document.querySelectorAll('#edit-key-roles input:checked')].map(node=>node.value); try { await api(`/api-keys/${id}`,{method:'PATCH',body:JSON.stringify({name:document.querySelector('#edit-key-display-name').value.trim(),file_access:document.querySelector('#edit-key-file-access').value,role_ids,chat_tracking:document.querySelector('#edit-key-chat-tracking').checked,prompt_template_id:document.querySelector('#edit-key-prompt-template')?.value || null})}); document.querySelector('#edit-key-dialog').close(); await loadAll(); } catch(error) { toast(error.message,'error'); } };
})();
</script>'''


# This must remain at EOF: the legacy console rebinds the Key editor several times.
ADMIN_PAGE += r'''<script>
(() => {
  const previousOpenKeyEditor = window.openKeyEditor;
  window.openKeyEditor = id => {
    previousOpenKeyEditor(id);
    const key = state.keys.find(item => item.id === id); if (!key) return;
    document.querySelector('#edit-key-output-schema-row')?.remove();
    const roles = document.querySelector('#edit-key-roles');
    roles.insertAdjacentHTML('beforebegin', `<label id="edit-key-output-schema-row" class="mb-5 block text-sm text-slate-300">最终输出 JSON Schema（留空则不限制）<textarea id="edit-key-output-schema" rows="10" spellcheck="false" class="field mt-2 font-mono text-xs" placeholder='{"type":"object","required":["items"],"properties":{"items":{"type":"array"}},"additionalProperties":false}'></textarea><span class="mt-2 block text-xs text-slate-500">启用后，服务端会校验最终回答；回答必须是纯 JSON，不能带 Markdown 或说明文字。</span></label>`);
    document.querySelector('#edit-key-output-schema').value = key.output_schema ? JSON.stringify(key.output_schema, null, 2) : '';
  };
  document.querySelector('#edit-key-form').onsubmit = async event => {
    event.preventDefault();
    const id = document.querySelector('#edit-key-id').value;
    const role_ids = [...document.querySelectorAll('#edit-key-roles input:checked')].map(node => node.value);
    const rawSchema = document.querySelector('#edit-key-output-schema')?.value.trim() || '';
    let output_schema = null;
    try { output_schema = rawSchema ? JSON.parse(rawSchema) : null; }
    catch (_) { toast('最终输出规则不是合法 JSON', 'error'); return; }
    if (rawSchema && (Array.isArray(output_schema) || typeof output_schema !== 'object')) { toast('JSON Schema 必须是对象', 'error'); return; }
    try {
      await api(`/api-keys/${id}`, {method:'PATCH', body:JSON.stringify({
        name:document.querySelector('#edit-key-display-name').value.trim(),
        file_access:document.querySelector('#edit-key-file-access').value,
        role_ids,
        chat_tracking:document.querySelector('#edit-key-chat-tracking').checked,
        prompt_template_id:document.querySelector('#edit-key-prompt-template')?.value || null,
        output_schema,
      })});
      document.querySelector('#edit-key-dialog').close(); await loadAll(); toast('API Key 配置已保存');
    } catch(error) { toast(error.message, 'error'); }
  };
})();
</script>'''
