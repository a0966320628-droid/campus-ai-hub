function escapeHTML(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function loadDashboardSummary() {
    const box = document.getElementById("recentAnnouncements");
    if (!box) return;

    try {
        const response = await fetch("/api/dashboard/summary", {
            method: "GET",
            cache: "no-store"
        });
        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.message || "讀取首頁資料失敗");
        }

        renderRecentAnnouncements(result.data?.recent_posts || []);
    } catch (error) {
        console.error(error);
        box.innerHTML = `
            <div class="empty-state">
                無法載入最新公告。<br><br>${escapeHTML(error.message)}
            </div>
        `;
    }
}

function renderRecentAnnouncements(posts) {
    const box = document.getElementById("recentAnnouncements");
    if (!box) return;

    box.innerHTML = "";

    if (!posts || posts.length === 0) {
        box.innerHTML = `
            <div class="empty-state">
                目前還沒有公告。<br><br>
                <a href="/announcements" style="color:#60a5fa;text-decoration:none;">前往公告資訊 →</a>
            </div>
        `;
        return;
    }

    posts.forEach(post => {
        const item = document.createElement("div");
        item.className = "announcement-item";
        item.onclick = () => { location.href = "/announcements"; };

        const priorityBadge = post.is_ai_priority
            ? '<span class="badge badge-priority">⭐ AI 優先</span>'
            : "";

        let content = post.content || "";
        if (content.length > 120) content = content.substring(0, 120) + "...";

        item.innerHTML = `
            <div class="announcement-title">${escapeHTML(post.title || "未命名公告")}</div>
            <div class="announcement-badges">
                <span class="badge badge-category">${escapeHTML(post.category || "一般資訊")}</span>
                ${priorityBadge}
            </div>
            <div class="announcement-content">${escapeHTML(content)}</div>
            <div class="announcement-meta">
                ${post.author_name ? `<span>👤 ${escapeHTML(post.author_name)}</span>` : ""}
                ${post.created_at ? `<span>🕒 ${escapeHTML(post.created_at)}</span>` : ""}
            </div>
        `;
        box.appendChild(item);
    });
}

async function refreshNotifications() {
    try {
        const response = await fetch("/api/notifications/summary", { cache: "no-store" });
        if (!response.ok) return;

        const result = await response.json();
        if (!result.success) return;

        const data = result.data || {};
        const badge = document.getElementById("notificationBadge");
        const friendCount = document.getElementById("pendingFriendCount");
        const unreadCount = document.getElementById("unreadMessageCount");

        if (badge) {
            const total = data.total_notification_count ?? 0;
            badge.textContent = total;
            badge.classList.toggle("is-zero", total === 0);
        }
        if (friendCount) friendCount.textContent = data.pending_friend_count ?? 0;
        if (unreadCount) unreadCount.textContent = data.unread_message_count ?? 0;
    } catch (error) {
        console.debug("通知更新暫時失敗", error);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadDashboardSummary();
    refreshNotifications();
    setInterval(refreshNotifications, 15000);
});

window.addEventListener("pageshow", () => {
    loadDashboardSummary();
    refreshNotifications();
});
