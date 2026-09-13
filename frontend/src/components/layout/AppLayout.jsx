import { useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { getHealth, getPipelines } from "../../services/api.js";
import Sidebar from "./Sidebar.jsx";
import SiteFooter from "./SiteFooter.jsx";
import Topbar from "./Topbar.jsx";

const pageDetails = {
  "/": { title: "Visão geral" },
  "/alerts": { title: "Alertas", subtitle: "Os sinais que merecem um olhar mais próximo." },
  "/actions": { title: "Plano de ação", subtitle: "Do sinal identificado ao trabalho em andamento." },
  "/assistant": { title: "Assistente", subtitle: "Pergunte sobre a operação. Confira as evidências." },
  "/pipelines": { title: "Pipelines", subtitle: "Acompanhe como os pedidos chegam à base operacional." },
  "/operation": { title: "Operação", subtitle: "Encontre onde estão os desvios e abra os dados por trás deles." },
  "/operation/delays": { title: "Atrasos", subtitle: "Veja onde os pedidos atrasados se concentram." },
  "/investigations": { title: "Investigações", subtitle: "Organize os fatos relacionados aos sinais operacionais." },
  "/investigations/delivery-delays": { title: "Investigação", subtitle: "Examine evidências relacionadas aos atrasos sem atribuir causalidade." },
};

export default function AppLayout() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(() => window.matchMedia("(max-width: 991.98px)").matches);
  const [apiStatus, setApiStatus] = useState("checking");
  const [pipelineSummary, setPipelineSummary] = useState(undefined);
  const menuRef = useRef(null);
  const closeRef = useRef(null);
  const sidebarRef = useRef(null);
  const isHome = location.pathname === "/";
  const currentPage = location.pathname.startsWith("/alerts/")
    ? { title: "Investigação", subtitle: "Entenda o impacto e os sinais relacionados." }
    : location.pathname.startsWith("/operation/branches/")
      ? { title: "Detalhe da filial", subtitle: "Compare a unidade e examine os pedidos do período." }
    : pageDetails[location.pathname] ?? pageDetails["/"];

  useEffect(() => {
    const controller = new AbortController();
    getHealth({ signal: controller.signal }).then(() => {
      if (!controller.signal.aborted) setApiStatus("online");
    }).catch((error) => {
      if (!controller.signal.aborted) {
        setApiStatus("offline");
        if (import.meta.env.DEV) console.error("[OpsMind] Health check indisponível", error);
      }
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    getPipelines({ signal: controller.signal })
      .then((pipelines) => setPipelineSummary(pipelines.find((item) => item.pipeline_key === "orders") ?? null))
      .catch((error) => {
        if (!controller.signal.aborted) {
          setPipelineSummary(null);
          if (import.meta.env.DEV) console.error("[OpsMind] Monitoramento da pipeline indisponível", error);
        }
      });
    return () => controller.abort();
  }, [location.pathname]);

  useEffect(() => {
    // Mesmo breakpoint do CSS: ao voltar ao desktop, desfazemos o estado do drawer.
    const query = window.matchMedia("(max-width: 991.98px)");
    const update = (event) => { setIsMobile(event.matches); setSidebarOpen(false); };
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (!isMobile || !sidebarOpen) return undefined;
    const previousOverflow = document.body.style.overflow;
    const menuButton = menuRef.current;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    // O conteúdo fica inert enquanto o drawer está aberto. Tab circula apenas
    // na navegação; Escape fecha e o foco retorna ao botão que abriu o menu.
    const onKeyDown = (event) => {
      if (event.key === "Escape") { event.preventDefault(); setSidebarOpen(false); }
      if (event.key !== "Tab") return;
      const items = [...sidebarRef.current.querySelectorAll("a[href], button:not([disabled])")].filter((item) => item.offsetParent !== null);
      const first = items[0];
      const last = items[items.length - 1];
      if (!sidebarRef.current.contains(document.activeElement)) { event.preventDefault(); (event.shiftKey ? last : first)?.focus(); }
      else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
      menuButton?.focus();
    };
  }, [isMobile, sidebarOpen]);

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content" inert={isMobile && sidebarOpen}>Pular para o conteúdo</a>
      <Sidebar isOpen={sidebarOpen} isMobile={isMobile} onNavigate={() => setSidebarOpen(false)} sidebarRef={sidebarRef} closeRef={closeRef} pipeline={pipelineSummary} />
      {isMobile && sidebarOpen && <div className="sidebar-backdrop" aria-hidden="true" onClick={() => setSidebarOpen(false)} />}
      <div className="app-content" inert={isMobile && sidebarOpen}>
        <Topbar title={currentPage.title} apiStatus={apiStatus} onMenuClick={() => setSidebarOpen(true)} menuRef={menuRef} sidebarOpen={sidebarOpen} />
        <main id="main-content" className="page-content" tabIndex={-1}>
          {!isHome && <header className="page-heading"><p className="eyebrow">Central de inteligência operacional</p><h1>{currentPage.title}</h1><p>{currentPage.subtitle}</p></header>}
          <Outlet />
        </main>
        <SiteFooter />
      </div>
    </div>
  );
}
