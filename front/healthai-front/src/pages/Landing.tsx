import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles.css";

const API = "http://localhost:8010";

const PLANS = [
  { id: "freemium",   name: "Freemium",  price: "0",     tagline: "Ideal pour demarrer",       popular: false, color: "#64748b",
    features: ["Tableau de bord personnnel","Suivi nutritionnel basique","5 exercices / semaine","Historique 30 jours"] },
  { id: "premium",    name: "Premium",   price: "9.99",  tagline: "Pour les sportifs reguliers",popular: true,  color: "#059669",
    features: ["Tout Freemium, plus :","Analyses IA personnalisees","Exercices illimites","Historique complet","Rapports hebdomadaires"] },
  { id: "premium_plus",name: "Premium+", price: "19.99", tagline: "Performance & coaching",     popular: false, color: "#6366f1",
    features: ["Tout Premium, plus :","Coach IA dedie","Plans sur mesure","Objets connectes","Support 24/7"] },
  { id: "b2b",        name: "B2B",       price: "49.99", tagline: "Pour les entreprises",       popular: false, color: "#f59e0b",
    features: ["Utilisateurs illimites","Dashboard multi-tenant","API entreprise","ETL & qualite des donnees","SLA garanti"] },
];

const FEATURES = [
  { icon: "", title: "Analytics avances",      desc: "BMI, frequence cardiaque, calories, tendances  tout en temps reel." },
  { icon: "", title: "Nutrition intelligente",  desc: "650+ aliments. Macros, micros, hydratation et recommendations IA." },
  { icon: "", title: "Programmes d exercices",  desc: "Cardio, musculation, HIIT  adaptes a votre profil et vos objectifs." },
  { icon: "", title: "Coach IA personnel",       desc: "Plans adaptes, suivi continu et alertes intelligentes 24/7." },
];

function fmtCard(v: string) {
  const digits = v.replace(/\D/g, "").slice(0, 16);
  return digits.replace(/(.{4})/g, "$1 ").trim();
}
function fmtExpiry(v: string) {
  const digits = v.replace(/\D/g, "").slice(0, 4);
  if (digits.length >= 3) return digits.slice(0, 2) + "/" + digits.slice(2);
  return digits;
}
function cardBrand(num: string): string {
  const n = num.replace(/\s/g, "");
  if (n.startsWith("4")) return "Visa";
  if (n.startsWith("5") || n.startsWith("2")) return "Mastercard";
  if (n.startsWith("3")) return "Amex";
  return "Carte";
}

