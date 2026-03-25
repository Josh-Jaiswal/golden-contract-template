import "./Toast.css";

export function Toast({ toast }) {
  if (!toast) return null;
  return (
    <div className={`toast toast--${toast.type} ${toast.visible ? "toast--show" : ""}`}>
      <span className="toast-indicator" />
      <span className="toast-msg">{toast.message}</span>
    </div>
  );
}
