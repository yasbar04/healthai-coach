import React from "react";

export default function FormField(props: {
  id: string;
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  const hintId = props.hint ? `${props.id}-hint` : undefined;
  return (
    <div className="form-field">
      <label htmlFor={props.id} className="form-label">{props.label}</label>
      {props.hint && <div id={hintId} className="form-hint">{props.hint}</div>}
      <div aria-describedby={hintId}>{props.children}</div>
    </div>
  );
}
