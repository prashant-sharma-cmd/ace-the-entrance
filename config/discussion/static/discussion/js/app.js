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

async function patchThread(id, data) {
  const res = await fetch(`${FORUM_CONFIG.apiBase}${id}/`, {
    method:  "PATCH",
    headers: { ...csrfHeader(), "Content-Type": "application/json" },
    body:    JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update thread");
  }
  return res.json();
}

/* Delete a thread */
async function deleteThread(id) {
  const res = await fetch(`${FORUM_CONFIG.apiBase}${id}/`, {
    method:  "DELETE",
    headers: { ...csrfHeader(), "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to delete thread");
  }
  // DELETE returns 204 No Content — no body to parse
}

/* Update (PATCH) a reply */
async function patchReply(id, body) {
  const base = FORUM_CONFIG.apiBase.replace(/\/threads\/$/, "/replies/");
  const res  = await fetch(`${base}${id}/`, {
    method:  "PATCH",
    headers: { ...csrfHeader(), "Content-Type": "application/json" },
    body:    JSON.stringify({ body }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update reply");
  }
  return res.json();
}

/* Delete a reply */
async function deleteReply(id) {
  const base = FORUM_CONFIG.apiBase.replace(/\/threads\/$/, "/replies/");
  const res  = await fetch(`${base}${id}/`, {
    method:  "DELETE",
    headers: { ...csrfHeader(), "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to delete reply");
  }
}

/*
 * editModal — handles the shared Edit modal for both threads and replies.
 * It stores a callback (onSave) that is set differently depending on
 * whether the user is editing a thread or a reply.
 */
const editModal = {
  overlay:    null,
  onSave:     null,   // set before opening
  editType:   null,   // "thread" | "reply"

  init() {
    this.overlay = document.getElementById("edit-modal-overlay");

    document.getElementById("btn-modal-close") .addEventListener("click", () => this.close());
    document.getElementById("btn-modal-cancel").addEventListener("click", () => this.close());
    document.getElementById("btn-modal-save")  .addEventListener("click", () => this._save());

    // Close when clicking the dim background
    this.overlay.addEventListener("click", (e) => {
      if (e.target === this.overlay) this.close();
    });

    // Close on Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && this.overlay.style.display !== "none") this.close();
    });
  },

  /** Open the modal pre-filled with existing values */
  open({ type, title = "", category = "", body = "", onSave }) {
    this.editType = type;
    this.onSave   = onSave;

    const threadFields = document.getElementById("edit-thread-fields");
    threadFields.style.display = (type === "thread") ? "" : "none";

    if (type === "thread") {
      document.getElementById("edit-title").value    = title;
      document.getElementById("edit-category").value = category;
    }
    document.getElementById("edit-body").value = body;
    document.getElementById("edit-modal-title").textContent =
      type === "thread" ? "Edit Thread" : "Edit Reply";

    this.overlay.style.display = "flex";
    // Focus first input for accessibility
    const first = this.overlay.querySelector("input, textarea");
    if (first) setTimeout(() => first.focus(), 50);
  },

  close() {
    this.overlay.style.display = "none";
    this.onSave  = null;
    this.editType = null;
  },

  async _save() {
    const body     = document.getElementById("edit-body").value.trim();
    const title    = document.getElementById("edit-title")?.value.trim();
    const category = document.getElementById("edit-category")?.value;

    if (!body) { showToast("Body cannot be empty.", "warning"); return; }
    if (this.editType === "thread" && !title) {
      showToast("Title cannot be empty.", "warning"); return;
    }

    const saveBtn = document.getElementById("btn-modal-save");
    saveBtn.disabled    = true;
    saveBtn.textContent = "Saving…";

    try {
      const payload = (this.editType === "thread")
        ? { title, category, body }
        : { body };
      await this.onSave(payload);
      this.close();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      saveBtn.disabled    = false;
      saveBtn.textContent = "Save Changes";
    }
  },
};


/**
 * Show a red confirmation bar inside a container element.
 * Calls onConfirm() when the user clicks "Yes, delete".
 * Removes itself on Cancel.
 *
 * @param {HTMLElement} container  — element to append the bar into
 * @param {Function}    onConfirm  — async function to call on confirm
 */
function showConfirmDeleteBar(container, onConfirm) {
  // Remove any existing bar first
  container.querySelector(".confirm-delete-bar")?.remove();

  const bar = document.createElement("div");
  bar.className = "confirm-delete-bar";
  bar.innerHTML = `
    <span>Are you sure you want to delete this?</span>
    <button class="btn-cancel-delete">Cancel</button>
    <button class="btn-confirm-delete">Yes, Delete</button>`;

  bar.querySelector(".btn-cancel-delete").addEventListener("click", () => bar.remove());
  bar.querySelector(".btn-confirm-delete").addEventListener("click", async () => {
    bar.querySelector(".btn-confirm-delete").disabled    = true;
    bar.querySelector(".btn-confirm-delete").textContent = "Deleting…";
    await onConfirm();
  });

  container.appendChild(bar);
}

/* ─────────────────────────────────────────
   Render helpers
───────────────────────────────────────── */
function renderThreadCard_NEW(thread) {
  const liked   = state.likedThreads.has(thread.id);
  const replies = thread.reply_count ?? 0;
  const hasImg  = !!thread.image_url;

  // Determine if the current user owns this thread
  const isOwner = FORUM_CONFIG.isAuthenticated &&
    (FORUM_CONFIG.currentUser === thread.author_username || FORUM_CONFIG.isSuperuser);

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
          ${isOwner ? `
          <span class="owner-actions">
            <button class="btn-edit"   data-action="edit-thread"   title="Edit thread">&#9998; Edit</button>
            <button class="btn-delete" data-action="delete-thread" title="Delete thread">&#x1F5D1; Delete</button>
          </span>` : ""}
        </div>
      </div>
    </div>`;

  card.querySelector(".like-btn").addEventListener("click", async (e) => {
    e.stopPropagation();
    await handleThreadLike(thread.id, card.querySelector(".like-btn"));
  });

  // Edit button on card (opens thread then triggers edit)
  if (isOwner) {
    card.querySelector("[data-action='edit-thread']").addEventListener("click", async (e) => {
      e.stopPropagation();
      await openThread(thread.id);  // navigate to detail view first
      // Small delay so detail view renders before we open modal
      setTimeout(() => triggerThreadEdit(), 100);
    });

    card.querySelector("[data-action='delete-thread']").addEventListener("click", async (e) => {
      e.stopPropagation();
      // Show confirm bar inside the card itself
      showConfirmDeleteBar(card, async () => {
        card.classList.add("being-deleted");
        try {
          await deleteThread(thread.id);
          showToast("Thread deleted.");
          await showList();
        } catch (err) {
          card.classList.remove("being-deleted");
          showToast(err.message, "error");
        }
      });
    });
  }

  card.addEventListener("click", () => openThread(thread.id));
  return card;
}



function renderReplyCard(reply) {
  const liked  = state.likedReplies.has(reply.id);
  const hasImg = !!reply.image_url;

  // Determine if the current user owns this reply
  const isOwner = FORUM_CONFIG.isAuthenticated &&
    (FORUM_CONFIG.currentUser === reply.author_username || FORUM_CONFIG.isSuperuser);

  const card   = document.createElement("div");
  card.className  = "reply-card";
  card.dataset.id = reply.id;
  card.innerHTML  = `
    <div class="reply-author">${esc(reply.author_username)}</div>
    <div class="reply-body-text">${esc(reply.body)}</div>
    ${hasImg ? `<div class="reply-image"><img src="${esc(reply.image_url)}" alt="Reply attachment"></div>` : ""}
    <div class="reply-meta">
      <span>${timeAgo(reply.created_at)}</span>
      <button class="like-btn${liked ? " liked" : ""}" data-reply-id="${reply.id}">
        &#x2665; <span class="like-count">${reply.likes}</span>
      </button>
      ${isOwner ? `
      <span class="owner-actions">
        <button class="btn-edit"   data-action="edit-reply"   title="Edit reply">&#9998; Edit</button>
        <button class="btn-delete" data-action="delete-reply" title="Delete reply">&#x1F5D1; Delete</button>
      </span>` : ""}
    </div>`;

  card.querySelector(".like-btn").addEventListener("click", async () => {
    await handleReplyLike(reply.id, card.querySelector(".like-btn"));
  });

  if (hasImg) {
    card.querySelector(".reply-image img").addEventListener("click", () => openLightbox(reply.image_url));
  }

  if (isOwner) {
    // Edit reply
    card.querySelector("[data-action='edit-reply']").addEventListener("click", () => {
      editModal.open({
        type: "reply",
        body: reply.body,
        onSave: async ({ body }) => {
          const updated = await patchReply(reply.id, body);
          // Update the displayed text in-place without re-fetching
          card.querySelector(".reply-body-text").textContent = updated.body;
          reply.body = updated.body;  // keep local state in sync
          showToast("Reply updated.");
        },
      });
    });

    // Delete reply
    card.querySelector("[data-action='delete-reply']").addEventListener("click", () => {
      showConfirmDeleteBar(card, async () => {
        card.classList.add("being-deleted");
        try {
          await deleteReply(reply.id);
          // Remove from local state array
          state.activeReplies = state.activeReplies.filter(r => r.id !== reply.id);
          card.remove();
          const count = state.activeReplies.length;
          document.getElementById("reply-count-divider").textContent =
            `${count} ${count === 1 ? "reply" : "replies"}`;
          if (!count) {
            document.getElementById("reply-list").innerHTML =
              `<div class="empty-state" style="margin-bottom:1rem;">Be the first to reply.</div>`;
          }
          showToast("Reply deleted.");
        } catch (err) {
          card.classList.remove("being-deleted");
          showToast(err.message, "error");
        }
      });
    });
  }

  return card;
}

/**
 * Opens the edit modal pre-filled with state.activeThread's values.
 * Updates the thread detail view in-place on save (no full reload).
 */
function triggerThreadEdit() {
  const thread = state.activeThread;
  if (!thread) return;

  editModal.open({
    type:     "thread",
    title:    thread.title,
    category: thread.category,
    body:     thread.body,
    onSave: async ({ title, category, body }) => {
      const updated = await patchThread(thread.id, { title, category, body });

      // Update local state
      state.activeThread = { ...thread, ...updated };

      // Patch the visible detail box without a full reload
      const box = document.getElementById("thread-detail-box");
      if (box) {
        box.querySelector(".thread-title").textContent  = updated.title;
        box.querySelector(".thread-body").textContent   = updated.body;
        box.querySelector(".thread-cat").textContent    = updated.category;
      }

      showToast("Thread updated.");
    },
  });
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
    state.threads.forEach(t => list.appendChild(renderThreadCard_NEW(t)));
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
    const isOwner = FORUM_CONFIG.isAuthenticated &&
      (FORUM_CONFIG.currentUser === thread.author_username || FORUM_CONFIG.isSuperuser);

    detailBox.innerHTML = `
      <div class="thread-cat">${esc(thread.category)}</div>
      <div class="thread-title">${esc(thread.title)}</div>
      <div class="thread-meta" style="margin-bottom:1rem;">
        <span>by <strong>${esc(thread.author_username)}</strong></span>
        <span>${timeAgo(thread.created_at)}</span>
        <button class="like-btn${liked ? " liked" : ""}" id="detail-like-btn">
          &#x2665; <span class="like-count">${thread.likes}</span>
        </button>
        ${isOwner ? `
        <span class="owner-actions">
          <button class="btn-edit"   id="btn-edit-thread"   title="Edit thread">&#9998; Edit</button>
          <button class="btn-delete" id="btn-delete-thread" title="Delete thread">&#x1F5D1; Delete</button>
        </span>` : ""}
      </div>
      <div class="thread-body">${esc(thread.body)}</div>
      ${hasImg ? `<div class="thread-image"><img src="${esc(thread.image_url)}" alt="Thread attachment"></div>` : ""}`;

    // Wire up existing like button
    detailBox.querySelector("#detail-like-btn").addEventListener("click", async (e) => {
      await handleThreadLike(thread.id, e.currentTarget);
    });

    if (hasImg) {
      detailBox.querySelector(".thread-image img").addEventListener("click", () => openLightbox(thread.image_url));
    }

    // Wire up owner edit/delete buttons (only present for owners)
    if (isOwner) {
      detailBox.querySelector("#btn-edit-thread")?.addEventListener("click", () => {
        triggerThreadEdit();
      });

      detailBox.querySelector("#btn-delete-thread")?.addEventListener("click", () => {
        showConfirmDeleteBar(detailBox, async () => {
          detailBox.classList.add("being-deleted");
          try {
            await deleteThread(thread.id);
            showToast("Thread deleted.");
            await showList();
          } catch (err) {
            detailBox.classList.remove("being-deleted");
            showToast(err.message, "error");
          }
        });
      });
    }
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
    editModal.init();
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

  editModal.init();

  showList();
});