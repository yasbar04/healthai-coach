import React from "react";

export default function Card({
  title,
  icon,
  children,
}: {
  title: string;
  icon?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="card" aria-label={title}>
      <h2 className="card-title">
        {icon && <span className="card-title-icon" aria-hidden="true">{icon}</span>}
        {title}
      </h2>
      {children}
    </section>
  );
}
