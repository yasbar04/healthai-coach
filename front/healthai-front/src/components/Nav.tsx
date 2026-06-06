import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const PLAN_BADGE: Record<string, { label: string; color: string }> = {
  premium:      { label: "PRO",   color: "bg-primary-500 text-white" },
  premium_plus: { label: "PRO+",  color: "bg-purple-600 text-white"  },
  b2b:          { label: "B2B",   color: "bg-gray-700 text-white"    },
  freemium:     { label: "FREE",  color: "bg-gray-200 text-gray-600" },
};

const MAIN_LINKS = [
  { to: "/dashboard",     end: true,  icon: "📊", label: "Dashboard"      },
  { to: "/activities",    end: false, icon: "💪", label: "Exercices"       },
  { to: "/activity",      end: false, icon: "🏋️", label: "Séance IA",     premium: true },
  { to: "/nutrition",     end: false, icon: "🥗", label: "Nutrition"       },
  { to: "/meal-analysis", end: false, icon: "📸", label: "Analyse repas",  premium: true },
  { to: "/program",       end: false, icon: "📅", label: "Programme IA",   premium: true },
  { to: "/profile",       end: false, icon: "👤", label: "Profil"          },
  { to: "/analytics",     end: false, icon: "📈", label: "Analytics"       },
];

const ADMIN_LINKS = [
  { to: "/users", end: false, icon: "👥", label: "Utilisateurs" },
  { to: "/etl",   end: false, icon: "⚙️", label: "Qualité ETL"  },
];

interface NavProps {
  onNavigate?: () => void;
}

export default function Nav({ onNavigate }: NavProps) {
  const { user } = useAuth();
  const plan = user?.plan ?? "freemium";
  const isPremium = plan === "premium" || plan === "premium_plus" || user?.role === "admin";
  const badge = PLAN_BADGE[plan] ?? PLAN_BADGE.freemium;

  return (
    <nav aria-label="Navigation principale">
      <div className="nav-plan-badge">
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${badge.color}`}>
          {badge.label}
        </span>
      </div>

      <div className="nav-section">
        {MAIN_LINKS.map(({ to, end, icon, label, premium }: any) => {
          const locked = premium && !isPremium;
          return (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={locked ? "opacity-60" : ""}
              onClick={onNavigate}
            >
              <span className="nav-icon" aria-hidden="true">{icon}</span>
              <span className="nav-label">{label}</span>
              {locked && <span className="nav-lock" aria-hidden="true">🔒</span>}
            </NavLink>
          );
        })}
      </div>

      {user?.role === "admin" && (
        <>
          <div className="nav-divider" />
          <p className="nav-section-title">Administration</p>
          <div className="nav-section">
            {ADMIN_LINKS.map(({ to, end, icon, label }) => (
              <NavLink key={to} to={to} end={end} onClick={onNavigate}>
                <span className="nav-icon" aria-hidden="true">{icon}</span>
                <span className="nav-label">{label}</span>
              </NavLink>
            ))}
          </div>
        </>
      )}
    </nav>
  );
}
