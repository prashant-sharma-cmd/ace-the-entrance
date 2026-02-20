let state = {
  view:          "list",
  threads:       [],
  activeThread:  null,
  activeReplies: [],
  category:      "All",
  sort:          "recent",
  likedThreads:  new Set(JSON.parse(localStorage.getItem("likedThreads") || "[]")),
  likedReplies:  new Set(JSON.parse(localStorage.getItem("likedReplies") || "[]")),
};

const MAX_FILE_SIZE = 5 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"];

/* ─────────────────────────────────────────
   Generic helpers
───────────────────────────────────────── */
function csrfHeader() {
  return { "X-CSRFToken": FORUM_CONFIG.csrfToken };
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

function esc(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

/* ─────────────────────────────────────────
   Image upload helpers
───────────────────────────────────────── */
function validateImageFile(file) {
  if (!ALLOWED_TYPES.includes(file.type)) return "Only JPG, PNG, GIF and WEBP images are allowed.";
  if (file.size > MAX_FILE_SIZE)          return "Image must be smaller than 5 MB.";
  return null;
}

function wireUploadZone(opts) {
  const zone       = document.getElementById(opts.zoneId);
  const input      = document.getElementById(opts.inputId);
  const idle       = document.getElementById(opts.idleId);
  const preview    = document.getElementById(opts.previewId);
  const previewImg = document.getElementById(opts.previewImgId);
  const filename   = document.getElementById(opts.filenameId);
  const removeBtn  = document.getElementById(opts.removeBtnId);
  if (!zone || !input) return;

  function showPreview(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      filename.textContent  = file.name;
      idle.style.display    = "none";
      preview.style.display = "";
    };
    reader.readAsDataURL(file);
  }

  function clearPreview() {
    input.value           = "";
    previewImg.src        = "";
    filename.textContent  = "";
    preview.style.display = "none";
    idle.style.display    = "";
  }

  function handleFile(file) {
    const err = validateImageFile(file);
    if (err) { showToast(err, "error"); return; }
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    showPreview(file);
  }

  zone.addEventListener("click", (e) => {
    if (e.target === removeBtn || removeBtn.contains(e.target)) return;
    input.click();
  });
  zone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); }
  });
  input.addEventListener("change", () => { if (input.files[0]) handleFile(input.files[0]); });

  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  removeBtn.addEventListener("click", (e) => { e.stopPropagation(); clearPreview(); });
}

/* ─────────────────────────────────────────
   Lightbox
───────────────────────────────────────── */
function openLightbox(src) {
  const overlay = document.createElement("div");
  overlay.className = "lightbox-overlay";
  overlay.innerHTML = `
    <button class="lightbox-close" title="Close">&#x2715;</button>
    <img src="${src}" alt="Full size image">`;
  document.body.appendChild(overlay);
  const close = () => overlay.remove();
  overlay.addEventListener("click", close);
  overlay.querySelector(".lightbox-close").addEventListener("click", (e) => { e.stopPropagation(); close(); });
  overlay.querySelector("img").addEventListener("click", (e) => e.stopPropagation());
  const onKey = (e) => { if (e.key === "Escape") { close(); document.removeEventListener("keydown", onKey); } };
  document.addEventListener("keydown", onKey);
}

/* ─────────────────────────────────────────
   API calls
───────────────────────────────────────── */
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

