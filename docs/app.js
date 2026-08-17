/* Dashboard do Desafio LH Nautical — le os JSON estaticos em data/ e desenha
   os graficos com Chart.js. Nao depende de nenhum backend. */

document.documentElement.classList.add("js-ready");

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

const COLOR = {
  series1: cssVar("--series-1"),
  series2: cssVar("--series-2"),
  series3: cssVar("--series-3"),
  text: cssVar("--text-secondary"),
  muted: cssVar("--text-muted"),
  grid: cssVar("--gridline"),
  baseline: cssVar("--baseline"),
  surface: cssVar("--surface-1"),
  border: cssVar("--border"),
};

Chart.defaults.font.family = "'Public Sans', system-ui, -apple-system, 'Segoe UI', sans-serif";
Chart.defaults.color = COLOR.text;
Chart.defaults.borderColor = COLOR.grid;
if (prefersReducedMotion) Chart.defaults.animation = false;
if (window.ChartDataLabels) Chart.register(ChartDataLabels);

const tooltipBase = {
  backgroundColor: COLOR.surface,
  titleColor: cssVar("--text-primary"),
  bodyColor: COLOR.text,
  borderColor: COLOR.border,
  borderWidth: 1,
  padding: 10,
  cornerRadius: 8,
  displayColors: false,
  titleFont: { weight: 600 },
};

const fmtBRL = (v) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(v);
const fmtBRLFull = (v) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
const fmtNum = (v) => new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(v);
const fmtDec2 = (v) => v.toFixed(2);
const fmtDate = (iso) => {
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
};
const fmtMonth = (iso) => {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("pt-BR", { month: "short", year: "2-digit" }).replace(".", "");
};

const FORMATTERS = { int: fmtNum, brl: fmtBRLFull, brl0: fmtBRL, dec2: fmtDec2 };

/* raw != null => vira contagem animada (count-up) quando a section entra na tela */
function tile(label, text, { small, raw, fmt } = {}) {
  const attrs = raw !== undefined ? ` data-raw="${raw}" data-fmt="${fmt || "int"}"` : "";
  return `<div class="tile reveal"><div class="tile-label">${label}</div><div class="tile-value${small ? " small" : ""}"${attrs}>${text}</div></div>`;
}

async function loadJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error("Falha ao carregar " + path);
  return res.json();
}

function verticalBarRadius() {
  return { topLeft: 5, topRight: 5, bottomLeft: 0, bottomRight: 0 };
}
function horizontalBarRadius() {
  return { topLeft: 0, bottomLeft: 0, topRight: 5, bottomRight: 5 };
}

function vGradient(ctx, chartArea, colorHex) {
  const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
  gradient.addColorStop(0, colorHex);
  gradient.addColorStop(1, `color-mix(in oklch, ${colorHex} 45%, transparent)`);
  return gradient;
}
function hGradient(ctx, chartArea, colorHex) {
  const gradient = ctx.createLinearGradient(chartArea.left, 0, chartArea.right, 0);
  gradient.addColorStop(0, `color-mix(in oklch, ${colorHex} 45%, transparent)`);
  gradient.addColorStop(1, colorHex);
  return gradient;
}

/* ---------------- animação: contagem numérica ---------------- */
function animateCount(el, target, formatter, duration = 900) {
  if (prefersReducedMotion || !isFinite(target)) {
    el.textContent = formatter(target);
    return;
  }
  const start = performance.now();
  function tick(now) {
    const p = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
    el.textContent = formatter(target * eased);
    if (p < 1) requestAnimationFrame(tick);
    else el.textContent = formatter(target);
  }
  requestAnimationFrame(tick);
}

function activateCountUps(root) {
  root.querySelectorAll(".tile-value[data-raw]").forEach((el) => {
    const target = parseFloat(el.dataset.raw);
    animateCount(el, target, FORMATTERS[el.dataset.fmt] || fmtNum);
  });
}

/* ---------------- animação: revelar ao rolar (com stagger) ---------------- */
function revealWithin(root) {
  const items = root.querySelectorAll(".reveal");
  items.forEach((el, i) => {
    el.style.transitionDelay = prefersReducedMotion ? "0ms" : `${Math.min(i, 8) * 70}ms`;
    el.classList.add("is-visible");
  });
}

