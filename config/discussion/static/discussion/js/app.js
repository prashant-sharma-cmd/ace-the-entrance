/**
 * forum.js
 * Vanilla JS — talks to Django REST API endpoints.
 * Place at: yourapp/static/forum/js/forum.js
 *
 * Expected Django URL names (namespaced as 'forum:'):
 *   forum:api-threads        GET  /forum/api/threads/          list + create
 *   forum:api-thread-detail  GET  /forum/api/threads/<id>/     single thread
 *   forum:api-replies        GET  /forum/api/threads/<id>/replies/  list + create
 *   forum:api-thread-like    POST /forum/api/threads/<id>/like/
 *   forum:api-reply-like     POST /forum/api/replies/<id>/like/
 *
 * FORUM_CONFIG is injected by the Django template (see forum.html).
 */

/* ── State ── */
let state = {
  view:            "list",   // "list" | "thread" | "new"
  threads:         [],
  activeThread:    null,
  activeReplies:   [],
  category:        "All",
  sort:            "recent",
  likedThreads:    new Set(JSON.parse(localStorage.getItem("likedThreads") || "[]")),
  likedReplies:    new Set(JSON.parse(localStorage.getItem("likedReplies") || "[]")),
};

/* ── Helpers ── */
function csrfHeaders() {
  return {
    "Content-Type": "application/json",
    "X-CSRFToken":  FORUM_CONFIG.csrfToken,
  };
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  const h = Math.floor(diff / 3600000);
  const d = Math.floor(diff / 86400000);
  if (m < 1)  return "just now";
  if (m < 60) return `${m}m ago`;
  if (h < 24) return `${h}h ago`;
  return `${d}d ago`;
}

function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast-msg toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4200);
}

function saveLikedThreads() {
  localStorage.setItem("likedThreads", JSON.stringify([...state.likedThreads]));
}
function saveLikedReplies() {
  localStorage.setItem("likedReplies", JSON.stringify([...state.likedReplies]));
}

/* ── API calls ── */
async function fetchThreads() {
  const params = new URLSearchParams();
  if (state.category !== "All") params.set("category", state.category);
  params.set("sort", state.sort);

  const res = await fetch(`${FORUM_CONFIG.apiBase}?${params}`);
  if (!res.ok) throw new Error("Failed to load threads");
  return res.json();
}

async function fetchThread(id) {
  const res = await fetch(`${FORUM_CONFIG.apiBase}${id}/`);
  if (!res.ok) throw new Error("Thread not found");
  return res.json();
}

async function fetchReplies(threadId) {
  const res = await fetch(`${FORUM_CONFIG.apiBase}${threadId}/replies/`);
  if (!res.ok) throw new Error("Failed to load replies");
  return res.json();
}