/* CHANGED: uses FormData instead of JSON so image file can be sent */
async function postThread(data, imageFile) {
  const fd = new FormData();
  fd.append("title",    data.title);
  fd.append("body",     data.body);
  fd.append("category", data.category);
  if (imageFile) fd.append("image", imageFile);
  const res = await fetch(FORUM_CONFIG.apiBase, {
    method: "POST", headers: csrfHeader(), body: fd,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create thread");
  }
  return res.json();
}

/* CHANGED: uses FormData so image file can be sent with reply */
async function postReply(threadId, body, imageFile) {
  const fd = new FormData();
  fd.append("body", body);
  if (imageFile) fd.append("image", imageFile);
  const res = await fetch(`${FORUM_CONFIG.apiBase}${threadId}/replies/`, {
    method: "POST", headers: csrfHeader(), body: fd,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to post reply");
  }
  return res.json();
}

async function likeThread(id) {
  const res = await fetch(`${FORUM_CONFIG.apiBase}${id}/like/`, {
    method: "POST", headers: { ...csrfHeader(), "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Like failed");
  return res.json();
}

async function likeReply(id) {
  const base = FORUM_CONFIG.apiBase.replace(/\/threads\/$/, "/replies/");
  const res  = await fetch(`${base}${id}/like/`, {
    method: "POST", headers: { ...csrfHeader(), "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Like failed");
  return res.json();
}

/* ─────────────────────────────────────────
   Render helpers
───────────────────────────────────────── */
function renderThreadCard(thread) {
  const liked   = state.likedThreads.has(thread.id);
  const replies = thread.reply_count ?? 0;
  const hasImg  = !!thread.image_url;
  const card    = document.createElement("div");
  card.className  = "thread-card";
  card.dataset.id = thread.id;
  card.innerHTML  = `
    <div class="thread-card-inner">
      ${hasImg ? `<img class="thread-thumb" src="${esc(thread.image_url)}" alt="Thread image">` : ""}
      <div class="thread-card-content">
        <div class="thread-cat">${esc(thread.category)}</div>
        <div class="thread-title">${esc(thread.title)}</div>
        <div class="thread-snippet">${esc(thread.body)}</div>
        <div class="thread-meta">
          <span>by <strong>${esc(thread.author_username)}</strong></span>
          <span>${timeAgo(thread.created_at)}</span>
          <span>&#x1F4AC; ${replies}</span>
          ${hasImg ? `<span>&#x1F5BC; image</span>` : ""}
          <button class="like-btn${liked ? " liked" : ""}" data-thread-id="${thread.id}">
            &#x2665; <span class="like-count">${thread.likes}</span>
          </button>
        </div>
      </div>
    </div>`;
  card.querySelector(".like-btn").addEventListener("click", async (e) => {
    e.stopPropagation();
    await handleThreadLike(thread.id, card.querySelector(".like-btn"));
  });
  card.addEventListener("click", () => openThread(thread.id));
  return card;
}

function renderReplyCard(reply) {
  const liked  = state.likedReplies.has(reply.id);
  const hasImg = !!reply.image_url;
  const card   = document.createElement("div");
  card.className  = "reply-card";
  card.dataset.id = reply.id;
  card.innerHTML  = `
    <div class="reply-author">${esc(reply.author_username)}</div>
    <div class="reply-body">${esc(reply.body)}</div>
    ${hasImg ? `<div class="reply-image"><img src="${esc(reply.image_url)}" alt="Reply attachment"></div>` : ""}
    <div class="reply-meta">
      <span>${timeAgo(reply.created_at)}</span>
      <button class="like-btn${liked ? " liked" : ""}" data-reply-id="${reply.id}">
        &#x2665; <span class="like-count">${reply.likes}</span>
      </button>
    </div>`;
  card.querySelector(".like-btn").addEventListener("click", async () => {
    await handleReplyLike(reply.id, card.querySelector(".like-btn"));
  });
  if (hasImg) {
    card.querySelector(".reply-image img").addEventListener("click", () => openLightbox(reply.image_url));
  }
  return card;
}

/* ─────────────────────────────────────────
   Like handlers
───────────────────────────────────────── */
async function handleThreadLike(threadId, btn) {
  if (!FORUM_CONFIG.isAuthenticated) { showToast("Please log in to like threads.", "warning"); return; }
  if (state.likedThreads.has(threadId)) { showToast("You already liked this thread.", "warning"); return; }
  try {
    const data = await likeThread(threadId);
    state.likedThreads.add(threadId); saveLikedThreads();
    btn.classList.add("liked");
    btn.querySelector(".like-count").textContent = data.likes;
  } catch { showToast("Could not record your like.", "error"); }
}

async function handleReplyLike(replyId, btn) {
  if (!FORUM_CONFIG.isAuthenticated) { showToast("Please log in to like replies.", "warning"); return; }
  if (state.likedReplies.has(replyId)) { showToast("You already liked this reply.", "warning"); return; }
  try {
    const data = await likeReply(replyId);
    state.likedReplies.add(replyId); saveLikedReplies();
    btn.classList.add("liked");
    btn.querySelector(".like-count").textContent = data.likes;
  } catch { showToast("Could not record your like.", "error"); }
}

/* ─────────────────────────────────────────
   Views
───────────────────────────────────────── */
async function showList() {
  state.view = "list";
  document.getElementById("view-list").style.display   = "";
  document.getElementById("view-thread").style.display = "none";
  document.getElementById("view-new").style.display    = "none";
  const list = document.getElementById("thread-list");
  list.innerHTML = `<div class="loading">Loading threads&#x2026;</div>`;
  try {
    state.threads = await fetchThreads();
    list.innerHTML = "";
    if (!state.threads.length) { list.innerHTML = `<div class="empty-state">No threads yet in this category.</div>`; return; }
    state.threads.forEach(t => list.appendChild(renderThreadCard(t)));
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Could not load threads. Please try again.</div>`;
    console.error(err);
  }
}

async function openThread(threadId) {
  state.view = "thread";
  document.getElementById("view-list").style.display   = "none";
  document.getElementById("view-thread").style.display = "";
  document.getElementById("view-new").style.display    = "none";
  const detailBox = document.getElementById("thread-detail-box");
  const replyList = document.getElementById("reply-list");
  const divider   = document.getElementById("reply-count-divider");
  detailBox.innerHTML = `<div class="loading">Loading&#x2026;</div>`;
  replyList.innerHTML = "";
  try {
    const [thread, replies] = await Promise.all([fetchThread(threadId), fetchReplies(threadId)]);
    state.activeThread  = thread;
    state.activeReplies = replies;
    const liked  = state.likedThreads.has(thread.id);
    const hasImg = !!thread.image_url;
    detailBox.innerHTML = `
      <div class="thread-cat">${esc(thread.category)}</div>
      <div class="thread-title">${esc(thread.title)}</div>
      <div class="thread-meta" style="margin-bottom:1rem;">
        <span>by <strong>${esc(thread.author_username)}</strong></span>
        <span>${timeAgo(thread.created_at)}</span>
        <button class="like-btn${liked ? " liked" : ""}" id="detail-like-btn">
          &#x2665; <span class="like-count">${thread.likes}</span>
        </button>
      </div>
      <div class="thread-body">${esc(thread.body)}</div>
      ${hasImg ? `<div class="thread-image"><img src="${esc(thread.image_url)}" alt="Thread attachment"></div>` : ""}`;
    detailBox.querySelector("#detail-like-btn").addEventListener("click", async (e) => {
      await handleThreadLike(thread.id, e.currentTarget);
    });
    if (hasImg) {
      detailBox.querySelector(".thread-image img").addEventListener("click", () => openLightbox(thread.image_url));
    }
    const count = replies.length;
    divider.textContent = `${count} ${count === 1 ? "reply" : "replies"}`;
    replyList.innerHTML = "";
    if (!count) {
      replyList.innerHTML = `<div class="empty-state" style="margin-bottom:1rem;">Be the first to reply.</div>`;
    } else {
      replies.forEach(r => replyList.appendChild(renderReplyCard(r)));
    }
    document.getElementById("view-thread").scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    detailBox.innerHTML = `<div class="empty-state">Could not load thread.</div>`;
    console.error(err);
  }
}

function showNew() {
  state.view = "new";
  document.getElementById("view-list").style.display   = "none";
  document.getElementById("view-thread").style.display = "none";
  document.getElementById("view-new").style.display    = "";
}

/* ─────────────────────────────────────────
   Submit handlers
───────────────────────────────────────── */
async function submitThread() {
  const title     = document.getElementById("new-title")?.value.trim();
  const body      = document.getElementById("new-body")?.value.trim();
  const category  = document.getElementById("new-category")?.value;
  const imageFile = document.getElementById("new-image")?.files[0] || null;
  if (!title || !body) { showToast("Please fill in a title and body.", "warning"); return; }
  const btn = document.getElementById("btn-publish");
  btn.disabled = true; btn.textContent = "Publishing\u2026";
  try {
    await postThread({ title, body, category }, imageFile);
    showToast("Thread published!");
    document.getElementById("new-title").value = "";
    document.getElementById("new-body").value  = "";
    document.getElementById("btn-remove-image")?.click();
    await showList();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false; btn.textContent = "Publish Thread";
  }
}

async function submitReply() {
  const body      = document.getElementById("reply-body")?.value.trim();
  const imageFile = document.getElementById("reply-image")?.files[0] || null;
  if (!body || !state.activeThread) return;
  const btn = document.getElementById("btn-post-reply");
  btn.disabled = true; btn.textContent = "Posting\u2026";
  try {
    const reply = await postReply(state.activeThread.id, body, imageFile);
    document.getElementById("reply-body").value = "";
    document.getElementById("btn-remove-reply-image")?.click();
    state.activeReplies.push(reply);
    const replyList   = document.getElementById("reply-list");
    const placeholder = replyList.querySelector(".empty-state");
    if (placeholder) placeholder.remove();
    replyList.appendChild(renderReplyCard(reply));
    const count = state.activeReplies.length;
    document.getElementById("reply-count-divider").textContent = `${count} ${count === 1 ? "reply" : "replies"}`;
    showToast("Reply posted!");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false; btn.textContent = "Post Reply";
  }
}

/* ─────────────────────────────────────────
   Initialisation
───────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-open-new") ?.addEventListener("click", showNew);
  document.getElementById("btn-back")     ?.addEventListener("click", () => showList());
  document.getElementById("btn-back-new") ?.addEventListener("click", () => showList());
  document.getElementById("btn-publish")  ?.addEventListener("click", submitThread);
  document.getElementById("btn-post-reply")?.addEventListener("click", submitReply);

  document.getElementById("category-controls").addEventListener("click", (e) => {
    const btn = e.target.closest(".cat-btn");
    if (!btn) return;
    document.querySelectorAll(".cat-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    state.category = btn.dataset.category;
    showList();
  });

  document.querySelectorAll(".sort-opt").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".sort-opt").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.sort = btn.dataset.sort;
      showList();
    });
  });

  wireUploadZone({
    zoneId: "upload-zone",       inputId: "new-image",
    idleId: "upload-idle",       previewId: "upload-preview",
    previewImgId: "upload-preview-img", filenameId: "upload-filename",
    removeBtnId: "btn-remove-image",
  });

  wireUploadZone({
    zoneId: "reply-upload-zone",       inputId: "reply-image",
    idleId: "reply-upload-idle",       previewId: "reply-upload-preview",
    previewImgId: "reply-preview-img", filenameId: "reply-upload-filename",
    removeBtnId: "btn-remove-reply-image",
  });

  showList();
});