/* ============================================================
   码潮 CodeTide — app.js
   云数据库(文章) + 云认证(邮箱) + 云存储(图片/附件) + SPA 路由
   ============================================================ */
"use strict";

/* ---------- 1. Cloud 客户端（endpoint + publishableKey 二者必传） ---------- */
const PUBLIC_CONFIG = {
  endpoint: "https://ai-tech-blog-94773.app.workbuddy.host",
  publishableKey: "wbpk_LUvreP0SQFLMMndz6QydE0_dwj4w8w6cwAHkEt46EWBSepctn9YV1O5",
};
const cloud = WorkBuddyCloud.createWorkBuddyCloud({
  endpoint: PUBLIC_CONFIG.endpoint,
  publishableKey: PUBLIC_CONFIG.publishableKey,
});

/* ---------- 2. 全局状态 ---------- */
let session = null;          // 当前登录会话（null = 游客）
let authUnsub = null;
const PAGE_SIZE = 9;

/* ---------- 3. 小工具 ---------- */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}
function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function toast(msg, type = "") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  $("#toast-box").appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .3s"; }, 2600);
  setTimeout(() => el.remove(), 3000);
}
function coverCss(hue) {
  const h = Number(hue) || 210;
  return `background:linear-gradient(135deg,hsl(${h},72%,38%),hsl(${(h + 42) % 360},80%,52%) 60%,hsl(${(h + 78) % 360},70%,44%))`;
}
function unwrap(res, ctx) {
  if (res.error) {
    console.error(`[CodeTide] ${ctx} failed:`, res.error.code || res.error.message);
    throw res.error;
  }
  return res.data;
}

/* ---------- 4. Markdown 渲染（marked + DOMPurify + hljs） ---------- */
marked.setOptions({ gfm: true, breaks: true });

function mdToHtml(md) {
  const raw = marked.parse(md || "");
  // cloudimg:/cloudfile: 自定义协议需要放行，否则 DOMPurify 会清掉 src
  const clean = DOMPurify.sanitize(raw, {
    ADD_URI_SAFE_ATTR: ["src", "href"],
    ADD_ATTR: ["target"],
  });
  return clean;
}
function enhanceMarkdown(container) {
  // 代码高亮
  $$("pre code", container).forEach((el) => {
    try { hljs.highlightElement(el); } catch (e) { /* 语法不支持则跳过 */ }
  });
  // 外链新窗口
  $$('a[href^="http"]', container).forEach((a) => { a.target = "_blank"; a.rel = "noopener"; });
  // 云端图片 / 附件
  resolveCloudAssets(container);
}

const _pendingAssets = []; // { el, kind, path, name }
function resolveCloudAssets(container) {
  _pendingAssets.length = 0;
  // 图片
  $$('img[src^="cloudimg:"]', container).forEach((img) => {
    const path = img.getAttribute("src").replace(/^cloudimg:/, "");
    const name = img.getAttribute("title") || path.split("/").pop();
    if (session) {
      const holder = document.createElement("span");
      img.replaceWith(holder);
      _pendingAssets.push({ kind: "img", path, name, holder });
    } else {
      const box = document.createElement("div");
      box.className = "cloud-asset";
      box.innerHTML = `<span class="ca-icon">🖼️</span>
        <span class="ca-info"><div class="ca-name">🖼️ ${escapeHtml(name)}</div>
        <div class="ca-hint">🔒 云端图片 · <a href="#/login">登录</a>后可查看</div></span>`;
      img.replaceWith(box);
    }
  });
  // 附件
  $$('a[href^="cloudfile:"]', container).forEach((a) => {
    const path = a.getAttribute("href").replace(/^cloudfile:/, "");
    const name = a.textContent.trim() || path.split("/").pop();
    const box = document.createElement("div");
    box.className = "cloud-asset";
    if (session) {
      box.innerHTML = `<span class="ca-icon">📎</span>
        <span class="ca-info"><div class="ca-name">📎 ${escapeHtml(name)}</div>
        <div class="ca-hint">云端附件 · 点击右侧下载</div></span>
        <button class="btn btn-sm btn-primary ca-dl">下载</button>`;
      box.querySelector(".ca-dl").addEventListener("click", async () => {
        try {
          const r = await cloud.storage.createSignedUrl(path, 600);
          if (r.error) throw r.error;
          window.open(r.data, "_blank");
        } catch (e) { toast("获取下载链接失败：" + (e.message || "请稍后再试"), "err"); }
      });
    } else {
      box.innerHTML = `<span class="ca-icon">📎</span>
        <span class="ca-info"><div class="ca-name">📎 ${escapeHtml(name)}</div>
        <div class="ca-hint">🔒 云端附件 · <a href="#/login">登录</a>后可下载</div></span>`;
    }
    a.replaceWith(box);
  });
  // 批量签发图片 URL
  if (_pendingAssets.length) signPendingImages();
}
async function signPendingImages() {
  const batch = [..._pendingAssets];
  _pendingAssets.length = 0;
  try {
    const r = await cloud.storage.createSignedUrls(batch.map((b) => b.path), 600);
    if (r.error) throw r.error;
    const map = r.data || {};
    batch.forEach((b) => {
      const url = map[b.path];
      const img = document.createElement("img");
      img.alt = b.name;
      img.loading = "lazy";
      img.style.cssText = "max-height:420px";
      if (url) { img.src = url; }
      else {
        img.alt = "";
        img.replaceWith(Object.assign(document.createElement("div"), {
          className: "cloud-asset", innerHTML: `<span class="ca-icon">🖼️</span><span class="ca-info">
          <div class="ca-name">🖼️ ${escapeHtml(b.name)}</div><div class="ca-hint">签名失败，请刷新重试</div></span>`,
        }));
        return;
      }
      b.holder.replaceWith(img);
    });
  } catch (e) {
    batch.forEach((b) => b.holder.replaceWith(Object.assign(document.createElement("div"), {
      className: "cloud-asset", innerHTML: `<span class="ca-icon">🖼️</span><span class="ca-info">
      <div class="ca-name">🖼️ ${escapeHtml(b.name)}</div><div class="ca-hint">图片加载失败：${escapeHtml(e.message || "请刷新重试")}</div></span>`,
    })));
  }
}