/* ================= Q1 — Diagnóstico ================= */
function mountQ1(data) {
  document.getElementById("q1-tiles").innerHTML = [
    tile("Total de pedidos", fmtNum(data.total_pedidos), { raw: data.total_pedidos, fmt: "int" }),
    tile("Colunas", data.total_colunas),
    tile("Data mínima", fmtDate(data.data_min), { small: true }),
    tile("Data máxima", fmtDate(data.data_max), { small: true }),
    tile("Total médio", fmtBRL(data.total_medio), { raw: data.total_medio, fmt: "brl0" }),
    tile("Total mín. / máx.", fmtBRL(data.total_min) + " – " + fmtBRL(data.total_max), { small: true }),
  ].join("");

  return new Chart(document.getElementById("chart-q1-status"), {
    type: "bar",
    data: {
      labels: data.status_breakdown.map((d) => d.status),
      datasets: [{
        data: data.status_breakdown.map((d) => d.quantidade),
        backgroundColor: (c) => c.chart.chartArea ? vGradient(c.chart.ctx, c.chart.chartArea, COLOR.series1) : COLOR.series1,
        borderRadius: verticalBarRadius(),
        maxBarThickness: 56,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      layout: { padding: { top: 24 } },
      plugins: {
        legend: { display: false },
        tooltip: { ...tooltipBase, callbacks: { label: (c) => fmtNum(c.parsed.y) + " pedidos" } },
        datalabels: {
          anchor: "end", align: "end", color: COLOR.text, font: { size: 11, weight: 600 },
          formatter: (v) => fmtNum(v),
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: COLOR.muted } },
        y: {
          beginAtZero: true, grid: { color: COLOR.grid }, ticks: { color: COLOR.muted },
          suggestedMax: Math.max(...data.status_breakdown.map((d) => d.quantidade)) * 1.15,
        },
      },
    },
  });
}

/* ================= Q4 — Clientes fiéis ================= */
function mountQ4(data) {
  const clientes = data.clientes;

  document.getElementById("q4-tiles").innerHTML = [
    tile("Categoria líder (top 10)", data.categoria_top.category_name),
    tile("Unidades dessa categoria", fmtNum(data.categoria_top.quantidade_total), { small: true, raw: data.categoria_top.quantidade_total, fmt: "int" }),
    tile("Cliente #1 em ticket médio", "Cliente " + clientes[0].customer_id, { small: true }),
  ].join("");

  const chart = new Chart(document.getElementById("chart-q4-clientes"), {
    type: "bar",
    data: {
      labels: clientes.map((c) => "Cliente " + c.customer_id),
      datasets: [{
        data: clientes.map((c) => c.ticket_medio),
        backgroundColor: (c) => c.chart.chartArea ? hGradient(c.chart.ctx, c.chart.chartArea, COLOR.series1) : COLOR.series1,
        borderRadius: horizontalBarRadius(),
        maxBarThickness: 22,
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { ...tooltipBase, callbacks: { label: (c) => fmtBRLFull(c.parsed.x) } },
        datalabels: {
          anchor: "end", align: "end", color: COLOR.text, font: { size: 10, weight: 600 },
          formatter: (v) => fmtBRL(v),
        },
      },
      scales: {
        x: { beginAtZero: true, grid: { color: COLOR.grid }, ticks: { color: COLOR.muted, callback: (v) => fmtBRL(v) } },
        y: { grid: { display: false }, ticks: { color: COLOR.muted } },
      },
    },
  });

  const rows = clientes.map((c) => `
    <tr>
      <td>Cliente ${c.customer_id}</td>
      <td>${c.frequencia}</td>
      <td>${fmtBRLFull(c.faturamento_total)}</td>
      <td>${fmtBRLFull(c.ticket_medio)}</td>
      <td>${c.diversidade_categorias}</td>
    </tr>`).join("");
  document.getElementById("q4-table").innerHTML = `
    <thead><tr><th>Cliente</th><th>Frequência</th><th>Faturamento</th><th>Ticket médio</th><th>Categorias</th></tr></thead>
    <tbody>${rows}</tbody>`;

  return chart;
}

/* ================= Q5 — Vendas por dia da semana ================= */
function mountQ5(data) {
  const worst = data.reduce((a, b) => (a.media_vendas < b.media_vendas ? a : b));
  const best = data.reduce((a, b) => (a.media_vendas > b.media_vendas ? a : b));
  document.getElementById("q5-caption").innerHTML =
    `Pior dia: <strong>${worst.dia_semana}</strong> (${fmtBRLFull(worst.media_vendas)}) — melhor dia: <strong>${best.dia_semana}</strong> (${fmtBRLFull(best.media_vendas)}). Média calculada sobre os ${worst.qtd_dias_no_calendario} dias do calendário, incluindo os sem venda.`;

  return new Chart(document.getElementById("chart-q5-weekday"), {
    type: "bar",
    data: {
      labels: data.map((d) => d.dia_semana.replace("-feira", "")),
      datasets: [{
        data: data.map((d) => d.media_vendas),
        backgroundColor: (c) => c.chart.chartArea ? vGradient(c.chart.ctx, c.chart.chartArea, COLOR.series2) : COLOR.series2,
        borderRadius: verticalBarRadius(),
        maxBarThickness: 48,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      layout: { padding: { top: 24 } },
      plugins: {
        legend: { display: false },
        tooltip: { ...tooltipBase, callbacks: { label: (c) => fmtBRLFull(c.parsed.y) } },
        datalabels: {
          anchor: "end", align: "end", color: COLOR.text, font: { size: 10, weight: 600 },
          formatter: (v) => fmtBRL(v),
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: COLOR.muted } },
        y: {
          beginAtZero: true, grid: { color: COLOR.grid }, ticks: { color: COLOR.muted, callback: (v) => fmtBRL(v) },
          suggestedMax: Math.max(...data.map((d) => d.media_vendas)) * 1.15,
        },
      },
    },
  });
}

/* ================= Q6 — Previsão de demanda ================= */
function mountQ6(all) {
  const recent = all.filter((d) => d.mes >= "2025-01-01");
  const testSet = all.filter((d) => d.conjunto === "teste");
  const mae = testSet.reduce((sum, d) => sum + Math.abs(d.quantidade_real - d.quantidade_prevista), 0) / testSet.length;
  const totalPrevisto = Math.round(testSet.reduce((s, d) => s + d.quantidade_prevista, 0));
  const totalReal = testSet.reduce((s, d) => s + d.quantidade_real, 0);

  document.getElementById("q6-tiles").innerHTML = [
    tile("MAE (jan–mar/2026)", fmtDec2(mae), { raw: mae, fmt: "dec2" }),
    tile("Previsto no trimestre", fmtNum(totalPrevisto) + " un.", { raw: totalPrevisto, fmt: "int" }),
    tile("Real no trimestre", fmtNum(totalReal) + " un.", { raw: totalReal, fmt: "int" }),
  ].join("");

  return new Chart(document.getElementById("chart-q6-forecast"), {
    type: "line",
    data: {
      labels: recent.map((d) => fmtMonth(d.mes)),
      datasets: [
        {
          label: "Real",
          data: recent.map((d) => d.quantidade_real),
          borderColor: COLOR.series1,
          backgroundColor: COLOR.series1,
          borderWidth: 2.5,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: COLOR.series1,
          pointBorderColor: COLOR.surface,
          pointBorderWidth: 2,
          tension: 0.15,
        },
        {
          label: "Previsto (média móvel 3m)",
          data: recent.map((d) => d.quantidade_prevista),
          borderColor: COLOR.series2,
          backgroundColor: COLOR.series2,
          borderWidth: 2.5,
          borderDash: [6, 4],
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: COLOR.series2,
          pointBorderColor: COLOR.surface,
          pointBorderWidth: 2,
          tension: 0.15,
          spanGaps: true,
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "top", align: "end", labels: { color: COLOR.text, boxWidth: 14, usePointStyle: true, font: { weight: 600 } } },
        datalabels: { display: false },
        tooltip: { ...tooltipBase, displayColors: true, callbacks: { label: (c) => `${c.dataset.label}: ${fmtNum(c.parsed.y)} un.` } },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: COLOR.muted } },
        y: { beginAtZero: true, grid: { color: COLOR.grid }, ticks: { color: COLOR.muted } },
      },
    },
  });
}

/* ================= Q7 — Recomendação ================= */
function mountQ7(data) {
  return new Chart(document.getElementById("chart-q7-similares"), {
    type: "bar",
    data: {
      labels: data.map((d) => d.produto_recomendado_nome),
      datasets: [{
        data: data.map((d) => d.similaridade),
        backgroundColor: (c) => c.chart.chartArea ? hGradient(c.chart.ctx, c.chart.chartArea, COLOR.series1) : COLOR.series1,
        borderRadius: horizontalBarRadius(),
        maxBarThickness: 28,
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { ...tooltipBase, callbacks: { label: (c) => "similaridade " + c.parsed.x.toFixed(4) } },
        datalabels: {
          anchor: "end", align: "end", color: COLOR.text, font: { size: 11, weight: 600 },
          formatter: (v) => v.toFixed(4),
        },
      },
      scales: {
        x: { beginAtZero: true, grid: { color: COLOR.grid }, ticks: { color: COLOR.muted } },
        y: { grid: { display: false }, ticks: { color: COLOR.muted } },
      },
    },
  });
}

/* ================= orquestração: fetch eager, montagem lazy ================= */
const MOUNTERS = { q1: mountQ1, q4: mountQ4, q5: mountQ5, q6: mountQ6, q7: mountQ7 };
const FILES = {
  q1: "data/q1_diagnostico.json",
  q4: "data/q4_clientes_fieis.json",
  q5: "data/q5_vendas_dia_semana.json",
  q6: "data/q6_previsao_demanda.json",
  q7: "data/q7_recomendacoes.json",
};

const dataPromises = Object.fromEntries(
  Object.entries(FILES).map(([id, path]) => [id, loadJSON(path)])
);

const chartsBySection = {};
const mountedSections = new Set();

function hideWithin(root) {
  root.querySelectorAll(".reveal").forEach((el) => el.classList.remove("is-visible"));
}

/* monta os dados (tiles + Chart) uma única vez por seção — seções sem
   mounter (ex.: a síntese final, que é só conteúdo estático) só recebem
   a animação de reveal, sem tentar buscar dado nenhum. */
async function mountSection(section) {
  const id = section.id;
  if (!MOUNTERS[id]) {
    mountedSections.add(id);
    return;
  }
  try {
    const data = await dataPromises[id];
    const chart = MOUNTERS[id](data);
    if (chart) chartsBySection[id] = chart;
  } catch (err) {
    console.error(err);
    section.insertAdjacentHTML(
      "beforeend",
      `<p style="color:#e34948;padding:12px 16px;border:1px solid currentColor;border-radius:8px;">
         Erro ao carregar os dados desta seção: ${err.message}. Confira se a página está sendo servida por um
         servidor (não aberta como <code>file://</code>).
       </p>`
    );
  }
  mountedSections.add(id);
}

/* toca a animação (fade/slide, contagem, gráfico) — roda toda vez que a seção entra na tela */
function playSection(section) {
  revealWithin(section);
  activateCountUps(section);
  const chart = chartsBySection[section.id];
  if (chart) chart.update();
}

/* deixa tudo pronto pra reanimar da próxima vez que a seção voltar a aparecer */
function pauseSection(section) {
  hideWithin(section);
  const chart = chartsBySection[section.id];
  if (chart) chart.reset();
}

const sectionObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach(async (entry) => {
      const section = entry.target;
      if (entry.isIntersecting) {
        if (!mountedSections.has(section.id)) await mountSection(section);
        playSection(section);
      } else if (mountedSections.has(section.id)) {
        pauseSection(section);
      }
    });
  },
  { threshold: 0.15, rootMargin: "0px 0px -10% 0px" }
);
document.querySelectorAll("section.viz-root").forEach((s) => sectionObserver.observe(s));

