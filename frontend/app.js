const state = {
  mode: "hot",
  posts: [],
  authors: [],
  tags: [],
  token: localStorage.getItem("synapse_access_token") || "",
  currentUser: null,
  topic: "all",
};

const dom = {
  authScreen: document.querySelector("#auth-screen"),
  appShell: document.querySelector(".app-shell"),
  authLoginForm: document.querySelector("#auth-login-form"),
  authLoginEmail: document.querySelector("#auth-login-email"),
  authLoginPassword: document.querySelector("#auth-login-password"),
  authRegisterForm: document.querySelector("#auth-register-form"),
  registerName: document.querySelector("#register-name"),
  registerEmail: document.querySelector("#register-email"),
  registerPassword: document.querySelector("#register-password"),
  authDemoLogin: document.querySelector("#auth-demo-login"),
  feed: document.querySelector("#feed-list"),
  stories: document.querySelector("#stories"),
  suggestions: document.querySelector("#suggestion-list"),
  trends: document.querySelector("#trend-list"),
  activity: document.querySelector("#activity-list"),
  trendCount: document.querySelector("#trend-count"),
  feedStatus: document.querySelector("#feed-status"),
  toast: document.querySelector("#toast"),
  search: document.querySelector("#search-input"),
  topLogout: document.querySelector("#top-logout"),
  railAccount: document.querySelector("#rail-account"),
  postDialog: document.querySelector("#post-dialog"),
  dialogBody: document.querySelector("#dialog-body"),
  createDialog: document.querySelector("#create-dialog"),
  createForm: document.querySelector("#create-form"),
};

function iconRefresh() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function escapeHtml(value = "") {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatCount(value = 0) {
  const number = Number(value) || 0;
  if (number >= 1000000) return `${(number / 1000000).toFixed(1)}M`;
  if (number >= 1000) return `${(number / 1000).toFixed(1)}K`;
  return String(number);
}

function formatDate(value) {
  if (!value) return "now";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "now";
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function avatarFor(user) {
  return user?.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(user?.name || "Guest")}`;
}

function postImage(post) {
  return post.cover_image_url || `https://picsum.photos/seed/synapse-${post.id}/1200/630`;
}

function toast(message) {
  dom.toast.textContent = message;
  dom.toast.classList.add("show");
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => dom.toast.classList.remove("show"), 2600);
}

function resetProtectedUi() {
  state.posts = [];
  state.authors = [];
  state.tags = [];
  dom.feed.innerHTML = "";
  dom.stories.innerHTML = "";
  dom.suggestions.innerHTML = "";
  dom.trends.innerHTML = "";
  dom.activity.innerHTML = "";
  dom.trendCount.textContent = "";
  dom.feedStatus.textContent = "Login required";
}

function showAuthScreen() {
  document.body.classList.add("auth-locked");
  resetProtectedUi();
  iconRefresh();
}

function showAppScreen() {
  document.body.classList.remove("auth-locked");
  iconRefresh();
}

function clearSession() {
  localStorage.removeItem("synapse_access_token");
  state.token = "";
  state.currentUser = null;
  renderAccount();
}

