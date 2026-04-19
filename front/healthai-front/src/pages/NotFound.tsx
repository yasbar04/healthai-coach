import React from "react";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="container">
      <h1>Page introuvable</h1>
      <p><Link to="/">Retour au dashboard</Link></p>
    </div>
  );
}