/* ---------------- barra de progresso de leitura ---------------- */
const progressBar = document.getElementById("scroll-progress");
let progressTicking = false;
function updateProgress() {
  const scrollTop = window.scrollY;
  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  const pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
  progressBar.style.width = pct + "%";
  progressTicking = false;
}
window.addEventListener("scroll", () => {
  if (!progressTicking) {
    requestAnimationFrame(updateProgress);
    progressTicking = true;
  }
}, { passive: true });
updateProgress();

/* ---------------- navegação com indicador ativo (scrollspy) ---------------- */
const navLinks = Array.from(document.querySelectorAll(".topnav a"));
const navIndicator = document.querySelector(".nav-indicator");

function moveIndicatorTo(link) {
  if (!link) { navIndicator.classList.remove("is-active"); return; }
  const nav = link.parentElement.getBoundingClientRect();
  const rect = link.getBoundingClientRect();
  navIndicator.style.width = rect.width + "px";
  navIndicator.style.transform = `translateX(${rect.left - nav.left}px)`;
  navIndicator.classList.add("is-active");
}

const navObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const link = navLinks.find((a) => a.getAttribute("href") === "#" + entry.target.id);
      navLinks.forEach((a) => a.classList.remove("active"));
      if (link) {
        link.classList.add("active");
        moveIndicatorTo(link);
      }
    });
  },
  { rootMargin: "-40% 0px -55% 0px", threshold: 0 }
);
document.querySelectorAll("section.viz-root").forEach((s) => navObserver.observe(s));

window.addEventListener("resize", () => {
  const active = document.querySelector(".topnav a.active");
  if (active) moveIndicatorTo(active);
});
