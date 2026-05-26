import {
  getProject,
  getAnalysis,
  getDebtItems,
  getDependencies,
  getRecommendations,
} from "@/lib/api-client";

const ACCENT = [79, 70, 229] as const;
const RED    = [220, 38, 38] as const;
const AMBER  = [217, 119, 6] as const;
const GRAY   = [107, 114, 128] as const;
const LGRAY  = [243, 244, 246] as const;
const BLACK  = [17, 24, 39] as const;

const SEVERITY_RGB: Record<string, readonly [number, number, number]> = {
  critical: RED,
  high: [249, 115, 22],
  medium: AMBER,
  low: GRAY,
};

const DIMENSION_LABELS: Record<string, string> = {
  code_health: "Code Health",
  dependency_health: "Dependency Health",
  architecture_quality: "Architecture Quality",
  test_coverage: "Test Coverage",
  documentation: "Documentation",
  infrastructure_readiness: "Infrastructure Readiness",
  security_posture: "Security Posture",
};

function scoreColor(score: number): readonly [number, number, number] {
  if (score >= 80) return [34, 197, 94];
  if (score >= 60) return [234, 179, 8];
  if (score >= 40) return [249, 115, 22];
  return RED;
}

function trunc(str: string, max: number): string {
  if (!str) return "";
  return str.length > max ? str.slice(0, max - 1) + "…" : str;
}

const IBM_PLEX_REGULAR_URL = "https://cdn.jsdelivr.net/npm/@ibm/plex@6.4.0/IBM-Plex-Sans/fonts/complete/ttf/IBMPlexSans-Regular.ttf";
const IBM_PLEX_BOLD_URL    = "https://cdn.jsdelivr.net/npm/@ibm/plex@6.4.0/IBM-Plex-Sans/fonts/complete/ttf/IBMPlexSans-Bold.ttf";

let _ibmPlexCache: { regular: string; bold: string } | null = null;

async function fetchAsBase64(url: string): Promise<string> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`fetch ${url} -> ${res.status}`);
  const buf = await res.arrayBuffer();
  const bytes = new Uint8Array(buf);
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode.apply(null, Array.from(bytes.subarray(i, i + chunk)));
  }
  return btoa(binary);
}

async function loadIBMPlex(): Promise<{ regular: string; bold: string } | null> {
  if (_ibmPlexCache) return _ibmPlexCache;
  try {
    const [regular, bold] = await Promise.all([
      fetchAsBase64(IBM_PLEX_REGULAR_URL),
      fetchAsBase64(IBM_PLEX_BOLD_URL),
    ]);
    _ibmPlexCache = { regular, bold };
    return _ibmPlexCache;
  } catch {
    return null;
  }
}

async function fetchAllDebt(projectId: string) {
  const first = await getDebtItems(projectId, 0, 100).catch(() => null);
  if (!first) return null;
  const total = first.total ?? 0;
  const all = [...(first.debt_items ?? [])];
  let skip = 100;
  const MAX_FETCH = 2000;
  while (skip < total && skip < MAX_FETCH) {
    const page = await getDebtItems(projectId, skip, 100).catch(() => null);
    if (!page || !page.debt_items?.length) break;
    all.push(...page.debt_items);
    skip += 100;
  }
  return {
    debt_items: all,
    total,
    by_severity: first.by_severity,
    by_category: first.by_category,
  };
}

