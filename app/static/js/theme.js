// Handles dark/light theme toggle and mobile sidebar toggle.
// Theme preference is also persisted server-side via /settings/update,
// but we flip it instantly client-side for a snappy feel.

document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const themeBtn = document.getElementById("themeToggle");

  function applyIcon() {
    if (!themeBtn) return;
    const icon = themeBtn.querySelector("i");
    if (!icon) return;
    icon.className = root.getAttribute("data-theme") === "dark"
      ? "fa-solid fa-moon"
      : "fa-solid fa-sun";
  }
  applyIcon();

  if (themeBtn) {
    themeBtn.addEventListener("click", async () => {
      const current = root.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      applyIcon();

      try {
        const form = new FormData();
        form.append("theme", next);
        form.append("screenshots_enabled", document.body.dataset.screenshotsEnabled || "");
        form.append("screenshot_interval", document.body.dataset.screenshotInterval || "300");
        form.append("daily_goal_minutes", document.body.dataset.dailyGoal || "120");
        await fetch("/settings/update", { method: "POST", body: form });
      } catch (e) {
        // Non-fatal: theme still applies client-side for this session.
        console.warn("Could not persist theme preference:", e);
      }
    });
  }

  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  }
});
