import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import Card from "../components/Card";
import Loading from "../components/Loading";
import ErrorBanner from "../components/ErrorBanner";

type Food = {
  id: number;
  name: string;
  category?: string;
  calories_kcal?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  fiber_g?: number;
  sugars_g?: number;
  sodium_mg?: number;
  cholesterol_mg?: number;
  meal_type?: string;
  water_intake_ml?: number;
};
type Log = { id: number; log_date: string; grams: number; food_id: number; food_name?: string; total_calories_kcal?: number };

const MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snack"];

const MEAL_COLORS: Record<string, string> = {
  Breakfast: "#f59e0b",
  Lunch:     "#059669",
  Dinner:    "#6366f1",
  Snack:     "#ec4899",
};

export default function Nutrition() {
  const [foodSearch, setFoodSearch] = useState("");
  const [mealTypeFilter, setMealTypeFilter] = useState("");
  const [foods, setFoods] = useState<Food[]>([]);
  const [logs, setLogs] = useState<Log[]>([]);
  const [userId, setUserId] = useState<string>("");

  const [from, setFrom] = useState(() => new Date(Date.now() - 6 * 86400000).toISOString().slice(0, 10));
  const [to, setTo] = useState(() => new Date().toISOString().slice(0, 10));

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setLoading(true); setErr(null);
    try {
      const [f, l] = await Promise.all([
        api.get("/foods", { params: { search: foodSearch || undefined, meal_type: mealTypeFilter || undefined, limit: 200 } }),
        api.get("/nutrition-logs", { params: { user_id: userId || undefined, from, to } })
      ]);
      setFoods(f.data?.items ?? f.data);
      setLogs(l.data?.items ?? l.data);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Impossible de charger nutrition.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  if (loading) return <Loading label="Chargement nutrition..." />;

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <div className="page-header">
        <div className="page-header-icon" aria-hidden="true">🥗</div>
        <div>
          <h1>Nutrition</h1>
          <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--text-muted)" }}>Référentiel alimentaire et journaux nutritionnels</p>
        </div>
      </div>

      {err && <ErrorBanner message={err} />}

      <div className="filters-row">
        <div className="filter-group">
          <span className="filter-label">User ID</span>
          <input id="uid" value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="ex: 1" style={{ width: 100 }} />
        </div>
        <div className="filter-group">
          <span className="filter-label">Recherche aliment</span>
          <input id="search" value={foodSearch} onChange={(e) => setFoodSearch(e.target.value)} placeholder="ex: chicken..." style={{ width: 160 }} />
        </div>
        <div className="filter-group">
          <span className="filter-label">Type de repas</span>
          <select id="meal_type" value={mealTypeFilter} onChange={(e) => setMealTypeFilter(e.target.value)}>
            <option value="">Tous</option>
            {MEAL_TYPES.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        <div className="filter-group">
          <span className="filter-label">Du</span>
          <input id="from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        </div>
        <div className="filter-group">
          <span className="filter-label">Au</span>
          <input id="to" type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        </div>
        <button className="btn-primary" onClick={load} style={{ alignSelf: "flex-end" }}>🔄 Actualiser</button>
      </div>

      <Card title={`Référentiel alimentaire (${foods.length} aliments)`} icon="🍽️">
        {foods.length === 0 ? (
          <p style={{ color: "var(--text-muted)", textAlign: "center", padding: "28px" }}>— Aucun aliment trouvé —</p>
        ) : (
          <div className="food-grid">
            {foods.map((x) => {
              const mealColor = x.meal_type ? (MEAL_COLORS[x.meal_type] ?? "var(--accent)") : undefined;
              return (
                <div key={x.id} className="food-card">
                  <div className="food-card-name">{x.name}</div>

                  <div className="food-card-badges">
                    {x.category && (
                      <span className="badge" style={{ background: "var(--accent-light)", color: "var(--accent)" }}>{x.category}</span>
                    )}
                    {x.meal_type && (
                      <span className="badge" style={{ background: mealColor + "22", color: mealColor }}>🍴 {x.meal_type}</span>
                    )}
                    {x.water_intake_ml != null && (
                      <span className="badge" style={{ background: "#e0f2fe", color: "#0369a1" }}>💧 {x.water_intake_ml} ml</span>
                    )}
                  </div>

                  <div className="food-card-macros">
                    <div className="food-macro-cell">
                      <span className="macro-val" style={{ color: "var(--warn)" }}>{x.calories_kcal ?? "—"}</span>
                      <span className="macro-lbl">kcal</span>
                    </div>
                    <div className="food-macro-cell">
                      <span className="macro-val" style={{ color: "#3b82f6" }}>{x.protein_g ?? "—"} g</span>
                      <span className="macro-lbl">Protéines</span>
                    </div>
                    <div className="food-macro-cell">
                      <span className="macro-val" style={{ color: "var(--primary)" }}>{x.carbs_g ?? "—"} g</span>
                      <span className="macro-lbl">Glucides</span>
                    </div>
                    <div className="food-macro-cell">
                      <span className="macro-val" style={{ color: "#f43f5e" }}>{x.fat_g ?? "—"} g</span>
                      <span className="macro-lbl">Lipides</span>
                    </div>
                  </div>

                  {(x.fiber_g != null || x.sugars_g != null || x.sodium_mg != null || x.cholesterol_mg != null) && (
                    <div className="food-card-micro">
                      {x.fiber_g != null && <span className="food-micro-item">Fibres <strong>{x.fiber_g} g</strong></span>}
                      {x.sugars_g != null && <span className="food-micro-item">Sucres <strong>{x.sugars_g} g</strong></span>}
                      {x.sodium_mg != null && <span className="food-micro-item">Sodium <strong>{x.sodium_mg} mg</strong></span>}
                      {x.cholesterol_mg != null && <span className="food-micro-item">Cholestérol <strong>{x.cholesterol_mg} mg</strong></span>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Card>

        <Card title="Nutrition logs" icon="📓">
          <div className="table-wrap" style={{ boxShadow: "none", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)" }}>
            <table className="table" aria-label="Table nutrition logs">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Aliment</th>
                  <th>Grammes</th>
                  <th>Total kcal</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr><td colSpan={4} style={{ textAlign: "center", color: "var(--text-light)", padding: "28px" }}>— Aucun log —</td></tr>
                ) : logs.map((x) => (
                  <tr key={x.id}>
                    <td><strong>{x.log_date}</strong></td>
                    <td>{x.food_name ?? `food_id=${x.food_id}`}</td>
                    <td>{x.grams} g</td>
                    <td>{x.total_calories_kcal ? <span className="badge badge-success">{x.total_calories_kcal} kcal</span> : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
    </div>
  );
}
