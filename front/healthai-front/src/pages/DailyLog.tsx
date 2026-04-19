import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import ErrorBanner from "../components/ErrorBanner";

const WORKOUT_TYPES = [
  "Cardio", "Musculation", "Yoga", "Running",
  "Natation", "Vélo", "Marche", "Autre",
];

type DayEntry = {
  id: number;
  activity_date: string;
  steps: number | null;
  active_minutes: number | null;
  calories_out: number | null;
  distance_km: number | null;
  workout_type: string | null;
  sleep_hours: number | null;
  water_ml: number | null;
  weight_kg: number | null;
};

function isoDate(d: Date) {
  return d.toISOString().slice(0, 10);
}

function addDays(iso: string, n: number) {
  const d = new Date(iso + "T00:00:00");
  d.setDate(d.getDate() + n);
  return isoDate(d);
}

function fmtDate(iso: string, todayIso: string) {
  if (iso === todayIso) return "Aujourd'hui";
  if (iso === addDays(todayIso, -1)) return "Hier";
  return new Date(iso + "T00:00:00").toLocaleDateString("fr-FR", {
    weekday: "long", day: "numeric", month: "long",
  });
}

const WATER_GOAL = 2000;

/** Returns a filled/empty dot to indicate section completion */
function SectionDot({ filled }: { filled: boolean }) {
  return (
    <span className={filled ? "section-dot section-dot--filled" : "section-dot"} aria-hidden="true" />
  );
}

