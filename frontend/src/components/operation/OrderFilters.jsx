const statuses = [
  ["", "Todos os status"], ["pending", "Pendente"], ["processing", "Em processamento"],
  ["shipped", "Enviado"], ["delivered", "Entregue"], ["delayed", "Atrasado"],
  ["cancelled", "Cancelado"],
];

export default function OrderFilters({ filters, branches = [], showBranch = true, onChange }) {
  return (
    <div className="operation-filters" aria-label="Filtros de pedidos">
      {showBranch && <label><span>Filial</span><select value={filters.branch} onChange={(event) => onChange({ branch: event.target.value })}><option value="">Todas as filiais</option>{branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.name}</option>)}</select></label>}
      <label><span>Status</span><select value={filters.status} onChange={(event) => onChange({ status: event.target.value })}>{statuses.map(([value, label]) => <option value={value} key={value || "all"}>{label}</option>)}</select></label>
      <label><span>Entrega</span><select value={filters.delivery} onChange={(event) => onChange({ delivery: event.target.value })}><option value="all">Todas as situações</option><option value="late">Atrasados no KPI</option></select></label>
    </div>
  );
}
