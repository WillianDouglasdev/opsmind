import { operationPeriods } from "../../utils/operation.js";

export default function PeriodSelector({ value, onChange }) {
  return (
    <div className="operation-period-selector" aria-label="Período da operação">
      {operationPeriods.map((days) => <button key={days} type="button" aria-pressed={value === days} onClick={() => onChange(days)}>{days} dias</button>)}
    </div>
  );
}
