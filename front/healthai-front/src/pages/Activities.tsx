import React, { useEffect, useState, useRef } from "react";
import { api } from "../api/client";
import Loading from "../components/Loading";
import ErrorBanner from "../components/ErrorBanner";

type Exercise = {
  exerciseId: string;
  name: string;
  imageUrl: string;
  bodyParts: string[];
  equipments: string[];
  exerciseType: string;
  targetMuscles: string[];
  secondaryMuscles: string[];
};

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
}

function ExerciseCard({ ex, onClick }: { ex: Exercise; onClick: () => void }) {
  const [imgErr, setImgErr] = useState(false);
  return (
    <article className="exercise-card" onClick={onClick} role="button" tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}>
      <div className="exercise-card-img">
        {!imgErr
          ? <img src={ex.imageUrl} alt={ex.name} loading="lazy" onError={() => setImgErr(true)} />
          : <div className="exercise-card-img-placeholder">💪</div>
        }
      </div>
      <div className="exercise-card-body">
        <h3 className="exercise-card-name">{capitalize(ex.name)}</h3>
        <div className="exercise-card-tags">
          {ex.bodyParts.map((b) => (
            <span key={b} className="exercise-tag" data-bp={b.toUpperCase()}>{capitalize(b)}</span>
          ))}
          <span className="exercise-tag exercise-tag--type">
            {capitalize(ex.exerciseType)}
          </span>
        </div>
        <p className="exercise-card-muscle">
          <strong>Muscle :</strong> {ex.targetMuscles.map(capitalize).join(", ") || "—"}
        </p>
        <p className="exercise-card-equip">
          <strong>Équipement :</strong> {ex.equipments.map(capitalize).join(", ") || "—"}
        </p>
      </div>
    </article>
  );
}

