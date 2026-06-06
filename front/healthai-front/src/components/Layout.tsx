import React, { useState } from "react";
import { Outlet, Link } from "react-router-dom";
import Nav from "./Nav";
import { useAuth } from "../auth/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const initials = user?.email
    ? user.email.slice(0, 2).toUpperCase()
    : "?";

  return (
    <div className="app-layout">
      <a className="skip-link" href="#main">Aller au contenu</a>

      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside className={`sidebar${sidebarOpen ? " sidebar-open" : ""}`} aria-label="Navigation principale">
        <div className="sidebar-header">
          <Link to="/" className="logo" aria-label="HealthAI Coach — Accueil" onClick={() => setSidebarOpen(false)}>
            <div className="logo-icon" aria-hidden="true">🌿</div>
            <span>HealthAI <span>Coach</span></span>
          </Link>
        </div>

        <Nav onNavigate={() => setSidebarOpen(false)} />

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div
              className="avatar-only"
              aria-label={`Connecté en tant que ${user?.email ?? ""}`}
              title={user?.email}
            >
              {initials}
            </div>
            <span className="sidebar-user-email">{user?.email}</span>
          </div>
          <button
            type="button"
            className="btn-logout"
            onClick={logout}
            aria-label="Se déconnecter"
            title="Se déconnecter"
          >
            ↪️
          </button>
        </div>
      </aside>

      <div className="app-main">
        <div className="mobile-topbar">
          <button
            type="button"
            className="hamburger-btn"
            onClick={() => setSidebarOpen((v) => !v)}
            aria-label={sidebarOpen ? "Fermer le menu" : "Ouvrir le menu"}
            aria-expanded={sidebarOpen ? "true" : "false"}
          >
            ☰
          </button>
          <Link to="/" className="logo" onClick={() => setSidebarOpen(false)}>
            <div className="logo-icon" aria-hidden="true">🌿</div>
            <span>HealthAI <span>Coach</span></span>
          </Link>
        </div>

        <main id="main" className="main-content" tabIndex={-1}>
          <Outlet />
        </main>

        <footer>
          Prototype MSPR · HealthAI Coach · Navigation clavier &amp; accessibilité OK
        </footer>
      </div>
    </div>
  );
}
