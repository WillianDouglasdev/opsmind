const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("pt-BR");

const percentageFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  signDisplay: "always",
});

const unsignedPercentageFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

const brazilDateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  timeZone: "America/Sao_Paulo",
});

const dateTimeFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatCurrency(value) {
  return currencyFormatter.format(Number(value));
}

export function formatNumber(value) {
  return numberFormatter.format(Number(value));
}

export function formatPercentage(value, includeSign = true) {
  if (value === null || value === undefined) return "Sem base";
  if (includeSign) return `${percentageFormatter.format(Number(value))}%`;

  return `${unsignedPercentageFormatter.format(Number(value))}%`;
}

export function formatDate(value) {
  // O meio-dia em UTC evita que uma data sem horário recue um dia no fuso brasileiro.
  const normalizedValue = typeof value === "string" ? `${value}T12:00:00Z` : value;
  return dateFormatter.format(new Date(normalizedValue));
}

export function formatBrazilDate(value) {
  return brazilDateFormatter.format(new Date(value));
}

export function formatDateTime(value) {
  return dateTimeFormatter.format(new Date(value));
}
