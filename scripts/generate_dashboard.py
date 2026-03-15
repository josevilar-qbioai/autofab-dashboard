#!/usr/bin/env python3
"""
Genera docs/index.html — Dashboard Modelo Logístico Anidado + Autofabricación 2027
Sin dependencias externas (solo stdlib + math).
Uso: python3 scripts/generate_dashboard.py
"""
import json, math, os
from pathlib import Path
from datetime import datetime

ROOT    = Path(__file__).parent.parent
OUT_DIR = ROOT / "docs"
OUT_DIR.mkdir(exist_ok=True)
OUT     = OUT_DIR / "index.html"

TODAY = datetime.now().strftime("%Y-%m-%d %H:%M")

# ═══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS DEL MODELO
# ═══════════════════════════════════════════════════════════════════════════════

BASE_YEAR = 2026.0  # t=0

WAVES = [
    {"name": "Ola 1: LLM / Software IA",         "t0": 0.5, "K": 1.5, "gamma": 1.4, "year": 2026, "color": "#79c0ff"},
    {"name": "Ola 2: Robótica + autofab inicial", "t0": 1.0, "K": 2.5, "gamma": 1.2, "year": 2027, "color": "#56d364"},
    {"name": "Ola 3: Agentes autónomos",          "t0": 3.0, "K": 3.5, "gamma": 0.9, "year": 2029, "color": "#d2a8ff"},
    {"name": "Ola 4: Autofab 2ª fase",            "t0": 5.0, "K": 5.0, "gamma": 0.7, "year": 2031, "color": "#ffa657"},
]

# Robot dynamics
T_ROBOT  = 1.0   # t=1 → año 2027
ALPHA_R  = 0.30
P_H      = 0.05
R0       = 1.0

# Scénarios de η (eficiencia autofabricación)
SCENARIOS = {
    "base":       {"eta": 0.20, "r": 0.10, "color": "#38bdf8",  "label": "Base (η=0.20)"},
    "acelerado":  {"eta": 0.35, "r": 0.18, "color": "#a78bfa",  "label": "Acelerado (η=0.35)"},
    "optimo":     {"eta": 0.50, "r": 0.25, "color": "#4ade80",  "label": "Óptimo (η=0.50)"},
}

# ── Cartera ejemplo: €10.000 inicial, distribución ilustrativa ──────────────
# Estos datos son ficticios y sirven únicamente como ejemplo pedagógico del modelo.
CAPITAL_TOTAL = 10000
PILLARS = [
    {"name": "Escasez Digital (BTC)",  "capital": 4000, "epsilon": 1.00, "r": 0.25, "color": "#f59e0b"},
    {"name": "Renta Variable Global",  "capital": 2000, "epsilon": 0.15, "r": 0.10, "color": "#3b82f6"},
    {"name": "Tecnología / IA",        "capital": 1500, "epsilon": 0.70, "r": 0.20, "color": "#8b5cf6"},
    {"name": "Energía / Nuclear",      "capital": 1000, "epsilon": 0.55, "r": 0.15, "color": "#22c55e"},
    {"name": "Metales",                "capital":  800, "epsilon": 0.45, "r": 0.08, "color": "#eab308"},
    {"name": "Computación Cuántica",   "capital":  400, "epsilon": 0.90, "r": 0.30, "color": "#ec4899"},
    {"name": "Energía / Grid",         "capital":  300, "epsilon": 0.45, "r": 0.12, "color": "#06b6d4"},
]

# ε ponderado
eps_w = sum(p["epsilon"] * p["capital"] for p in PILLARS) / CAPITAL_TOTAL

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DEL MODELO
# ═══════════════════════════════════════════════════════════════════════════════

def logistic(t, t0, K, gamma):
    return K / (1 + math.exp(-gamma * (t - t0)))

def phi_nested(t):
    return 1 + sum(logistic(t, w["t0"], w["K"], w["gamma"]) for w in WAVES)

PHI0 = phi_nested(0)

def phi_norm(t):
    return phi_nested(t) / PHI0

def robot_pop(t, eta):
    if t < T_ROBOT:
        return 1.0
    dt = t - T_ROBOT
    return (R0 + P_H / ALPHA_R) * math.exp(ALPHA_R * eta * dt) - P_H / ALPHA_R

def scarcity(t, epsilon, eta):
    R = robot_pop(t, eta)
    return 1 + epsilon * (R - 1) / R

