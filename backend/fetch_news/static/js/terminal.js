(function () {
  const API = {
    LIVE_TICKER: "/api/live-ticker/",
    NEWS: "/api/fetch-news/",
    CHART_DATA: "/api/chart-data/",
    ANALYZE_SENTIMENT: "/api/analyze-sentiment/",
    ANALYZE_WITH_INSIGHTS: "/api/analyze-with-insights/",
    AGENTS_RUN: "/api/agents/run/",
    SYMBOL_DEEP_DIVE: "/api/agents/symbol-deep-dive/",
  };

  let sentimentChart = null;
  let trendChart = null;
  let ws = null;

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function sentimentClass(s) {
    const t = (s || "neutral").toLowerCase();
    if (t === "positive") return "sentiment-positive";
    if (t === "negative") return "sentiment-negative";
    return "sentiment-neutral";
  }

  // ---------- Live ticker strip (indices / prices) ----------
  async function loadTickerStrip() {
    const el = document.getElementById("ticker-strip-inner");
    if (!el) return;
    try {
      const r = await fetch(API.LIVE_TICKER);
      const data = await r.json();
      const tickers = data.tickers || [];
      if (!tickers.length) {
        el.innerHTML = "<span class=\"text-muted\">No ticker data. Check yfinance.</span>";
        return;
      }
      const fragment = tickers.map((t) => {
        const ch = t.change_pct != null ? t.change_pct : 0;
        const chClass = ch >= 0 ? "positive" : "negative";
        return `<span class="ticker-item">
          <span class="sym">${escapeHtml(t.symbol)}</span>
          <span class="name" title="${escapeHtml(t.name)}">${escapeHtml(t.name)}</span>
          <span class="price">${typeof t.price === "number" ? t.price.toFixed(2) : t.price}</span>
          <span class="ch ${chClass}">${ch >= 0 ? "+" : ""}${ch.toFixed(2)}%</span>
        </span>`;
      }).join("");
      el.innerHTML = fragment + fragment;
    } catch (e) {
      el.innerHTML = "<span class=\"text-muted\">Ticker unavailable</span>";
    }
  }

  // ---------- News ticker (scrolling headlines) ----------
  function buildNewsTicker(articles) {
    const el = document.getElementById("news-ticker");
    if (!el) return;
    if (!articles || !articles.length) {
      el.innerHTML = "<span>No headlines</span>";
      return;
    }
    const parts = articles.map((a) => {
      const sent = (a.sentiment || "neutral").toLowerCase();
      return `<span class="${sentimentClass(sent)}">${escapeHtml((a.title || "").substring(0, 80))}${(a.title && a.title.length > 80) ? "…" : ""} • ${escapeHtml(sent)}</span>`;
    });
    el.innerHTML = parts.join(" &nbsp; | &nbsp; ") + " &nbsp; | &nbsp; " + parts.join(" &nbsp; | &nbsp; ");
  }

  // ---------- News feed list ----------
  function renderNewsFeed(articles) {
    const el = document.getElementById("news-feed");
    if (!el) return;
    if (!articles || !articles.length) {
      el.innerHTML = "<li class=\"text-muted\">No news</li>";
      return;
    }
    el.innerHTML = articles.map((a) => {
      const url = a.url || "#";
      const sent = (a.sentiment || "neutral").toLowerCase();
      return `<li>
        <span class="news-title"><a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(a.title || "Untitled")}</a></span>
        <span class="sentiment ${sentimentClass(sent)}">${escapeHtml(sent)}</span>
      </li>`;
    }).join("");
  }

  async function refreshNews() {
    try {
      const r = await fetch(API.NEWS);
      const data = await r.json();
      const articles = data.articles || [];
      buildNewsTicker(articles);
      renderNewsFeed(articles);
    } catch (e) {
      renderNewsFeed([]);
      buildNewsTicker([]);
    }
  }

  // ---------- Charts ----------
  async function loadCharts() {
    try {
      const r = await fetch(API.CHART_DATA);
      const d = await r.json();
      const dist = d.distribution || { labels: ["Positive", "Negative", "Neutral"], data: [33, 33, 34] };
      const trend = d.trend || { labels: ["D1", "D2", "D3", "D4", "D5"], positive: [50, 55, 52, 58, 60], negative: [25, 22, 26, 20, 18] };

      const ctx1 = document.getElementById("sentimentChart")?.getContext("2d");
      if (ctx1) {
        if (sentimentChart) sentimentChart.destroy();
        sentimentChart = new Chart(ctx1, {
          type: "doughnut",
          data: {
            labels: dist.labels,
            datasets: [{ data: dist.data, backgroundColor: ["#3fb950", "#f85149", "#d29922"] }],
          },
          options: { responsive: true, maintainAspectRatio: false },
        });
      }

      const ctx2 = document.getElementById("trendChart")?.getContext("2d");
      if (ctx2) {
        if (trendChart) trendChart.destroy();
        trendChart = new Chart(ctx2, {
          type: "line",
          data: {
            labels: trend.labels,
            datasets: [
              { label: "Positive", data: trend.positive, borderColor: "#3fb950", fill: true, tension: 0.3 },
              { label: "Negative", data: trend.negative, borderColor: "#f85149", fill: true, tension: 0.3 },
            ],
          },
          options: { responsive: true, maintainAspectRatio: false },
        });
      }
    } catch (_) {
      const ctx1 = document.getElementById("sentimentChart")?.getContext("2d");
      if (ctx1 && !sentimentChart) {
        sentimentChart = new Chart(ctx1, {
          type: "doughnut",
          data: { labels: ["P", "N", "U"], datasets: [{ data: [33, 33, 34], backgroundColor: ["#3fb950", "#f85149", "#d29922"] }] },
          options: { responsive: true, maintainAspectRatio: false },
        });
      }
    }
  }

  // ---------- Symbol Deep-Dive ----------
  async function runDeepDive() {
    const symEl = document.getElementById("deep-dive-symbol");
    const outEl = document.getElementById("deep-dive-result");
    if (!symEl || !outEl) return;
    const symbol = symEl.value.trim().toUpperCase();
    if (!symbol) {
      outEl.innerHTML = "<span class=\"text-muted\">Enter a symbol</span>";
      return;
    }
    outEl.innerHTML = "<span class=\"text-muted\">Running deep-dive…</span>";
    try {
      const r = await fetch(API.SYMBOL_DEEP_DIVE + "?symbol=" + encodeURIComponent(symbol));
      const data = await r.json();
      if (data.error && !data.prediction) {
        outEl.innerHTML = "<span class=\"text-danger\">" + escapeHtml(data.error) + "</span>";
        return;
      }
      let html = "";
      if (data.current_price != null) html += "<p class=\"price\">Price: " + escapeHtml(String(data.current_price)) + "</p>";
      if (data.company_name) html += "<p class=\"small text-muted\">" + escapeHtml(data.company_name) + " · " + escapeHtml(data.sector || "") + "</p>";
      if (data.similar_stocks && data.similar_stocks.length) html += "<p class=\"similar-stocks\">Similar stocks: " + escapeHtml(data.similar_stocks.join(", ")) + "</p>";
      if (data.prediction) html += "<div class=\"prediction\">" + escapeHtml(data.prediction) + "</div>";
      outEl.innerHTML = html || "<span class=\"text-muted\">No result</span>";
    } catch (e) {
      outEl.innerHTML = "<span class=\"text-danger\">" + escapeHtml(e.message) + "</span>";
    }
  }

  // ---------- Run agents ----------
  async function runAgents() {
    const outEl = document.getElementById("agents-result");
    if (!outEl) return;
    outEl.innerHTML = "<span class=\"text-muted\">Running agents…</span>";
    try {
      const r = await fetch(API.AGENTS_RUN, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      const data = await r.json();
      const rec = data.recommendation || data.error || "—";
      outEl.innerHTML = "<div class=\"agent-reco\">" + escapeHtml(rec) + "</div>";
    } catch (e) {
      outEl.innerHTML = "<span class=\"text-danger\">" + escapeHtml(e.message) + "</span>";
    }
  }

  // ---------- Analyze news (quick) ----------
  async function analyzeNews() {
    const textEl = document.getElementById("news-text");
    const resultEl = document.getElementById("news-analysis-result");
    const insightsEl = document.getElementById("insights-panel");
    if (!textEl || !resultEl) return;
    const text = textEl.value.trim();
    if (!text) {
      resultEl.textContent = "Paste news first.";
      return;
    }
    try {
      const r = await fetch(API.ANALYZE_SENTIMENT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await r.json();
      const sent = (data.sentiment || "neutral").toLowerCase();
      resultEl.innerHTML = "Sentiment: <span class=\"" + sentimentClass(sent) + "\">" + escapeHtml(sent) + "</span>";
      if (insightsEl) insightsEl.classList.remove("show");
    } catch (e) {
      resultEl.textContent = "Error";
    }
  }

  // ---------- Full insights ----------
  async function analyzeWithInsights() {
    const textEl = document.getElementById("news-text");
    const resultEl = document.getElementById("news-analysis-result");
    const insightsEl = document.getElementById("insights-panel");
    if (!textEl || !resultEl) return;
    const text = textEl.value.trim();
    if (!text) {
      resultEl.textContent = "Paste news first.";
      return;
    }
    resultEl.textContent = "Loading insights…";
    try {
      const r = await fetch(API.ANALYZE_WITH_INSIGHTS, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await r.json();
      const sent = (data.sentiment || "neutral").toLowerCase();
      resultEl.innerHTML = "Sentiment: <span class=\"" + sentimentClass(sent) + "\">" + escapeHtml(sent) + "</span>";
      const ins = data.insights || {};
      const whyEl = document.getElementById("insight-why");
      const risksEl = document.getElementById("insight-risks");
      const impactEl = document.getElementById("insight-impact");
      if (whyEl) whyEl.textContent = ins.why_sentiment || "—";
      if (risksEl) risksEl.textContent = (ins.risk_drivers || []).join("; ") || "—";
      if (impactEl) impactEl.textContent = ins.event_impact_summary || "—";
      if (insightsEl) insightsEl.classList.add("show");
    } catch (e) {
      resultEl.textContent = "Error";
    }
  }

  // ---------- WebSocket ----------
  function connectWs() {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = proto + "//" + window.location.host + "/ws/dashboard/";
    try {
      ws = new WebSocket(url);
      ws.onopen = () => {
        const el = document.getElementById("ws-status");
        if (el) { el.textContent = "Live"; el.className = "badge bg-success ws-status connected"; }
      };
      ws.onclose = () => {
        const el = document.getElementById("ws-status");
        if (el) { el.textContent = "Offline"; el.className = "badge bg-secondary ws-status disconnected"; }
      };
    } catch (_) {}
  }

  // ---------- Init & export ----------
  function init() {
    loadTickerStrip();
    refreshNews();
    loadCharts();
    connectWs();
    setInterval(loadTickerStrip, 120000);
    setInterval(refreshNews, 180000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.terminal = {
    refreshNews,
    runDeepDive,
    runAgents,
    analyzeNews,
    analyzeWithInsights,
  };
})();
