import React, { useState, useEffect } from "react";

interface ErrorBannerProps {
  message: string;
  onClose?: () => void;
  autoClose?: number; // milliseconds
}

export default function ErrorBanner({ message, onClose, autoClose }: ErrorBannerProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (!autoClose) return;
    const timeout = setTimeout(() => {
      setVisible(false);
      onClose?.();
    }, autoClose);
    return () => clearTimeout(timeout);
  }, [autoClose, onClose]);

  if (!visible) return null;

  return (
    <div role="alert" className="error-banner">
      <div className="error-banner-content">
        <span className="error-banner-icon" aria-hidden="true">⚠️</span>
        <span><strong>Erreur :</strong> {message}</span>
      </div>
      <button
        className="error-banner-close"
        onClick={() => {
          setVisible(false);
          onClose?.();
        }}
        aria-label="Fermer l'alerte"
      >
        ✕
      </button>
    </div>
  );
}
