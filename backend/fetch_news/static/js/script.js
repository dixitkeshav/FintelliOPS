const API_BASE = "";
const API = {
  NEWS: API_BASE + "/api/fetch-news/",
  CHART_DATA: API_BASE + "/api/chart-data/",
  ANALYZE_SENTIMENT: API_BASE + "/api/analyze-sentiment/",
  ANALYZE_WITH_INSIGHTS: API_BASE + "/api/analyze-with-insights/",
  CUSTOM_SENTIMENT: API_BASE + "/api/custom-sentiment/",
  SEARCH_TICKER: API_BASE + "/api/search-ticker/",
  AGENTS_RUN: API_BASE + "/api/agents/run/",
  QUANT_BACKTEST: API_BASE + "/api/quant/backtest/",
  EVALUATION_LATENCY: API_BASE + "/api/evaluation/latency/",
  CROSS_DOMAIN: API_BASE + "/api/cross-domain/",
};

let sentimentChart = null;
let trendChart = null;
let ws = null;

function getWsScheme() {
  return window.location.protocol === "https:" ? "wss:" : "ws:";
}

function connectWebSocket() {
  const host = window.location.host;
  const url = `${getWsScheme()}//${host}/ws/dashboard/`;
  try {
    ws = new WebSocket(url);
    ws.onopen = () => {
      const el = document.getElementById("ws-status");
      if (el) el.textContent = "WebSocket: connected";
      el?.classList.remove("bg-secondary", "bg-danger");
      el?.classList.add("bg-success");
    };
    ws.onclose = () => {
      const el = document.getElementById("ws-status");
      if (el) el.textContent = "WebSocket: disconnected";
      el?.classList.remove("bg-success");
      el?.classList.add("bg-secondary");
    };
    ws.onerror = () => {
      const el = document.getElementById("ws-status");
      if (el) el.textContent = "WebSocket: error";
      el?.classList.add("bg-danger");
    };
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "pong") return;
        if (data.recommendation) document.getElementById("market-impact").textContent = data.recommendation.substring(0, 80) + "...";
      } catch (_) {}
    };
  } catch (e) {
    const el = document.getElementById("ws-status");
    if (el) el.textContent = "WebSocket: unavailable";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  fetchNews();
  loadChartData();
  const marketImpact = document.getElementById("market-impact");
  if (marketImpact) marketImpact.textContent = "📊 Run agents or analyze news for impact.";
  const tickerInput = document.getElementById("ticker-input");
  if (tickerInput) tickerInput.addEventListener("input", handleTickerInput);
  connectWebSocket();
});

async function fetchNews() {
  const newsFeed = document.getElementById("news-feed");
  if (!newsFeed) return;
  newsFeed.innerHTML = "<div class=\"text-muted\">🔄 Fetching news...</div>";
  try {
    const response = await fetch(API.NEWS);
    if (!response.ok) throw new Error(`Server error: ${response.status}`);
    const data = await response.json();
    const articles = data.articles ?? [];
    displayNews(articles);
  } catch (error) {
    console.error("Error fetching news:", error);
    newsFeed.innerHTML = `<p class="text-danger">❌ ${error.message}</p><button class="btn btn-sm btn-outline-danger mt-2" onclick="fetchNews()">Retry</button>`;
  }
}

function displayNews(articles) {
  const newsFeed = document.getElementById("news-feed");
  if (!newsFeed) return;
  if (!articles.length) {
    newsFeed.innerHTML = "<p>No financial news available.</p>";
    return;
  }
  newsFeed.innerHTML = articles.map((a) => {
    const sentiment = (a.sentiment || "neutral").toLowerCase();
    const title = a.title || "Untitled";
    return `<p class="mb-1"><strong>${escapeHtml(title)}</strong> — <span class="sentiment-${sentiment}">${sentiment.toUpperCase()}</span></p>`;
  }).join("");
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

async function fetchCustomSentiment() {
  const tickerInput = document.getElementById("ticker-input");
  const resultEl = document.getElementById("custom-sentiment-result");
  if (!tickerInput || !resultEl) return;
  const ticker = tickerInput.value.trim().toUpperCase();
  if (!ticker) {
    resultEl.textContent = "Enter a ticker.";
    return;
  }
  try {
    const res = await fetch(API.CUSTOM_SENTIMENT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
    });
    if (!res.ok) throw new Error("API failed");
    const data = await res.json();
    const sentiment = (data.sentiment || "neutral").toLowerCase();
    const { className, emoji } = getSentimentStyling(sentiment);
    resultEl.innerHTML = `${ticker}: <span class="${className}">${sentiment}</span> ${emoji}` + (data.count ? ` (${data.count} articles)` : "");
  } catch (e) {
    resultEl.textContent = "Error fetching sentiment.";
  }
}

