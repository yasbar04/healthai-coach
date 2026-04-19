import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import Card from "../components/Card";
import Loading from "../components/Loading";
import ErrorBanner from "../components/ErrorBanner";
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, Legend,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid 
} from "recharts";
import { exportAnalyticsSummary, exportQualityReport } from "../utils/export";

type Summary = {
  total_calories_in?: number;
  total_calories_out?: number;
  total_steps?: number;
  active_days?: number;
};

type Point = { date: string; value: number };

type TodaySnap = {
  date: string;
  has_entry: boolean;
  steps: number | null;
  active_minutes: number | null;
  calories_out: number | null;
  sleep_hours: number | null;
  water_ml: number | null;
  weight_kg: number | null;
  calories_in: number | null;
};

type ETLQuality = {
  summary?: {
    total_users: number;
    total_activities: number;
    total_nutrition_logs: number;
    total_foods: number;
  };
  data_completeness?: {
    [key: string]: {
      completeness_percent: number;
      valid_count: number;
      total_count: number;
    };
  };
};

// SVG-based bar avoids the "no inline styles" lint rule
function ProgressBar({ value, max, color, label }: { value: number; max: number; color: string; label: string }) {
  const pct = Math.min(100, (value / max) * 100);
  const pctRounded = Math.round(pct);
  return (
    <div className="progress-bar-wrap">
      <svg
        className="today-progress-svg"
        aria-label={`${label} : ${value} / ${max} (${pctRounded} %)`}
        role="img"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect className="today-svg-track" x="0" y="0" width="100%" height="7" rx="4" />
        <rect x="0" y="0" width={`${pct}%`} height="7" rx="4" fill={color} />
      </svg>
      <span className="progress-pct">{pctRounded} %</span>
    </div>
  );
}

