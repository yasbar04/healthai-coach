import React, { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import Card from "../components/Card";
import Loading from "../components/Loading";
import ErrorBanner from "../components/ErrorBanner";

// ── Types ────────────────────────────────────────────────────────────────────

type HealthData = {
  disease_type?: string;
  severity?: string;
  physical_activity_level?: string;
  cholesterol_mg_dl?: number;
  blood_pressure_mmhg?: number;
  glucose_mg_dl?: number;
};
type Nutrition = {
  diet_recommendation?: string;
  adherence_to_diet_plan?: number;
  preferred_cuisine?: string;
  water_intake?: number;
  dietary_restrictions?: string;
  allergies?: string;
};
type Daily = {
  workout_type?: string;
  exercise_hours?: number;
  calories_burned?: number;
  daily_caloric_intake?: number;
  max_bpm?: number;
  resting_bpm?: number;
  avg_bpm?: number;
};
type Weekly = {
  weight?: number;
  bmi?: number;
  fat_percentage?: number;
  workout_frequency?: number;
};
type Abonnement = { name: string; price: number };

type Patient = {
  id: number;
  name: string;
  age?: number;
  gender?: string;
  email?: string;
  company?: string;
  health_data?: HealthData;
  nutrition?: Nutrition;
  daily?: Daily;
  weekly?: Weekly;
  abonnements?: Abonnement[];
};

// ── Helpers ──────────────────────────────────────────────────────────────────

const PAGE_SIZE = 20;

const SEVERITY_COLOR: Record<string, string> = {
  Mild:     "#059669",
  Moderate: "#f59e0b",
  Severe:   "#ef4444",
};

const PLAN_COLOR: Record<string, string> = {
  Freemium:   "#94a3b8",
  Premium:    "#6366f1",
  "Premium+": "#059669",
  B2B:        "#f59e0b",
};

function planBadge(abonnements?: Abonnement[]) {
  if (!abonnements?.length) return null;
  const a = abonnements[0];
  const color = PLAN_COLOR[a.name] ?? "#64748b";
  return (
    <span
      className="badge"
      style={{ background: color + "22", color }}
    >
      {a.name}
    </span>
  );
}

function sevBadge(sev?: string) {
  if (!sev) return <span style={{ color: "var(--text-muted)" }}>—</span>;
  const color = SEVERITY_COLOR[sev] ?? "#64748b";
  return <span className="badge" style={{ background: color + "22", color }}>{sev}</span>;
}

function bmiTag(bmi?: number) {
  if (!bmi) return "—";
  if (bmi < 18.5) return { label: bmi.toFixed(1), color: "#3b82f6" };
  if (bmi < 25)   return { label: bmi.toFixed(1), color: "#059669" };
  if (bmi < 30)   return { label: bmi.toFixed(1), color: "#f59e0b" };
  return { label: bmi.toFixed(1), color: "#ef4444" };
}

// ── Drawer ───────────────────────────────────────────────────────────────────

function Field({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="drawer-field">
      <span className="drawer-field-label">{label}</span>
      <span className="drawer-field-value">{value ?? "—"}</span>
    </div>
  );
}

function Drawer({ patient, onClose }: { patient: Patient; onClose: () => void }) {
  const initials = patient.name?.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase();
  const bmi = bmiTag(patient.weekly?.bmi);

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label={`Détail patient ${patient.name}`}>
        <div className="drawer-header">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div className={`drawer-avatar avatar-${patient.gender}`}>{initials}</div>
            <div>
              <h2>{patient.name}</h2>
              <div style={{ display: "flex", gap: 6, marginTop: 4, flexWrap: "wrap" }}>
                {planBadge(patient.abonnements)}
                {patient.gender && (
                  <span className="badge" style={{
                    background: patient.gender === "M" ? "#dbeafe" : "#fce7f3",
                    color: patient.gender === "M" ? "#1d4ed8" : "#be185d",
                  }}>
                    {patient.gender === "M" ? "♂ Homme" : "♀ Femme"}
                  </span>
                )}
                {patient.company && (
                  <span className="badge" style={{ background: "var(--accent-light)", color: "var(--accent)" }}>
                    🏢 {patient.company}
                  </span>
                )}
              </div>
            </div>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Fermer">✕</button>
        </div>

        <div className="drawer-body">

          {/* Identité */}
          <div className="drawer-section">
            <div className="drawer-section-title">Identité</div>
            <div className="drawer-grid">
              <Field label="Nom" value={patient.name} />
              <Field label="Email" value={patient.email} />
              <Field label="Âge" value={patient.age ? `${patient.age} ans` : undefined} />
              <Field label="Genre" value={patient.gender === "M" ? "Homme" : patient.gender === "F" ? "Femme" : patient.gender} />
            </div>
          </div>

          {/* Santé */}
          {patient.health_data && (
            <div className="drawer-section">
              <div className="drawer-section-title">Données de santé</div>
              <div className="drawer-grid">
                <Field label="Maladie" value={patient.health_data.disease_type} />
                <div className="drawer-field">
                  <span className="drawer-field-label">Sévérité</span>
                  <span className="drawer-field-value">{sevBadge(patient.health_data.severity)}</span>
                </div>
                <Field label="Activité" value={patient.health_data.physical_activity_level} />
                <Field label="Cholestérol" value={patient.health_data.cholesterol_mg_dl ? `${patient.health_data.cholesterol_mg_dl} mg/dL` : undefined} />
                <Field label="Tension art." value={patient.health_data.blood_pressure_mmhg ? `${patient.health_data.blood_pressure_mmhg} mmHg` : undefined} />
                <Field label="Glycémie" value={patient.health_data.glucose_mg_dl ? `${patient.health_data.glucose_mg_dl} mg/dL` : undefined} />
              </div>
            </div>
          )}

          {/* Nutrition */}
          {patient.nutrition && (
            <div className="drawer-section">
              <div className="drawer-section-title">Profil nutritionnel</div>
              <div className="drawer-grid">
                <Field label="Recommandation" value={patient.nutrition.diet_recommendation} />
                <Field label="Adhérence régime" value={patient.nutrition.adherence_to_diet_plan != null ? `${patient.nutrition.adherence_to_diet_plan}%` : undefined} />
                <Field label="Cuisine préférée" value={patient.nutrition.preferred_cuisine} />
                <Field label="Eau quotidienne" value={patient.nutrition.water_intake ? `${patient.nutrition.water_intake} L` : undefined} />
                <Field label="Restrictions" value={patient.nutrition.dietary_restrictions} />
                <Field label="Allergies" value={patient.nutrition.allergies} />
              </div>
            </div>
          )}

          {/* Daily */}
          {patient.daily && (
            <div className="drawer-section">
              <div className="drawer-section-title">Activité quotidienne</div>
              <div className="drawer-grid">
                <Field label="Entraînement" value={patient.daily.workout_type} />
                <Field label="Durée session" value={patient.daily.exercise_hours ? `${patient.daily.exercise_hours}h` : undefined} />
                <Field label="Calories brûlées" value={patient.daily.calories_burned ? `${patient.daily.calories_burned} kcal` : undefined} />
                <Field label="Apport calorique" value={patient.daily.daily_caloric_intake ? `${patient.daily.daily_caloric_intake} kcal` : undefined} />
                <Field label="BPM max" value={patient.daily.max_bpm} />
                <Field label="BPM repos" value={patient.daily.resting_bpm} />
                <Field label="BPM moy." value={patient.daily.avg_bpm} />
              </div>
            </div>
          )}

          {/* Weekly */}
          {patient.weekly && (
            <div className="drawer-section">
              <div className="drawer-section-title">Bilan hebdomadaire</div>
              <div className="drawer-grid">
                <Field label="Poids" value={patient.weekly.weight ? `${patient.weekly.weight} kg` : undefined} />
                <div className="drawer-field">
                  <span className="drawer-field-label">IMC (BMI)</span>
                  <span className="drawer-field-value" style={{ color: typeof bmi === "object" ? bmi.color : undefined }}>
                    {typeof bmi === "object" ? bmi.label : "—"}
                  </span>
                </div>
                <Field label="% Graisse" value={patient.weekly.fat_percentage ? `${patient.weekly.fat_percentage}%` : undefined} />
                <Field label="Fréq. sport" value={patient.weekly.workout_frequency ? `${patient.weekly.workout_frequency}j/sem` : undefined} />
              </div>
            </div>
          )}

          {/* Abonnement */}
          {patient.abonnements?.length ? (
            <div className="drawer-section">
              <div className="drawer-section-title">Abonnement</div>
              <div className="drawer-grid">
                {patient.abonnements.map((a, i) => (
                  <React.Fragment key={i}>
                    <Field label="Plan" value={a.name} />
                    <Field label="Tarif" value={a.price === 0 ? "Gratuit" : `${a.price} €/mois`} />
                  </React.Fragment>
                ))}
              </div>
            </div>
          ) : null}

        </div>
      </aside>
    </>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function Users() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [gender, setGender] = useState("");
  const [plan, setPlan] = useState("");
  const [disease, setDisease] = useState("");
  const [page, setPage] = useState(0);

  const [diseases, setDiseases] = useState<string[]>([]);
  const [plans, setPlans] = useState<string[]>([]);

  const [selected, setSelected] = useState<Patient | null>(null);

  // Load filter options once
  useEffect(() => {
    api.get("/bdd/utilisateurs/filter-options").then(r => {
      setDiseases(r.data.diseases ?? []);
      setPlans(r.data.plans ?? []);
    }).catch(() => {});
  }, []);

  const load = useCallback(async (p = page) => {
    setLoading(true); setErr(null);
    try {
      const r = await api.get("/bdd/utilisateurs", {
        params: {
          limit: PAGE_SIZE,
          offset: p * PAGE_SIZE,
          search: search || undefined,
          gender: gender || undefined,
          plan: plan || undefined,
          disease: disease || undefined,
        }
      });
      setPatients(r.data.items ?? []);
      setTotal(r.data.total ?? 0);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Impossible de charger les utilisateurs.");
    } finally {
      setLoading(false);
    }
  }, [page, search, gender, plan, disease]);

  useEffect(() => { load(); }, []);

  function applyFilters() { setPage(0); load(0); }
  function goPage(p: number) { setPage(p); load(p); }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      {/* Header */}
      <div className="page-header">
        <div className="page-header-icon" aria-hidden="true">👥</div>
        <div>
          <h1>Gestion des utilisateurs</h1>
          <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--text-muted)" }}>
            {total.toLocaleString()} patients enregistrés — Cliquez une ligne pour le détail complet
          </p>
        </div>
      </div>

      {err && <ErrorBanner message={err} />}

      {/* Filters */}
      <Card title="Filtres" icon="🔍">
        <div className="filters-row" style={{ flexWrap: "wrap" }}>
          <div className="filter-group">
            <span className="filter-label">Recherche</span>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              onKeyDown={e => e.key === "Enter" && applyFilters()}
              placeholder="Nom ou email…"
              style={{ width: 200 }}
            />
          </div>
          <div className="filter-group">
            <span className="filter-label">Genre</span>
            <select value={gender} onChange={e => setGender(e.target.value)} title="Genre">
              <option value="">Tous</option>
              <option value="M">Homme</option>
              <option value="F">Femme</option>
            </select>
          </div>
          <div className="filter-group">
            <span className="filter-label">Plan</span>
            <select value={plan} onChange={e => setPlan(e.target.value)} title="Plan">
              <option value="">Tous</option>
              {plans.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div className="filter-group">
            <span className="filter-label">Maladie</span>
            <select value={disease} onChange={e => setDisease(e.target.value)} title="Maladie">
              <option value="">Toutes</option>
              {diseases.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <button className="btn-primary" onClick={applyFilters} style={{ alignSelf: "flex-end" }}>
            🔎 Appliquer
          </button>
          <button className="btn-secondary" onClick={() => {
            setSearch(""); setGender(""); setPlan(""); setDisease(""); setPage(0); load(0);
          }} style={{ alignSelf: "flex-end" }}>
            ✕ Reset
          </button>
        </div>
      </Card>

      {/* Table */}
      <Card title={loading ? "Chargement…" : `Résultats (${total.toLocaleString()} utilisateurs, page ${page + 1}/${Math.max(totalPages, 1)})`} icon="📋">
        {loading ? <Loading label="Chargement…" /> : (
          <>
            <div className="table-wrap" style={{ boxShadow: "none" }}>
              <table className="table" aria-label="Tableau utilisateurs">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Nom</th>
                    <th>Âge</th>
                    <th>Genre</th>
                    <th>Plan</th>
                    <th>Maladie</th>
                    <th>Sévérité</th>
                    <th>Entraîn.</th>
                    <th>BMI</th>
                    <th>Calories</th>
                  </tr>
                </thead>
                <tbody>
                  {patients.length === 0 ? (
                    <tr><td colSpan={10} style={{ textAlign: "center", color: "var(--text-muted)", padding: 32 }}>— Aucun résultat —</td></tr>
                  ) : patients.map(p => {
                    const bmi = bmiTag(p.weekly?.bmi);
                    return (
                      <tr
                        key={p.id}
                        onClick={() => setSelected(p)}
                        style={{ cursor: "pointer" }}
                        title="Cliquer pour le détail"
                      >
                        <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{p.id}</td>
                        <td>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <div
                              className={`drawer-avatar avatar-${p.gender}`}
                              style={{ width: 30, height: 30, fontSize: "0.75rem", fontWeight: 800 }}
                            >
                              {p.name?.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase()}
                            </div>
                            <div>
                              <div style={{ fontWeight: 600, fontSize: "0.88rem" }}>{p.name}</div>
                              {p.company && <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>🏢 {p.company}</div>}
                            </div>
                          </div>
                        </td>
                        <td>{p.age ?? "—"}</td>
                        <td>
                          {p.gender === "M"
                            ? <span className="badge" style={{ background: "#dbeafe", color: "#1d4ed8" }}>♂ M</span>
                            : p.gender === "F"
                              ? <span className="badge" style={{ background: "#fce7f3", color: "#be185d" }}>♀ F</span>
                              : "—"}
                        </td>
                        <td>{planBadge(p.abonnements)}</td>
                        <td style={{ fontSize: "0.85rem" }}>{p.health_data?.disease_type ?? "—"}</td>
                        <td>{sevBadge(p.health_data?.severity)}</td>
                        <td style={{ fontSize: "0.85rem" }}>{p.daily?.workout_type ?? "—"}</td>
                        <td>
                          {typeof bmi === "object"
                            ? <span style={{ fontWeight: 700, color: bmi.color }}>{bmi.label}</span>
                            : "—"}
                        </td>
                        <td>
                          {p.daily?.calories_burned
                            ? <span className="badge badge-info">{p.daily.calories_burned} kcal</span>
                            : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="pagination">
                <button onClick={() => goPage(0)} disabled={page === 0}>«</button>
                <button onClick={() => goPage(page - 1)} disabled={page === 0}>‹ Préc.</button>
                {Array.from({ length: Math.min(7, totalPages) }, (_, i) => {
                  const start = Math.max(0, Math.min(page - 3, totalPages - 7));
                  const p = start + i;
                  return (
                    <button
                      key={p}
                      className={p === page ? "active" : ""}
                      onClick={() => goPage(p)}
                    >
                      {p + 1}
                    </button>
                  );
                })}
                <button onClick={() => goPage(page + 1)} disabled={page >= totalPages - 1}>Suiv. ›</button>
                <button onClick={() => goPage(totalPages - 1)} disabled={page >= totalPages - 1}>»</button>
              </div>
            )}
          </>
        )}
      </Card>

      {/* Drawer */}
      {selected && <Drawer patient={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