export default function Landing() {
  const nav = useNavigate();
  const [open, setOpen]             = useState(false);
  const [step, setStep]             = useState<1 | 2 | 3>(1);
  const [selectedPlan, setSelectedPlan] = useState("freemium");
  const [email, setEmail]           = useState("");
  const [password, setPassword]     = useState("");
  const [showPw, setShowPw]         = useState(false);
  const [cardNum , setCardNum]      = useState("");
  const [expiry  , setExpiry]       = useState("");
  const [cvv     , setCvv]          = useState("");
  const [holder  , setHolder]       = useState("");
  const [busy, setBusy]             = useState(false);
  const [err , setErr]              = useState<string | null>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const cardRef  = useRef<HTMLInputElement>(null);

  function openModal(planId: string) {
    setSelectedPlan(planId); setStep(1);
    setEmail(""); setPassword(""); setShowPw(false);
    setCardNum(""); setExpiry(""); setCvv(""); setHolder("");
    setErr(null); setBusy(false); setOpen(true);
  }
  function closeModal() { if (!busy) setOpen(false); }

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => {
      if (step === 1) emailRef.current?.focus();
      if (step === 2) cardRef.current?.focus();
    }, 80);
    return () => clearTimeout(t);
  }, [open, step]);

  async function handleStep1(e: React.FormEvent) {
    e.preventDefault(); setErr(null);
    const p = PLANS.find((x) => x.id === selectedPlan)!;
    if (p.price === "0") { await doRegister(); }
    else { setStep(2); }
  }

  async function handlePayment(e: React.FormEvent) {
    e.preventDefault(); setErr(null); setBusy(true);
    await new Promise((r) => setTimeout(r, 1500));
    await doRegister();
  }

  async function doRegister() {
    setBusy(true);
    try {
      const res = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password, plan: selectedPlan }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur lors de l inscription.");
      localStorage.setItem("healthai_token", data.access_token);
      setStep(3);
      setTimeout(() => nav("/dashboard", { replace: true }), 2200);
    } catch (ex: any) {
      setErr(ex.message || "Erreur reseau.");
      setBusy(false);
    }
  }

  const plan   = PLANS.find((p) => p.id === selectedPlan)!;
  const isPaid = plan?.price !== "0";

  return (
    <div className="landing">
      <header className="landing-nav">
        <a href="/" className="landing-nav-logo"><span></span>Health<span>AI</span> Coach</a>
        <div className="landing-nav-actions">
          <a href="#pricing" className="btn-ghost landing-nav-btn">Tarifs</a>
          <Link to="/login" className="btn-ghost landing-nav-btn">Se connecter</Link>
          <button className="btn-primary landing-nav-btn" onClick={() => openModal("premium")}>Essayer gratuitement</button>
        </div>
      </header>

      <section className="landing-hero">
        <div>
          <div className="hero-eyebrow"> Sante &amp; Performance</div>
          <h1 className="hero-title">Votre coach sante<br /><span>propulse par l IA</span></h1>
          <p className="hero-subtitle">Nutrition, exercices, biometriques  tout en un. Des recommandations intelligentes adaptees a votre profil unique.</p>
          <div className="hero-ctas">
            <button className="btn-primary hero-cta-primary" onClick={() => openModal("freemium")}>Commencer gratuitement </button>
            <Link to="/login" className="btn-secondary hero-cta-primary">J ai deja un compte</Link>
          </div>
          <div className="hero-stats">
            {[["1 000+","Utilisateurs actifs"],["650+","Aliments references"],["98%","Satisfaction"]].map(([n,l]) => (
              <div className="hero-stat-item" key={l}><span className="hero-stat-num">{n}</span><span className="hero-stat-lbl">{l}</span></div>
            ))}
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="hero-card"><div className="hero-card-icon"></div><div className="hero-card-label">Score sante</div><div className="hero-card-value">87 / 100</div><div className="hero-card-sub"> +4 pts cette semaine</div></div>
          <div className="hero-card"><div className="hero-card-icon"></div><div className="hero-card-label">Calories</div><div className="hero-card-value">512 kcal</div><div className="hero-card-sub">Seance Cardio</div></div>
          <div className="hero-card"><div className="hero-card-icon"></div><div className="hero-card-label">Hydratation</div><div className="hero-card-value">2 400 ml</div><div className="hero-card-sub">Objectif atteint </div></div>
        </div>
      </section>

      <section className="landing-features">
        <p className="section-eyebrow">Fonctionnalites</p>
        <h2 className="section-title">Tout ce dont vous avez besoin</h2>
        <p className="section-sub">Une plateforme complete pour prendre en main votre sante, du suivi quotidien aux analyses approfondies.</p>
        <div className="features-grid">
          {FEATURES.map((f) => (
            <div className="feature-card" key={f.title}><div className="feature-icon">{f.icon}</div><div className="feature-title">{f.title}</div><div className="feature-desc">{f.desc}</div></div>
          ))}
        </div>
      </section>

      <section className="landing-pricing" id="pricing">
        <p className="section-eyebrow">Tarifs</p>
        <h2 className="section-title">Choisissez votre offre</h2>
        <p className="section-sub">Commencez gratuitement, evoluez a votre rythme. Sans engagement, resiliable a tout moment.</p>
        <div className="pricing-grid">
          {PLANS.map((p) => (
            <div className={`pricing-card${p.popular ? " popular" : ""}`} key={p.id}>
              {p.popular && <div className="pricing-badge-popular"> Le plus populaire</div>}
              <div className="pricing-plan-name">{p.name}</div>
              <div className="pricing-price">{p.price === "0" ? "Gratuit" : <><sup>€</sup>{p.price}<span> /mois</span></>}</div>
              <div className="pricing-tagline">{p.tagline}</div>
              <div className="pricing-divider" />
              <ul className="pricing-features-list">{p.features.map((feat) => <li className="pricing-feature-item" key={feat}>{feat}</li>)}</ul>
              <button className={`pricing-cta${p.popular ? " primary-cta" : " outline-cta"}`} onClick={() => openModal(p.id)}>
                {p.price === "0" ? "Demarrer gratuitement" : `Choisir ${p.name}`}
              </button>
            </div>
          ))}
        </div>
      </section>

      <footer className="landing-footer">
        <span> {new Date().getFullYear()} HealthAI Coach</span>
        <span className="landing-footer-links">
          <a href="#pricing" className="landing-footer-link">Tarifs</a>
          <Link to="/login" className="landing-footer-link">Connexion</Link>
        </span>
      </footer>

      {open && (
        <div className="register-modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) closeModal(); }} role="dialog" aria-modal="true">
          <div className="register-modal">
            <div className="register-modal-header">
              <div className="register-modal-header-info">
                {step !== 3 && (
                  <div className="modal-steps">
                    <div className={`modal-step${step >= 1 ? " active" : ""}`}><span>{step > 1 ? "" : "1"}</span> Compte</div>
                    {isPaid && <><div className="modal-step-sep" /><div className={`modal-step${step >= 2 ? " active" : ""}`}><span>{step > 2 ? "" : "2"}</span> Paiement</div></>}
                  </div>
                )}
                <h2 className="modal-title">
                  {step === 1 && "Creer votre compte"}
                  {step === 2 && "Paiement securise "}
                  {step === 3 && "Bienvenue ! "}
                </h2>
                {step === 1 && <p className="modal-subtitle">Offre&nbsp;: <strong className={`plan-name-color-${plan.id}`}>{plan.name}</strong>{isPaid && <> — <strong>€{plan.price}/mois</strong></>}</p>}
                {step === 2 && <p className="modal-subtitle">Montant a regler&nbsp;: <strong>€{plan.price}</strong></p>}
              </div>
              {step !== 3 && <button onClick={closeModal} className="modal-close-btn" disabled={busy} aria-label="Fermer"></button>}
            </div>

            <div className="register-modal-body">
              {step === 1 && (
                <form onSubmit={handleStep1} className="register-form">
                  <div>
                    <p className="register-plan-label">Offre choisie</p>
                    <div className="register-plan-selector" role="radiogroup">
                      {PLANS.map((p) => (
                        <label key={p.id} className={`register-plan-option${selectedPlan === p.id ? " selected" : ""}`}>
                          <input type="radio" name="plan" value={p.id} checked={selectedPlan === p.id} onChange={() => setSelectedPlan(p.id)} className="sr-only" />
                          <span className="register-plan-option-name">{p.name}</span>
                          <span className="register-plan-option-price">{p.price === "0" ? "Gratuit" : `€${p.price}/mois`}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  {err && <div className="register-error"> {err}</div>}
                  <div>
                    <label htmlFor="reg-email" className="register-form-label">Adresse e-mail</label>
                    <input ref={emailRef} id="reg-email" type="email" required autoComplete="email" placeholder="vous@exemple.com" value={email} onChange={(e) => setEmail(e.target.value)} className="register-form-input" />
                  </div>
                  <div>
                    <label htmlFor="reg-password" className="register-form-label">Mot de passe</label>
                    <div className="pw-wrapper">
                      <input id="reg-password" type={showPw ? "text" : "password"} required autoComplete="new-password" placeholder="6 caracteres minimum" minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} className="register-form-input pw-input" />
                      <button type="button" className="pw-toggle" onClick={() => setShowPw((v) => !v)} aria-label={showPw ? "Masquer" : "Afficher"}>{showPw ? "" : ""}</button>
                    </div>
                  </div>
                  <button type="submit" disabled={busy} className="btn-primary register-submit-btn">
                    {busy ? "..." : isPaid ? "Continuer vers le paiement " : " Creer mon compte gratuitement"}
                  </button>
                  <p className="register-modal-footer">Deja un compte ?{" "}<Link to="/login" className="register-modal-login-link" onClick={closeModal}>Se connecter</Link></p>
                </form>
              )}

              {step === 2 && (
                <form onSubmit={handlePayment} className="register-form">
                  <div className="payment-demo-hint">
                    <span className="payment-demo-icon"></span>
                    <div><strong>Mode demo</strong>  utilisez la carte test&nbsp;:<br /><code>4242 4242 4242 4242</code> | <code>12/28</code> | <code>123</code></div>
                  </div>
                  <div className="payment-card-visual">
                    <div className="pcv-top"><span className="pcv-brand">{cardBrand(cardNum)}</span><span className="pcv-chip"></span></div>
                    <div className="pcv-number">{cardNum || "   "}</div>
                    <div className="pcv-bottom"><span>{holder || "NOM PRENOM"}</span><span>{expiry || "MM/YY"}</span></div>
                  </div>
                  {err && <div className="register-error"> {err}</div>}
                  <div>
                    <label htmlFor="card-num" className="register-form-label">Numero de carte</label>
                    <input ref={cardRef} id="card-num" type="text" inputMode="numeric" required placeholder="4242 4242 4242 4242" value={cardNum} onChange={(e) => setCardNum(fmtCard(e.target.value))} maxLength={19} className="register-form-input" autoComplete="cc-number" />
                  </div>
                  <div className="payment-row">
                    <div className="payment-col">
                      <label htmlFor="card-expiry" className="register-form-label">Expiration</label>
                      <input id="card-expiry" type="text" inputMode="numeric" required placeholder="MM/YY" value={expiry} onChange={(e) => setExpiry(fmtExpiry(e.target.value))} maxLength={5} className="register-form-input" autoComplete="cc-exp" />
                    </div>
                    <div className="payment-col">
                      <label htmlFor="card-cvv" className="register-form-label">CVV</label>
                      <input id="card-cvv" type="text" inputMode="numeric" required placeholder="123" value={cvv} onChange={(e) => setCvv(e.target.value.replace(/\D/g,"").slice(0,4))} maxLength={4} className="register-form-input" autoComplete="cc-csc" />
                    </div>
                  </div>
                  <div>
                    <label htmlFor="card-holder" className="register-form-label">Titulaire</label>
                    <input id="card-holder" type="text" required placeholder="Jean Dupont" value={holder} onChange={(e) => setHolder(e.target.value)} className="register-form-input" autoComplete="cc-name" />
                  </div>
                  <button type="submit" disabled={busy} className="btn-primary register-submit-btn payment-pay-btn">
                    {busy ? <span className="pay-spinner"> Traitement...</span> : <> Payer €{plan.price} en toute securite</>}
                  </button>
                  <button type="button" className="btn-secondary payment-back-btn" onClick={() => { setStep(1); setErr(null); }} disabled={busy}> Retour</button>
                  <p className="payment-secure-note"> Chiffrement 256-bit TLS  <em>Demo : aucun debit reel</em></p>
                </form>
              )}

              {step === 3 && (
                <div className="register-success">
                  <div className="success-circle">
                    <svg viewBox="0 0 52 52" className="success-svg"><circle className="success-circle-bg" cx="26" cy="26" r="25" fill="none" /><path className="success-check" fill="none" d="M14 27 l8 8 l16-16" /></svg>
                  </div>
                  <h3>Compte cree avec succes !</h3>
                  <p>Bienvenue sur <strong>HealthAI Coach</strong>. Redirection vers votre tableau de bord</p>
                  <div className={`success-plan-badge plan-badge-${plan.id}`}>{plan.name} activé ✓</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
