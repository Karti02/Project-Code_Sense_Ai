

const TICK_INTERVAL_MS = 5000;
const REFRESH_INTERVAL_MS = 5000;

async function tickActivity() {
  try {
    const res = await fetch("/activity/tick", { method: "POST" });
    const data = await res.json();
    const liveApp = document.getElementById("liveApp");
    const liveLang = document.getElementById("liveLang");
    const liveStatus = document.getElementById("liveStatus");
    if (liveApp) liveApp.textContent = data.app_name || "Unknown";
    if (liveLang) liveLang.textContent = data.language || "Unknown";
    if (liveStatus) {
      liveStatus.textContent = data.is_idle ? "Idle" : "Coding";
      liveStatus.style.color = data.is_idle ? "var(--warn)" : "var(--mint)";
    }
  } catch (e) {
    console.warn("tick failed", e);
  }
}

function fmtHMS(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = Math.floor(totalSeconds % 60);
  return `${h}h ${m}m ${s}s`;
}

let weeklyChart = null;
let langChart = null;

function renderCharts(chartData, langDist) {
  const weeklyCtx = document.getElementById("weeklyChart");
  if (weeklyCtx) {
    if (weeklyChart) weeklyChart.destroy();
    weeklyChart = new Chart(weeklyCtx, {
      type: "bar",
      data: {
        labels: chartData.labels,
        datasets: [{
          label: "Hours coded",
          data: chartData.hours,
          backgroundColor: "rgba(124, 92, 255, 0.55)",
          borderRadius: 6,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: "rgba(150,150,150,0.1)" } },
          x: { grid: { display: false } },
        },
      },
    });
  }

  const langCtx = document.getElementById("langChart");
  if (langCtx) {
    const labels = Object.keys(langDist);
    const values = Object.values(langDist).map(v => Math.round((v / 3600) * 100) / 100);
    if (langChart) langChart.destroy();
    if (labels.length) {
      langChart = new Chart(langCtx, {
        type: "doughnut",
        data: {
          labels,
          datasets: [{
            data: values,
            backgroundColor: ["#7c5cff", "#00e5a0", "#ffb84d", "#ff5c7a", "#4dabf7", "#c084fc", "#f472b6"],
            borderWidth: 0,
          }],
        },
        options: { plugins: { legend: { position: "bottom", labels: { boxWidth: 10 } } } },
      });
    }
  }
}

async function refreshDashboard() {
  try {
    const res = await fetch("/api/dashboard-data");
    const data = await res.json();

    const codingTimeEl = document.getElementById("statCodingTime");
    const keyboardEl = document.getElementById("statKeyboard");
    const mouseEl = document.getElementById("statMouse");
    const compileEl = document.getElementById("statCompile");
    const scoreEl = document.getElementById("statScore");
    const sessionsEl = document.getElementById("statSessions");
    const streakEl = document.getElementById("statStreak");

    if (codingTimeEl) codingTimeEl.textContent = fmtHMS(data.daily.coding_time_seconds);
    if (keyboardEl) keyboardEl.textContent = data.daily.keyboard_count.toLocaleString();
    if (mouseEl) mouseEl.textContent = data.daily.mouse_clicks.toLocaleString();
    if (compileEl) compileEl.textContent = data.daily.compile_count;
    if (scoreEl) scoreEl.textContent = data.daily.productivity_score + "/100";
    if (sessionsEl) sessionsEl.textContent = data.daily.sessions_count;
    if (streakEl) streakEl.textContent = data.streak + " days";

    renderCharts(data.chart, data.lang_dist);

    if (data.goal_reached) {
      const banner = document.getElementById("goalBanner");
      if (banner) banner.classList.remove("d-none");
    }
  } catch (e) {
    console.warn("dashboard refresh failed", e);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("weeklyChart") || document.getElementById("langChart")) {
    refreshDashboard();
    setInterval(refreshDashboard, REFRESH_INTERVAL_MS);
  }
  if (document.getElementById("liveApp")) {
    tickActivity();
    setInterval(tickActivity, TICK_INTERVAL_MS);
  }

  const compileBtn = document.getElementById("logCompileBtn");
  if (compileBtn) {
    compileBtn.addEventListener("click", async () => {
      await fetch("/activity/compile", { method: "POST" });
      compileBtn.textContent = "Logged ✓";
      setTimeout(() => { compileBtn.textContent = "Log a compile/run"; }, 1500);
    });
  }
});
