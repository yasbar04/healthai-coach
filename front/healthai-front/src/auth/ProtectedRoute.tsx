import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import Loading from "../components/Loading";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, isLoading } = useAuth();
  if (isLoading) return <Loading label="Chargement de la session..." />;
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
