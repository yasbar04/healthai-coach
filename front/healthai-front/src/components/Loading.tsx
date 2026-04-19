import React from "react";

export default function Loading({ label = "Chargement..." }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="loading-wrap">
      <div className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
