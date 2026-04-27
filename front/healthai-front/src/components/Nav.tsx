import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const links = [
  { to: "/dashboard",  end: true,  icon: "📊", label: "Dashboard"     },
  { to: "/daily-log",  end: false, icon: "📝", label: "Journal"        },
  { to: "/activities", end: false, icon: "💪", label: "Exercices"      },
  { to: "/nutrition",  end: false, icon: "🥗", label: "Nutrition"      },
  { to: "/users",      end: false, icon: "👥", label: "Utilisateurs",  adminOnly: true },
  { to: "/etl",        end: false, icon: "⚙️", label: "Qualité ETL",  adminOnly: true },
];

export default function Nav() {
  const { user } = useAuth();
  
  return (
    <nav aria-label="Navigation principale">
      {links.map(({ to, end, icon, label, adminOnly }: any) => {
        // Masquer le lien Users pour les non-admin
        if (adminOnly && user?.role !== "admin") {
          return null;
        }
        return (
          <NavLink key={to} to={to} end={end}>
            <span className="nav-icon" aria-hidden="true">{icon}</span>
            {label}
          </NavLink>
        );
      })}
    </nav>
  );
}
