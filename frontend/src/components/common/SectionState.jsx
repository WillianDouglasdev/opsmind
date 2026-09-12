import { RefreshCw } from "lucide-react";

// O mesmo estado atende seções pequenas e páginas: falha nunca se torna lista vazia.
export default function SectionState({ status, title, description, onRetry }) {
  return (
    <div className={`section-state ${status}`} role={status === "error" ? "alert" : "status"}>
      {status === "loading" && <span className="loading-line" aria-hidden="true" />}
      <strong>{title ?? (status === "loading" ? "Consultando dados…" : "Não foi possível carregar os dados.")}</strong>
      {description && <p>{description}</p>}
      {status === "error" && onRetry && (
        <button className="quiet-button" type="button" onClick={onRetry}>
          <RefreshCw size={14} aria-hidden="true" /> Tentar novamente
        </button>
      )}
    </div>
  );
}
