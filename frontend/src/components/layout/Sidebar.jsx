import {
  Activity,
  BellRing,
  LayoutDashboard,
  ListChecks,
  Sparkles,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const navigationItems = [
  { label: "Visão Geral", path: "/", icon: LayoutDashboard, end: true },
  { label: "Alertas", path: "/alerts", icon: BellRing },
  { label: "OpsMind AI", path: "/assistant", icon: Sparkles },
  { label: "Ações", path: "/actions", icon: ListChecks },
];

function Sidebar({ isOpen, onNavigate }) {
  return (
    <aside className={`sidebar ${isOpen ? "is-open" : ""}`}>
      <div className="sidebar-brand">
        <span className="brand-symbol" aria-hidden="true">
          <Activity size={21} strokeWidth={2.4} />
        </span>
        <span>
          <strong>OpsMind</strong>
          <small>Inteligência Operacional</small>
        </span>
      </div>

      <nav className="sidebar-nav" aria-label="Navegação principal">
        <p className="sidebar-section-label">Navegação</p>
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.end}
              onClick={onNavigate}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? "active" : ""}`
              }
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="environment-card">
        <span className="environment-icon" aria-hidden="true">
          <span />
        </span>
        <span>
          <strong>Ambiente de Demonstração</strong>
          <small>Dados operacionais sintéticos</small>
        </span>
      </div>
    </aside>
  );
}

export default Sidebar;
