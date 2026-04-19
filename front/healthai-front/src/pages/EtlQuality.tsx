import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import Card from "../components/Card";
import Loading from "../components/Loading";
import ErrorBanner from "../components/ErrorBanner";

type Run = { id: number; source_name: string; status: string; started_at: string; ended_at?: string; rows_in: number; rows_out: number; errors_count: number };
type Err = { id: number; severity: string; row_reference?: string; message: string; created_at: string };

export default function EtlQuality() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<number | null>(null);
  const [errors, setErrors] = useState<Err[]>([]);

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setLoading(true); setErr(null);
    try {
      const r = await api.get("/quality/etl-runs");
      const items = r.data?.items ?? r.data;
      setRuns(items);
      if (items?.length && selectedRun == null) setSelectedRun(items[0].id);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Impossible de charger qualité ETL.");
    } finally {
      setLoading(false);
    }
  }

  async function loadErrors(runId: number) {
    setErr(null);
    try {
      const e = await api.get(`/quality/etl-runs/${runId}/errors`);
      setErrors(e.data?.items ?? e.data);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Impossible de charger les erreurs ETL.");
    }
  }

  useEffect(() => { load(); }, []);
  useEffect(() => { if (selectedRun != null) loadErrors(selectedRun); }, [selectedRun]);

  const statusBadge = (s: string) => {
    if (s === "success") return <span className="badge badge-success">✅ {s}</span>;
    if (s === "partial")  return <span className="badge badge-warn">⚠️ {s}</span>;
    return <span className="badge badge-danger">❌ {s}</span>;
  };

  const sevBadge = (s: string) => {
    if (s === "error") return <span className="badge badge-danger">{s}</span>;
    if (s === "warn")  return <span className="badge badge-warn">{s}</span>;
    return <span className="badge badge-info">{s}</span>;
  };

  if (loading) return <Loading label="Chargement qualité ETL..." />;

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <div className="page-header">
        <div className="page-header-icon" aria-hidden="true">⚙️</div>
        <div>
          <h1>Qualité ETL</h1>
          <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--text-muted)" }}>Monitoring des pipelines de collecte et de nettoyage des données</p>
        </div>
      </div>

      {err && <ErrorBanner message={err} />}

      <div className="grid grid-2">
        <Card title="ETL runs" icon="📂">
          <div className="table-wrap" style={{ boxShadow: "none", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <table className="table" aria-label="Table ETL runs">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Source</th>
                  <th>Statut</th>
                  <th>In</th>
                  <th>Out</th>
                  <th>Err.</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id} style={{ cursor: "pointer", background: selectedRun === r.id ? "var(--primary-light)" : undefined }}
                    onClick={() => setSelectedRun(r.id)}>
                    <td><strong style={{ color: "var(--primary)" }}>#{r.id}</strong></td>
                    <td>{r.source_name}</td>
                    <td>{statusBadge(r.status)}</td>
                    <td>{r.rows_in.toLocaleString()}</td>
                    <td>{r.rows_out.toLocaleString()}</td>
                    <td>
                      {r.errors_count > 0
                        ? <span style={{ color: "var(--danger)", fontWeight: 600 }}>{r.errors_count}</span>
                        : <span style={{ color: "var(--primary)" }}>0</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="small" style={{ marginTop: 10 }}>Clique sur une ligne pour voir les erreurs associées.</p>
        </Card>

        <Card title={`Erreurs — run #${selectedRun ?? "?"}`} icon="🔍">
          <div className="table-wrap" style={{ boxShadow: "none", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <table className="table" aria-label="Table erreurs ETL">
              <thead>
                <tr>
                  <th>Sév.</th>
                  <th>Réf.</th>
                  <th>Message</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {errors.length === 0 ? (
                  <tr><td colSpan={4} style={{ textAlign: "center", color: "var(--text-light)", padding: "28px" }}>✅ Aucune erreur</td></tr>
                ) : errors.map((e) => (
                  <tr key={e.id}>
                    <td>{sevBadge(e.severity)}</td>
                    <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{e.row_reference ?? "-"}</td>
                    <td>{e.message}</td>
                    <td style={{ fontSize: "0.8rem", whiteSpace: "nowrap", color: "var(--text-light)" }}>{e.created_at.slice(0, 19).replace("T", " ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
