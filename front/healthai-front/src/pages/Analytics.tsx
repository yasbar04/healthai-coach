import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Loading from "../components/Loading";
import ErrorBanner from "../components/ErrorBanner";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Cell,
} from "recharts";

/* ── types ── */
type GoalItem      = { goal_label: string; users_count: number };
type AgeItem       = { age_bucket: string; users_count: number };
type ActivityItem  = { body_part: string; exercises_count: number };
type FoodItem      = { name: string; category: string; kcal_per_100g: number };
type KPIs = {
  total_users: number;
  premium_users: number;
  conversion_rate: number;
  active_users_30d: number;
  engagement_rate: number;
};

const COLORS = ["#059669", "#6366f1", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899"];

/* ── composant graphique accessible ── */
function AccessibleChart({
  titleId,
  ariaLabel,
  children,
  fallbackItems,
  fallbackLabel,
}: {
  titleId: string;
  ariaLabel: string;
  children: React.ReactNode;
  fallbackItems: string[];
  fallbackLabel: string;
}) {
  return (
    <div role="img" aria-labelledby={titleId} aria-label={ariaLabel}>
      <div className="chart-container" aria-hidden="true">
        {children}
      </div>
      {/* alternative textuelle pour lecteurs d'écran et noscript */}
      <p id={titleId + "-desc"} className="visually-hidden">{ariaLabel}</p>
      <noscript>
        <p>{fallbackLabel}</p>
        <ul>
          {fallbackItems.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </noscript>
    </div>
  );
}

export default function Analytics() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [loading, setLoading]       = useState(true);
  const [err, setErr]               = useState<string | null>(null);
  const [goals, setGoals]           = useState<GoalItem[]>([]);
  const [ages, setAges]             = useState<AgeItem[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [topFoods, setTopFoods]     = useState<FoodItem[]>([]);
  const [kpis, setKpis]             = useState<KPIs | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setErr(null);
      try {
        const safe = (p: Promise<any>) => p.catch(() => ({ data: { items: [] } }));
        const [foods, ...adminResults] = await Promise.all([
          safe(api.get("/analytics/dashboard/foods-top")),
          ...(isAdmin ? [
            safe(api.get("/analytics/dashboard/users-by-goal")),
            safe(api.get("/analytics/dashboard/users-by-age")),
            safe(api.get("/analytics/dashboard/activities-by-type")),
            api.get("/analytics/dashboard/kpis").catch(() => ({ data: null })),
          ] : []),
        ]);
        setTopFoods(foods.data.items ?? []);
        if (isAdmin) {
          setGoals(adminResults[0]?.data?.items ?? []);
          setAges(adminResults[1]?.data?.items ?? []);
          setActivities(adminResults[2]?.data?.items ?? []);
          setKpis(adminResults[3]?.data ?? null);
        }
      } catch (e: any) {
        setErr(e?.response?.data?.detail || "Impossible de charger les analytics.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [isAdmin]);

  if (loading) return <Loading label="Chargement des analytics…" />;

  return (
    <div className="analytics-page">
      <div className="page-header">
        <div className="page-header-icon" aria-hidden="true">📈</div>
        <div>
          <h1>Analytics &amp; Visualisation</h1>
          <p className="page-subtitle">Indicateurs métier et analyse des données de santé</p>
        </div>
      </div>

      {err && <ErrorBanner message={err} />}

      {/* ── KPIs business (admin) ── */}
      {isAdmin && kpis && (
        <section aria-labelledby="kpis-heading">
          <h2 id="kpis-heading" className="section-heading">KPIs Business</h2>
          <p className="section-desc">
            Engagement, conversion Premium et activité sur les 30 derniers jours.
          </p>
          <div className="stat-grid">
            {[
              { icon: "👥", label: "Utilisateurs totaux",       val: kpis.total_users.toLocaleString("fr-FR") },
              { icon: "⭐", label: "Comptes Premium",           val: kpis.premium_users.toLocaleString("fr-FR") },
              { icon: "📈", label: "Taux de conversion",        val: `${kpis.conversion_rate} %` },
              { icon: "🏃", label: "Utilisateurs actifs (30 j)", val: kpis.active_users_30d.toLocaleString("fr-FR") },
              { icon: "💡", label: "Taux d'engagement",         val: `${kpis.engagement_rate} %` },
            ].map(({ icon, label, val }) => (
              <div key={label} className="stat-card">
                <div className="stat-icon" aria-hidden="true">{icon}</div>
                <div className="stat-label">{label}</div>
                <div className="stat-value">{val}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Métriques utilisateurs (admin) ── */}
      {isAdmin && (
        <section aria-labelledby="user-metrics-heading">
          <h2 id="user-metrics-heading" className="section-heading">Métriques Utilisateurs</h2>
          <p className="section-desc">
            Répartition par objectif (abonnement) et par cohorte d'inscription.
          </p>
          <div className="grid grid-2">

            {/* Répartition par objectif */}
            <div className="card">
              <h3 id="chart-goals-heading">Répartition par objectif</h3>
              <AccessibleChart
                titleId="chart-goals-heading"
                ariaLabel={
                  `Diagramme en barres : répartition des ${goals.reduce((s, g) => s + g.users_count, 0)} utilisateurs par objectif. ` +
                  goals.map((g) => `${g.goal_label} : ${g.users_count}`).join(", ") + "."
                }
                fallbackLabel="Répartition des utilisateurs par objectif :"
                fallbackItems={goals.map((g) => `${g.goal_label} : ${g.users_count} utilisateurs`)}
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={goals} layout="vertical" margin={{ left: 8, right: 16 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis dataKey="goal_label" type="category" width={148} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(v) => [`${v} utilisateurs`, "Effectif"]} />
                    <Bar dataKey="users_count" name="Utilisateurs">
                      {goals.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </AccessibleChart>
            </div>

            {/* Cohortes d'inscription */}
            <div className="card">
              <h3 id="chart-ages-heading">Cohortes d'inscription par mois</h3>
              <AccessibleChart
                titleId="chart-ages-heading"
                ariaLabel={
                  `Diagramme en barres : inscriptions par mois. ` +
                  ages.map((a) => `${a.age_bucket} : ${a.users_count}`).join(", ") + "."
                }
                fallbackLabel="Inscriptions par mois :"
                fallbackItems={ages.map((a) => `${a.age_bucket} : ${a.users_count} utilisateurs`)}
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={ages} margin={{ left: 8, right: 16 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="age_bucket" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(v) => [`${v} utilisateurs`, "Effectif"]} />
                    <Bar dataKey="users_count" fill="#6366f1" name="Utilisateurs" />
                  </BarChart>
                </ResponsiveContainer>
              </AccessibleChart>
            </div>
          </div>
        </section>
      )}

      {/* ── Statistiques fitness (admin) ── */}
      {isAdmin && (
        <section aria-labelledby="fitness-heading">
          <h2 id="fitness-heading" className="section-heading">Statistiques Fitness</h2>
          <p className="section-desc">
            Types d'activités les plus pratiqués, classés par volume de séances.
          </p>
          <div className="card">
            <h3 id="chart-body-heading">Exercices par type d'activité</h3>
            <AccessibleChart
              titleId="chart-body-heading"
              ariaLabel={
                `Diagramme en barres : volume de séances par type d'activité. ` +
                activities.map((a) => `${a.body_part} : ${a.exercises_count} séances`).join(", ") + "."
              }
              fallbackLabel="Séances par type d'activité :"
              fallbackItems={activities.map((a) => `${a.body_part} : ${a.exercises_count} séances`)}
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={activities} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis dataKey="body_part" type="category" width={100} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => [`${v} séances`, "Volume"]} />
                  <Bar dataKey="exercises_count" name="Séances">
                    {activities.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </AccessibleChart>
          </div>
        </section>
      )}

      {/* ── Analyses nutritionnelles (tous) ── */}
      <section aria-labelledby="nutrition-heading">
        <h2 id="nutrition-heading" className="section-heading">Analyses Nutritionnelles</h2>
        <p className="section-desc">
          Top 20 des aliments les plus caloriques de la base de données.
        </p>
        <div className="card">
          <h3 id="tbl-foods-heading">Top 20 aliments les plus caloriques</h3>
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label="Tableau des 20 aliments les plus caloriques — défilable au clavier"
          >
            <table aria-labelledby="tbl-foods-heading" className="table">
              <caption className="visually-hidden">
                Classement des 20 aliments par apport calorique décroissant (kcal pour 100 g).
              </caption>
              <thead>
                <tr>
                  <th scope="col">#</th>
                  <th scope="col">Aliment</th>
                  <th scope="col">Catégorie</th>
                  <th scope="col">kcal / 100 g</th>
                </tr>
              </thead>
              <tbody>
                {topFoods.length === 0 ? (
                  <tr>
                    <td colSpan={4}>Aucune donnée disponible.</td>
                  </tr>
                ) : (
                  topFoods.map((f, i) => (
                    <tr key={f.name + i}>
                      <td>{i + 1}</td>
                      <td>{f.name}</td>
                      <td>{f.category}</td>
                      <td>{f.kcal_per_100g.toLocaleString("fr-FR")}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}
