import React from "react";
import { Outlet, Link } from "react-router-dom";
import Nav from "./Nav";
import { useAuth } from "../auth/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();

  const initials = user?.email
    ? user.email.slice(0, 2).toUpperCase()
    : "?";

  return (
    <>
      <a className="skip-link" href="#main">Aller au contenu</a>

      <header>
        <div className="header-inner">
          <div className="header-start">
            <Link to="/" className="logo" aria-label="HealthAI Coach — Accueil">
              <div className="logo-icon" aria-hidden="true">🌿</div>
              <span>HealthAI <span>Coach</span></span>
            </Link>
            <Nav />
          </div>

          <div className="header-user">
            {user?.email && (
              <div className="user-badge" aria-label={`Connecté en tant que ${user.email}`}>
                <div className="avatar" aria-hidden="true">{initials}</div>
                <span className="user-email">{user.email}</span>
              </div>
            )}
            <button className="btn-logout" onClick={logout} aria-label="Se déconnecter">
              Déconnexion
            </button>
          </div>
        </div>
      </header>

      <main id="main" className="container" tabIndex={-1}>
        <Outlet />
      </main>

      <footer>
        Prototype MSPR · HealthAI Coach · Navigation clavier &amp; accessibilité OK
      </footer>
    </>
  );
}