export default function Dashboard() {
  const [from, setFrom] = useState(() => new Date(Date.now() - 6 * 86400000).toISOString().slice(0, 10));
  const [to, setTo] = useState(() => new Date().toISOString().slice(0, 10));

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [summary, setSummary] = useState<Summary | null>(null);
  const [steps, setSteps] = useState<Point[]>([]);
  const [calIn, setCalIn] = useState<Point[]>([]);
  const [calOut, setCalOut] = useState<Point[]>([]);
  const [today, setToday] = useState<TodaySnap | null>(null);
  const [etlQuality, setEtlQuality] = useState<ETLQuality | null>(null);

  const params = useMemo(() => ({ from, to }), [from, to]);

  async function load() {
    setLoading(true); setErr(null);
    try {
      const [s, st, ci, co, td, eq] = await Promise.all([
        api.get("/analytics/summary", { params }),
        api.get("/analytics/trends/steps", { params }),
        api.get("/analytics/trends/calories-in", { params }),
        api.get("/analytics/trends/calories-out", { params }),
        api.get("/analytics/today"),
        api.get("/quality/data-quality-summary").catch(() => ({ data: null })), // Optional
      ]);
      setSummary(s.data);
      setSteps(st.data?.points ?? st.data);
      setCalIn(ci.data?.points ?? ci.data);
      setCalOut(co.data?.points ?? co.data);
      setToday(td.data);
      setEtlQuality(eq.data);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Impossible de charger le dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  if (loading) return <Loading label="Chargement du dashboard..." />;

  return (
    <div className="dashboard-grid">
      <div className="page-header">
        <div className="page-header-icon" aria-hidden="true">📊</div>
        <div>
          <h1>Dashboard</h1>
          <p className="page-subtitle">Vue globale de vos indicateurs santé</p>
        </div>
      </div>

      {err && <ErrorBanner message={err} />}

      {/* ── Today's snapshot ── */}
      <Card title="Aujourd'hui" icon="📅">
        <div className="today-snapshot">
          {!today?.has_entry ? (
            <div className="today-cta">
              <div className="today-cta-text">
                <strong>Rien de logé aujourd'hui</strong>
                <span>Prenez 30 secondes pour enregistrer votre journée.</span>
              </div>
              <Link to="/daily-log" className="btn-primary today-log-btn">📝 Saisir mon journal</Link>
            </div>
          ) : (
            <div className="today-done-badge" role="status">
              <span>✓ Entrée enregistrée</span>
              <Link to="/daily-log" className="btn-ghost today-edit-btn">✏️ Modifier</Link>
            </div>
          )}
          <div className="today-metrics">
            {([
              { icon: "👣", label: "Pas",      val: today?.steps,        max: 10000, color: "var(--primary)" },
              { icon: "🔥", label: "Cal OUT",  val: today?.calories_out, max: 2000,  color: "#f59e0b" },
              { icon: "🌙", label: "Sommeil",  val: today?.sleep_hours,  max: 8,     color: "#6366f1" },
              { icon: "💧", label: "Eau (ml)", val: today?.water_ml,     max: 2000,  color: "#0ea5e9" },
            ] as const).map(({ icon, label, val, max, color }) => (
              <div key={label} className="today-metric-row">
                <div className="today-metric-header">
                  <span className="today-metric-label">{icon} {label}</span>
                  <span className="today-metric-val">
                    {val != null ? val.toLocaleString("fr-FR") : "—"}
                    <span className="today-metric-max"> / {max.toLocaleString("fr-FR")}</span>
                  </span>
                </div>
                <ProgressBar value={val ?? 0} max={max} color={color} label={label} />
              </div>
            ))}
          </div>
          {today?.weight_kg != null && (
            <p className="today-weight-line">⚖️ Poids aujourd'hui : <strong>{today.weight_kg} kg</strong></p>
          )}
        </div>
      </Card>

      <div className="filters-row" aria-label="Filtres de période">
        <div className="filter-group">
          <label htmlFor="from" className="filter-label">Du</label>
          <input id="from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} aria-label="Date de début" />
        </div>
        <div className="filter-group">
          <label htmlFor="to" className="filter-label">Au</label>
          <input id="to" type="date" value={to} onChange={(e) => setTo(e.target.value)} aria-label="Date de fin" />
        </div>
        <button className="btn-primary" onClick={load}>🔄 Actualiser</button>
        <div className="export-buttons">
          <button 
            className="btn-secondary"
            onClick={() => summary && exportAnalyticsSummary(summary, { from, to }, 'csv')}
            title="Exporter les statistiques en CSV"
          >
            📥 CSV
          </button>
          <button 
            className="btn-secondary"
            onClick={() => summary && exportAnalyticsSummary(summary, { from, to }, 'json')}
            title="Exporter les statistiques en JSON"
          >
            📥 JSON
          </button>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-icon" aria-hidden="true">👣</div>
          <div className="stat-label">Pas totaux</div>
          <div className="stat-value">{summary?.total_steps?.toLocaleString() ?? "-"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" aria-hidden="true">🥗</div>
          <div className="stat-label">Calories IN</div>
          <div className="stat-value">{summary?.total_calories_in?.toLocaleString() ?? "-"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" aria-hidden="true">🔥</div>
          <div className="stat-label">Calories OUT</div>
          <div className="stat-value">{summary?.total_calories_out?.toLocaleString() ?? "-"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" aria-hidden="true">✅</div>
          <div className="stat-label">Jours actifs</div>
          <div className="stat-value">{summary?.active_days ?? "-"}</div>
        </div>
      </div>

      <div className="grid grid-2">
        <Card title="Pas (tendance)" icon="👣">
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={steps}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#059669" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Calories IN (tendance)" icon="🥗">
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={calIn}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Calories OUT (tendance)" icon="🔥">
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={calOut}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#f59e0b" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Résumé période" icon="📅">
          <ul className="summary-list">
            {[
              { label: "Pas totaux",   val: summary?.total_steps?.toLocaleString() },
              { label: "Calories IN",  val: summary?.total_calories_in?.toLocaleString() },
              { label: "Calories OUT", val: summary?.total_calories_out?.toLocaleString() },
              { label: "Jours actifs", val: summary?.active_days },
            ].map(({ label, val }) => (
              <li key={label} className="summary-list-item">
                {label} : <strong>{val ?? "-"}</strong>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {/* ── Quality & ETL Section ── */}
      {etlQuality?.summary && (
        <Card title="Qualité des Données" icon="✅">
          <div className="quality-section">
            <div className="quality-grid">
              <div className="quality-stat">
                <div className="quality-stat-icon">👥</div>
                <div className="quality-stat-label">Utilisateurs</div>
                <div className="quality-stat-value">{etlQuality.summary.total_users}</div>
              </div>
              <div className="quality-stat">
                <div className="quality-stat-icon">📊</div>
                <div className="quality-stat-label">Activités</div>
                <div className="quality-stat-value">{etlQuality.summary.total_activities}</div>
              </div>
              <div className="quality-stat">
                <div className="quality-stat-icon">🥗</div>
                <div className="quality-stat-label">Aliments</div>
                <div className="quality-stat-value">{etlQuality.summary.total_foods}</div>
              </div>
              <div className="quality-stat">
                <div className="quality-stat-icon">📝</div>
                <div className="quality-stat-label">Logs Nutrition</div>
                <div className="quality-stat-value">{etlQuality.summary.total_nutrition_logs}</div>
              </div>
            </div>

            {etlQuality.data_completeness && (
              <div className="completeness-list">
                <h4>Complétude des Données</h4>
                {Object.entries(etlQuality.data_completeness).map(([key, stats]) => (
                  <div key={key} className="completeness-item">
                    <div className="completeness-header">
                      <span className="completeness-name">{key}</span>
                      <span className="completeness-percent">
                        {Math.round(stats.completeness_percent * 100) / 100}%
                      </span>
                    </div>
                    <div className="completeness-bar">
                      <div 
                        className={`completeness-fill ${stats.completeness_percent >= 90 ? 'quality-excellent' : stats.completeness_percent >= 70 ? 'quality-warning' : 'quality-critical'}`}
                        role="progressbar"
                        aria-valuenow={Math.round(stats.completeness_percent * 100) / 100}
                        aria-valuemin={0}
                        aria-valuemax={100}
                        style={{
                          '--width-percent': `${Math.min(100, Math.round(stats.completeness_percent * 100) / 100 * 100)}%`
                        } as React.CSSProperties}
                      ></div>
                    </div>
                    <span className="completeness-count">
                      {stats.valid_count} / {stats.total_count}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="quality-export-buttons">
              <Link to="/quality" className="btn-secondary">📊 Voir détails ETL</Link>
              <button 
                className="btn-secondary"
                onClick={() => etlQuality && exportQualityReport(etlQuality, 'csv')}
                title="Exporter le rapport qualité en CSV"
              >
                📥 CSV
              </button>
              <button 
                className="btn-secondary"
                onClick={() => etlQuality && exportQualityReport(etlQuality, 'json')}
                title="Exporter le rapport qualité en JSON"
              >
                📥 JSON
              </button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

