import { cn, formatNumber, gradeColor, severityBgColor, severityColor } from "@/lib/utils";

// ── cn ────────────────────────────────────────────────────────────────────────

describe("cn", () => {
  it("returns a string", () => {
    expect(typeof cn("a")).toBe("string");
  });

  it("merges multiple class strings", () => {
    const result = cn("foo", "bar");
    expect(result).toContain("foo");
    expect(result).toContain("bar");
  });

  it("handles falsy values without throwing", () => {
    expect(() => cn("a", false, undefined, null as never)).not.toThrow();
  });

  it("deduplicates conflicting Tailwind classes (last wins)", () => {
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });

  it("returns empty string for no arguments", () => {
    expect(cn()).toBe("");
  });
});

// ── formatNumber ──────────────────────────────────────────────────────────────

describe("formatNumber", () => {
  it("returns plain string for values under 1000", () => {
    expect(formatNumber(0)).toBe("0");
    expect(formatNumber(999)).toBe("999");
  });

  it("formats thousands with K suffix", () => {
    expect(formatNumber(1000)).toBe("1.0K");
    expect(formatNumber(1500)).toBe("1.5K");
  });

  it("formats millions with M suffix", () => {
    expect(formatNumber(1_000_000)).toBe("1.0M");
    expect(formatNumber(2_500_000)).toBe("2.5M");
  });

  it("boundary: 999 has no suffix, 1000 gets K", () => {
    expect(formatNumber(999)).not.toContain("K");
    expect(formatNumber(1000)).toContain("K");
  });

  it("boundary: 999999 gets K, 1000000 gets M", () => {
    expect(formatNumber(999_999)).toContain("K");
    expect(formatNumber(1_000_000)).toContain("M");
  });
});

// ── gradeColor ────────────────────────────────────────────────────────────────

describe("gradeColor", () => {
  it("A → text-success", () => expect(gradeColor("A")).toBe("text-success"));
  it("B → green class", () => expect(gradeColor("B")).toContain("green"));
  it("C → warning class", () => expect(gradeColor("C")).toContain("warning"));
  it("D → orange class", () => expect(gradeColor("D")).toContain("orange"));
  it("F → destructive class", () => expect(gradeColor("F")).toContain("destructive"));
  it("unknown → muted class", () => expect(gradeColor("Z")).toContain("muted"));
});

// ── severityColor ─────────────────────────────────────────────────────────────

describe("severityColor", () => {
  it("critical → destructive", () => expect(severityColor("critical")).toContain("destructive"));
  it("high → orange", () => expect(severityColor("high")).toContain("orange"));
  it("medium → warning", () => expect(severityColor("medium")).toContain("warning"));
  it("low → muted", () => expect(severityColor("low")).toContain("muted"));
  it("unknown → muted", () => expect(severityColor("unknown")).toContain("muted"));
});

// ── severityBgColor ───────────────────────────────────────────────────────────

describe("severityBgColor", () => {
  it("critical → destructive bg", () => expect(severityBgColor("critical")).toContain("destructive"));
  it("high → orange bg", () => expect(severityBgColor("high")).toContain("orange"));
  it("medium → warning bg", () => expect(severityBgColor("medium")).toContain("warning"));
  it("low → muted bg", () => expect(severityBgColor("low")).toContain("muted"));
  it("unknown → muted bg", () => expect(severityBgColor("unknown")).toContain("muted"));
});