/* ---------- 5. 认证 ---------- */
async function initAuth() {
  const { data, error } = await cloud.auth.getSession();
  session = error ? null : (data || null);
  renderAuthArea();
  authUnsub = cloud.auth.onAuthStateChange((event, s) => {
    session = event === "SIGNED_OUT" ? null : (s || session);
    renderAuthArea();
    if (event === "SIGNED_OUT") { toast("已退出登录"); render(); }
  });
}
function renderAuthArea() {
  const area = $("#auth-area");
  $("#nav-write").style.display = session ? "" : "none";
  if (session && session.user) {
    const name = (session.user.email || "博主").split("@")[0];
    area.innerHTML = `
      <div class="user-chip" id="user-chip" title="我的文章 / 退出">
        <span class="user-avatar">${escapeHtml(name[0]?.toUpperCase() || "B")}</span>
        <span class="user-name">${escapeHtml(name)}</span>
      </div>`;
    $("#user-chip").addEventListener("click", () => { location.hash = "#/mine"; });
  } else {
    area.innerHTML = `<button class="btn btn-primary" id="btn-login">登录 / 注册</button>`;
    $("#btn-login").addEventListener("click", () => { location.hash = "#/login"; });
  }
}

/* ============ OTP 状态（跨事件保存，发送与提交分离） ============ */
let pendingEmailOtp = null; // { email, verificationId, isExistingUser, purpose }

