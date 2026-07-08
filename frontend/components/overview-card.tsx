type OverviewCardProps = {
  label: string;
  value: string;
  detail: string;
};

export function OverviewCard({ label, value, detail }: OverviewCardProps) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 20,
        padding: 20,
        backdropFilter: "blur(10px)"
      }}
    >
      <p style={{ margin: 0, color: "var(--muted)", fontSize: 12, letterSpacing: "0.08em", textTransform: "uppercase" }}>
        {label}
      </p>
      <p style={{ margin: "12px 0 8px", fontSize: 34 }}>{value}</p>
      <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.5 }}>{detail}</p>
    </div>
  );
}

