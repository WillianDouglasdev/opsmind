import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { getHealth } from "../../services/api.js";
import Sidebar from "./Sidebar.jsx";
import Topbar from "./Topbar.jsx";

const pageDetails = {
  "/": {
    title: "Visão Geral da Operação",
    subtitle: "Monitore desempenho, riscos e sinais da operação.",
  },
  "/alerts": {
    title: "Alertas Operacionais",
    subtitle: "Sinais detectados automaticamente a partir dos dados da operação.",
  },
  "/actions": {
    title: "Plano de Ação",
    subtitle: "Acompanhe as ações geradas a partir dos sinais identificados na operação.",
  },
  "/assistant": {
    title: "OpsMind AI",
    subtitle: "Consulte os dados da operação usando linguagem natural.",
  },
};

function AppLayout() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState("checking");
  const currentPage = location.pathname.startsWith("/alerts/")
    ? {
        title: "Investigação Operacional",
        subtitle: "Analise impacto, evidências e fatores associados ao alerta.",
      }
    : pageDetails[location.pathname] ?? pageDetails["/"];

  useEffect(() => {
    let isActive = true;

    getHealth()
      .then(() => {
        if (isActive) setApiStatus("online");
      })
      .catch(() => {
        if (isActive) setApiStatus("offline");
      });

    return () => {
      isActive = false;
    };
  }, []);

  return (
    <div className="app-shell">
      <Sidebar
        isOpen={sidebarOpen}
        onNavigate={() => setSidebarOpen(false)}
      />

      {sidebarOpen && (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Fechar navegação"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="app-content">
        <Topbar
          title={currentPage.title}
          subtitle={currentPage.subtitle}
          apiStatus={apiStatus}
          onMenuClick={() => setSidebarOpen(true)}
        />
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
