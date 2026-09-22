import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

/**
 * Tiện ích xuất báo cáo — Excel / CSV / PDF.
 * Dashboard chỉ định dạng và tải file; dữ liệu đến từ API.
 */

export type Row = Record<string, string | number | boolean | null | undefined>;

export async function exportExcel(rows: Row[], filename = "report.xlsx"): Promise<void> {
  // SheetJS khá lớn; chỉ tải khi người dùng thực sự xuất Excel để lỗi tải
  // chunk báo cáo không thể làm trắng toàn bộ dashboard/Live Camera.
  const XLSX = await import("xlsx");
  const ws = XLSX.utils.json_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Report");
  XLSX.writeFile(wb, filename);
}

export function exportCSV(rows: Row[], filename = "report.csv"): void {
  if (rows.length === 0) {
    downloadBlob(new Blob([""], { type: "text/csv" }), filename);
    return;
  }
  const headers = Object.keys(rows[0]);
  const escape = (v: unknown) => {
    const s = v == null ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [
    headers.join(","),
    ...rows.map((r) => headers.map((h) => escape(r[h])).join(",")),
  ];
  downloadBlob(new Blob([lines.join("\n")], { type: "text/csv" }), filename);
}

export function exportPDF(
  rows: Row[],
  filename = "report.pdf",
  title = "AEMS Report"
): void {
  const doc = new jsPDF();
  doc.setFontSize(14);
  doc.text(title, 14, 16);
  const headers = rows.length ? Object.keys(rows[0]) : [];
  autoTable(doc, {
    startY: 22,
    head: [headers],
    body: rows.map((r) => headers.map((h) => String(r[h] ?? ""))),
    styles: { fontSize: 8 },
    headStyles: { fillColor: [37, 99, 235] },
  });
  doc.save(filename);
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
