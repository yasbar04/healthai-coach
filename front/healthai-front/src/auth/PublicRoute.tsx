import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import Loading from "../components/Loading";

/**
 * Wraps public-only pages (Landing, Login).
 * If the user is already authenticated → redirect straight to /dashboard.
 */
export default function PublicRoute({ children }: { children: React.ReactNode }) {
  const { token, isLoading } = useAuth();
  if (isLoading) return <Loading label="Chargement…" />;
  if (token) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}