def V_pillar(t, capital, r, epsilon, eta):
    return capital * (1 + r)**t * phi_norm(t) * scarcity(t, epsilon, eta)

def V_total(t, eta):
    return sum(V_pillar(t, p["capital"], p["r"], p["epsilon"], eta) for p in PILLARS)

# ═══════════════════════════════════════════════════════════════════════════════
# CALCULAR SERIES TEMPORALES
# ═══════════════════════════════════════════════════════════════════════════════

T_RANGE = [i * 0.1 for i in range(0, 151)]   # t=0..15 (2026-2041)
YEARS   = [round(BASE_YEAR + t, 1) for t in T_RANGE]

# Φ_nested normalizado
phi_series = [round(phi_norm(t), 4) for t in T_RANGE]

# Olas individuales (normalizadas al K de cada ola)
wave_series = []
for w in WAVES:
    series = [round(logistic(t, w["t0"], w["K"], w["gamma"]) / w["K"], 4) for t in T_RANGE]
    wave_series.append(series)

# R(t) y C(t) por escenario
robot_series = {}
cost_series  = {}
for sc, params in SCENARIOS.items():
    rs = [round(robot_pop(t, params["eta"]), 4) for t in T_RANGE]
    cs = [round(1 / r if r > 0 else 1, 4) for r in rs]
    robot_series[sc] = rs
    cost_series[sc]  = cs

# Valor total del portfolio por escenario (t=0..15)
portfolio_series = {}
for sc, params in SCENARIOS.items():
    portfolio_series[sc] = [round(V_total(t, params["eta"]) / 1e6, 4) for t in T_RANGE]

# Proyección por pilar (escenario base, cada año entero)
T_YEARS = list(range(0, 16))  # 0..15
proj_years_labels = [str(int(BASE_YEAR + t)) for t in T_YEARS]
pillar_projections = {}
for p in PILLARS:
    pillar_projections[p["name"]] = [
        round(V_pillar(t, p["capital"], p["r"], p["epsilon"], SCENARIOS["base"]["eta"]) / 1e6, 4)
        for t in T_YEARS
    ]

# Tabla resumen años clave
TABLE_YEARS = [0, 1, 2, 3, 5, 7, 10, 15]
table_data = []
for t in TABLE_YEARS:
    row = {"year": int(BASE_YEAR + t)}
    for sc, params in SCENARIOS.items():
        row[sc] = round(V_total(t, params["eta"]) / 1e6, 2)
    row["phi"] = round(phi_norm(t), 3)
    row["R_base"] = round(robot_pop(t, SCENARIOS["base"]["eta"]), 2)
    row["R_opt"]  = round(robot_pop(t, SCENARIOS["optimo"]["eta"]), 2)
    table_data.append(row)

# Señales actuales (t ≈ 0 = hoy, 2026)
T_NOW = 0.0
phi_now = phi_norm(T_NOW)
R_now   = robot_pop(T_NOW, SCENARIOS["base"]["eta"])

# ═══════════════════════════════════════════════════════════════════════════════
# SERIALIZAR PARA JAVASCRIPT
# ═══════════════════════════════════════════════════════════════════════════════

js_data = json.dumps({
    "years":             YEARS,
    "phi_series":        phi_series,
    "wave_series":       wave_series,
    "waves_meta":        [{"name": w["name"], "color": w["color"], "year": w["year"]} for w in WAVES],
    "robot_base":        robot_series["base"],
    "robot_acc":         robot_series["acelerado"],
    "robot_opt":         robot_series["optimo"],
    "cost_base":         cost_series["base"],
    "cost_opt":          cost_series["optimo"],
    "portfolio_base":    portfolio_series["base"],
    "portfolio_acc":     portfolio_series["acelerado"],
    "portfolio_opt":     portfolio_series["optimo"],
    "pillar_labels":     proj_years_labels,
    "pillar_projections": pillar_projections,
    "pillar_colors":     {p["name"]: p["color"] for p in PILLARS},
    "table_data":        table_data,
    "capital_total":     CAPITAL_TOTAL,
    "eps_weighted":      round(eps_w, 3),
    "phi_raw":           round(PHI0, 3),         # phi_nested(0) bruto
    "phi_now":           round(phi_now, 3),       # normalizado = 1.0
    "phi_2027":          round(phi_norm(1.0), 3), # multiplicador en 2027
    "phi_2031":          round(phi_norm(5.0), 3), # multiplicador en 2031
    "T_ROBOT":           int(BASE_YEAR + T_ROBOT),
    "updated":           TODAY,
}, ensure_ascii=False)