async function handleTickerInput(event) {
  const input = event.target;
  const dropdown = getOrCreateTickerDropdown(input);
  const query = input.value.trim().toUpperCase();
  if (!query) {
    dropdown.innerHTML = "";
    dropdown.style.display = "none";
    return;
  }
  try {
    const res = await fetch(`${API.SEARCH_TICKER}?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    const results = data.results || [];
    dropdown.innerHTML = results.length ? results.map((t) => `<div class="dropdown-item" onclick="selectTicker('${t}')">${t}</div>`).join("") : "<div class=\"dropdown-item disabled\">No matches</div>";
    dropdown.style.display = "block";
  } catch (_) {
    dropdown.innerHTML = "<div class=\"dropdown-item disabled\">Error</div>";
    dropdown.style.display = "block";
  }
}

function getOrCreateTickerDropdown(input) {
  let dropdown = document.getElementById("ticker-dropdown");
  if (!dropdown) {
    dropdown = document.createElement("div");
    dropdown.id = "ticker-dropdown";
    dropdown.className = "dropdown-menu show";
    dropdown.style.position = "absolute";
    dropdown.style.width = input.offsetWidth + "px";
    input.parentNode.appendChild(dropdown);
    input.setAttribute("autocomplete", "off");
  }
  return dropdown;
}

window.selectTicker = function (ticker) {
  const tickerInput = document.getElementById("ticker-input");
  const dropdown = document.getElementById("ticker-dropdown");
  if (tickerInput) tickerInput.value = ticker;
  if (dropdown) { dropdown.innerHTML = ""; dropdown.style.display = "none"; }
};

async function analyzeNews() {
  const textArea = document.getElementById("news-text");
  const resultDiv = document.getElementById("news-analysis-result");
  const insightsPanel = document.getElementById("insights-panel");
  if (!textArea || !resultDiv) return;
  const text = textArea.value.trim();
  if (!text) {
    resultDiv.textContent = "Enter news text.";
    return;
  }
  try {
    const res = await fetch(API.ANALYZE_SENTIMENT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error("API failed");
    const data = await res.json();
    const sentiment = (data.sentiment || "neutral").toLowerCase();
    const { className, emoji } = getSentimentStyling(sentiment);
    resultDiv.innerHTML = `Sentiment: <span class="${className}">${capitalize(sentiment)}</span> ${emoji}`;
    if (data.insights && insightsPanel) {
      renderInsights(data.insights);
      insightsPanel.classList.add("show");
    } else if (insightsPanel) insightsPanel.classList.remove("show");
  } catch (e) {
    resultDiv.textContent = "Error analyzing.";
  }
}

async function analyzeWithInsights() {
  const textArea = document.getElementById("news-text");
  const resultDiv = document.getElementById("news-analysis-result");
  const insightsPanel = document.getElementById("insights-panel");
  if (!textArea || !resultDiv) return;
  const text = textArea.value.trim();
  if (!text) {
    resultDiv.textContent = "Enter news text.";
    return;
  }
  resultDiv.textContent = "Loading full insights...";
  try {
    const res = await fetch(API.ANALYZE_WITH_INSIGHTS, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error("API failed");
    const data = await res.json();
    const sentiment = (data.sentiment || "neutral").toLowerCase();
    const { className, emoji } = getSentimentStyling(sentiment);
    resultDiv.innerHTML = `Sentiment: <span class="${className}">${capitalize(sentiment)}</span> ${emoji}`;
    if (data.insights && insightsPanel) {
      renderInsights(data.insights);
      insightsPanel.classList.add("show");
    }
  } catch (e) {
    resultDiv.textContent = "Error loading insights.";
  }
}

function renderInsights(insights) {
  const set = (id, content) => { const el = document.getElementById(id); if (el) el.textContent = content; };
  const setHtml = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };
  set("insight-why", insights.why_sentiment || "—");
  setHtml("insight-risks", (insights.risk_drivers || []).map((r) => `<li>${escapeHtml(r)}</li>`).join(""));
  set("insight-impact", insights.event_impact_summary || "—");
  setHtml("insight-events", (insights.events || []).map((e) => `<li>${escapeHtml((e.type || "") + ": " + (e.description || ""))}</li>`).join(""));
  const aspect = insights.aspect_sentiment;
  set("insight-aspect", aspect ? JSON.stringify(aspect, null, 2) : "—");
}

async function runAgents() {
  const resultEl = document.getElementById("agents-result");
  if (!resultEl) return;
  resultEl.innerHTML = "<span class=\"text-muted\">Running agents...</span>";
  try {
    const res = await fetch(API.AGENTS_RUN, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    let html = "<p><strong>Recommendation:</strong> " + escapeHtml(data.recommendation || "—") + "</p>";
    if (data.news_scout) html += "<p class=\"small\"><strong>News Scout:</strong> " + escapeHtml(data.news_scout.summary || "") + "</p>";
    if (data.risk && data.risk.risk_flags && data.risk.risk_flags.length) html += "<p class=\"small text-warning\"><strong>Risk flags:</strong> " + escapeHtml(data.risk.risk_flags.join("; ")) + "</p>";
    resultEl.innerHTML = html;
    const marketImpact = document.getElementById("market-impact");
    if (marketImpact && data.recommendation) marketImpact.textContent = data.recommendation.substring(0, 100) + (data.recommendation.length > 100 ? "…" : "");
  } catch (e) {
    resultEl.innerHTML = "<span class=\"text-danger\">Error: " + escapeHtml(e.message) + "</span>";
  }
}

async function runBacktest() {
  const tickerEl = document.getElementById("backtest-ticker");
  const resultEl = document.getElementById("backtest-result");
  if (!resultEl) return;
  const ticker = (tickerEl && tickerEl.value.trim()) || "AAPL";
  resultEl.textContent = "Running backtest...";
  try {
    const res = await fetch(API.QUANT_BACKTEST + "?ticker=" + encodeURIComponent(ticker));
    const data = await res.ok ? await res.json() : { error: res.statusText };
    resultEl.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    resultEl.textContent = "Error: " + e.message;
  }
}

async function runLatencyBenchmark() {
  const resultEl = document.getElementById("latency-result");
  if (!resultEl) return;
  resultEl.textContent = "Running benchmark...";
  try {
    const res = await fetch(API.EVALUATION_LATENCY);
    const data = await res.ok ? await res.json() : {};
    resultEl.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    resultEl.textContent = "Error: " + e.message;
  }
}

async function fetchCrossDomain() {
  const select = document.getElementById("domain-select");
  const reasoningEl = document.getElementById("cross-domain-reasoning");
  const articlesEl = document.getElementById("cross-domain-articles");
  if (!select || !reasoningEl || !articlesEl) return;
  const domain = select.value;
  reasoningEl.textContent = "Loading...";
  articlesEl.innerHTML = "";
  try {
    const res = await fetch(API.CROSS_DOMAIN + "?domain=" + encodeURIComponent(domain));
    const data = await res.ok ? await res.json() : {};
    reasoningEl.textContent = data.cross_domain_reasoning || "—";
    const articles = data.articles || [];
    articlesEl.innerHTML = articles.slice(0, 8).map((a) => `<p class="mb-1"><strong>${escapeHtml(a.title || "")}</strong> — <span class="sentiment-${(a.sentiment || "neutral")}">${(a.sentiment || "neutral").toUpperCase()}</span></p>`).join("");
  } catch (e) {
    reasoningEl.textContent = "Error: " + e.message;
  }
}

async function loadChartData() {
  try {
    const res = await fetch(API.CHART_DATA);
    const chartData = await res.json();
    renderSentimentChart(chartData.distribution || { labels: [], data: [] });
    renderTrendChart(chartData.trend || { labels: [], positive: [], negative: [] });
  } catch (_) {
    renderSentimentChart({ labels: ["Positive", "Negative", "Neutral"], data: [33, 33, 34] });
    renderTrendChart({ labels: ["D1", "D2", "D3", "D4", "D5"], positive: [50, 55, 52, 58, 60], negative: [25, 22, 26, 20, 18] });
  }
}

function renderSentimentChart(distribution) {
  const ctx = document.getElementById("sentimentChart")?.getContext("2d");
  if (!ctx) return;
  if (sentimentChart) sentimentChart.destroy();
  sentimentChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: distribution.labels || [],
      datasets: [{ data: distribution.data || [], backgroundColor: ["#28a745", "#dc3545", "#ffc107"] }],
    },
  });
}

function renderTrendChart(trend) {
  const ctx = document.getElementById("trendChart")?.getContext("2d");
  if (!ctx) return;
  if (trendChart) trendChart.destroy();
  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: trend.labels || [],
      datasets: [
        { label: "Positive", data: trend.positive || [], borderColor: "#28a745", fill: true },
        { label: "Negative", data: trend.negative || [], borderColor: "#dc3545", fill: true },
      ],
    },
  });
}

function refreshNews() {
  const el = document.getElementById("news-feed");
  if (el) el.innerHTML = "<p>🔄 Refreshing...</p>";
  fetchNews();
}

function getSentimentStyling(sentiment) {
  if (sentiment === "positive") return { className: "sentiment-positive", emoji: "📈" };
  if (sentiment === "negative") return { className: "sentiment-negative", emoji: "📉" };
  return { className: "sentiment-neutral", emoji: "⚖️" };
}

function capitalize(str) {
  return (str && str.charAt(0).toUpperCase() + str.slice(1)) || "";
}