function ExerciseModal({ ex, onClose }: { ex: Exercise; onClose: () => void }) {
  const [imgErr, setImgErr] = useState(false);
  const closeRef = React.useRef<HTMLButtonElement>(null);
  const modalRef = React.useRef<HTMLDivElement>(null);
  const titleId = `modal-title-${ex.exerciseId}`;

  useEffect(() => {
    closeRef.current?.focus();
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") { onClose(); return; }
      if (e.key === "Tab" && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey ? document.activeElement === first : document.activeElement === last) {
          e.preventDefault();
          (e.shiftKey ? last : first).focus();
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <div className="modal-overlay" onClick={onClose} aria-hidden="true">
      <div
        className="modal-card"
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <button ref={closeRef} className="modal-close" onClick={onClose} aria-label="Fermer la fiche exercice">✕</button>
        <div className="modal-img">
          {!imgErr
            ? <img src={ex.imageUrl} alt={`Illustration : ${capitalize(ex.name)}`} onError={() => setImgErr(true)} />
            : <div className="exercise-card-img-placeholder large" aria-hidden="true">💪</div>
          }
        </div>
        <div className="modal-body">
          <h2 id={titleId}>{capitalize(ex.name)}</h2>
          <div className="modal-tags">
            {ex.bodyParts.map((b) => (
              <span key={b} className="exercise-tag" data-bp={b.toUpperCase()}>{capitalize(b)}</span>
            ))}
            <span className="exercise-tag exercise-tag--type">
              {capitalize(ex.exerciseType)}
            </span>
          </div>
          <div className="modal-info-grid">
            <div className="modal-info-block">
              <span className="modal-info-label">Muscles ciblés</span>
              <p>{ex.targetMuscles.map(capitalize).join(", ") || "—"}</p>
            </div>
            <div className="modal-info-block">
              <span className="modal-info-label">Muscles secondaires</span>
              <p>{ex.secondaryMuscles.map(capitalize).join(", ") || "—"}</p>
            </div>
            <div className="modal-info-block">
              <span className="modal-info-label">Équipements</span>
              <p>{ex.equipments.map(capitalize).join(", ") || "—"}</p>
            </div>
            <div className="modal-info-block">
              <span className="modal-info-label">Type</span>
              <p>{capitalize(ex.exerciseType)}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Activities() {
  const [search, setSearch] = useState("");
  const [bodyPart, setBodyPart] = useState("");
  const [bodyParts, setBodyParts] = useState<string[]>([]);

  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [selected, setSelected] = useState<Exercise | null>(null);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load bodyparts on mount
  useEffect(() => {
    api.get("/exercises-ext/bodyparts")
      .then((r) => setBodyParts(r.data?.data ?? []))
      .catch(() => {});
  }, []);

  async function load(reset = true) {
    reset ? setLoading(true) : setLoadingMore(true);
    setErr(null);
    try {
      let res;
      if (search.trim()) {
        res = await api.get("/exercises-ext/exercises/search", { params: { name: search.trim(), limit: 20 } });
        setExercises(res.data?.data ?? []);
        setHasMore(false);
        setTotal(res.data?.meta?.total ?? res.data?.data?.length ?? 0);
        setCursor(null);
      } else {
        const params: Record<string, any> = { limit: 20 };
        if (!reset && cursor) params.cursor = cursor;
        res = await api.get("/exercises-ext/exercises", { params });
        const items: Exercise[] = res.data?.data ?? [];
        // client-side filter by body part if selected
        const filtered = bodyPart ? items.filter((e) => e.bodyParts.includes(bodyPart)) : items;
        setExercises((prev) => reset ? filtered : [...prev, ...filtered]);
        setHasMore(res.data?.meta?.hasNextPage ?? false);
        setTotal(res.data?.meta?.total ?? 0);
        setCursor(res.data?.meta?.nextCursor ?? null);
      }
    } catch (e: any) {
      const status = e?.response?.status;
      if (status === 429) {
        setErr("Limite de requêtes ExerciseDB atteinte. Patientez quelques secondes puis réactualisez.");
      } else {
        setErr("Impossible de charger les exercices. Réessayez.");
      }
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }

  useEffect(() => { load(true); }, [bodyPart]);

  // Debounce search
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => load(true), 400);
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
  }, [search]);

  return (
    <div className="page-grid">
      <div className="page-header">
        <div className="page-header-icon" aria-hidden="true">💪</div>
        <div>
          <h1>Exercices</h1>
          <p className="page-subtitle">
            {total > 0 ? `${total.toLocaleString()} exercices disponibles` : "Catalogue complet des exercices"} · Source : ExerciseDB
          </p>
        </div>
      </div>

      {err && <ErrorBanner message={err} />}

      <div className="filters-row">
        <div className="filter-group filter-group-grow">
          <label htmlFor="ex-search" className="filter-label">🔍 Recherche</label>
          <input
            id="ex-search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Ex: squat, bench press, plank..."
          />
        </div>
        <div className="filter-group">
          <label htmlFor="ex-bodypart" className="filter-label">Partie du corps</label>
          <select id="ex-bodypart" value={bodyPart} onChange={(e) => { setBodyPart(e.target.value); setSearch(""); }}>
            <option value="">Toutes</option>
            {bodyParts.map((b) => (
              <option key={b} value={b}>{capitalize(b)}</option>
            ))}
          </select>
        </div>
        {(search || bodyPart) && (
          <button
            className="btn-secondary"
            onClick={() => { setSearch(""); setBodyPart(""); }}
            aria-label="Réinitialiser les filtres"
          >
            <span aria-hidden="true">✕</span> Réinitialiser
          </button>
        )}
      </div>

      {loading ? (
        <Loading label="Chargement des exercices..." />
      ) : exercises.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🏋️</div>
          <p>Aucun exercice trouvé{search ? ` pour « ${search} »` : ""}</p>
        </div>
      ) : (
        <>
          <div className="exercise-grid">
            {exercises.map((ex) => (
              <ExerciseCard key={ex.exerciseId} ex={ex} onClick={() => setSelected(ex)} />
            ))}
          </div>

          {hasMore && !search && (
            <div className="load-more-row">
              <button className="btn-primary btn-load-more" onClick={() => load(false)} disabled={loadingMore}>
                {loadingMore ? "Chargement..." : "Charger plus d'exercices"}
              </button>
            </div>
          )}
        </>
      )}

      {selected && <ExerciseModal ex={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
