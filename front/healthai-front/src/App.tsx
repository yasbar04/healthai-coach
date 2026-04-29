import React from "react";
import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "./auth/ProtectedRoute";
import AdminRoute from "./auth/AdminRoute";
import PublicRoute from "./auth/PublicRoute";
import Layout from "./components/Layout";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Activities from "./pages/Activities";
import Nutrition from "./pages/Nutrition";
import EtlQuality from "./pages/EtlQuality";
import Users from "./pages/Users";
import DailyLog from "./pages/DailyLog";
import Analytics from "./pages/Analytics";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <Routes>
      {/* Public-only routes — redirect to /dashboard if already logged in */}
      <Route path="/" element={<PublicRoute><Landing /></PublicRoute>} />
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />

      {/* Protected app — pathless layout wrapper */}
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/daily-log" element={<DailyLog />} />
        <Route path="/activities" element={<Activities />} />
        <Route path="/nutrition" element={<Nutrition />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/users" element={<AdminRoute><Users /></AdminRoute>} />
        <Route path="/etl" element={<AdminRoute><EtlQuality /></AdminRoute>} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
