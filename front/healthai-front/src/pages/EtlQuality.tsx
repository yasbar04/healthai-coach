import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import Loading from "../components/Loading";
import ErrorBanner from "../components/ErrorBanner";

type Run  = { id: number; source_name: string; status: string; started_at: string; ended_at?: string; rows_in: number; rows_out: number; errors_count: number };
type Err  = { id: number; severity: string; row_reference?: string; message: string; created_at: string };
type Stats = { total_runs: number; success_count: number; failed_count: number; success_rate: number; total_rows_processed: number; total_errors: number };

function statusBadge(s: string) {
  if (s === "success") return <span className="badge badge-success">Succès</span>;
  if (s === "partial")  return <span className="badge badge-warn">Partiel</span>;
  return <span className="badge badge-danger">Échec</span>;
}

function sevBadge(s: string) {
  if (s === "error") return <span className="badge badge-danger">erreur</span>;
  if (s === "warn")  return <span className="badge badge-warn">alerte</span>;
  return <span className="badge badge-info">{s}</span>;
}

export default function EtlQuality() {
  const [runs, setRuns]               = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<number | null>(null);
  const [errors, setErrors]           = useState<Err[]>([]);
  const [stats, setStats]             = useState<Stats | null>(null);
  const [loading, setLoading]         = useState(true);
  const [err, setErr]                 = useState<string | null>(null);

  async function load() {
    setLoading(true); setErr(null);
    try {
      const [runsRes, statsRes] = await Promise.all([
        api.get("/quality/etl-runs"),
        api.get("/quality/etl-stats").catch(() => ({ data: null })),
      ]);
      const items: Run[] = runsRes.data?.items ?? runsRes.data ?? [];
      setRuns(items);
      setStats(statsRes.data);
      if (items.length && selectedRun == null) setSelectedRun(items[0].id);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Impossible de charger la qualité ETL.");
    } finally {
      setLoading(false);
    }
  }

  async function loadErrors(runId: number) {
    try {
      const res = await api.get(`/quality/etl-runs/${runId}/errors`);
      setErrors(res.data?.items ?? res.data ?? []);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Impossible de charger les erreurs ETL.");
    }
  }

  useEffect(() => { load(); }, []);
  useEffect(() => { if (selectedRun != null) loadErrors(selectedRun); }, [selectedRun]);

  if (loading) return <Loading label="Chargement qualité ETL…" />;

  const selectedRunData = runs.find((r) => r.id === selectedRun);

  return (
    <div className="etl-page">

      {/* En-tête */}
      <div className="page-header">
        <div className="page-header-icon" aria-hidden="true">⚙️</div>
        <div>
          <h1>Qualité ETL</h1>
          <p className="page-subtitle">Monitoring des pipelines de collecte et de nettoyage des données</p>
        </div>
      </div>

      {err && <ErrorBanner message={err} />}

      {/* Statistiques globales */}
      {stats && (
        <section aria-labelledby="etl-stats-heading">
          <h2 id="etl-stats-heading" className="section-heading">Vue d'ensemble — 7 derniers jours</h2>
          <div className="etl-stats-row">
            {[
              { icon: "🔄", label: "Exécutions",       val: stats.total_runs,                                  cls: ""            },
              { icon: "✅", label: "Succès",            val: stats.success_count,                               cls: stats.success_count > 0 ? "text-success" : "" },
              { icon: "❌", label: "Échecs",            val: stats.failed_count,                                cls: stats.failed_count  > 0 ? "text-danger"  : "" },
              { icon: "📊", label: "Taux de succès",   val: `${stats.success_rate.toFixed(0)} %`,              cls: stats.success_rate >= 95 ? "text-success" : stats.success_rate >= 80 ? "text-warn" : "text-danger" },
              { icon: "📦", label: "Lignes traitées",  val: stats.total_rows_processed.toLocaleString("fr-FR"), cls: ""            },
              { icon: "⚠️", label: "Erreurs totales",  val: stats.total_errors,                                cls: stats.total_errors > 0 ? "text-warn" : "text-success" },
            ].map(({ icon, label, val, cls }) => (
              <div key={label} className="etl-stat-card">
                <div className="etl-stat-icon" aria-hidden="true">{icon}</div>
                <div className="etl-stat-label">{label}</div>
                <div className={`etl-stat-value ${cls}`}>{val}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Détail runs + erreurs */}
      <section aria-labelledby="etl-detail-heading">
        <h2 id="etl-detail-heading" className="section-heading">Détail des exécutions</h2>
        <div className="etl-panels">

          {/* Panel gauche : liste des runs */}
          <div className="etl-panel">
            <div className="etl-panel-header">
              <h3 className="etl-panel-title">
                <span aria-hidden="true">📂</span> Historique des runs
              </h3>
              <p className="etl-panel-subtitle">
                {runs.length} exécution{runs.length !== 1 ? "s" : ""} enregistrée{runs.length !== 1 ? "s" : ""}
              </p>
            </div>

            {runs.length === 0 ? (
              <p className="etl-empty">Aucune exécution ETL enregistrée.</p>
            ) : (
              <>
                <div
                  className="table-scroll"
                  tabIndex={0}
                  role="region"
                  aria-label="Liste des exécutions ETL — défilable au clavier"
                >
                  <table className="table" aria-label="Historique des exécutions ETL">
                    <thead>
                      <tr>
                        <th scope="col">#</th>
                        <th scope="col">Source</th>
                        <th scope="col">Statut</th>
                        <th scope="col">Lignes in</th>
                        <th scope="col">Lignes out</th>
                        <th scope="col">Erreurs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {runs.map((r) => (
                        <tr
                          key={r.id}
                          className={`etl-run-row${selectedRun === r.id ? " etl-run-row--selected" : ""}`}
                          onClick={() => setSelectedRun(r.id)}
                          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && setSelectedRun(r.id)}
                          tabIndex={0}
                          role="button"
                          aria-pressed={selectedRun === r.id}
                          aria-label={`Run #${r.id} — ${r.source_name} — statut ${r.status}`}
                        >
                          <td><strong>#{r.id}</strong></td>
                          <td>{r.source_name}</td>
                          <td>{statusBadge(r.status)}</td>
                          <td>{r.rows_in.toLocaleString("fr-FR")}</td>
                          <td>{r.rows_out.toLocaleString("fr-FR")}</td>
                          <td>
                            <span className={r.errors_count > 0 ? "badge badge-danger" : "badge badge-success"}>
                              {r.errors_count}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="etl-hint">Sélectionnez une ligne pour afficher les erreurs associées.</p>
              </>
            )}
          </div>

          {/* Panel droit : erreurs du run sélectionné */}
          <div className="etl-panel">
            <div className="etl-panel-header">
              <h3 className="etl-panel-title">
                <span aria-hidden="true">🔍</span> Erreurs
                {selectedRunData && <> — run #{selectedRunData.id}</>}
              </h3>
              <p className="etl-panel-subtitle">
                {selectedRunData
                  ? `${selectedRunData.source_name} · ${new Date(selectedRunData.started_at).toLocaleString("fr-FR")}`
                  : "Sélectionnez un run dans la liste de gauche"}
              </p>
            </div>

            {selectedRun == null ? (
              <p className="etl-empty">Aucun run sélectionné.</p>
            ) : errors.length === 0 ? (
              <p className="etl-empty">✅ Aucune erreur pour ce run.</p>
            ) : (
              <div
                className="table-scroll"
                tabIndex={0}
                role="region"
                aria-label="Erreurs de l'exécution ETL sélectionnée — défilable au clavier"
              >
                <table className="table" aria-label={`Erreurs du run #${selectedRun}`}>
                  <thead>
                    <tr>
                      <th scope="col">Sévérité</th>
                      <th scope="col">Réf. ligne</th>
                      <th scope="col">Message</th>
                      <th scope="col">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {errors.map((e) => (
                      <tr key={e.id}>
                        <td>{sevBadge(e.severity)}</td>
                        <td className="small">{e.row_reference ?? "—"}</td>
                        <td>{e.message}</td>
                        <td className="small nowrap">
                          {e.created_at.slice(0, 19).replace("T", " ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>
      </section>
    </div>
  );
}