/* ---------- 6. 路由 ---------- */
const ROUTE_TITLES = { "": "首页", tags: "标签", about: "关于", login: "登录", write: "写文章", mine: "我的文章", search: "搜索" };
function parseRoute() {
  const h = location.hash.replace(/^#\/?/, "");
  const parts = h.split("/").filter(Boolean);
  let name = parts[0] || "", arg = decodeURIComponent(parts[1] || "");
  // 纯数字路由（#/2）视为首页分页
  if (/^\d+$/.test(name)) { arg = name; name = ""; }
  return { name, arg, extra: parts[2] || "" };
}
async function render() {
  const { name, arg } = parseRoute();
  // 导航高亮
  $$(".nav-link").forEach((el) => {
    el.classList.toggle("active", el.dataset.route === name);
  });
  const app = $("#app");
  const isPost = name === "post";
  $("#read-progress").style.display = isPost ? "block" : "none";
  try {
    switch (name) {
      case "": return await pageHome(app, arg);
      case "post": return await pagePost(app, Number(arg));
      case "tags": return await pageTags(app);
      case "tag": return await pageTagFilter(app, arg);
      case "about": return pageAbout(app);
      case "login": return pageLogin(app);
      case "write": return await pageWrite(app);
      case "edit": return await pageWrite(app, Number(arg));
      case "mine": return await pageMine(app);
      case "search": return await pageSearch(app, arg);
      default: return pageNotFound(app);
    }
  } catch (e) {
    console.error("[CodeTide] route error:", e.code || e.message);
    app.innerHTML = `<div class="empty-state page-fade"><div class="es-icon">🌊</div>
      <p>页面被浪打走了：${escapeHtml(e.message || "未知错误")}</p>
      <button class="btn btn-primary" onclick="location.hash='#/'">回到首页</button></div>`;
  }
}

/* ---------- 7. 页面：首页 ---------- */
async function pageHome(app, pageStr) {
  const page = Math.max(1, Number(pageStr) || 1);
  const from = (page - 1) * PAGE_SIZE, to = from + PAGE_SIZE - 1;
  app.innerHTML = `
    <section class="hero page-fade">
      <div class="hero-tagline">🌊 BACKEND · AI · ARCHITECTURE</div>
      <h1>码潮 CodeTide</h1>
      <p>记录每一次技术涨潮：Java 后端、数据库与中间件、系统架构，以及大模型时代的持续修炼。文章存于云端数据库，随时随地冲浪阅读。</p>
      <div class="hero-stats" id="hero-stats"></div>
    </section>
    <div class="section-head page-fade">
      <h2 id="list-title">最新文章</h2>
      <span class="sub" style="display:flex;gap:8px;align-items:center">
        <button class="btn btn-sm ${true ? "" : ""}" id="sort-latest">最新</button>
        <button class="btn btn-sm" id="sort-hot">最热</button>
      </span>
    </div>
    <div id="post-area"><div class="skeleton-grid">${'<div class="skel"></div>'.repeat(6)}</div></div>
    <div id="pager"></div>`;
  loadHeroStats();
  bindSort(page);
  await loadPostList({ page, sort: window.__sort || "latest" });
}
window.__sort = "latest";
function bindSort(page) {
  const l = $("#sort-latest"), h = $("#sort-hot");
  const paint = () => {
    l.classList.toggle("btn-primary", window.__sort === "latest");
    h.classList.toggle("btn-primary", window.__sort === "hot");
  };
  paint();
  l.onclick = () => { window.__sort = "latest"; paint(); loadPostList({ page: 1, sort: "latest" }); };
  h.onclick = () => { window.__sort = "hot"; paint(); loadPostList({ page: 1, sort: "hot" }); };
}
async function loadHeroStats() {
  try {
    const { data, count } = await cloud.database
      .from("posts").select("id,tags,views", { count: "exact" })
      .eq("status", "published");
    const posts = data || [];
    const tagSet = new Set();
    posts.forEach((p) => (p.tags || []).forEach((t) => tagSet.add(t)));
    const totalViews = posts.reduce((s, p) => s + (p.views || 0), 0);
    $("#hero-stats").innerHTML = `
      <div class="stat-pill"><b>${count ?? posts.length}</b><span>文章</span></div>
      <div class="stat-pill"><b>${tagSet.size}</b><span>标签</span></div>
      <div class="stat-pill"><b>${totalViews}</b><span>总阅读</span></div>`;
  } catch (e) { /* 统计失败不阻塞 */ }
}
async function loadPostList({ page, sort, baseQuery }) {
  const area = $("#post-area");
  if (!area) return;
  const from = (page - 1) * PAGE_SIZE, to = from + PAGE_SIZE - 1;
  try {
    let q = baseQuery || cloud.database.from("posts");
    const cols = "id,title,summary,tags,cover_emoji,cover_hue,status,views,created_at,owner_id";
    let res;
    if (baseQuery) {
      res = await baseQuery.select(cols, { count: "exact" })
        .order(window.__sort === "hot" ? "views" : "created_at", { ascending: false })
        .range(from, to);
    } else {
      res = await cloud.database.from("posts").select(cols, { count: "exact" })
        .eq("status", "published")
        .order(window.__sort === "hot" ? "views" : "created_at", { ascending: false })
        .range(from, to);
    }
    unwrap(res, "load posts");
    const { data: posts, count } = res;
    if (!posts || posts.length === 0) {
      area.innerHTML = `<div class="empty-state"><div class="es-icon">🏝️</div>
        <p>还没有文章 —— 涨潮之前，海面总是安静的。</p>
        ${session ? '<button class="btn btn-primary" onclick="location.hash=\'#/write\'">写下第一篇</button>' : ""}</div>`;
      $("#pager").innerHTML = "";
      return;
    }
    area.innerHTML = `<div class="post-grid">${posts.map((p, i) => postCardHtml(p, i)).join("")}</div>`;
    bindCardActions(posts);
    renderPager(page, count ?? posts.length);
  } catch (e) {
    area.innerHTML = `<div class="empty-state"><div class="es-icon">⚠️</div><p>文章加载失败：${escapeHtml(e.message || "")}</p></div>`;
  }
}
function postCardHtml(p, i) {
  const own = session && p.owner_id === session.user.id;
  return `<article class="post-card" style="animation-delay:${Math.min(i * 60, 480)}ms" data-id="${p.id}">
    <div class="post-cover" style="${coverCss(p.cover_hue)}">
      <span class="cover-tag">${p.status === "draft" ? "📝 草稿" : escapeHtml((p.tags || [])[0] || "随笔")}</span>
      <span class="cover-emoji">${escapeHtml(p.cover_emoji || "📝")}</span>
    </div>
    <div class="post-body">
      <div class="post-title">${escapeHtml(p.title)}</div>
      <div class="post-summary">${escapeHtml(p.summary || "（暂无摘要）")}</div>
      <div class="post-meta">
        <span>📅 ${fmtDate(p.created_at)}</span><span class="dot">·</span>
        <span>👁 ${p.views || 0}</span>
        ${(p.tags || []).slice(0, 3).map((t) => `<span class="tag-chip" data-tag="${escapeHtml(t)}">${escapeHtml(t)}</span>`).join("")}
        ${own ? '<span class="draft-chip tag-chip">我的</span>' : ""}
      </div>
      ${own ? `<div class="own-actions">
        <button class="btn btn-sm" data-act="edit">编辑</button>
        <button class="btn btn-sm btn-danger" data-act="del">删除</button></div>` : ""}
    </div></article>`;
}
function bindCardActions(posts) {
  $$(".post-card").forEach((card) => {
    const id = Number(card.dataset.id);
    const post = posts.find((p) => p.id === id);
    card.addEventListener("click", (ev) => {
      const tagChip = ev.target.closest(".tag-chip[data-tag]");
      if (tagChip) { ev.stopPropagation(); location.hash = `#/tag/${encodeURIComponent(tagChip.dataset.tag)}`; return; }
      const act = ev.target.closest("[data-act]");
      if (act) {
        ev.stopPropagation();
        if (act.dataset.act === "edit") location.hash = `#/edit/${id}`;
        if (act.dataset.act === "del") deletePost(id, post?.title);
        return;
      }
      location.hash = `#/post/${id}`;
    });
  });
}
async function deletePost(id, title) {
  if (!confirm(`确定删除《${title || id}》吗？此操作不可恢复。`)) return;
  try {
    const { data } = await cloud.database.from("posts").delete().eq("id", id).select();
    if (!Array.isArray(data) || data.length === 0) {
      toast("删除失败：文章不存在或不属于当前账号", "err");
      return;
    }
    toast("文章已删除", "ok");
    render();
  } catch (e) { toast("删除失败：" + (e.message || ""), "err"); }
}
function renderPager(page, total) {
  const pager = $("#pager");
  if (!pager) return;
  const pages = Math.ceil(total / PAGE_SIZE);
  if (pages <= 1) { pager.innerHTML = ""; return; }
  let html = "";
  for (let i = 1; i <= pages; i++) {
    if (pages > 7 && i > 2 && i < pages - 1 && Math.abs(i - page) > 1) {
      if (!html.endsWith("…</span>")) html += '<span style="color:var(--text-2)">…</span>';
      continue;
    }
    html += `<button class="${i === page ? "cur" : ""}" data-p="${i}">${i}</button>`;
  }
  pager.innerHTML = html;
  $$("#pager button").forEach((b) => {
    b.onclick = () => {
      const p = Number(b.dataset.p);
      location.hash = p === 1 ? "#/" : `#/${p}`;
      window.scrollTo({ top: 0 });
    };
  });
}

/* ---------- 8. 页面：文章详情 ---------- */
async function pagePost(app, id) {
  if (!id) return pageNotFound(app);
  app.innerHTML = '<div class="spinner"></div>';
  let post;
  try {
    const res = await cloud.database.from("posts").select("*").eq("id", id).maybeSingle();
    post = unwrap(res, "load post");
  } catch (e) {
    app.innerHTML = `<div class="empty-state"><div class="es-icon">⚠️</div><p>加载失败：${escapeHtml(e.message || "")}</p></div>`;
    return;
  }
  if (!post) {
    app.innerHTML = `<div class="empty-state"><div class="es-icon">🌊</div><p>这篇文章已随潮水漂走（不存在或未公开）。</p>
      <button class="btn btn-primary" onclick="location.hash='#/'">回到首页</button></div>`;
    return;
  }
  const own = session && post.owner_id === session.user.id;
  // 阅读计数（游客可执行；失败不影响阅读）
  try { cloud.database.rpc("increment_views", { p_id: id }); } catch (e) { /* 忽略 */ }

  const prevNext = await loadPrevNext(post);
  app.innerHTML = `
    <div class="article-wrap page-fade">
      <span class="back-link" onclick="history.length>1?history.back():location.hash='#/'">← 返回</span>
      <div class="article-cover" style="${coverCss(post.cover_hue)}">
        <span class="cover-emoji">${escapeHtml(post.cover_emoji || "📝")}</span>
      </div>
      <div class="article-head">
        <h1>${escapeHtml(post.title)}</h1>
        <div class="article-meta">
          <span class="m">📅 ${fmtDate(post.created_at)}</span>
          <span class="m">👁 ${post.views || 0} 阅读</span>
          ${post.status === "draft" ? '<span class="tag-chip draft-chip">📝 草稿（仅自己可见）</span>' : ""}
          <span class="article-tags">${(post.tags || []).map((t) => `<span class="tag-chip" data-tag="${escapeHtml(t)}">${escapeHtml(t)}</span>`).join("")}</span>
        </div>
      </div>
      ${own ? `<div class="editor-toolbar" style="border:none;padding:0 0 18px">
        <button class="btn btn-sm" id="p-edit">✏️ 编辑本文</button>
        <button class="btn btn-sm btn-danger" id="p-del">🗑 删除</button></div>` : ""}
      <div class="md" id="md-body"></div>
      <div class="article-nav">
        ${prevNext.prev ? `<div class="an-card" data-goto="${prevNext.prev.id}"><div class="an-label">← 上一篇</div><div class="an-title">${escapeHtml(prevNext.prev.title)}</div></div>` : '<div class="an-card an-empty"></div>'}
        ${prevNext.next ? `<div class="an-card next" data-goto="${prevNext.next.id}"><div class="an-label">下一篇 →</div><div class="an-title">${escapeHtml(prevNext.next.title)}</div></div>` : '<div class="an-card next an-empty"></div>'}
      </div>
    </div>`;
  const body = $("#md-body");
  body.innerHTML = mdToHtml(post.content);
  enhanceMarkdown(body);
  $$(".article-tags .tag-chip", app).forEach((c) => {
    c.onclick = () => { location.hash = `#/tag/${encodeURIComponent(c.dataset.tag)}`; };
  });
  $$("[data-goto]", app).forEach((c) => { c.onclick = () => { location.hash = `#/post/${c.dataset.goto}`; window.scrollTo({ top: 0 }); }; });
  if (own) {
    $("#p-edit").onclick = () => { location.hash = `#/edit/${post.id}`; };
    $("#p-del").onclick = () => deletePost(post.id, post.title);
  }
  window.scrollTo({ top: 0 });
}
async function loadPrevNext(post) {
  const out = { prev: null, next: null };
  try {
    const cols = "id,title,created_at";
    const newer = await cloud.database.from("posts").select(cols)
      .eq("status", "published").gt("created_at", post.created_at)
      .order("created_at", { ascending: true }).limit(1);
    const older = await cloud.database.from("posts").select(cols)
      .eq("status", "published").lt("created_at", post.created_at)
      .order("created_at", { ascending: false }).limit(1);
    out.prev = newer.data?.[0] || null;
    out.next = older.data?.[0] || null;
  } catch (e) { /* 非关键 */ }
  return out;
}

/* ---------- 9. 页面：标签 ---------- */
async function collectTagCounts() {
  const { data, error } = await cloud.database.from("posts").select("tags").eq("status", "published");
  if (error) throw error;
  const counts = {};
  (data || []).forEach((p) => (p.tags || []).forEach((t) => { counts[t] = (counts[t] || 0) + 1; }));
  return Object.entries(counts).sort((a, b) => b[1] - a[1]);
}
async function pageTags(app) {
  app.innerHTML = `<div class="page-fade"><div class="section-head"><h2>标签分类</h2><span class="sub">点击标签浏览该主题下的全部文章</span></div>
    <div class="spinner"></div></div>`;
  try {
    const tags = await collectTagCounts();
    if (!tags.length) {
      app.querySelector(".page-fade").innerHTML = `<div class="section-head"><h2>标签分类</h2></div>
        <div class="empty-state"><div class="es-icon">🏷️</div><p>还没有任何标签。</p></div>`;
      return;
    }
    const max = tags[0][1];
    app.querySelector(".page-fade").innerHTML = `<div class="section-head"><h2>标签分类</h2><span class="sub">共 ${tags.length} 个标签</span></div>
      <div class="tag-cloud">${tags.map(([t, n]) => {
        const scale = 0.85 + 0.55 * (n / max);
        return `<span class="tag-chip" data-tag="${escapeHtml(t)}" style="font-size:${scale.toFixed(2)}em">${escapeHtml(t)}<b> ${n}</b></span>`;
      }).join("")}</div>`;
    $$(".tag-cloud .tag-chip", app).forEach((c) => {
      c.onclick = () => { location.hash = `#/tag/${encodeURIComponent(c.dataset.tag)}`; };
    });
  } catch (e) {
    toast("标签加载失败：" + (e.message || ""), "err");
  }
}
async function pageTagFilter(app, tag) {
  app.innerHTML = `<div class="page-fade"><div class="section-head"><h2>🏷️ ${escapeHtml(tag)}</h2>
      <span class="sub"><a href="#/tags">← 全部标签</a></span></div><div id="post-area"><div class="spinner"></div></div><div id="pager"></div></div>`;
  const base = cloud.database.from("posts").contains("tags", [tag]).eq("status", "published");
  await loadPostList({ page: 1, baseQuery: base });
}

/* ---------- 10. 页面：关于 ---------- */
function pageAbout(app) {
  app.innerHTML = `
  <div class="about-card page-fade">
    <div class="about-avatar">🧑‍💻</div>
    <h1>关于博主</h1>
    <div class="about-sub">后端工程师 · AI 学习者 · 修炼中</div>
    <p>一名在 Java 后端世界摸爬滚打的工程师，白天和 Spring、MySQL、Kafka 打交道，晚上追大模型的论文和浪潮。
    相信技术是需要"长期修炼"的手艺，所以开了这个博客，把学习笔记、面试复盘和踩坑记录都沉在这里。</p>
    <h3>🧭 这里写什么</h3>
    <ul>
      <li><b>后端八股与原理</b> —— MySQL、JVM、并发、Kafka、Nginx、Linux，问到底层的那种。</li>
      <li><b>系统架构</b> —— 分布式、高并发、稳定性设计的思考与方案沉淀。</li>
      <li><b>AI 学习路线</b> —— 机器学习 / 深度学习 / 大模型 / Agent 的学习记录与实践。</li>
      <li><b>数据结构与算法</b> —— 面试刷题与思维训练。</li>
    </ul>
    <h3>🛠 技术栈</h3>
    <div class="skill-row">
      <span class="tag-chip">Java</span><span class="tag-chip">Spring</span><span class="tag-chip">MySQL</span>
      <span class="tag-chip">Redis</span><span class="tag-chip">Kafka</span><span class="tag-chip">Nginx</span>
      <span class="tag-chip">Linux</span><span class="tag-chip">微服务</span><span class="tag-chip">Python</span>
      <span class="tag-chip">LLM</span><span class="tag-chip">Agent</span><span class="tag-chip">RAG</span>
    </div>
    <h3>📮 找到我</h3>
    <p>文章评论区暂未开放，有交流欲可以直接邮件轰炸。看到必回（忙时随缘）。</p>
    <h3>🌊 关于「码潮」</h3>
    <p>技术的更新像潮水，一波接一波，拦不住也不必拦。与其焦虑被拍在沙滩上，不如学会冲浪。
    这个博客就是我练习冲浪的 beach —— 记录，沉淀，然后再次出发。</p>
  </div>`;
}

/* ---------- 11. 页面：登录 / 注册（邮箱四件套） ---------- */
function pageLogin(app) {
  if (session) { location.hash = "#/mine"; return; }
  app.innerHTML = `
  <div class="auth-wrap page-fade"><div class="auth-card">
    <h2>👋 欢迎来到码潮</h2>
    <div class="auth-sub">登录后可以撰写文章、上传图片与管理草稿</div>
    <div class="auth-tabs">
      <button class="auth-tab active" data-tab="pwd">密码登录</button>
      <button class="auth-tab" data-tab="otp">验证码登录</button>
      <button class="auth-tab" data-tab="reg">注册</button>
    </div>
    <div class="form-msg" id="auth-msg"></div>

    <form id="form-pwd" novalidate>
      <div class="field"><label>邮箱</label><input id="pwd-email" type="email" autocomplete="email" placeholder="you@example.com" required></div>
      <div class="field"><label>密码</label><input id="pwd-pass" type="password" autocomplete="current-password" placeholder="••••••••" required></div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin:4px 0 16px">
        <span></span><button type="button" class="link-btn" id="to-forgot">忘记密码？</button>
      </div>
      <button class="btn btn-primary" style="width:100%;padding:11px" type="submit">登 录</button>
    </form>

    <form id="form-otp" style="display:none" novalidate>
      <div class="field"><label>邮箱</label><input id="otp-email" type="email" autocomplete="email" placeholder="you@example.com" required></div>
      <div class="field"><label>验证码</label>
        <div class="otp-row">
          <input id="otp-code" inputmode="numeric" maxlength="8" placeholder="6 位验证码" required>
          <button type="button" class="btn" id="otp-send">获取验证码</button>
        </div>
        <div class="hint">已注册用户可直接凭验证码登录</div>
      </div>
      <button class="btn btn-primary" style="width:100%;padding:11px" type="submit">验证并登录</button>
    </form>

    <form id="form-reg" style="display:none" novalidate>
      <div class="field"><label>邮箱</label><input id="reg-email" type="email" autocomplete="email" placeholder="you@example.com" required></div>
      <div class="field"><label>验证码</label>
        <div class="otp-row">
          <input id="reg-code" inputmode="numeric" maxlength="8" placeholder="6 位验证码" required>
          <button type="button" class="btn" id="reg-send">获取验证码</button>
        </div>
      </div>
      <div class="field"><label>设置密码</label><input id="reg-pass" type="password" autocomplete="new-password" placeholder="至少 6 位，用于之后的密码登录" required>
        <div class="hint">注册必须设置密码，否则之后无法用密码登录</div></div>
      <button class="btn btn-primary" style="width:100%;padding:11px" type="submit">注 册</button>
    </form>

    <form id="form-forgot" style="display:none" novalidate>
      <div class="field"><label>邮箱</label>
        <div class="otp-row">
          <input id="fg-email" type="email" autocomplete="email" placeholder="you@example.com" required>
          <button type="button" class="btn" id="fg-send">发送重置邮件</button>
        </div></div>
      <div class="field"><label>邮件验证码</label><input id="fg-nonce" inputmode="numeric" maxlength="8" placeholder="查收邮件中的验证码" required></div>
      <div class="field"><label>新密码</label><input id="fg-pass" type="password" autocomplete="new-password" placeholder="新密码（至少 6 位）" required></div>
      <button class="btn btn-primary" style="width:100%;padding:11px" type="submit">重置密码</button>
      <div class="auth-foot"><span id="back-login">← 返回登录</span></div>
    </form>

    <div class="auth-foot" id="reg-switch">还没有账号？<span id="to-reg">注册一个 →</span></div>
  </div></div>`;

  const msg = $("#auth-msg");
  const showMsg = (m, ok = false) => { msg.className = "form-msg " + (ok ? "ok" : "err"); msg.textContent = m; };
  const hideMsg = () => { msg.className = "form-msg"; msg.textContent = ""; };
  const forms = { pwd: $("#form-pwd"), otp: $("#form-otp"), reg: $("#form-reg"), forgot: $("#form-forgot") };
  const foot = $("#reg-switch");
  function switchTab(tab) {
    hideMsg();
    $$(".auth-tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === tab));
    Object.entries(forms).forEach(([k, f]) => { f.style.display = k === tab ? "" : "none"; });
    foot.style.display = tab === "forgot" ? "none" : "";
  }
  $$(".auth-tab").forEach((t) => { t.onclick = () => switchTab(t.dataset.tab); });
  $("#to-reg").onclick = () => switchTab("reg");
  $("#back-login").onclick = () => switchTab("pwd");
  $("#to-forgot").onclick = () => switchTab("forgot");

  const validEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  let sendLock = { otp: false, reg: false };
  const countdown = (btn, sec = 60) => {
    let left = sec;
    btn.disabled = true;
    const t = setInterval(() => {
      left -= 1;
      btn.textContent = left > 0 ? `${left}s` : "获取验证码";
      if (left <= 0) { clearInterval(t); btn.disabled = false; }
    }, 1000);
  };

  // —— 密码登录 ——
  forms.pwd.addEventListener("submit", async (ev) => {
    ev.preventDefault(); hideMsg();
    const email = $("#pwd-email").value.trim(), password = $("#pwd-pass").value;
    if (!validEmail(email)) return showMsg("请输入有效的邮箱地址");
    if (!password) return showMsg("请输入密码");
    const btn = ev.target.querySelector("button[type=submit]");
    btn.disabled = true;
    try {
      const r = await cloud.auth.signInWithPassword({ email, password });
      if (r.error) {
        const kind = r.error.kind || "";
        showMsg(kind === "unauthenticated" || kind === "invalid_grant" ? "账号或密码不正确" : (r.error.message || "登录失败，请稍后再试"));
        return;
      }
      session = r.data;
      renderAuthArea();
      toast("登录成功，欢迎回来 🌊", "ok");
      location.hash = "#/";
    } catch (e) {
      showMsg("网络异常，请稍后再试");
    } finally { btn.disabled = false; }
  });

  // —— OTP 登录：先发码 ——
  $("#otp-send").addEventListener("click", async () => {
    hideMsg();
    const email = $("#otp-email").value.trim();
    if (!validEmail(email)) return showMsg("请输入有效的邮箱地址");
    const btn = $("#otp-send");
    btn.disabled = true;
    try {
      const sent = await cloud.auth.sendOtp({ email });
      if (sent.error) { showMsg(sent.error.message || "验证码发送失败"); return; }
      pendingEmailOtp = { email, verificationId: sent.data.verificationId, isExistingUser: sent.data.isExistingUser, purpose: "otp" };
      showMsg("验证码已发送至邮箱，请查收（注意垃圾箱）", true);
      countdown(btn);
    } catch (e) { showMsg("验证码发送失败，请稍后再试"); }
    finally { btn.disabled = false; }
  });
  // —— OTP 登录：再验证 ——
  forms.otp.addEventListener("submit", async (ev) => {
    ev.preventDefault(); hideMsg();
    const code = $("#otp-code").value.trim();
    const pending = pendingEmailOtp;
    if (!pending || pending.purpose !== "otp") return showMsg("请先获取当前邮箱的验证码");
    if ($("#otp-email").value.trim() !== pending.email) return showMsg("邮箱已变更，请重新获取验证码");
    if (!code) return showMsg("请输入验证码");
    const btn = ev.target.querySelector("button[type=submit]");
    btn.disabled = true;
    try {
      const done = await cloud.auth.verifyOtp({
        email: pending.email, verificationId: pending.verificationId,
        isExistingUser: pending.isExistingUser, token: code,
      });
      if (done.error) { showMsg(done.error.message || "验证码错误或已过期"); return; }
      pendingEmailOtp = null;
      session = done.data;
      renderAuthArea();
      toast("登录成功 🌊", "ok");
      location.hash = "#/";
    } catch (e) { showMsg("验证失败，请稍后再试"); }
    finally { btn.disabled = false; }
  });

  // —— 注册：先发码 ——
  $("#reg-send").addEventListener("click", async () => {
    hideMsg();
    const email = $("#reg-email").value.trim();
    if (!validEmail(email)) return showMsg("请输入有效的邮箱地址");
    const btn = $("#reg-send");
    btn.disabled = true;
    try {
      const sent = await cloud.auth.sendOtp({ email });
      if (sent.error) { showMsg(sent.error.message || "验证码发送失败"); return; }
      pendingEmailOtp = { email, verificationId: sent.data.verificationId, isExistingUser: sent.data.isExistingUser, purpose: "reg" };
      showMsg("验证码已发送，请查收", true);
      countdown(btn);
    } catch (e) { showMsg("验证码发送失败，请稍后再试"); }
    finally { btn.disabled = false; }
  });
  // —— 注册：验证 + 设置密码 ——
  forms.reg.addEventListener("submit", async (ev) => {
    ev.preventDefault(); hideMsg();
    const code = $("#reg-code").value.trim();
    const password = $("#reg-pass").value;
    const pending = pendingEmailOtp;
    if (!pending || pending.purpose !== "reg") return showMsg("请先获取当前邮箱的验证码");
    if ($("#reg-email").value.trim() !== pending.email) return showMsg("邮箱已变更，请重新获取验证码");
    if (!code) return showMsg("请输入验证码");
    if ((password || "").length < 6) return showMsg("密码至少 6 位");
    const btn = ev.target.querySelector("button[type=submit]");
    btn.disabled = true;
    try {
      const done = await cloud.auth.verifyOtp({
        email: pending.email, verificationId: pending.verificationId,
        isExistingUser: pending.isExistingUser, token: code, password,
      });
      if (done.error) {
        showMsg(pending.isExistingUser ? "该邮箱已注册，请直接登录" : (done.error.message || "注册失败"));
        return;
      }
      pendingEmailOtp = null;
      session = done.data;
      renderAuthArea();
      toast("注册成功，开始冲浪 🏄", "ok");
      location.hash = "#/";
    } catch (e) { showMsg("注册失败，请稍后再试"); }
    finally { btn.disabled = false; }
  });

  // —— 忘记密码（两段式：先发邮件 → 再凭验证码重置） ——
  let forgotPending = null; // 保存 resetPasswordForEmail 的返回，updateUser 挂在它身上
  $("#fg-send").addEventListener("click", async () => {
    hideMsg();
    const email = $("#fg-email").value.trim();
    if (!validEmail(email)) return showMsg("请输入有效的邮箱地址");
    const btn = $("#fg-send");
    btn.disabled = true;
    try {
      const started = await cloud.auth.resetPasswordForEmail(email);
      if (started.error) { showMsg(started.error.message || "重置邮件发送失败"); return; }
      forgotPending = started;
      showMsg("重置邮件已发送，请查收邮件中的验证码", true);
      countdown(btn);
    } catch (e) { showMsg("重置邮件发送失败，请稍后再试"); }
    finally { btn.disabled = false; }
  });
  forms.forgot.addEventListener("submit", async (ev) => {
    ev.preventDefault(); hideMsg();
    const nonce = $("#fg-nonce").value.trim();
    const password = $("#fg-pass").value;
    if (!forgotPending) return showMsg("请先点击「发送重置邮件」");
    if (!nonce) return showMsg("请输入邮件中的验证码");
    if ((password || "").length < 6) return showMsg("新密码至少 6 位");
    const btn = ev.target.querySelector("button[type=submit]");
    btn.disabled = true;
    try {
      const done = await forgotPending.data.updateUser({ nonce, password });
      if (done.error) { showMsg(done.error.message || "验证码错误或已过期"); return; }
      forgotPending = null;
      showMsg("密码已重置，请使用新密码登录", true);
      $("#pwd-pass").value = "";
      setTimeout(() => switchTab("pwd"), 1200);
    } catch (e) { showMsg("重置失败，请稍后再试"); }
    finally { btn.disabled = false; }
  });
}

/* ---------- 12. 页面：写作 / 编辑 ---------- */
const EMOJIS = ["📝", "🚀", "🧠", "⚙️", "🔥", "📚", "🛠️", "💡", "🌊", "🧭", "⚡", "🗄️", "🧩", "🔬", "🧪", "📈"];
async function pageWrite(app, editId) {
  if (!session || !session.user) { toast("请先登录再写作", "err"); location.hash = "#/login"; return; }
  let post = null;
  if (editId) {
    app.innerHTML = '<div class="spinner"></div>';
    try {
      const res = await cloud.database.from("posts").select("*").eq("id", editId).maybeSingle();
      post = unwrap(res, "load post for edit");
    } catch (e) { /* fallthrough */ }
    if (!post) { toast("文章不存在", "err"); location.hash = "#/mine"; return; }
    if (post.owner_id !== session.user.id) { toast("只能编辑自己的文章", "err"); location.hash = `#/post/${editId}`; return; }
  }
  const isEdit = !!post;
  app.innerHTML = `
  <div class="page-fade">
    <div class="section-head"><h2>${isEdit ? "✏️ 编辑文章" : "✍️ 撰写新文章"}</h2>
      <span class="sub">支持 Markdown · 正文与封面实时预览</span></div>
    <div class="field" style="margin-bottom:14px"><label>标题</label>
      <input id="w-title" maxlength="120" placeholder="给文章起个响亮的名字…" value="${isEdit ? escapeHtml(post.title) : ""}"></div>
    <div class="field" style="margin-bottom:14px"><label>摘要</label>
      <textarea id="w-summary" maxlength="300" placeholder="一句话介绍这篇文章（展示在列表卡片上）">${isEdit ? escapeHtml(post.summary || "") : ""}</textarea></div>
    <div class="field-row" style="margin-bottom:14px">
      <div class="field" style="flex:1"><label>标签（英文逗号分隔，最多 6 个）</label>
        <input id="w-tags" placeholder="例如：Java, MySQL, 面试" value="${isEdit ? escapeHtml((post.tags || []).join(", ")) : ""}"></div>
      <div class="field"><label>状态</label>
        <select id="w-status">
          <option value="published" ${isEdit && post.status === "published" ? "selected" : ""}>公开发布</option>
          <option value="draft" ${isEdit && post.status === "draft" ? "selected" : ""}>存为草稿</option>
        </select></div>
    </div>
    <div class="field-row" style="margin-bottom:14px">
      <div class="field"><label>封面图案</label><div class="emoji-picker" id="emoji-picker"></div></div>
      <div class="field"><label>封面色相</label>
        <div class="hue-row">
          <div class="hue-preview" id="hue-preview"></div>
          <input type="range" class="hue-slider" id="w-hue" min="0" max="359" value="${isEdit ? post.cover_hue || 210 : Math.floor(Math.random() * 360)}">
        </div></div>
    </div>
    <div class="editor-wrap">
      <div class="editor-pane">
        <div class="pane-head"><span>📝 Markdown 源码</span><span class="markdown-help"><code>## 标题</code> · <code>**加粗**</code> · <code>\`\`\`java</code> 代码块</span></div>
        <textarea id="w-content" placeholder="用 Markdown 书写正文……&#10;&#10;图片：点击下方「插入图片」上传到云端存储&#10;附件：点击「插入附件」上传，读者登录后可下载" spellcheck="false">${isEdit ? escapeHtml(post.content) : ""}</textarea>
      </div>
      <div class="preview-pane">
        <div class="pane-head"><span>👁 实时预览</span><span id="word-count"></span></div>
        <div class="md" id="w-preview"></div>
      </div>
    </div>
    <div class="editor-toolbar">
      <button class="btn btn-sm" id="w-upload-img">🖼️ 插入图片（云存储）</button>
      <button class="btn btn-sm" id="w-upload-file">📎 插入附件（云存储）</button>
      <input type="file" id="file-img" accept="image/*" style="display:none">
      <input type="file" id="file-any" style="display:none">
      <span style="flex:1"></span>
      <button class="btn" id="w-cancel">取消</button>
      <button class="btn btn-primary" id="w-save">💾 ${isEdit ? "保存修改" : "发布文章"}</button>
    </div>
  </div>`;

  // emoji picker
  let curEmoji = isEdit ? (post.cover_emoji || "📝") : "📝";
  const picker = $("#emoji-picker");
  picker.innerHTML = EMOJIS.map((e) => `<span class="emoji-opt ${e === curEmoji ? "sel" : ""}" data-e="${e}">${e}</span>`).join("");
  picker.addEventListener("click", (ev) => {
    const opt = ev.target.closest(".emoji-opt");
    if (!opt) return;
    curEmoji = opt.dataset.e;
    $$(".emoji-opt", picker).forEach((o) => o.classList.toggle("sel", o === opt));
  });
  // hue
  const hueInput = $("#w-hue"), huePrev = $("#hue-preview");
  const paintHue = () => { huePrev.style.cssText = coverCss(hueInput.value); };
  paintHue();
  hueInput.addEventListener("input", paintHue);
  // 预览
  const ta = $("#w-content"), preview = $("#w-preview"), wc = $("#word-count");
  let previewTimer = null;
  const doPreview = () => {
    preview.innerHTML = mdToHtml(ta.value);
    $$("pre code", preview).forEach((el) => { try { hljs.highlightElement(el); } catch (e) { } });
    wc.textContent = `${(ta.value || "").length} 字符`;
  };
  doPreview();
  ta.addEventListener("input", () => {
    clearTimeout(previewTimer);
    previewTimer = setTimeout(doPreview, 250);
  });
  ta.addEventListener("keydown", (ev) => {
    if (ev.key === "Tab") {
      ev.preventDefault();
      const s = ta.selectionStart, epos = ta.selectionEnd;
      ta.value = ta.value.slice(0, s) + "  " + ta.value.slice(epos);
      ta.selectionStart = ta.selectionEnd = s + 2;
    }
  });
  // 上传
  $("#w-upload-img").onclick = () => $("#file-img").click();
  $("#w-upload-file").onclick = () => $("#file-any").click();
  $("#file-img").addEventListener("change", (ev) => handleUpload(ev, "img"));
  $("#file-any").addEventListener("change", (ev) => handleUpload(ev, "file"));
  async function handleUpload(ev, kind) {
    const file = ev.target.files?.[0];
    ev.target.value = "";
    if (!file) return;
    if (kind === "img" && !file.type.startsWith("image/")) return toast("请选择图片文件", "err");
    if (file.size > 20 * 1024 * 1024) return toast("文件不能超过 20MB", "err");
    const safeName = file.name.replace(/[^\w.\-\u4e00-\u9fa5]/g, "_").slice(-60);
    const sub = kind === "img" ? "blog-images" : "attachments";
    const ext = safeName.includes(".") ? "" : (kind === "img" ? ".png" : "");
    const path = cloud.storage.sharedPath(session.user.id, `${sub}/${Date.now()}-${safeName}${ext}`);
    const btn = kind === "img" ? $("#w-upload-img") : $("#w-upload-file");
    const old = btn.textContent;
    btn.textContent = "⏳ 上传中…";
    try {
      const r = await cloud.storage.upload(path, file, { contentType: file.type || "application/octet-stream" });
      if (r.error) throw r.error;
      const scheme = kind === "img" ? "cloudimg:" : "cloudfile:";
      const insert = kind === "img"
        ? `\n![${safeName}](${scheme}${path} "${safeName}")\n`
        : `\n[${safeName}](${scheme}${path})\n`;
      const s = ta.selectionStart;
      ta.value = ta.value.slice(0, s) + insert + ta.value.slice(ta.selectionEnd);
      doPreview();
      toast(`${kind === "img" ? "图片" : "附件"}已上传至云端存储`, "ok");
    } catch (e) {
      toast("上传失败：" + (e.message || "请稍后再试"), "err");
    } finally { btn.textContent = old; }
  }
  // 保存
  $("#w-cancel").onclick = () => { history.length > 1 ? history.back() : (location.hash = "#/"); };
  $("#w-save").onclick = async () => {
    const title = $("#w-title").value.trim();
    const summary = $("#w-summary").value.trim();
    const content = ta.value;
    const tags = [...new Set($("#w-tags").value.split(/[,，]/).map((t) => t.trim()).filter(Boolean))].slice(0, 6);
    const status = $("#w-status").value;
    const hue = Number(hueInput.value) || 210;
    if (!title) return toast("标题不能为空", "err");
    if (!content.trim()) return toast("正文不能为空", "err");
    const btn = $("#w-save");
    btn.disabled = true; btn.textContent = "⏳ 保存中…";
    const row = { title, summary, content, tags, status, cover_emoji: curEmoji, cover_hue: hue, updated_at: new Date().toISOString() };
    try {
      let res;
      if (isEdit) {
        res = await cloud.database.from("posts").update(row).eq("id", editId).select();
        if (!Array.isArray(res.data) || res.data.length === 0) throw { message: "保存失败：文章不存在或不属于当前账号" };
      } else {
        res = await cloud.database.from("posts").insert(row).select();
      }
      if (res.error) throw res.error;
      toast(isEdit ? "修改已保存" : (status === "draft" ? "草稿已保存" : "发布成功 🎉"), "ok");
      location.hash = status === "draft" ? "#/mine" : `#/post/${res.data[0].id}`;
    } catch (e) {
      toast("保存失败：" + (e.message || "请稍后再试"), "err");
      btn.disabled = false; btn.textContent = isEdit ? "💾 保存修改" : "💾 发布文章";
    }
  };
}

/* ---------- 13. 页面：我的文章 ---------- */
async function pageMine(app) {
  if (!session || !session.user) { location.hash = "#/login"; return; }
  app.innerHTML = `<div class="page-fade"><div class="section-head"><h2>📂 我的文章</h2>
    <span class="sub"><button class="btn btn-sm btn-primary" onclick="location.hash='#/write'">✍️ 写新文章</button></span></div>
    <div id="post-area"><div class="spinner"></div></div><div id="pager"></div></div>`;
  try {
    const res = await cloud.database.from("posts")
      .select("id,title,summary,tags,cover_emoji,cover_hue,status,views,created_at,owner_id", { count: "exact" })
      .eq("owner_id", session.user.id)
      .order("updated_at", { ascending: false })
      .range(0, PAGE_SIZE - 1);
    unwrap(res, "load mine");
    const { data: posts, count } = res;
    const area = $("#post-area");
    if (!posts || !posts.length) {
      area.innerHTML = `<div class="empty-state"><div class="es-icon">🪶</div><p>你还没有发布过文章。</p>
        <button class="btn btn-primary" onclick="location.hash='#/write'">写下第一篇</button></div>`;
      $("#pager").innerHTML = "";
      return;
    }
    area.innerHTML = `<div class="post-grid">${posts.map((p, i) => postCardHtml(p, i)).join("")}</div>`;
    bindCardActions(posts);
    renderPager(1, count ?? posts.length);
  } catch (e) {
    $("#post-area").innerHTML = `<div class="empty-state"><div class="es-icon">⚠️</div><p>加载失败：${escapeHtml(e.message || "")}</p></div>`;
  }
}

/* ---------- 14. 页面：搜索 ---------- */
async function pageSearch(app, kw) {
  app.innerHTML = `<div class="page-fade"><div class="section-head"><h2>🔍 「${escapeHtml(kw)}」的搜索结果</h2></div>
    <div id="post-area"><div class="spinner"></div></div><div id="pager"></div></div>`;
  const safe = kw.replace(/[%_,()]/g, " ").trim();
  if (!safe) {
    $("#post-area").innerHTML = '<div class="empty-state"><div class="es-icon">🔍</div><p>请输入有效的搜索关键词。</p></div>';
    return;
  }
  try {
    const res = await cloud.database.from("posts")
      .select("id,title,summary,tags,cover_emoji,cover_hue,status,views,created_at,owner_id")
      .or(`title.ilike.%${safe}%,summary.ilike.%${safe}%`)
      .eq("status", "published")
      .order("created_at", { ascending: false })
      .limit(30);
    unwrap(res, "search");
    const posts = res.data || [];
    const area = $("#post-area");
    if (!posts.length) {
      area.innerHTML = `<div class="empty-state"><div class="es-icon">🏝️</div><p>没有找到与「${escapeHtml(kw)}」相关的文章。</p></div>`;
      $("#pager").innerHTML = "";
      return;
    }
    area.innerHTML = `<div class="post-grid">${posts.map((p, i) => postCardHtml(p, i)).join("")}</div>`;
    bindCardActions(posts);
    $("#pager").innerHTML = "";
  } catch (e) {
    $("#post-area").innerHTML = `<div class="empty-state"><div class="es-icon">⚠️</div><p>搜索失败：${escapeHtml(e.message || "")}</p></div>`;
  }
}

/* ---------- 15. 404 ---------- */
function pageNotFound(app) {
  app.innerHTML = `<div class="empty-state page-fade" style="margin-top:40px"><div class="es-icon">🧭</div>
    <p>这片海域还没有航路 —— 页面不存在。</p>
    <button class="btn btn-primary" onclick="location.hash='#/'">回到首页</button></div>`;
}

/* ---------- 16. 启动 ---------- */
function bindChrome() {
  $("#foot-year").textContent = new Date().getFullYear();
  // 导航
  $$(".nav-link").forEach((el) => {
    el.addEventListener("click", () => {
      const r = el.dataset.route;
      location.hash = r ? `#/${r}` : "#/";
    });
  });
  // 搜索
  $("#nav-search").addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") {
      const kw = ev.target.value.trim();
      if (kw) { location.hash = `#/search/${encodeURIComponent(kw)}`; ev.target.value = ""; }
    }
  });
  // 进度条 & 回到顶部
  window.addEventListener("scroll", () => {
    const st = window.scrollY, dh = document.documentElement.scrollHeight - innerHeight;
    $("#read-progress").style.width = dh > 0 ? `${(st / dh) * 100}%` : "0%";
    $("#back-top").classList.toggle("show", st > 500);
  }, { passive: true });
  window.addEventListener("hashchange", render);
}

(async function boot() {
  bindChrome();
  await initAuth();
  await render();
})();