async function api(path, options = {}, auth = false) {
  const headers = { ...(options.headers || {}) };
  if (auth && state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(path, { ...options, headers });
  if (response.status === 401) {
    clearSession();
    showAuthScreen();
    throw new Error("Login required");
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed: ${response.status}`);
  }

  if (response.status === 204) return null;
  return response.json();
}

function ensureAuth() {
  if (state.token && state.currentUser) return true;
  showAuthScreen();
  toast("Login first");
  return false;
}

async function loadCurrentUser() {
  if (!state.token) {
    renderAccount();
    showAuthScreen();
    return false;
  }

  try {
    state.currentUser = await api("/user/me", {}, true);
  } catch {
    clearSession();
    state.currentUser = null;
    showAuthScreen();
    return false;
  }
  renderAccount();
  showAppScreen();
  return true;
}

function renderAccount() {
  const user = state.currentUser;
  const img = avatarFor(user);
  dom.railAccount.innerHTML = `
    <img src="${escapeHtml(img)}" alt="" />
    <span>
      <strong>${escapeHtml(user?.name || "Guest")}</strong>
      <small>${escapeHtml(user ? `@${user.email.split("@")[0]}` : "Explore mode")}</small>
    </span>
  `;
  dom.topLogout.hidden = !state.token;
}

async function loadDiscovery() {
  if (!ensureAuth()) return;
  const params = new URLSearchParams({
    mode: state.mode === "following" ? "hot" : state.mode,
    limit: state.mode === "visual" ? "24" : "18",
  });
  state.posts = await api(`/blog/feed/discover?${params}`, {}, true);
  renderPosts();
}

async function loadFollowing() {
  if (!ensureAuth()) {
    return;
  }

  try {
    state.posts = await api("/blog/feed/following?limit=18", {}, true);
  } catch (error) {
    toast(error.message);
    state.posts = [];
  }
  renderPosts();
}

async function loadBookmarks() {
  if (!ensureAuth()) return;
  state.mode = "bookmarks";
  setSegments();
  state.posts = await api("/blog/bookmarks", {}, true);
  renderPosts();
}

async function loadSearch(term) {
  if (!ensureAuth()) return;
  const value = term.trim();
  if (!value) {
    await loadMode(state.mode === "bookmarks" ? "hot" : state.mode);
    return;
  }

  state.posts = await api(`/blog/?limit=18&search=${encodeURIComponent(value)}`);
  dom.feedStatus.textContent = `Search: ${value}`;
  renderPosts();
}

async function loadMode(mode) {
  if (!ensureAuth()) return;
  state.mode = mode;
  setSegments();
  if (mode === "following") {
    await loadFollowing();
  } else {
    await loadDiscovery();
  }
}

async function loadSidebarData() {
  if (!ensureAuth()) return;
  const [authors, tags] = await Promise.all([
    api("/blog/suggestions/authors?limit=8", {}, true),
    api("/blog/trending/tags?limit=12", {}, true),
  ]);
  state.authors = authors;
  state.tags = tags;
  renderStories();
  renderSuggestions();
  renderTrends();
}

function setSegments() {
  document.querySelectorAll(".segment").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === state.mode);
  });
  document.querySelectorAll(".nav-item[data-feed-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.feedMode === state.mode || (state.mode === "hot" && button.dataset.feedMode === "hot"));
  });
}

function renderStories() {
  dom.stories.innerHTML = state.authors
    .map((item) => {
      const user = item.user;
      return `
        <button class="story" data-author="${user.id}" title="${escapeHtml(user.name)}">
          <span class="story-avatar">
            <img src="${escapeHtml(avatarFor(user))}" alt="" />
          </span>
          <span>${escapeHtml(user.name.split(" ")[0])}</span>
        </button>
      `;
    })
    .join("");
  iconRefresh();
}

function renderSuggestions() {
  dom.suggestions.innerHTML = state.authors
    .map((item) => {
      const user = item.user;
      return `
        <article class="suggestion">
          <img src="${escapeHtml(avatarFor(user))}" alt="" />
          <span>
            <strong>${escapeHtml(user.name)}</strong>
            <small>${formatCount(item.followers_count)} followers · ${formatCount(item.posts_count)} posts</small>
          </span>
          <button class="follow-button" data-follow="${user.id}">${item.is_following ? "Following" : "Follow"}</button>
        </article>
      `;
    })
    .join("");
}

function renderTrends() {
  dom.trendCount.textContent = `${state.tags.length} tags`;
  dom.trends.innerHTML = state.tags
    .map((tag) => `
      <button class="trend" data-trend="${escapeHtml(tag.name)}">
        <span>#${escapeHtml(tag.name)}</span>
        <small>${formatCount(tag.post_count)} posts</small>
      </button>
    `)
    .join("");
}

function renderActivity() {
  const activityPosts = state.posts.slice(0, 5);
  dom.activity.innerHTML = activityPosts
    .map((post) => `
      <article class="activity">
        <img class="activity-avatar" src="${escapeHtml(avatarFor(post.creator))}" alt="" />
        <span>
          <strong>${escapeHtml(post.creator.name)}</strong>
          <small>${escapeHtml(post.title)}</small>
        </span>
      </article>
    `)
    .join("");
}

function renderPosts() {
  dom.feed.classList.toggle("visual-grid", state.mode === "visual");

  if (state.posts.length === 0) {
    dom.feed.innerHTML = `<div class="empty-state">No posts found</div>`;
    renderActivity();
    iconRefresh();
    return;
  }

  dom.feedStatus.textContent = {
    hot: "For You",
    following: "Following",
    latest: "Latest",
    visual: "Visual Grid",
    bookmarks: "Saved",
  }[state.mode] || "Feed";

  dom.feed.innerHTML = state.posts.map(renderPost).join("");
  renderActivity();
  iconRefresh();
}

function renderPost(post) {
  const category = post.category?.name || "General";
  const tags = (post.tags || []).slice(0, 4);
  const excerpt = String(post.content || "").replace(/\s+/g, " ").trim();
  const preview = excerpt.length > 280 ? `${excerpt.slice(0, 277)}...` : excerpt;
  const score = (post.likes_count || 0) * 2 + (post.share_count || 0) + Math.round((post.comments_count || 0) * 1.5);

  return `
    <article class="post-card" data-post="${post.id}">
      <aside class="vote-rail" aria-label="Post ranking">
        <button class="vote-button up" data-like="${post.id}" title="Upvote">
          <i data-lucide="chevron-up"></i>
        </button>
        <span class="vote-count">${formatCount(score)}</span>
        <button class="vote-button" data-less="${post.id}" title="Less like this">
          <i data-lucide="chevron-down"></i>
        </button>
      </aside>
      <div class="post-content">
        <header class="post-header">
          <div class="author-line">
            <img src="${escapeHtml(avatarFor(post.creator))}" alt="" />
            <span class="author-meta">
              <strong>${escapeHtml(post.creator.name)}</strong>
              <small>s/${escapeHtml(category.toLowerCase().replace(/\s+/g, "-"))} · ${formatDate(post.created_at)}</small>
            </span>
          </div>
          <button class="follow-button" data-follow="${post.creator.id}">Follow</button>
        </header>

        <div class="media-wrap">
          <img src="${escapeHtml(postImage(post))}" alt="" loading="lazy" />
          <span class="category-badge">${escapeHtml(category)}</span>
        </div>

        <h2 class="post-title">${escapeHtml(post.title)}</h2>
        <p class="post-excerpt">${escapeHtml(preview)}</p>
        <span class="char-count">${Math.min(preview.length, 280)}/280 chars</span>

        <div class="tag-row">
          ${tags.map((tag) => `<button class="chip" data-trend="${escapeHtml(tag.name)}">#${escapeHtml(tag.name)}</button>`).join("")}
        </div>

        <footer class="post-footer">
          <div class="engagements">
            <button class="engage-button" data-like="${post.id}">
              <i data-lucide="heart"></i>
              <span>${formatCount(post.likes_count)} likes</span>
            </button>
            <button class="engage-button" data-open-post="${post.id}">
              <i data-lucide="message-circle"></i>
              <span>${formatCount(post.comments_count)} comments</span>
            </button>
            <button class="engage-button" data-share="${post.id}">
              <i data-lucide="repeat-2"></i>
              <span>${formatCount(post.share_count)} shares</span>
            </button>
            <button class="engage-button" data-bookmark="${post.id}">
              <i data-lucide="bookmark"></i>
              <span>${formatCount(post.bookmarks_count)} saves</span>
            </button>
            <button class="engage-button" data-report="${post.id}">
              <i data-lucide="flag"></i>
              <span>Report</span>
            </button>
          </div>
          <button class="ghost-action read-button" data-open-post="${post.id}">
            <i data-lucide="panel-top-open"></i>
            <span>Expand Thread</span>
          </button>
        </footer>
      </div>
    </article>
  `;
}

function updatePostCount(postId, key, delta) {
  const post = state.posts.find((item) => item.id === postId);
  if (!post) return;
  post[key] = Math.max(0, (post[key] || 0) + delta);
  renderPosts();
}

async function likePost(postId) {
  if (!ensureAuth()) return;
  const response = await api(`/blog/${postId}/like`, { method: "POST" }, true);
  updatePostCount(postId, "likes_count", response.active ? 1 : -1);
  toast(response.message);
}

async function bookmarkPost(postId) {
  if (!ensureAuth()) return;
  const response = await api(`/blog/${postId}/bookmark`, { method: "POST" }, true);
  updatePostCount(postId, "bookmarks_count", response.active ? 1 : -1);
  toast(response.message);
}

async function sharePost(postId) {
  if (!ensureAuth()) return;
  const response = await api(`/blog/${postId}/share`, { method: "POST" });
  updatePostCount(postId, "share_count", 1);
  const url = `${window.location.origin}/?post=${postId}`;
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(url).catch(() => {});
  }
  toast(response.message);
}

async function reportPost(postId) {
  if (!ensureAuth()) return;
  const reason = window.prompt("Reason", "low-quality");
  if (!reason) return;
  await api(
    `/blog/${postId}/report`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    },
    true
  );
  toast("Report submitted");
}

async function followAuthor(userId) {
  if (!ensureAuth()) return;
  const response = await api(`/user/${userId}/follow`, { method: "POST" }, true);
  toast(response.message);
  await loadSidebarData();
}

async function openPost(postId) {
  if (!ensureAuth()) return;
  const [post, comments] = await Promise.all([
    api(`/blog/${postId}`),
    api(`/blog/${postId}/comments`),
  ]);

  dom.dialogBody.innerHTML = `
    <div class="dialog-image">
      <img src="${escapeHtml(postImage(post))}" alt="" />
    </div>
    <h2 class="post-title">${escapeHtml(post.title)}</h2>
    <div class="author-line">
      <img src="${escapeHtml(avatarFor(post.creator))}" alt="" />
      <span class="author-meta">
        <strong>${escapeHtml(post.creator.name)}</strong>
        <small>${escapeHtml(post.category?.name || "General")} · ${formatDate(post.created_at)}</small>
      </span>
    </div>
    <p class="dialog-body-text">${escapeHtml(post.content)}</p>
    <div class="engagements">
      <button class="engage-button" data-like="${post.id}">
        <i data-lucide="heart"></i>
        <span>${formatCount(post.likes_count)} likes</span>
      </button>
      <button class="engage-button" data-bookmark="${post.id}">
        <i data-lucide="bookmark"></i>
        <span>${formatCount(post.bookmarks_count)} saves</span>
      </button>
      <button class="engage-button" data-share="${post.id}">
        <i data-lucide="repeat-2"></i>
        <span>${formatCount(post.share_count)} shares</span>
      </button>
    </div>
    <section class="comment-list" id="comment-list">
      ${comments.map(renderComment).join("")}
    </section>
    <form class="create-form" id="comment-form">
      <label>
        <span>Comment</span>
        <textarea id="comment-content" rows="3" required></textarea>
      </label>
      <button class="primary-action full" type="submit">
        <i data-lucide="send"></i>
        <span>Post Comment</span>
      </button>
    </form>
  `;

  dom.dialogBody.querySelector("#comment-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!ensureAuth()) return;
    const textarea = dom.dialogBody.querySelector("#comment-content");
    const created = await api(
      `/blog/${post.id}/comments`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: textarea.value.trim() }),
      },
      true
    );
    textarea.value = "";
    dom.dialogBody.querySelector("#comment-list").insertAdjacentHTML("beforeend", renderComment(created));
    updatePostCount(post.id, "comments_count", 1);
    toast("Comment posted");
  });

  dom.postDialog.showModal();
  iconRefresh();
}

function renderComment(comment) {
  return `
    <article class="comment">
      <strong>${escapeHtml(comment.user?.name || "Reader")}</strong>
      <p>${escapeHtml(comment.content)}</p>
    </article>
  `;
}

async function login(email, password) {
  const body = new URLSearchParams({ username: email, password });
  const response = await api("/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  state.token = response.access_token;
  localStorage.setItem("synapse_access_token", state.token);
  const isValidUser = await loadCurrentUser();
  if (!isValidUser) return;
  state.mode = state.mode === "following" ? "following" : "hot";
  await Promise.all([loadSidebarData(), loadMode(state.mode)]);
  toast("Logged in");
}

async function register(event) {
  event.preventDefault();
  const payload = {
    name: dom.registerName.value.trim(),
    email: dom.registerEmail.value.trim(),
    password: dom.registerPassword.value,
  };

  await api("/user/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await login(payload.email, payload.password);
  dom.authRegisterForm.reset();
  toast("Account created");
}

async function logout() {
  clearSession();
  if (dom.postDialog.open) dom.postDialog.close();
  if (dom.createDialog.open) dom.createDialog.close();
  showAuthScreen();
  toast("Logged out");
}

async function createPost(event) {
  event.preventDefault();
  if (!ensureAuth()) return;
  if (!["author", "admin"].includes(state.currentUser?.role)) {
    toast("Author login required");
    return;
  }

  const payload = {
    title: document.querySelector("#create-title").value.trim(),
    content: document.querySelector("#create-content").value.trim(),
    cover_image_url: document.querySelector("#create-cover").value.trim() || null,
    category: document.querySelector("#create-category").value.trim() || null,
    tags: document.querySelector("#create-tags").value.split(",").map((tag) => tag.trim()).filter(Boolean),
    is_public: true,
    is_published: true,
  };

  await api(
    "/blog/",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    true
  );

  dom.createForm.reset();
  dom.createDialog.close();
  await loadMode("latest");
  toast("Post published");
}

function debounce(callback, delay = 260) {
  let timer;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => callback(...args), delay);
  };
}

function wireEvents() {
  document.querySelectorAll(".segment").forEach((button) => {
    button.addEventListener("click", () => loadMode(button.dataset.mode));
  });

  document.querySelectorAll(".nav-item[data-feed-mode]").forEach((button) => {
    button.addEventListener("click", () => loadMode(button.dataset.feedMode));
  });

  document.querySelectorAll(".node").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".node").forEach((node) => node.classList.remove("active"));
      button.classList.add("active");
      const topic = button.dataset.topic;
      state.topic = topic;
      dom.search.value = topic === "all" ? "" : topic;
      loadSearch(topic === "all" ? "" : topic);
    });
  });

  dom.feed.addEventListener("click", (event) => {
    const action = event.target.closest("button");
    if (!action) return;

    if (action.dataset.like) likePost(Number(action.dataset.like));
    if (action.dataset.bookmark) bookmarkPost(Number(action.dataset.bookmark));
    if (action.dataset.share) sharePost(Number(action.dataset.share));
    if (action.dataset.report) reportPost(Number(action.dataset.report));
    if (action.dataset.openPost) openPost(Number(action.dataset.openPost));
    if (action.dataset.follow) followAuthor(Number(action.dataset.follow));
    if (action.dataset.trend) {
      dom.search.value = action.dataset.trend;
      loadSearch(action.dataset.trend);
    }
    if (action.dataset.less) {
      state.posts = state.posts.filter((post) => post.id !== Number(action.dataset.less));
      renderPosts();
    }
  });

  dom.suggestions.addEventListener("click", (event) => {
    const button = event.target.closest("[data-follow]");
    if (button) followAuthor(Number(button.dataset.follow));
  });

  dom.trends.addEventListener("click", (event) => {
    const button = event.target.closest("[data-trend]");
    if (!button) return;
    dom.search.value = button.dataset.trend;
    loadSearch(button.dataset.trend);
  });

  dom.search.addEventListener("input", debounce((event) => loadSearch(event.target.value)));

  document.querySelector("#refresh-feed").addEventListener("click", () => loadMode(state.mode === "bookmarks" ? "hot" : state.mode));
  document.querySelector("#load-bookmarks").addEventListener("click", loadBookmarks);
  document.querySelector("#focus-login").addEventListener("click", () => {
    document.querySelector("#rail-account").scrollIntoView({ behavior: "smooth", block: "center" });
  });

  dom.authDemoLogin.addEventListener("click", () => login("seed_author_0001@example.com", "SeedPass123").catch((error) => toast(error.message)));
  dom.authLoginForm.addEventListener("submit", (event) => {
    event.preventDefault();
    login(dom.authLoginEmail.value.trim(), dom.authLoginPassword.value).catch((error) => toast(error.message));
  });
  dom.authRegisterForm.addEventListener("submit", (event) => {
    register(event).catch((error) => toast(error.message));
  });
  dom.topLogout.addEventListener("click", logout);

  document.querySelector("#open-create").addEventListener("click", () => dom.createDialog.showModal());
  document.querySelector("#open-create-inline").addEventListener("click", () => dom.createDialog.showModal());
  document.querySelector("[data-close-dialog]").addEventListener("click", () => dom.postDialog.close());
  document.querySelector("[data-close-create]").addEventListener("click", () => dom.createDialog.close());
  dom.createForm.addEventListener("submit", createPost);
}

async function init() {
  wireEvents();
  renderAccount();
  setSegments();
  const isValidUser = await loadCurrentUser();
  if (isValidUser) {
    await Promise.all([loadSidebarData(), loadDiscovery()]);
  } else {
    showAuthScreen();
  }
  iconRefresh();
}

init().catch((error) => {
  console.error(error);
  toast(error.message || "Something went wrong");
});
