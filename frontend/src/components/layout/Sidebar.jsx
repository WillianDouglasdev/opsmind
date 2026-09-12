import { Activity, ArrowLeftRight, BellRing, Database, GitBranch, LayoutDashboard, ListChecks, MessagesSquare, Search, ShieldCheck, X } from "lucide-react";
import { NavLink } from "react-router-dom";
import { demoMetadata } from "../../data/demoMetadata.js";
import { formatRelativeTime } from "../../utils/formatters.js";

const groups = [
  { label: "Hoje", items: [{ label: "Visão geral", path: "/", Icon: LayoutDashboard, end: true }, { label: "Operação", path: "/operation", Icon: ArrowLeftRight }] },
  { label: "Decisões", items: [{ label: "Alertas", path: "/alerts", Icon: BellRing }, { label: "Investigações", Icon: Search }, { label: "Ações", path: "/actions", Icon: ListChecks }] },
  { label: "Dados", items: [{ label: "Pipelines", path: "/pipelines", Icon: GitBranch }, { label: "Qualidade", Icon: ShieldCheck }, { label: "Fontes", Icon: Database }] },
  { label: "IA", items: [{ label: "Assistente", path: "/assistant", Icon: MessagesSquare }] },
];

export default function Sidebar({ isOpen, isMobile, onNavigate, sidebarRef, closeRef, pipeline }) {
  const latest = pipeline?.latest_run;
  const statusTone = latest?.status ?? (pipeline === undefined ? "running" : "empty");
  const statusLabel = latest?.status === "failed" ? "Pipeline com falha"
    : latest?.status === "running" ? "Pipeline em execução"
      : latest ? "Pedidos publicados" : pipeline === undefined ? "Consultando dados" : "Pipeline nunca executada";
  const freshness = pipeline?.last_published_at
    ? `Publicados ${formatRelativeTime(pipeline.last_published_at)}`
    : pipeline === undefined ? "Consultando monitoramento" : "Sem publicação registrada";
  return (
    <aside id="main-navigation" ref={sidebarRef} className={"sidebar " + (isOpen ? "is-open" : "")}
      role={isMobile && isOpen ? "dialog" : undefined} aria-modal={isMobile && isOpen ? true : undefined}
      aria-label="Navegação do OpsMind2" inert={isMobile && !isOpen}>
      <div className="sidebar-brand">
        <NavLink to="/" onClick={onNavigate} aria-label="OpsMind2 — Visão geral"><Activity size={25} strokeWidth={2} aria-hidden="true" /><strong>OpsMind<span>2</span></strong></NavLink>
        <button ref={closeRef} className="sidebar-close" type="button" onClick={onNavigate} aria-label="Fechar navegação"><X size={20} aria-hidden="true" /></button>
      </div>
      <p className="sidebar-product-label">Inteligência operacional</p>
      <nav className="sidebar-nav" aria-label="Navegação principal">
        {groups.map((group) => <div className="nav-group" key={group.label}><p className="sidebar-section-label">{group.label}</p>{group.items.map(({ label, path, Icon, end }) => (
          // Itens futuros não fingem ser links. Investigações atuais continuam
          // acessíveis pelos alertas; este item reserva a futura lista persistida.
          path ? <NavLink key={label} to={path} end={end} onClick={onNavigate} className={({ isActive }) => "sidebar-link" + (isActive ? " active" : "")}><Icon size={16} aria-hidden="true" /><span>{label}</span></NavLink>
            : <span key={label} className="sidebar-link future" aria-disabled="true"><Icon size={16} aria-hidden="true" /><span>{label}</span><small>Em breve</small></span>
        ))}</div>)}
      </nav>
      <div className={`sidebar-data-status ${statusTone}`}><span className="sidebar-status-label"><i aria-hidden="true" />{statusLabel}</span><p>{freshness}</p><small>{demoMetadata.organization}</small></div>
    </aside>
  );
}
