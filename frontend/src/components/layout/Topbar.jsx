import { Menu } from "lucide-react";
import { Link } from "react-router-dom";
import { demoMetadata } from "../../data/demoMetadata.js";
import ThemeToggle from "./ThemeToggle.jsx";

const statusLabels = { checking: "Verificando conexão", online: "API disponível", offline: "API indisponível" };

export default function Topbar({ title, apiStatus, onMenuClick, menuRef, sidebarOpen }) {
  return (
    <header className="topbar">
      <div className="topbar-heading">
        <button ref={menuRef} className="mobile-menu-button" type="button" aria-label="Abrir navegação" aria-expanded={sidebarOpen} aria-controls="main-navigation" onClick={onMenuClick}><Menu size={21} aria-hidden="true" /></button>
        <nav className="topbar-breadcrumb" aria-label="Seção atual"><Link to="/">OpsMind2</Link><span aria-hidden="true">/</span><span aria-current="page">{title}</span></nav>
      </div>
      <div className="topbar-meta"><span className={"connection-status " + apiStatus} role="status"><i aria-hidden="true" />{statusLabels[apiStatus]}</span><ThemeToggle /><span className="demo-tag">{demoMetadata.label}</span></div>
    </header>
  );
}