async function postThread(data) {
  const res = await fetch(FORUM_CONFIG.apiBase, {
    method:  "POST",
    headers: csrfHeaders(),
    body:    JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create thread");
  }
  return res.json();
}

async function postReply(threadId, body) {
  const res = await fetch(`${FORUM_CONFIG.apiBase}${threadId}/replies/`, {
    method:  "POST",
    headers: csrfHeaders(),
    body:    JSON.stringify({ body }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to post reply");
  }
  return res.json();
}

async function likeThread(id) {
  const res = await fetch(`${FORUM_CONFIG.apiBase}${id}/like/`, {
    method:  "POST",
    headers: csrfHeaders(),
  });
  if (!res.ok) throw new Error("Like failed");
  return res.json();
}

async function likeReply(id) {
  const res = await fetch(`${FORUM_CONFIG.apiBase.replace("threads", "replies")}${id}/like/`, {
    method:  "POST",
    headers: csrfHeaders(),
  });
  if (!res.ok) throw new Error("Like failed");
  return res.json();
}

/* ── Render helpers ── */
function renderThreadCard(thread) {
  const liked   = state.likedThreads.has(thread.id);
  const replies = thread.reply_count ?? 0;

  const card = document.createElement("div");
  card.className = "thread-card";
  card.dataset.id = thread.id;
  card.innerHTML = `
    <div class="thread-cat">${thread.category}</div>
    <div class="thread-title">${thread.title}</div>
    <div class="thread-snippet">${thread.body}</div>
    <div class="thread-meta">
      <span>by <strong>${thread.author_username}</strong></span>
      <span>${timeAgo(thread.created_at)}</span>
      <span>💬 ${replies}</span>
      <button class="like-btn${liked ? " liked" : ""}" data-thread-id="${thread.id}">
        ♥ <span class="like-count">${thread.likes}</span>
      </button>
    </div>`;

  card.querySelector(".like-btn").addEventListener("click", async (e) => {
    e.stopPropagation();
    await handleThreadLike(thread.id, card.querySelector(".like-btn"));
  });
  card.addEventListener("click", () => openThread(thread.id));
  return card;
}

function renderReplyCard(reply) {
  const liked = state.likedReplies.has(reply.id);
  const card  = document.createElement("div");
  card.className = "reply-card";
  card.dataset.id = reply.id;
  card.innerHTML = `
    <div class="reply-author">${reply.author_username}</div>
    <div class="reply-body">${reply.body}</div>
    <div class="reply-meta">
      <span>${timeAgo(reply.created_at)}</span>
      <button class="like-btn${liked ? " liked" : ""}" data-reply-id="${reply.id}">
        ♥ <span class="like-count">${reply.likes}</span>
      </button>
    </div>`;

  card.querySelector(".like-btn").addEventListener("click", async () => {
    await handleReplyLike(reply.id, card.querySelector(".like-btn"));
  });
  return card;
}

/* ── Like handlers ── */
async function handleThreadLike(threadId, btn) {
  if (!FORUM_CONFIG.isAuthenticated) {
    showToast("Please log in to like threads.", "warning"); return;
  }
  if (state.likedThreads.has(threadId)) {
    showToast("You already liked this thread.", "warning"); return;
  }
  try {
    const data = await likeThread(threadId);
    state.likedThreads.add(threadId);
    saveLikedThreads();
    btn.classList.add("liked");
    btn.querySelector(".like-count").textContent = data.likes;
  } catch {
    showToast("Could not record your like.", "error");
  }
}

async function handleReplyLike(replyId, btn) {
  if (!FORUM_CONFIG.isAuthenticated) {
    showToast("Please log in to like replies.", "warning"); return;
  }
  if (state.likedReplies.has(replyId)) {
    showToast("You already liked this reply.", "warning"); return;
  }
  try {
    const data = await likeReply(replyId);
    state.likedReplies.add(replyId);
    saveLikedReplies();
    btn.classList.add("liked");
    btn.querySelector(".like-count").textContent = data.likes;
  } catch {
    showToast("Could not record your like.", "error");
  }
}

/* ── View: List ── */
async function showList() {
  state.view = "list";
  document.getElementById("view-list").style.display   = "";
  document.getElementById("view-thread").style.display = "none";
  document.getElementById("view-new").style.display    = "none";

  const list = document.getElementById("thread-list");
  list.innerHTML = `<div class="loading">Loading threads…</div>`;

  try {
    state.threads = await fetchThreads();
    list.innerHTML = "";
    if (!state.threads.length) {
      list.innerHTML = `<div class="empty-state">No threads yet in this category.</div>`;
      return;
    }
    state.threads.forEach(t => list.appendChild(renderThreadCard(t)));
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Could not load threads. Please try again.</div>`;
    console.error(err);
  }
}

/* ── View: Thread Detail ── */
async function openThread(threadId) {
  state.view = "thread";
  document.getElementById("view-list").style.display   = "none";
  document.getElementById("view-thread").style.display = "";
  document.getElementById("view-new").style.display    = "none";

  const detailBox  = document.getElementById("thread-detail-box");
  const replyList  = document.getElementById("reply-list");
  const divider    = document.getElementById("reply-count-divider");

  detailBox.innerHTML = `<div class="loading">Loading…</div>`;
  replyList.innerHTML = "";

  try {
    const [thread, replies] = await Promise.all([
      fetchThread(threadId),
      fetchReplies(threadId),
    ]);
    state.activeThread  = thread;
    state.activeReplies = replies;

    const liked = state.likedThreads.has(thread.id);
    detailBox.innerHTML = `
      <div class="thread-cat">${thread.category}</div>
      <div class="thread-title">${thread.title}</div>
      <div class="thread-meta" style="margin-bottom:1rem;">
        <span>by <strong>${thread.author_username}</strong></span>
        <span>${timeAgo(thread.created_at)}</span>
        <button class="like-btn${liked ? " liked" : ""}" id="detail-like-btn">
          ♥ <span class="like-count">${thread.likes}</span>
        </button>
      </div>
      <div class="thread-body">${thread.body}</div>`;

    detailBox.querySelector("#detail-like-btn").addEventListener("click", async (e) => {
      await handleThreadLike(thread.id, e.currentTarget);
    });

    const count   = replies.length;
    divider.textContent = `${count} ${count === 1 ? "reply" : "replies"}`;

    replyList.innerHTML = "";
    if (!count) {
      replyList.innerHTML = `<div class="empty-state" style="margin-bottom:1rem;">Be the first to reply.</div>`;
    } else {
      replies.forEach(r => replyList.appendChild(renderReplyCard(r)));
    }

    // Scroll to top of thread
    document.getElementById("view-thread").scrollIntoView({ behavior: "smooth" });

  } catch (err) {
    detailBox.innerHTML = `<div class="empty-state">Could not load thread.</div>`;
    console.error(err);
  }
}

/* ── View: New Thread ── */
function showNew() {
  state.view = "new";
  document.getElementById("view-list").style.display   = "none";
  document.getElementById("view-thread").style.display = "none";
  document.getElementById("view-new").style.display    = "";
}

/* ── Submit: New Thread ── */
async function submitThread() {
  const title    = document.getElementById("new-title")?.value.trim();
  const body     = document.getElementById("new-body")?.value.trim();
  const category = document.getElementById("new-category")?.value;

  if (!title || !body) {
    showToast("Please fill in a title and body.", "warning"); return;
  }

  const btn = document.getElementById("btn-publish");
  btn.disabled    = true;
  btn.textContent = "Publishing…";

  try {
    await postThread({ title, body, category });
    showToast("Thread published!");
    document.getElementById("new-title").value = "";
    document.getElementById("new-body").value  = "";
    await showList();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled    = false;
    btn.textContent = "Publish Thread";
  }
}

/* ── Submit: Reply ── */
async function submitReply() {
  const body = document.getElementById("reply-body")?.value.trim();
  if (!body || !state.activeThread) return;

  const btn = document.getElementById("btn-post-reply");
  btn.disabled    = true;
  btn.textContent = "Posting…";

  try {
    const reply = await postReply(state.activeThread.id, body);
    document.getElementById("reply-body").value = "";

    state.activeReplies.push(reply);
    const replyList = document.getElementById("reply-list");

    // Remove "be the first" placeholder if present
    const placeholder = replyList.querySelector(".empty-state");
    if (placeholder) placeholder.remove();

    replyList.appendChild(renderReplyCard(reply));

    const count = state.activeReplies.length;
    document.getElementById("reply-count-divider").textContent =
      `${count} ${count === 1 ? "reply" : "replies"}`;

    showToast("Reply posted!");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled    = false;
    btn.textContent = "Post Reply";
  }
}

/* ── Event wiring ── */
document.addEventListener("DOMContentLoaded", () => {

  // Nav buttons
  document.getElementById("btn-open-new") ?.addEventListener("click", showNew);
  document.getElementById("btn-back")     ?.addEventListener("click", () => showList());
  document.getElementById("btn-back-new") ?.addEventListener("click", () => showList());
  document.getElementById("btn-publish")  ?.addEventListener("click", submitThread);
  document.getElementById("btn-post-reply")?.addEventListener("click", submitReply);

  // Category filter
  document.getElementById("category-controls").addEventListener("click", (e) => {
    const btn = e.target.closest(".cat-btn");
    if (!btn) return;
    document.querySelectorAll(".cat-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    state.category = btn.dataset.category;
    showList();
  });

  // Sort
  document.querySelectorAll(".sort-opt").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".sort-opt").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.sort = btn.dataset.sort;
      showList();
    });
  });

  // Initial load
  showList();
});