import { CalendarDays, Menu, Wifi, WifiOff } from "lucide-react";
import { formatBrazilDate } from "../../utils/formatters.js";

const statusContent = {
  checking: { label: "Verificando API", className: "checking", Icon: Wifi },
  online: { label: "Sistema Online", className: "online", Icon: Wifi },
  offline: { label: "API Offline", className: "offline", Icon: WifiOff },
};

function Topbar({ title, subtitle, apiStatus, onMenuClick }) {
  const status = statusContent[apiStatus] ?? statusContent.checking;
  const StatusIcon = status.Icon;
  // O cabeçalho mostra o dia de uso; os indicadores continuam presos à data da demo.
  const currentDate = formatBrazilDate(new Date());

  return (
    <header className="topbar">
      <div className="topbar-heading">
        <button
          className="mobile-menu-button"
          type="button"
          aria-label="Abrir navegação"
          onClick={onMenuClick}
        >
          <Menu size={21} />
        </button>
        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </div>

      <div className="topbar-meta">
        <span className="date-label">
          <CalendarDays size={16} />
          {currentDate}
        </span>
        <span className={`api-status ${status.className}`}>
          <StatusIcon size={15} />
          {status.label}
        </span>
      </div>
    </header>
  );
}

export default Topbar;
