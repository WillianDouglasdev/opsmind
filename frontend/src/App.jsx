import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout.jsx";
import ActionsPage from "./pages/ActionsPage.jsx";
import AlertsPage from "./pages/AlertsPage.jsx";
import AlertInvestigationPage from "./pages/AlertInvestigationPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import AssistantPage from "./pages/AssistantPage.jsx";
import PipelinesPage from "./pages/PipelinesPage.jsx";
import OperationPage from "./pages/OperationPage.jsx";
import OperationDelaysPage from "./pages/OperationDelaysPage.jsx";
import OperationBranchPage from "./pages/OperationBranchPage.jsx";
import InvestigationsPage from "./pages/InvestigationsPage.jsx";
import DeliveryDelayInvestigationPage from "./pages/DeliveryDelayInvestigationPage.jsx";

function App() {
  // O layout é compartilhado entre páginas. Uma nova rota também precisa de título
  // em AppLayout e, quando navegável pelo menu, de entrada em Sidebar.
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="alerts/:alertKey" element={<AlertInvestigationPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="actions" element={<ActionsPage />} />
        <Route path="pipelines" element={<PipelinesPage />} />
        <Route path="operation" element={<OperationPage />} />
        <Route path="operation/delays" element={<OperationDelaysPage />} />
        <Route path="operation/branches/:branchId" element={<OperationBranchPage />} />
        <Route path="investigations" element={<InvestigationsPage />} />
        <Route path="investigations/delivery-delays" element={<DeliveryDelayInvestigationPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
