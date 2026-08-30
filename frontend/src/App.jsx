import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout.jsx";
import ActionsPage from "./pages/ActionsPage.jsx";
import AlertsPage from "./pages/AlertsPage.jsx";
import AlertInvestigationPage from "./pages/AlertInvestigationPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import AssistantPage from "./pages/AssistantPage.jsx";

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="alerts/:alertKey" element={<AlertInvestigationPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="actions" element={<ActionsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