export default function DailyLog() {
  const today = isoDate(new Date());
  const [date, setDate] = useState(today);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Form fields
  const [steps, setSteps] = useState("");
  const [activeMin, setActiveMin] = useState("");
  const [calOut, setCalOut] = useState("");
  const [distance, setDistance] = useState("");
  const [workoutType, setWorkoutType] = useState("");
  const [sleep, setSleep] = useState("");
  const [weight, setWeight] = useState("");
  const [water, setWater] = useState("");
  const [entryId, setEntryId] = useState<number | null>(null);

  const loadEntry = useCallback(async (d: string) => {
    setLoading(true);
    setErr(null);
    setSuccess(false);
    try {
      const res = await api.get<DayEntry[]>("/activities", { params: { from: d, to: d } });
      const entry = res.data[0] ?? null;
      if (entry) {
        setEntryId(entry.id);
        setSteps(entry.steps?.toString() ?? "");
        setActiveMin(entry.active_minutes?.toString() ?? "");
        setCalOut(entry.calories_out?.toString() ?? "");
        setDistance(entry.distance_km?.toString() ?? "");
        setWorkoutType(entry.workout_type ?? "");
        setSleep(entry.sleep_hours?.toString() ?? "");
        setWeight(entry.weight_kg?.toString() ?? "");
        setWater(entry.water_ml?.toString() ?? "");
      } else {
        setEntryId(null);
        setSteps(""); setActiveMin(""); setCalOut(""); setDistance("");
        setWorkoutType(""); setSleep(""); setWeight(""); setWater("");
      }
    } catch {
      setErr("Impossible de charger l'entrée.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadEntry(date); }, [date, loadEntry]);

  // Auto-dismiss success banner after 3s
  useEffect(() => {
    if (!success) return;
    const t = setTimeout(() => setSuccess(false), 3000);
    return () => clearTimeout(t);
  }, [success]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setErr(null);
    setSuccess(false);
    try {
      const payload: Record<string, unknown> = { activity_date: date };
      if (steps !== "")      payload.steps           = parseInt(steps, 10);
      if (activeMin !== "")  payload.active_minutes  = parseInt(activeMin, 10);
      if (calOut !== "")     payload.calories_out    = parseInt(calOut, 10);
      if (distance !== "")   payload.distance_km     = parseFloat(distance);
      if (workoutType !== "") payload.workout_type   = workoutType;
      if (sleep !== "")      payload.sleep_hours     = parseFloat(sleep);
      if (weight !== "")     payload.weight_kg       = parseFloat(weight);
      if (water !== "")      payload.water_ml        = parseInt(water, 10);

      const res = await api.post<DayEntry>("/activities", payload);
      setEntryId(res.data.id);
      setSuccess(true);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Erreur lors de la sauvegarde.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!entryId || !window.confirm("Supprimer cette entrée ?")) return;
    try {
      await api.delete(`/activities/${entryId}`);
      setEntryId(null);
      setSteps(""); setActiveMin(""); setCalOut(""); setDistance("");
      setWorkoutType(""); setSleep(""); setWeight(""); setWater("");
      setSuccess(false);
    } catch {
      setErr("Impossible de supprimer l'entrée.");
    }
  }

  const waterPct = Math.min(100, ((parseInt(water, 10) || 0) / WATER_GOAL) * 100);
  const isFuture = date > today;

  // Section completion hints
  const actFilled = !!(workoutType || steps || activeMin || calOut || distance);
  const bodyFilled = !!(sleep || weight);
  const waterFilled = !!(water && parseInt(water, 10) > 0);

  const dateLabel = fmtDate(date, today);
  const isToday = date === today;

  return (
    <div className="daily-log-page">
      {/* Header */}
      <div className="page-header">
        <div className="page-header-icon" aria-hidden="true">📝</div>
        <div>
          <h1>Journal du jour</h1>
          <p className="page-subtitle">
            {isToday ? "Enregistrez vos données de santé d'aujourd'hui" : `Modifiez l'entrée du ${dateLabel.toLowerCase()}`}
          </p>
        </div>
        {entryId && (
          <span className="entry-status-badge" role="status">✓ Enregistré</span>
        )}
      </div>

      <Link to="/dashboard" className="back-link">← Retour au Dashboard</Link>

      {/* Date navigation */}
      <div className="log-date-nav">
        <button
          type="button"
          className="btn-ghost btn-nav-day"
          onClick={() => setDate(d => addDays(d, -1))}
          aria-label="Jour précédent"
        >
          ←
        </button>
        <div className="log-date-center">
          <span className={isToday ? "log-date-display log-date-today" : "log-date-display"}>{dateLabel}</span>
          <input
            type="date"
            value={date}
            max={today}
            onChange={e => setDate(e.target.value)}
            className="log-date-input"
            aria-label="Date"
          />
        </div>
        <button
          type="button"
          className="btn-ghost btn-nav-day"
          onClick={() => setDate(d => addDays(d, 1))}
          disabled={date >= today}
          aria-label="Jour suivant"
        >
          →
        </button>
        {!isToday && (
          <button type="button" className="btn-ghost btn-today-shortcut" onClick={() => setDate(today)}>
            Aujourd'hui
          </button>
        )}
      </div>

      {err && <ErrorBanner message={err} />}
      {success && (
        <div className="success-banner" role="status">
          ✅ Entrée enregistrée avec succès !
        </div>
      )}
      {isFuture && (
        <div className="warn-banner" role="alert">
          ⚠️ Vous ne pouvez pas enregistrer une entrée dans le futur.
        </div>
      )}

      {loading ? (
        <p className="loading-text">Chargement…</p>
      ) : (
        <form onSubmit={handleSave} aria-label="Formulaire de journal quotidien">
          {/* Section 1: Activity */}
          <section className="log-section" aria-labelledby="act-title">
            <h2 id="act-title" className="log-section-title">
              <SectionDot filled={actFilled} />
              🏃 Activité
            </h2>
            <div className="log-field-grid">
              <div>
                <label htmlFor="workout-type" className="log-field-label">Type d'entraînement</label>
                <select
                  id="workout-type"
                  className="log-input"
                  value={workoutType}
                  onChange={e => setWorkoutType(e.target.value)}
                >
                  <option value="">-- Sélectionner --</option>
                  {WORKOUT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="steps" className="log-field-label">Nombre de pas</label>
                <input
                  id="steps"
                  type="number"
                  min="0"
                  className="log-input"
                  value={steps}
                  onChange={e => setSteps(e.target.value)}
                  placeholder="ex : 8 000"
                />
              </div>
              <div>
                <label htmlFor="active-min" className="log-field-label">Minutes actives</label>
                <input
                  id="active-min"
                  type="number"
                  min="0"
                  className="log-input"
                  value={activeMin}
                  onChange={e => setActiveMin(e.target.value)}
                  placeholder="ex : 45"
                />
              </div>
              <div>
                <label htmlFor="cal-out" className="log-field-label">Calories brûlées (kcal)</label>
                <input
                  id="cal-out"
                  type="number"
                  min="0"
                  className="log-input"
                  value={calOut}
                  onChange={e => setCalOut(e.target.value)}
                  placeholder="ex : 350"
                />
              </div>
              <div>
                <label htmlFor="distance" className="log-field-label">Distance (km)</label>
                <input
                  id="distance"
                  type="number"
                  min="0"
                  step="0.01"
                  className="log-input"
                  value={distance}
                  onChange={e => setDistance(e.target.value)}
                  placeholder="ex : 5.2"
                />
              </div>
            </div>
          </section>

          {/* Section 2: Body */}
          <section className="log-section" aria-labelledby="body-title">
            <h2 id="body-title" className="log-section-title">
              <SectionDot filled={bodyFilled} />
              😴 Corps
            </h2>
            <div className="log-field-grid">
              <div>
                <label htmlFor="sleep" className="log-field-label">Heures de sommeil</label>
                <input
                  id="sleep"
                  type="number"
                  min="0"
                  max="24"
                  step="0.5"
                  className="log-input"
                  value={sleep}
                  onChange={e => setSleep(e.target.value)}
                  placeholder="ex : 7.5"
                />
              </div>
              <div>
                <label htmlFor="weight" className="log-field-label">Poids (kg)</label>
                <input
                  id="weight"
                  type="number"
                  min="0"
                  step="0.1"
                  className="log-input"
                  value={weight}
                  onChange={e => setWeight(e.target.value)}
                  placeholder="ex : 72.5"
                />
              </div>
            </div>
          </section>

          {/* Section 3: Hydration */}
          <section className="log-section" aria-labelledby="water-title">
            <h2 id="water-title" className="log-section-title">
              <SectionDot filled={waterFilled} />
              💧 Hydratation
            </h2>
            <div>
              <label htmlFor="water" className="log-field-label">
                Eau bue (ml) — objectif : {WATER_GOAL} ml
              </label>
              <input
                id="water"
                type="number"
                min="0"
                step="50"
                className="log-input log-input-water"
                value={water}
                onChange={e => setWater(e.target.value)}
                placeholder="ex : 1500"
              />
              <svg
                className="today-progress-svg"
                role="img"
                aria-label={`Hydratation : ${parseInt(water, 10) || 0} / ${WATER_GOAL} ml`}
                xmlns="http://www.w3.org/2000/svg"
              >
                <rect className="today-svg-track" x="0" y="0" width="100%" height="10" rx="5" />
                <rect x="0" y="0" width={`${waterPct}%`} height="10" rx="5" fill="#0ea5e9" />
              </svg>
              <p className="water-bar-label">
                {parseInt(water, 10) || 0} / {WATER_GOAL} ml
                {waterPct >= 100 && " 🎉 Objectif atteint !"}
              </p>
            </div>
          </section>

          {/* Actions */}
          <div className="log-actions">
            <button
              type="submit"
              className="btn-primary"
              disabled={saving || isFuture}
            >
              {saving ? "Enregistrement…" : entryId ? "💾 Mettre à jour" : "💾 Enregistrer"}
            </button>
            {entryId && (
              <button
                type="button"
                className="btn-danger"
                onClick={handleDelete}
                disabled={saving}
              >
                🗑️ Supprimer l'entrée
              </button>
            )}
          </div>
        </form>
      )}
    </div>
  );
}
