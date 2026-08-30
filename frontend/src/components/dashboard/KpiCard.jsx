import {
  ArrowDownRight,
  ArrowUpRight,
  CircleDollarSign,
  ClockAlert,
  Minus,
  PackageCheck,
  TicketCheck,
} from "lucide-react";

const iconMap = {
  revenue: CircleDollarSign,
  orders: PackageCheck,
  delays: ClockAlert,
  tickets: TicketCheck,
};

function KpiCard({ metric }) {
  const Icon = iconMap[metric.id] ?? PackageCheck;
  const isDown = metric.direction === "down";
  const TrendIcon = metric.direction === "neutral"
    ? Minus
    : isDown
      ? ArrowDownRight
      : ArrowUpRight;

  return (
    <article className="panel kpi-card">
      <div className="kpi-heading">
        <span className={`kpi-icon ${metric.id}`}>
          <Icon size={19} />
        </span>
        <span className="kpi-label">{metric.label}</span>
      </div>
      <p className="kpi-value">{metric.value}</p>
      <div className="metric-change-row">
        {metric.change && (
          <span className={`metric-change ${metric.tone ?? metric.direction}`}>
            <TrendIcon size={14} />
            {metric.change}
          </span>
        )}
        <span>{metric.context}</span>
      </div>
    </article>
  );
}

export default KpiCard;