# ═══════════════════════════════════════════════════════════════════════════════
# GENERAR HTML
# ═══════════════════════════════════════════════════════════════════════════════

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>🤖 Modelo Autofabricación 2027 · Jose Vilar</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0a0f1a;color:#e2e8f0;font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}}
.wrap{{max-width:960px;margin:0 auto;padding:24px 16px}}
h1{{font-size:1.4rem;font-weight:700;letter-spacing:.04em}}
h2{{font-size:.8rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#64748b;margin-bottom:14px}}
.card{{background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:20px;margin-bottom:18px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
@media(max-width:640px){{.grid2{{grid-template-columns:1fr}}.grid4{{grid-template-columns:1fr 1fr}}}}
.kpi{{text-align:center;padding:16px}}
.kpi .val{{font-size:1.8rem;font-weight:700;line-height:1.1}}
.kpi .lbl{{font-size:.72rem;color:#64748b;margin-top:5px;text-transform:uppercase;letter-spacing:.08em}}
.kpi .sub{{font-size:.8rem;margin-top:4px}}
.tag{{display:inline-block;padding:3px 10px;border-radius:999px;font-size:.8rem;font-weight:600}}
.upd{{color:#475569;font-size:.78rem}}
.chart-wrap{{position:relative;height:240px}}
.chart-wrap-lg{{position:relative;height:300px}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
thead tr{{border-bottom:1px solid #1e293b}}
th{{color:#64748b;font-weight:500;padding:6px 8px;text-align:right;font-size:.75rem}}
th:first-child{{text-align:left}}
td{{padding:6px 8px;text-align:right;border-bottom:1px solid #0f172a}}
td:first-child{{text-align:left;color:#94a3b8}}
tr:hover td{{background:#1e293b22}}
.badge{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}}
.wave-card{{border-left:3px solid;padding:10px 14px;border-radius:4px;background:#0a0f1a;margin-bottom:8px}}
.pill{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.75rem;margin-right:6px}}
.highlight{{color:#f8fafc;font-weight:600}}
</style>
</head>
<body>
<div class="wrap">

<!-- HEADER -->
<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:22px;flex-wrap:wrap;gap:10px">
  <div>
    <h1>🤖 Modelo Logístico Anidado · Autofabricación 2027</h1>
    <p style="color:#475569;font-size:.85rem;margin-top:5px">
      V(t) = Capital × (1+r)ᵗ × Φ_nested(t) × S(t) &nbsp;·&nbsp; Jose Vilar
    </p>
  </div>
  <div style="text-align:right">
    <span class="tag" style="background:#56d36422;color:#56d364;border:1px solid #56d36444">AUTOFAB → 2027</span>
    <p class="upd" style="margin-top:5px">Generado: {TODAY}</p>
  </div>
</div>

<!-- KPIs -->
<div class="grid4" style="margin-bottom:18px">
  <div class="card kpi">
    <div class="val" style="color:#56d364" id="kpi-phi">—</div>
    <div class="lbl">Φ_nested(0) bruto</div>
    <div class="sub" style="color:#64748b">→ <span id="kpi-phi-2027">—</span> en 2027</div>
  </div>
  <div class="card kpi">
    <div class="val" style="color:#79c0ff" id="kpi-capital">€10K</div>
    <div class="lbl">Capital ejemplo</div>
    <div class="sub" style="color:#64748b">datos ilustrativos</div>
  </div>
  <div class="card kpi">
    <div class="val" style="color:#ffa657" id="kpi-eps">—</div>
    <div class="lbl">ε ponderado</div>
    <div class="sub" style="color:#64748b">sensibilidad escasez</div>
  </div>
  <div class="card kpi">
    <div class="val" style="color:#f59e0b" id="kpi-proj">—</div>
    <div class="lbl">Proyección 2036</div>
    <div class="sub" style="color:#64748b">escenario base</div>
  </div>
</div>

<!-- OLAS TECNOLÓGICAS -->
<div class="card">
  <h2>🌊 Las 4 olas tecnológicas</h2>
  <div id="wave-cards"></div>
  <div class="chart-wrap" style="margin-top:16px">
    <canvas id="chart-waves"></canvas>
  </div>
</div>

<!-- PHI NESTED -->
<div class="card">
  <h2>Φ_nested(t) — multiplicador compuesto normalizado</h2>
  <p style="color:#94a3b8;font-size:.82rem;margin-bottom:14px">
    Cuántas veces se amplifica la economía respecto a 2026 · Φ_nested(0) = <span id="phi0" style="color:#e2e8f0;font-weight:600">1.00</span>
  </p>
  <div class="chart-wrap-lg">
    <canvas id="chart-phi"></canvas>
  </div>
</div>

<!-- ROBOT DYNAMICS (2 charts) -->
<div class="grid2">
  <div class="card">
    <h2>R(t) — población de robots autofabricantes</h2>
    <div class="chart-wrap">
      <canvas id="chart-robot"></canvas>
    </div>
  </div>
  <div class="card">
    <h2>C(t) — coste relativo de producción robótica</h2>
    <div class="chart-wrap">
      <canvas id="chart-cost"></canvas>
    </div>
  </div>
</div>

<!-- PORTFOLIO TOTAL -->
<div class="card">
  <h2>📈 Proyección total del portfolio (€446K base)</h2>
  <div class="chart-wrap-lg">
    <canvas id="chart-portfolio"></canvas>
  </div>
</div>

<!-- PORTFOLIO POR PILAR -->
<div class="card">
  <h2>🏗️ Proyección por pilar — escenario base</h2>
  <div class="chart-wrap-lg">
    <canvas id="chart-pillars"></canvas>
  </div>
</div>

<!-- TABLA RESUMEN -->
<div class="card">
  <h2>📋 Tabla de proyección — años clave</h2>
  <div style="overflow-x:auto">
    <table id="proj-table">
      <thead>
        <tr>
          <th style="text-align:left">Año</th>
          <th>Φ_nested</th>
          <th>R(base)</th>
          <th>R(óptimo)</th>
          <th style="color:#38bdf8">Base (M€)</th>
          <th style="color:#a78bfa">Acelerado (M€)</th>
          <th style="color:#4ade80">Óptimo (M€)</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>
</div>

<!-- MODELO MATEMÁTICO -->
<div class="card">
  <h2>📐 Formulación matemática</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
    <div>
      <p style="color:#64748b;font-size:.78rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Ola logística individual</p>
      <p style="font-family:monospace;color:#d2a8ff;background:#0a0f1a;padding:10px;border-radius:6px;font-size:.85rem;line-height:1.7">
        φᵢ(t) = Kᵢ / (1 + e^(−γᵢ(t−t₀ᵢ)))<br>
        Φ_nested(t) = 1 + Σᵢ φᵢ(t)<br>
        Φ_norm(t) = Φ(t) / Φ(0)
      </p>
    </div>
    <div>
      <p style="color:#64748b;font-size:.78rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Dinámica robot + prima de escasez</p>
      <p style="font-family:monospace;color:#56d364;background:#0a0f1a;padding:10px;border-radius:6px;font-size:.85rem;line-height:1.7">
        dR/dt = α_R · η(t) · R(t) + P_H<br>
        Sᵢ(t) = 1 + εᵢ · (R(t)−1)/R(t)<br>
        Vᵢ(t) = Cᵢ·(1+rᵢ)ᵗ·Φ_norm·Sᵢ
      </p>
    </div>
  </div>
  <div style="margin-top:14px;display:flex;flex-wrap:wrap;gap:8px">
    <span class="pill" style="background:#1e293b;color:#79c0ff">α_R = {ALPHA_R}</span>
    <span class="pill" style="background:#1e293b;color:#56d364">P_H = {P_H}</span>
    <span class="pill" style="background:#1e293b;color:#ffa657">η base = 0.20 · acelerado = 0.35 · óptimo = 0.50</span>
    <span class="pill" style="background:#f8717133;color:#f87171">Autofab: {int(BASE_YEAR + T_ROBOT)}</span>
  </div>
</div>

<!-- NOTAS DE MODELO -->
<div style="margin-top:16px;margin-bottom:30px;color:#475569;font-size:.78rem;text-align:center;line-height:1.6">
  Modelo V1.4 · Bass (1969), Rogers (1962), Kondratiev (1925) ·
  <strong style="color:#f87171">Datos ilustrativos — cartera de ejemplo €10.000, no refleja ningún portfolio real</strong> ·
  <a href="https://github.com/josevilar-qbioai/autofab-dashboard" style="color:#38bdf8;text-decoration:none">GitHub</a>
</div>

</div><!-- /wrap -->

<script>
// ═══════════════════════════════════════════════════════════════════════════
// DATOS
// ═══════════════════════════════════════════════════════════════════════════
const DATA = {js_data};

// ═══════════════════════════════════════════════════════════════════════════
// KPIs
// ═══════════════════════════════════════════════════════════════════════════
document.getElementById('kpi-phi').textContent   = DATA.phi_raw.toFixed(2) + '×';
document.getElementById('kpi-phi-2027').textContent = DATA.phi_2027.toFixed(2) + '×';
document.getElementById('kpi-eps').textContent   = (DATA.eps_weighted * 100).toFixed(0) + '%';

// Proyección 2036 (t=10)
const idx10 = DATA.years.findIndex(y => Math.abs(y - 2036) < 0.05);
const proj2036 = idx10 >= 0 ? DATA.portfolio_base[idx10] : null;
if (proj2036) document.getElementById('kpi-proj').textContent = '€' + proj2036.toFixed(1) + 'M';

// φ0
const phi0 = (DATA.phi_series[0] !== undefined) ? 1.00 : 1.00;
document.getElementById('phi0').textContent = phi0.toFixed(2);

// ═══════════════════════════════════════════════════════════════════════════
// WAVE CARDS
// ═══════════════════════════════════════════════════════════════════════════
const wc = document.getElementById('wave-cards');
DATA.waves_meta.forEach((w, i) => {{
  const pct = Math.round((DATA.wave_series[i][DATA.wave_series[i].length-1]) * 100);
  wc.innerHTML += `<div class="wave-card" style="border-color:${{w.color}}">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <span style="font-weight:600;color:${{w.color}}">${{w.name}}</span>
      <span class="pill" style="background:${{w.color}}22;color:${{w.color}}">arranque ${{w.year}}</span>
    </div>
  </div>`;
}});

// ═══════════════════════════════════════════════════════════════════════════
// CHART CONFIG
// ═══════════════════════════════════════════════════════════════════════════
Chart.defaults.color = '#64748b';
Chart.defaults.borderColor = '#1e293b';
const FONT = {{ family: "'Segoe UI', system-ui, sans-serif", size: 11 }};

function mkLine(id, datasets, opts={{}}) {{
  const ctx = document.getElementById(id).getContext('2d');
  return new Chart(ctx, {{
    type: 'line',
    data: {{ labels: DATA.years, datasets }},
    options: {{
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ labels: {{ font: FONT, padding: 14, boxWidth: 12 }} }},
        tooltip: {{ backgroundColor: '#1e293b', borderColor: '#334155', borderWidth: 1,
                    titleFont: FONT, bodyFont: FONT }}
      }},
      scales: {{
        x: {{ ticks: {{ font: FONT, maxTicksLimit: 10, callback: (v,i) => {{
              const y = DATA.years[i]; return y && Number.isInteger(y) ? y : '';
            }} }},
          grid: {{ color: '#1e293b' }}
        }},
        y: {{ ticks: {{ font: FONT }}, grid: {{ color: '#1e293b' }}, ...opts.y }}
      }},
      ...opts.extra
    }}
  }});
}}

// ── Chart 1: Olas individuales ───────────────────────────────────────────────
mkLine('chart-waves',
  DATA.waves_meta.map((w, i) => ({{
    label: w.name,
    data: DATA.wave_series[i],
    borderColor: w.color,
    backgroundColor: w.color + '18',
    fill: false,
    borderWidth: 2,
    pointRadius: 0,
    tension: 0.4
  }}))
);

// ── Chart 2: Φ_nested ────────────────────────────────────────────────────────
mkLine('chart-phi', [{{
  label: 'Φ_nested normalizado',
  data: DATA.phi_series,
  borderColor: '#38bdf8',
  backgroundColor: 'rgba(56,189,248,0.08)',
  fill: true,
  borderWidth: 2.5,
  pointRadius: 0,
  tension: 0.4
}}]);

// ── Chart 3: Robot population ────────────────────────────────────────────────
mkLine('chart-robot', [
  {{ label: 'Base (η=0.20)',      data: DATA.robot_base, borderColor: '#38bdf8', borderWidth: 2, pointRadius: 0, tension: 0.4, fill: false }},
  {{ label: 'Acelerado (η=0.35)', data: DATA.robot_acc,  borderColor: '#a78bfa', borderWidth: 2, pointRadius: 0, tension: 0.4, fill: false, borderDash: [5,3] }},
  {{ label: 'Óptimo (η=0.50)',    data: DATA.robot_opt,  borderColor: '#4ade80', borderWidth: 2, pointRadius: 0, tension: 0.4, fill: false, borderDash: [2,2] }},
]);

// ── Chart 4: Coste relativo ───────────────────────────────────────────────────
mkLine('chart-cost', [
  {{ label: 'C(t) Base',   data: DATA.cost_base, borderColor: '#38bdf8', borderWidth: 2, pointRadius: 0, tension: 0.4, fill: false }},
  {{ label: 'C(t) Óptimo', data: DATA.cost_opt,  borderColor: '#4ade80', borderWidth: 2, pointRadius: 0, tension: 0.4, fill: false, borderDash: [2,2] }},
]);

// ── Chart 5: Portfolio total ──────────────────────────────────────────────────
mkLine('chart-portfolio', [
  {{ label: 'Base (M€)',       data: DATA.portfolio_base, borderColor: '#38bdf8', backgroundColor: 'rgba(56,189,248,0.07)', fill: true, borderWidth: 2.5, pointRadius: 0, tension: 0.4 }},
  {{ label: 'Acelerado (M€)',  data: DATA.portfolio_acc,  borderColor: '#a78bfa', borderWidth: 2, pointRadius: 0, tension: 0.4, fill: false, borderDash: [5,3] }},
  {{ label: 'Óptimo (M€)',     data: DATA.portfolio_opt,  borderColor: '#4ade80', backgroundColor: 'rgba(74,222,128,0.05)', fill: true, borderWidth: 2, pointRadius: 0, tension: 0.4, borderDash: [2,2] }},
], {{ y: {{ title: {{ display: true, text: 'M€', font: FONT, color: '#64748b' }} }} }});

// ── Chart 6: Stacked pillars ──────────────────────────────────────────────────
{{
  const ctx6 = document.getElementById('chart-pillars').getContext('2d');
  const pillarNames = Object.keys(DATA.pillar_projections);
  new Chart(ctx6, {{
    type: 'line',
    data: {{
      labels: DATA.pillar_labels,
      datasets: pillarNames.map(name => ({{
        label: name,
        data: DATA.pillar_projections[name],
        borderColor: DATA.pillar_colors[name],
        backgroundColor: DATA.pillar_colors[name] + '40',
        fill: true,
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.4,
        stack: 'pillars'
      }}))
    }},
    options: {{
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ labels: {{ font: FONT, padding: 10, boxWidth: 10 }}, position: 'right' }},
        tooltip: {{ backgroundColor: '#1e293b', borderColor: '#334155', borderWidth: 1, titleFont: FONT, bodyFont: FONT }}
      }},
      scales: {{
        x: {{ ticks: {{ font: FONT }}, grid: {{ color: '#1e293b' }} }},
        y: {{ ticks: {{ font: FONT }}, grid: {{ color: '#1e293b' }}, stacked: true,
             title: {{ display: true, text: 'M€', font: FONT, color: '#64748b' }} }}
      }}
    }}
  }});
}}

// ═══════════════════════════════════════════════════════════════════════════
// TABLA
// ═══════════════════════════════════════════════════════════════════════════
const tbody = document.getElementById('table-body');
DATA.table_data.forEach(row => {{
  const mult = (row.base / (DATA.capital_total / 1e6)).toFixed(1);
  tbody.innerHTML += `<tr>
    <td><strong>${{row.year}}</strong></td>
    <td>${{row.phi.toFixed(3)}}×</td>
    <td>${{row.R_base.toFixed(2)}}×</td>
    <td>${{row.R_opt.toFixed(2)}}×</td>
    <td style="color:#38bdf8"><strong>${{row.base.toFixed(2)}} M€</strong></td>
    <td style="color:#a78bfa">${{row.acelerado.toFixed(2)}} M€</td>
    <td style="color:#4ade80">${{row.optimo.toFixed(2)}} M€</td>
  </tr>`;
}});
</script>
</body>
</html>"""

OUT.write_text(html, encoding="utf-8")
print(f"✅  Dashboard generado → {OUT}")
print(f"    Capital base:   €{CAPITAL_TOTAL:,}")
print(f"    ε ponderado:    {eps_w:.3f} ({eps_w*100:.1f}%)")
print(f"    Φ_nested(0):    {PHI0:.4f}")
print(f"    Autofabricación: {int(BASE_YEAR + T_ROBOT)}")
