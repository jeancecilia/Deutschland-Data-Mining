import type { CSSProperties, ReactNode } from "react";

type PanelProps = {
  title: string;
  description?: string;
  meta?: string;
  children: ReactNode;
};

export function PageHeader({
  eyebrow,
  title,
  description
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <header
      style={{
        padding: 28,
        borderRadius: 28,
        background: "var(--surface-strong)",
        border: "1px solid var(--border)",
        boxShadow: "0 24px 60px rgba(70, 53, 24, 0.08)",
        display: "grid",
        gap: 14
      }}
    >
      <p
        style={{
          margin: 0,
          color: "var(--muted)",
          textTransform: "uppercase",
          letterSpacing: "0.12em",
          fontSize: 12
        }}
      >
        {eyebrow}
      </p>
      <h2 style={{ margin: 0, fontSize: "clamp(2rem, 4vw, 3.8rem)", lineHeight: 0.95 }}>{title}</h2>
      <p style={{ margin: 0, maxWidth: 780, color: "var(--muted)", lineHeight: 1.6, fontSize: 18 }}>
        {description}
      </p>
    </header>
  );
}

export function Panel({ title, description, meta, children }: PanelProps) {
  return (
    <section style={panelStyle}>
      <div style={panelHeaderStyle}>
        <div>
          <h3 style={{ margin: 0, fontSize: 24 }}>{title}</h3>
          {description ? (
            <p style={{ margin: "8px 0 0", color: "var(--muted)", lineHeight: 1.6 }}>{description}</p>
          ) : null}
        </div>
        {meta ? <span style={metricBadgeStyle}>{meta}</span> : null}
      </div>
      <div style={{ display: "grid", gap: 12, marginTop: 22 }}>{children}</div>
    </section>
  );
}

export function EmptyState({ text }: { text: string }) {
  return (
    <div
      style={{
        border: "1px dashed var(--border)",
        borderRadius: 18,
        padding: 18,
        color: "var(--muted)"
      }}
    >
      {text}
    </div>
  );
}

export function CompactList({ items, emptyText }: { items: string[]; emptyText: string }) {
  if (items.length === 0) {
    return <span style={{ color: "var(--muted)", fontSize: 14 }}>{emptyText}</span>;
  }

  return (
    <div style={{ display: "grid", gap: 6 }}>
      {items.map((item, index) => (
        <span key={`${item}-${index}`} style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
          {item}
        </span>
      ))}
    </div>
  );
}

export function MetricTile({ label, value }: { label: string; value: number | string | null }) {
  return (
    <div style={metricTileStyle}>
      <span
        style={{
          color: "var(--muted)",
          fontSize: 12,
          textTransform: "uppercase",
          letterSpacing: "0.08em"
        }}
      >
        {label}
      </span>
      <strong style={{ fontSize: 18 }}>{value ?? "n/a"}</strong>
    </div>
  );
}

export function Badge({ children }: { children: ReactNode }) {
  return <span style={pillStyle}>{children}</span>;
}

export function MetricBadge({ children }: { children: ReactNode }) {
  return <span style={metricBadgeStyle}>{children}</span>;
}

export function ActionButton({
  children,
  primary = false
}: {
  children: ReactNode;
  primary?: boolean;
}) {
  return <button type="submit" style={primary ? primaryButtonStyle : secondaryButtonStyle}>{children}</button>;
}

export function ButtonLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a href={href} style={linkButtonStyle}>
      {children}
    </a>
  );
}

export function SignalList({
  items
}: {
  items: { label: string; summary: string; score: number; direction: string }[];
}) {
  if (items.length === 0) {
    return <span style={{ color: "var(--muted)", fontSize: 14 }}>No signals stored yet.</span>;
  }

  return (
    <div style={{ display: "grid", gap: 8 }}>
      {items.map((item, index) => (
        <div
          key={`${item.label}-${index}`}
          style={{
            border: "1px solid var(--border)",
            borderRadius: 14,
            padding: "12px 14px",
            background: item.direction === "negative" ? "rgba(179, 64, 24, 0.08)" : "rgba(40, 92, 77, 0.08)"
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
            <strong style={{ fontSize: 14 }}>{item.label}</strong>
            <span style={metricBadgeStyle}>
              {item.direction} {item.score}
            </span>
          </div>
          <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>{item.summary}</span>
        </div>
      ))}
    </div>
  );
}

export function scoreBadgeStyle(score: number | null): CSSProperties {
  const background =
    score === null ? "#fff" : score >= 65 ? "#dcefd8" : score >= 40 ? "#f4ebc8" : "#f5d7d7";
  const color =
    score === null ? "var(--muted)" : score >= 65 ? "#2d6b2f" : score >= 40 ? "#8a6500" : "#8a2323";

  return {
    borderRadius: 999,
    padding: "8px 12px",
    background,
    color,
    fontSize: 13,
    fontWeight: 700,
    width: "fit-content"
  };
}

export function decisionBadgeStyle(decision: string): CSSProperties {
  if (decision === "GO") {
    return {
      ...pillStyle,
      background: "#dcefd8",
      color: "#2d6b2f"
    };
  }

  if (decision === "MAYBE") {
    return {
      ...pillStyle,
      background: "#f4ebc8",
      color: "#8a6500"
    };
  }

  return {
    ...pillStyle,
    background: "#f5d7d7",
    color: "#8a2323"
  };
}

export function formatDateLabel(value: string | null | undefined): string {
  if (!value) {
    return "n/a";
  }

  return new Date(value).toLocaleString("de-DE", {
    dateStyle: "short",
    timeStyle: "short"
  });
}

export const panelStyle = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: 24,
  padding: 24,
  backdropFilter: "blur(10px)"
} satisfies CSSProperties;

export const panelHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 16,
  flexWrap: "wrap"
} satisfies CSSProperties;

export const primaryButtonStyle = {
  border: 0,
  borderRadius: 14,
  padding: "12px 16px",
  background: "var(--accent)",
  color: "#fff",
  font: "inherit",
  cursor: "pointer"
} satisfies CSSProperties;

export const secondaryButtonStyle = {
  borderRadius: 12,
  border: "1px solid var(--border)",
  padding: "10px 14px",
  background: "#fff",
  font: "inherit",
  cursor: "pointer"
} satisfies CSSProperties;

export const linkButtonStyle = {
  borderRadius: 12,
  border: "1px solid var(--border)",
  padding: "10px 14px",
  background: "#fff",
  color: "inherit",
  font: "inherit",
  textDecoration: "none",
  width: "fit-content"
} satisfies CSSProperties;

export const metricBadgeStyle = {
  borderRadius: 999,
  border: "1px solid var(--border)",
  padding: "8px 12px",
  background: "#fff",
  color: "var(--muted)",
  fontSize: 13,
  width: "fit-content"
} satisfies CSSProperties;

export const metricTileStyle = {
  display: "grid",
  gap: 6,
  borderRadius: 16,
  border: "1px solid var(--border)",
  padding: 12,
  background: "#fff"
} satisfies CSSProperties;

export const pillStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  width: "fit-content",
  borderRadius: 999,
  background: "var(--accent-soft)",
  color: "var(--accent)",
  padding: "6px 10px",
  fontSize: 12,
  textTransform: "uppercase",
  letterSpacing: "0.06em"
} satisfies CSSProperties;

export const sectionLabelStyle = {
  color: "var(--muted)",
  fontSize: 12,
  textTransform: "uppercase",
  letterSpacing: "0.08em"
} satisfies CSSProperties;