export async function downloadReport(projectId: string): Promise<void> {
  const [{ default: jsPDF }, proj, anal, debtRes, depsRes, recsRes] = await Promise.all([
    import("jspdf"),
    getProject(projectId),
    getAnalysis(projectId).catch(() => null),
    fetchAllDebt(projectId),
    getDependencies(projectId, 0, 100).catch(() => null),
    getRecommendations(projectId, 0, 20).catch(() => null),
  ]);

  if (!anal) {
    throw new Error("No completed analysis found. Run analysis first.");
  }

  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const W = doc.internal.pageSize.getWidth();
  const H = doc.internal.pageSize.getHeight();
  const ML = 40;
  const MR = W - 40;
  const CW = MR - ML;
  let y = 40;

  // Register IBM Plex Sans (graceful fallback to helvetica on load failure)
  let FONT: string = "helvetica";
  const fontData = await loadIBMPlex();
  if (fontData) {
    try {
      (doc as any).addFileToVFS("IBMPlexSans-Regular.ttf", fontData.regular);
      (doc as any).addFont("IBMPlexSans-Regular.ttf", "IBMPlex", "normal");
      (doc as any).addFileToVFS("IBMPlexSans-Bold.ttf", fontData.bold);
      (doc as any).addFont("IBMPlexSans-Bold.ttf", "IBMPlex", "bold");
      FONT = "IBMPlex";
    } catch {
      FONT = "helvetica";
    }
  }

  const newPage = () => { doc.addPage(); y = 40; };
  const checkY = (needed: number) => { if (y + needed > H - 40) newPage(); };

  // Header accent bar
  doc.setFillColor(...ACCENT);
  doc.rect(ML, y, CW, 4, "F");
  y += 20;

  // jsPDF coords = text BASELINE. Each row baseline = previous + fontSize + gap.
  // Row1: 24pt name   → baseline at y+22  (top ≈ y+4)
  // Row2: 10pt url    → baseline at y+22+18 = y+40
  // Row3:  9pt date   → baseline at y+40+14 = y+54
  const R1 = y + 22;
  const R2 = y + 40;
  const R3 = y + 54;

  // LEFT: project name
  doc.setFont(FONT, "bold");
  doc.setFontSize(24);
  doc.setTextColor(...BLACK);
  doc.text(trunc(proj?.name ?? "Unnamed Project", 42), ML, R1);

  // LEFT: repo URL
  doc.setFont(FONT, "normal");
  doc.setFontSize(10);
  doc.setTextColor(...GRAY);
  doc.text(trunc(proj?.repo_url ?? "", 60), ML, R2);

  // LEFT: date
  const dateStr = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
  doc.setFontSize(9);
  doc.text(`Generated ${dateStr}`, ML, R3);

  // RIGHT: CODELENS AI — baseline aligned with project name row
  doc.setFont(FONT, "bold");
  doc.setFontSize(22);
  doc.setTextColor(...ACCENT);
  doc.text("CODELENS AI", MR, R1, { align: "right" });

  // RIGHT: subtitle — baseline aligned with repo URL row
  doc.setFont(FONT, "normal");
  doc.setFontSize(9);
  doc.setTextColor(...GRAY);
  doc.text("AI-Powered Legacy Modernization", MR, R2, { align: "right" });

  y = R3 + 22;  // advance past header rows

  // Score badge
  if (anal?.overall_score != null) {
    const score = Math.round(anal.overall_score);
    const grade = anal.grade ?? "—";
    const [r, g, b] = scoreColor(score);

    const badgeW = 170;
    const badgeH = 68;
    doc.setFillColor(r, g, b);
    doc.roundedRect(ML, y, badgeW, badgeH, 6, 6, "F");

    // Tiny "SCORE" caption inside badge, top-left
    doc.setFont(FONT, "normal");
    doc.setFontSize(8);
    doc.setTextColor(255, 255, 255);
    doc.text("SCORE", ML + 14, y + 16);

    // Row 1: score number — large, left-aligned, no overflow
    doc.setFont(FONT, "bold");
    doc.setFontSize(28);
    doc.setTextColor(255, 255, 255);
    doc.text(`${score}%`, ML + 14, y + 44);

    // Row 2: grade on its own line, well below score baseline
    doc.setFont(FONT, "normal");
    doc.setFontSize(11);
    doc.setTextColor(230, 240, 255);
    doc.text(`Grade ${grade}`, ML + 14, y + 60);

    // Labels right-aligned outside badge
    doc.setFont(FONT, "normal");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    doc.text("MODERNIZATION SCORE", MR, y + 20, { align: "right" });
    doc.setFont(FONT, "bold");
    doc.setFontSize(14);
    doc.setTextColor(r, g, b);
    doc.text(`${score} / 100`, MR, y + 42, { align: "right" });
    doc.setFont(FONT, "normal");
    doc.setFontSize(10);
    doc.setTextColor(...GRAY);
    doc.text(`Grade ${grade}`, MR, y + 58, { align: "right" });

    y += badgeH + 14;
  } else {
    y += 10;
  }

  // Stats row
  const allDeps: any[] = depsRes?.dependencies ?? [];
  const vulnCount = allDeps.filter((d: any) => d.vulnerability_count > 0).length;
  const stats: Array<[string, string]> = [];
  if (proj?.total_files != null) stats.push(["Files", proj.total_files.toLocaleString()]);
  if (proj?.total_loc != null)   stats.push(["Lines of Code", proj.total_loc.toLocaleString()]);
  stats.push(["Debt Issues", String(debtRes?.total ?? 0)]);
  stats.push(["Dependencies", String(depsRes?.total ?? 0)]);
  if (vulnCount > 0) stats.push(["Vulnerable", String(vulnCount)]);

  if (stats.length > 0) {
    const boxW = Math.floor(CW / stats.length) - 4;
    stats.forEach(([label, value], idx) => {
      const bx = ML + idx * (boxW + 4);
      doc.setFillColor(...LGRAY);
      doc.roundedRect(bx, y, boxW, 36, 3, 3, "F");
      doc.setFont(FONT, "bold");
      doc.setFontSize(16);
      doc.setTextColor(...BLACK);
      doc.text(value, bx + 10, y + 22);
      doc.setFont(FONT, "normal");
      doc.setFontSize(8);
      doc.setTextColor(...GRAY);
      doc.text(label.toUpperCase(), bx + 10, y + 32);
    });
    y += 50;
  }

  // Executive summary
  const execSummary: string = anal?.summary?.executive_summary ?? "";
  if (execSummary) {
    checkY(40);
    // Set font BEFORE splitTextToSize so metrics match the render size
    doc.setFont(FONT, "normal");
    doc.setFontSize(11);
    const lineH = 15;
    const lines = doc.splitTextToSize(execSummary, CW - 24);
    const boxH = lines.length * lineH + 22;
    doc.setFillColor(240, 245, 255);
    doc.roundedRect(ML, y, CW, boxH, 3, 3, "F");
    doc.setFillColor(...ACCENT);
    doc.rect(ML, y, 3, boxH, "F");
    doc.setTextColor(...BLACK);
    lines.forEach((line: string, i: number) => doc.text(line, ML + 14, y + 16 + i * lineH));
    y += boxH + 14;
  }

  const sectionTitle = (title: string) => {
    checkY(40);
    y += 12; // top padding
    doc.setFont(FONT, "bold");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    doc.text(title.toUpperCase(), ML, y);
    y += 6;
    doc.setDrawColor(...LGRAY);
    doc.line(ML, y, MR, y);
    y += 16; // bottom padding
  };

  // Score breakdown — always render
  const subScores: Record<string, number> = anal?.sub_scores ?? {};
  sectionTitle("Score Breakdown");
  const subEntries = Object.entries(subScores);
  if (subEntries.length > 0) {
    const cols = 2;
    const colW = CW / cols;
    const subRowH = 26;
    for (let i = 0; i < subEntries.length; i += cols) {
      checkY(subRowH + 4);
      for (let c = 0; c < cols; c++) {
        const entry = subEntries[i + c];
        if (!entry) continue;
        const [key, val] = entry;
        const v = Number(val) || 0;
        const bx = ML + c * colW;
        doc.setFillColor(...LGRAY);
        doc.roundedRect(bx, y, colW - 6, subRowH, 2, 2, "F");
        doc.setFont(FONT, "normal");
        doc.setFontSize(11);
        doc.setTextColor(...BLACK);
        doc.text(DIMENSION_LABELS[key] ?? key, bx + 8, y + 17);
        const barX = bx + 150;
        const barW = colW - 200;
        doc.setFillColor(229, 231, 235);
        doc.roundedRect(barX, y + 10, barW, 6, 2, 2, "F");
        const [r, g, b] = scoreColor(v);
        doc.setFillColor(r, g, b);
        doc.roundedRect(barX, y + 10, barW * (v / 100), 6, 2, 2, "F");
        doc.setFont(FONT, "bold");
        doc.setFontSize(11);
        doc.setTextColor(r, g, b);
        doc.text(String(Math.round(v)), bx + colW - 14, y + 17, { align: "right" });
      }
      y += subRowH + 6;
    }
  } else {
    checkY(18);
    doc.setFont(FONT, "normal");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    doc.text("Score breakdown not available for this analysis.", ML, y + 10);
    y += 18;
  }
  y += 6;

  // Technical debt — always render
  const debtItems: any[] = debtRes?.debt_items ?? [];
  sectionTitle(`Technical Debt — ${debtRes?.total ?? debtItems.length} Issues`);

  if (debtItems.length > 0) {
    // ---- Category × Severity matrix ----
    const CATEGORIES: Array<{ key: string; label: string }> = [
      { key: "bug_risk",       label: "Bug Risk" },
      { key: "security",       label: "Security" },
      { key: "best_practices", label: "Best Practice" },
      { key: "code_style",     label: "Code Style" },
      { key: "documentation",  label: "Documentation" },
    ];
    const SEV_ROWS: Array<{ key: string; label: string }> = [
      { key: "critical", label: "Critical" },
      { key: "high",     label: "High" },
      { key: "medium",   label: "Medium" },
      { key: "low",      label: "Low" },
    ];

    const matrix: Record<string, Record<string, number>> = {};
    for (const s of SEV_ROWS) {
      matrix[s.key] = {};
      for (const c of CATEGORIES) matrix[s.key][c.key] = 0;
    }
    for (const it of debtItems) {
      const sev = String(it.severity ?? "").toLowerCase();
      const cat = String(it.category ?? "").toLowerCase();
      if (matrix[sev] && matrix[sev][cat] !== undefined) {
        matrix[sev][cat] += 1;
      }
    }

    const sevColW = 80;
    const catColW = (CW - sevColW) / CATEGORIES.length;
    const matrixHeaderH = 26;
    const matrixRowH    = 26;

    checkY(matrixHeaderH + SEV_ROWS.length * matrixRowH + 10);

    // Header row
    doc.setFillColor(...LGRAY);
    doc.rect(ML, y, CW, matrixHeaderH, "F");
    doc.setFont(FONT, "bold");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    doc.text("SEVERITY", ML + 8, y + 17);
    CATEGORIES.forEach((c, i) => {
      const cx = ML + sevColW + i * catColW + catColW / 2;
      doc.text(c.label.toUpperCase(), cx, y + 17, { align: "center" });
    });
    y += matrixHeaderH;

    // Severity rows
    SEV_ROWS.forEach((s, rowIdx) => {
      const [sr, sg, sb] = SEVERITY_RGB[s.key] ?? GRAY;
      if (rowIdx % 2 === 1) {
        doc.setFillColor(249, 250, 251);
        doc.rect(ML, y, CW, matrixRowH, "F");
      }
      // Severity pill in column 1
      doc.setFillColor(sr, sg, sb);
      doc.roundedRect(ML + 8, y + 5, 62, matrixRowH - 10, 2, 2, "F");
      doc.setFont(FONT, "bold");
      doc.setFontSize(9);
      doc.setTextColor(255, 255, 255);
      doc.text(s.label.toUpperCase(), ML + 8 + 31, y + matrixRowH / 2 + 3, { align: "center" });

      // Count cells
      doc.setFont(FONT, "bold");
      doc.setFontSize(13);
      CATEGORIES.forEach((c, i) => {
        const count = matrix[s.key][c.key];
        const cx = ML + sevColW + i * catColW + catColW / 2;
        if (count > 0) {
          doc.setTextColor(sr, sg, sb);
        } else {
          doc.setTextColor(...LGRAY);
        }
        doc.text(String(count), cx, y + matrixRowH / 2 + 5, { align: "center" });
      });

      // Row border
      doc.setDrawColor(...LGRAY);
      doc.line(ML, y + matrixRowH, MR, y + matrixRowH);

      y += matrixRowH;
    });

    // Outer matrix border
    doc.setDrawColor(...LGRAY);
    doc.rect(ML, y - SEV_ROWS.length * matrixRowH - matrixHeaderH, CW, SEV_ROWS.length * matrixRowH + matrixHeaderH, "S");

    y += 14;

    // ---- Detailed list ----
    checkY(40);
    y += 12;
    doc.setFont(FONT, "bold");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    doc.text(`ALL ISSUES BY SEVERITY — ${debtItems.length} SHOWN`, ML, y);
    y += 6;
    doc.setDrawColor(...LGRAY);
    doc.line(ML, y, MR, y);
    y += 16;

    const colW = [72, 96, 180, 117];
    const headers = ["Severity", "Category", "Issue", "File"];
    const rowH = 24;

    checkY(rowH + 4);
    doc.setFillColor(...LGRAY);
    doc.rect(ML, y, CW, rowH - 2, "F");
    doc.setFont(FONT, "bold");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    let cx = ML + 6;
    headers.forEach((h, i) => { doc.text(h, cx, y + 15); cx += colW[i]; });
    y += rowH;

    const catLabelMap: Record<string, string> = {};
    CATEGORIES.forEach((c) => { catLabelMap[c.key] = c.label; });

    const drawDetailHeader = () => {
      doc.setFillColor(...LGRAY);
      doc.rect(ML, y, CW, rowH - 2, "F");
      doc.setFont(FONT, "bold");
      doc.setFontSize(9);
      doc.setTextColor(...GRAY);
      let hx = ML + 6;
      headers.forEach((h, i) => { doc.text(h, hx, y + 15); hx += colW[i]; });
      y += rowH;
    };

    const SEV_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
    const sortedItems = [...debtItems].sort((a, b) => {
      const sa = SEV_ORDER[String(a.severity ?? "").toLowerCase()] ?? 99;
      const sb = SEV_ORDER[String(b.severity ?? "").toLowerCase()] ?? 99;
      return sa - sb;
    });

    for (const item of sortedItems) {
      // Page break: redraw header at top of new page
      if (y + rowH > H - 40) {
        newPage();
        drawDetailHeader();
      }
      const sev = String(item.severity ?? "").toLowerCase();
      const [r, g, b] = SEVERITY_RGB[sev] ?? GRAY;
      doc.setFillColor(r, g, b);
      doc.roundedRect(ML + 4, y + 5, 62, 14, 2, 2, "F");
      doc.setFont(FONT, "bold");
      doc.setFontSize(8);
      doc.setTextColor(255, 255, 255);
      doc.text(sev.toUpperCase(), ML + 8, y + 15);
      doc.setFont(FONT, "normal");
      doc.setFontSize(10);
      doc.setTextColor(...GRAY);
      const catLabel = catLabelMap[String(item.category ?? "").toLowerCase()] ?? (item.category ?? "");
      doc.text(trunc(catLabel, 14), ML + colW[0] + 6, y + 15);
      doc.setTextColor(...BLACK);
      doc.text(trunc(item.title ?? "", 36), ML + colW[0] + colW[1] + 6, y + 15);
      doc.setTextColor(...GRAY);
      const fp = (item.file_path ?? "").split("/").slice(-2).join("/") + (item.line_start ? `:${item.line_start}` : "");
      doc.text(trunc(fp, 24), ML + colW[0] + colW[1] + colW[2] + 6, y + 15);
      doc.setDrawColor(...LGRAY);
      doc.line(ML, y + rowH - 2, MR, y + rowH - 2);
      y += rowH;
    }
    y += 8;
  } else {
    checkY(18);
    doc.setFont(FONT, "normal");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    doc.text("No technical debt issues detected in this repository.", ML, y + 10);
    y += 22;
  }

  // Vulnerable dependencies
  const vulnDeps = allDeps.filter((d) => d.vulnerability_count > 0);
  if (vulnDeps.length > 0) {
    sectionTitle("Dependency Risk — Vulnerable");
    const colW = [155, 85, 85, 55, 85];
    const headers = ["Package", "Current", "Latest", "CVEs", "Ecosystem"];
    const rowH = 24;

    checkY(rowH);
    doc.setFillColor(254, 242, 242);
    doc.rect(ML, y, CW, rowH - 2, "F");
    doc.setFont(FONT, "bold");
    doc.setFontSize(9);
    doc.setTextColor(...RED);
    let cx = ML + 6;
    headers.forEach((h, i) => { doc.text(h, cx, y + 15); cx += colW[i]; });
    y += rowH;

    for (const dep of vulnDeps.slice(0, 20)) {
      checkY(rowH);
      doc.setFont(FONT, "bold");
      doc.setFontSize(10);
      doc.setTextColor(...BLACK);
      doc.text(trunc(dep.package_name ?? "", 24), ML + 6, y + 16);
      doc.setFont(FONT, "normal");
      doc.setTextColor(...GRAY);
      doc.text(trunc(dep.current_version ?? "—", 12), ML + colW[0] + 6, y + 16);
      doc.text(trunc(dep.latest_version ?? "—", 12), ML + colW[0] + colW[1] + 6, y + 16);
      doc.setFillColor(...RED);
      doc.roundedRect(ML + colW[0] + colW[1] + colW[2] + 4, y + 5, 38, 14, 2, 2, "F");
      doc.setFont(FONT, "bold");
      doc.setFontSize(9);
      doc.setTextColor(255, 255, 255);
      doc.text(String(dep.vulnerability_count), ML + colW[0] + colW[1] + colW[2] + 23, y + 15, { align: "center" });
      doc.setFont(FONT, "normal");
      doc.setFontSize(10);
      doc.setTextColor(...GRAY);
      doc.text(trunc(dep.ecosystem ?? "—", 14), ML + colW[0] + colW[1] + colW[2] + colW[3] + 6, y + 16);
      doc.setDrawColor(...LGRAY);
      doc.line(ML, y + rowH - 2, MR, y + rowH - 2);
      y += rowH;
    }
    y += 8;
  }

  // Severely outdated deps
  const outdatedDeps = allDeps.filter((d) => d.days_behind > 365);
  if (outdatedDeps.length > 0) {
    sectionTitle("Dependency Risk — Severely Outdated (>1 year)");
    const colW = [155, 85, 85, 85, 55];
    const headers = ["Package", "Current", "Latest", "Days Behind", "Ecosystem"];
    const rowH = 24;

    checkY(rowH);
    doc.setFillColor(255, 251, 235);
    doc.rect(ML, y, CW, rowH - 2, "F");
    doc.setFont(FONT, "bold");
    doc.setFontSize(9);
    doc.setTextColor(...AMBER);
    let cx = ML + 6;
    headers.forEach((h, i) => { doc.text(h, cx, y + 15); cx += colW[i]; });
    y += rowH;

    for (const dep of outdatedDeps.slice(0, 15)) {
      checkY(rowH);
      doc.setFont(FONT, "bold");
      doc.setFontSize(10);
      doc.setTextColor(...BLACK);
      doc.text(trunc(dep.package_name ?? "", 24), ML + 6, y + 16);
      doc.setFont(FONT, "normal");
      doc.setTextColor(...GRAY);
      doc.text(trunc(dep.current_version ?? "—", 12), ML + colW[0] + 6, y + 16);
      doc.text(trunc(dep.latest_version ?? "—", 12), ML + colW[0] + colW[1] + 6, y + 16);
      doc.setTextColor(...AMBER);
      doc.setFont(FONT, "bold");
      doc.text(String(dep.days_behind), ML + colW[0] + colW[1] + colW[2] + 6, y + 16);
      doc.setFont(FONT, "normal");
      doc.setTextColor(...GRAY);
      doc.text(trunc(dep.ecosystem ?? "—", 12), ML + colW[0] + colW[1] + colW[2] + colW[3] + 6, y + 16);
      doc.setDrawColor(...LGRAY);
      doc.line(ML, y + rowH - 2, MR, y + rowH - 2);
      y += rowH;
    }
    y += 8;
  }

  // AI recommendations
  const recs: any[] = recsRes?.recommendations ?? [];
  if (recs.length > 0) {
    sectionTitle(`AI Recommendations — ${recsRes?.total ?? recs.length} Total`);
    for (const rec of recs.slice(0, 8)) {
      const [r, g, b] = SEVERITY_RGB[rec.priority] ?? GRAY;
      // Compute desc lines at render font size BEFORE drawing the background
      doc.setFont(FONT, "normal");
      doc.setFontSize(10);
      const descLines = doc.splitTextToSize(rec.description ?? "", CW - 24);
      const shownLines = descLines.slice(0, 4);
      const hasMeta = !!(rec.category || rec.estimated_hours);
      const titleRow = 30;
      const descLineH = 14;
      const metaRow = hasMeta ? 16 : 8;
      const cardH = titleRow + shownLines.length * descLineH + metaRow;
      checkY(cardH + 6);
      doc.setFillColor(249, 250, 251);
      doc.roundedRect(ML, y, CW, cardH, 3, 3, "F");
      doc.setFillColor(r, g, b);
      doc.roundedRect(ML + 8, y + 8, 58, 15, 2, 2, "F");
      doc.setFont(FONT, "bold");
      doc.setFontSize(8.5);
      doc.setTextColor(255, 255, 255);
      doc.text((rec.priority ?? "").toUpperCase(), ML + 12, y + 18);
      doc.setFont(FONT, "bold");
      doc.setFontSize(11);
      doc.setTextColor(...BLACK);
      doc.text(trunc(rec.title ?? "", 70), ML + 74, y + 19);
      doc.setFont(FONT, "normal");
      doc.setFontSize(10);
      doc.setTextColor(...GRAY);
      shownLines.forEach((line: string, i: number) => doc.text(line, ML + 8, y + titleRow + 4 + i * descLineH));
      if (hasMeta) {
        doc.setFontSize(9);
        doc.setTextColor(...ACCENT);
        const meta = [rec.category, rec.estimated_hours ? `~${rec.estimated_hours}h` : null].filter(Boolean).join("  ·  ");
        doc.text(meta, ML + 8, y + titleRow + 4 + shownLines.length * descLineH + 6);
      }
      y += cardH + 8;
    }
  }

  // Footer on every page
  const totalPages = (doc.internal as any).getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFillColor(...LGRAY);
    doc.rect(0, H - 26, W, 26, "F");
    doc.setFont(FONT, "normal");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    doc.text("CodeLens AI — AI-Powered Legacy Modernization Platform", ML, H - 9);
    doc.text(`Page ${i} of ${totalPages}`, MR - 6, H - 9, { align: "right" });
  }

  const safeName = (proj?.name ?? "report").replace(/[^a-z0-9]/gi, "_").toLowerCase();
  const now = new Date();
  const datestr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  doc.save(`codelens_${safeName}_${datestr}.pdf`);
}
