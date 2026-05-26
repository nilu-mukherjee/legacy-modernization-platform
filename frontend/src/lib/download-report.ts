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

export async function downloadReport(projectId: string): Promise<void> {
  const [{ default: jsPDF }, proj, anal, debtRes, depsRes, recsRes] = await Promise.all([
    import("jspdf"),
    getProject(projectId),
    getAnalysis(projectId).catch(() => null),
    getDebtItems(projectId, 0, 200).catch(() => null),
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
  doc.setFont("helvetica", "bold");
  doc.setFontSize(24);
  doc.setTextColor(...BLACK);
  doc.text(trunc(proj?.name ?? "Unnamed Project", 42), ML, R1);

  // LEFT: repo URL
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(...GRAY);
  doc.text(trunc(proj?.repo_url ?? "", 60), ML, R2);

  // LEFT: date
  const dateStr = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
  doc.setFontSize(9);
  doc.text(`Generated ${dateStr}`, ML, R3);

  // RIGHT: CODELENS AI — baseline aligned with project name row
  doc.setFont("helvetica", "bold");
  doc.setFontSize(22);
  doc.setTextColor(...ACCENT);
  doc.text("CODELENS AI", MR, R1, { align: "right" });

  // RIGHT: subtitle — baseline aligned with repo URL row
  doc.setFont("helvetica", "normal");
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
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(255, 255, 255);
    doc.text("SCORE", ML + 14, y + 16);

    // Row 1: score number — large, left-aligned, no overflow
    doc.setFont("helvetica", "bold");
    doc.setFontSize(28);
    doc.setTextColor(255, 255, 255);
    doc.text(`${score}%`, ML + 14, y + 44);

    // Row 2: grade on its own line, well below score baseline
    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);
    doc.setTextColor(230, 240, 255);
    doc.text(`Grade ${grade}`, ML + 14, y + 60);

    // Labels right-aligned outside badge
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    doc.text("MODERNIZATION SCORE", MR, y + 20, { align: "right" });
    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.setTextColor(r, g, b);
    doc.text(`${score} / 100`, MR, y + 42, { align: "right" });
    doc.setFont("helvetica", "normal");
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
      doc.setFont("helvetica", "bold");
      doc.setFontSize(16);
      doc.setTextColor(...BLACK);
      doc.text(value, bx + 10, y + 22);
      doc.setFont("helvetica", "normal");
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
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    const lines = doc.splitTextToSize(execSummary, CW - 24);
    const boxH = lines.length * 13 + 20;
    doc.setFillColor(240, 245, 255);
    doc.roundedRect(ML, y, CW, boxH, 3, 3, "F");
    doc.setFillColor(...ACCENT);
    doc.rect(ML, y, 3, boxH, "F");
    doc.setTextColor(...BLACK);
    lines.forEach((line: string, i: number) => doc.text(line, ML + 12, y + 14 + i * 13));
    y += boxH + 14;
  }

  const sectionTitle = (title: string) => {
    checkY(28);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    doc.text(title.toUpperCase(), ML, y);
    y += 5;
    doc.setDrawColor(...LGRAY);
    doc.line(ML, y, MR, y);
    y += 12;
  };

  // Score breakdown — always render
  const subScores: Record<string, number> = anal?.sub_scores ?? {};
  sectionTitle("Score Breakdown");
  const subEntries = Object.entries(subScores);
  if (subEntries.length > 0) {
    const cols = 2;
    const colW = CW / cols;
    for (let i = 0; i < subEntries.length; i += cols) {
      checkY(22);
      for (let c = 0; c < cols; c++) {
        const entry = subEntries[i + c];
        if (!entry) continue;
        const [key, val] = entry;
        const v = Number(val) || 0;
        const bx = ML + c * colW;
        doc.setFillColor(...LGRAY);
        doc.roundedRect(bx, y, colW - 6, 22, 2, 2, "F");
        doc.setFont("helvetica", "normal");
        doc.setFontSize(9);
        doc.setTextColor(...BLACK);
        doc.text(DIMENSION_LABELS[key] ?? key, bx + 6, y + 14);
        const barX = bx + 140;
        const barW = colW - 178;
        doc.setFillColor(229, 231, 235);
        doc.roundedRect(barX, y + 8, barW, 6, 2, 2, "F");
        const [r, g, b] = scoreColor(v);
        doc.setFillColor(r, g, b);
        doc.roundedRect(barX, y + 8, barW * (v / 100), 6, 2, 2, "F");
        doc.setFont("helvetica", "bold");
        doc.setFontSize(9);
        doc.setTextColor(r, g, b);
        doc.text(String(Math.round(v)), bx + colW - 14, y + 14);
      }
      y += 26;
    }
  } else {
    checkY(18);
    doc.setFont("helvetica", "normal");
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

    const sevColW = 70;
    const catColW = (CW - sevColW) / CATEGORIES.length;
    const matrixHeaderH = 24;
    const matrixRowH    = 22;

    checkY(matrixHeaderH + SEV_ROWS.length * matrixRowH + 10);

    // Header row
    doc.setFillColor(...LGRAY);
    doc.rect(ML, y, CW, matrixHeaderH, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(8.5);
    doc.setTextColor(...GRAY);
    doc.text("SEVERITY", ML + 6, y + 15);
    CATEGORIES.forEach((c, i) => {
      const cx = ML + sevColW + i * catColW + catColW / 2;
      doc.text(c.label.toUpperCase(), cx, y + 15, { align: "center" });
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
      doc.roundedRect(ML + 6, y + 4, 56, matrixRowH - 8, 2, 2, "F");
      doc.setFont("helvetica", "bold");
      doc.setFontSize(8);
      doc.setTextColor(255, 255, 255);
      doc.text(s.label.toUpperCase(), ML + 6 + 28, y + matrixRowH / 2 + 2.5, { align: "center" });

      // Count cells
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      CATEGORIES.forEach((c, i) => {
        const count = matrix[s.key][c.key];
        const cx = ML + sevColW + i * catColW + catColW / 2;
        if (count > 0) {
          doc.setTextColor(sr, sg, sb);
        } else {
          doc.setTextColor(...LGRAY);
        }
        doc.text(String(count), cx, y + matrixRowH / 2 + 4, { align: "center" });
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

    // ---- Detailed list (top items per severity) ----
    checkY(28);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    doc.text("TOP ISSUES BY SEVERITY", ML, y);
    y += 5;
    doc.setDrawColor(...LGRAY);
    doc.line(ML, y, MR, y);
    y += 12;

    const colW = [68, 90, 180, 127];
    const headers = ["Severity", "Category", "Issue", "File"];
    const rowH = 22;

    checkY(rowH + 4);
    doc.setFillColor(...LGRAY);
    doc.rect(ML, y, CW, rowH - 2, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    let cx = ML + 4;
    headers.forEach((h, i) => { doc.text(h, cx, y + 13); cx += colW[i]; });
    y += rowH;

    const catLabelMap: Record<string, string> = {};
    CATEGORIES.forEach((c) => { catLabelMap[c.key] = c.label; });

    for (const sev of ["critical", "high", "medium", "low"]) {
      const items = debtItems.filter((d) => d.severity === sev).slice(0, 8);
      for (const item of items) {
        checkY(rowH);
        const [r, g, b] = SEVERITY_RGB[sev] ?? GRAY;
        doc.setFillColor(r, g, b);
        doc.roundedRect(ML + 2, y + 4, 58, 13, 2, 2, "F");
        doc.setFont("helvetica", "bold");
        doc.setFontSize(7.5);
        doc.setTextColor(255, 255, 255);
        doc.text(sev.toUpperCase(), ML + 6, y + 13);
        doc.setFont("helvetica", "normal");
        doc.setFontSize(9);
        doc.setTextColor(...GRAY);
        const catLabel = catLabelMap[String(item.category ?? "").toLowerCase()] ?? (item.category ?? "");
        doc.text(trunc(catLabel, 14), ML + colW[0] + 4, y + 13);
        doc.setTextColor(...BLACK);
        doc.text(trunc(item.title ?? "", 34), ML + colW[0] + colW[1] + 4, y + 13);
        doc.setTextColor(...GRAY);
        const fp = (item.file_path ?? "").split("/").slice(-2).join("/") + (item.line_start ? `:${item.line_start}` : "");
        doc.text(trunc(fp, 26), ML + colW[0] + colW[1] + colW[2] + 4, y + 13);
        doc.setDrawColor(...LGRAY);
        doc.line(ML, y + rowH - 2, MR, y + rowH - 2);
        y += rowH;
      }
    }
    y += 8;
  } else {
    checkY(18);
    doc.setFont("helvetica", "normal");
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
    const rowH = 22;

    checkY(rowH);
    doc.setFillColor(254, 242, 242);
    doc.rect(ML, y, CW, rowH - 2, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(...RED);
    let cx = ML + 4;
    headers.forEach((h, i) => { doc.text(h, cx, y + 13); cx += colW[i]; });
    y += rowH;

    for (const dep of vulnDeps.slice(0, 20)) {
      checkY(rowH);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(9);
      doc.setTextColor(...BLACK);
      doc.text(trunc(dep.package_name ?? "", 24), ML + 4, y + 14);
      doc.setFont("helvetica", "normal");
      doc.setTextColor(...GRAY);
      doc.text(trunc(dep.current_version ?? "—", 12), ML + colW[0] + 4, y + 14);
      doc.text(trunc(dep.latest_version ?? "—", 12), ML + colW[0] + colW[1] + 4, y + 14);
      doc.setFillColor(...RED);
      doc.roundedRect(ML + colW[0] + colW[1] + colW[2] + 4, y + 4, 34, 13, 2, 2, "F");
      doc.setFont("helvetica", "bold");
      doc.setFontSize(8);
      doc.setTextColor(255, 255, 255);
      doc.text(String(dep.vulnerability_count), ML + colW[0] + colW[1] + colW[2] + 14, y + 13);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(9);
      doc.setTextColor(...GRAY);
      doc.text(trunc(dep.ecosystem ?? "—", 14), ML + colW[0] + colW[1] + colW[2] + colW[3] + 4, y + 14);
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
    const rowH = 22;

    checkY(rowH);
    doc.setFillColor(255, 251, 235);
    doc.rect(ML, y, CW, rowH - 2, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(...AMBER);
    let cx = ML + 4;
    headers.forEach((h, i) => { doc.text(h, cx, y + 13); cx += colW[i]; });
    y += rowH;

    for (const dep of outdatedDeps.slice(0, 15)) {
      checkY(rowH);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(9);
      doc.setTextColor(...BLACK);
      doc.text(trunc(dep.package_name ?? "", 24), ML + 4, y + 14);
      doc.setFont("helvetica", "normal");
      doc.setTextColor(...GRAY);
      doc.text(trunc(dep.current_version ?? "—", 12), ML + colW[0] + 4, y + 14);
      doc.text(trunc(dep.latest_version ?? "—", 12), ML + colW[0] + colW[1] + 4, y + 14);
      doc.setTextColor(...AMBER);
      doc.setFont("helvetica", "bold");
      doc.text(String(dep.days_behind), ML + colW[0] + colW[1] + colW[2] + 4, y + 14);
      doc.setFont("helvetica", "normal");
      doc.setTextColor(...GRAY);
      doc.text(trunc(dep.ecosystem ?? "—", 12), ML + colW[0] + colW[1] + colW[2] + colW[3] + 4, y + 14);
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
      doc.setFont("helvetica", "normal");
      doc.setFontSize(9);
      const descLines = doc.splitTextToSize(rec.description ?? "", CW - 20);
      const shownLines = descLines.slice(0, 3);
      const hasMeta = !!(rec.category || rec.estimated_hours);
      const cardH = 26 + shownLines.length * 12 + (hasMeta ? 14 : 6);
      checkY(cardH + 4);
      doc.setFillColor(249, 250, 251);
      doc.roundedRect(ML, y, CW, cardH, 3, 3, "F");
      doc.setFillColor(r, g, b);
      doc.roundedRect(ML + 6, y + 7, 52, 13, 2, 2, "F");
      doc.setFont("helvetica", "bold");
      doc.setFontSize(8);
      doc.setTextColor(255, 255, 255);
      doc.text((rec.priority ?? "").toUpperCase(), ML + 10, y + 16);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10);
      doc.setTextColor(...BLACK);
      doc.text(trunc(rec.title ?? "", 65), ML + 64, y + 16);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(9);
      doc.setTextColor(...GRAY);
      shownLines.forEach((line: string, i: number) => doc.text(line, ML + 6, y + 28 + i * 12));
      if (hasMeta) {
        doc.setFontSize(8);
        const meta = [rec.category, rec.estimated_hours ? `~${rec.estimated_hours}h` : null].filter(Boolean).join(" · ");
        doc.text(meta, ML + 6, y + 28 + shownLines.length * 12 + 4);
      }
      y += cardH + 6;
    }
  }

  // Footer on every page
  const totalPages = (doc.internal as any).getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFillColor(...LGRAY);
    doc.rect(0, H - 26, W, 26, "F");
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8.5);
    doc.setTextColor(...GRAY);
    doc.text("CodeLens AI — AI-Powered Legacy Modernization Platform", ML, H - 9);
    doc.text(`Page ${i} of ${totalPages}`, MR - 30, H - 9);
  }

  const safeName = (proj?.name ?? "report").replace(/[^a-z0-9]/gi, "_").toLowerCase();
  const now = new Date();
  const datestr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  doc.save(`codelens_${safeName}_${datestr}.pdf`);
}
