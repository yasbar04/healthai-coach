import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import FormField from "../components/FormField";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../auth/AuthContext";
import { getErrorMessage } from "../api/client";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await login(email.trim(), password);
      nav("/dashboard", { replace: true });
    } catch (e) {
      const errorMsg = getErrorMessage(e);
      setErr(errorMsg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <div className="login-logo-icon" aria-hidden="true">🌿</div>
          <div>
            <div className="login-title">HealthAI <span>Coach</span></div>
            <div className="login-tagline">Plateforme d'administration</div>
          </div>
        </div>

        <p className="login-subtitle">Connects-toi pour accéder au tableau de bord et aux données.</p>

        {err && <ErrorBanner message={err} />}

        <form onSubmit={onSubmit} className="login-form" aria-label="Formulaire de connexion">
          <FormField id="email" label="Email">
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              placeholder="ex: user@demo.fr"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </FormField>

          <FormField id="password" label="Mot de passe">
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </FormField>

          <button className="btn-primary login-submit-btn" disabled={busy} type="submit">
            {busy ? "Connexion en cours..." : "🔒  Se connecter"}
          </button>
        </form>

        <p className="login-demo-hint">
          Démo : <code>user@demo.fr</code> / <code>Demo123!</code>
        </p>
        <p className="login-register-hint">
          Pas encore de compte ?{" "}
          <Link to="/" className="login-register-link">Voir les offres</Link>
        </p>
      </div>
    </div>
  );
}
