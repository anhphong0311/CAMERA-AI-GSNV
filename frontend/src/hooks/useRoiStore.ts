import { useCallback, useEffect, useState } from "react";
import { logAction } from "@/lib/logger";
import type { ROI } from "@/types";

/**
 * Kho ROI phía client (bản nháp editor) — lưu localStorage.
 *
 * Ghi chú: khi backend expose Zone/ROI API, thay bằng gọi API. Ở đây ROI chỉ
 * là dữ liệu hiển thị/soạn thảo, không phải business logic.
 */
const KEY = "aems.rois";

function load(): ROI[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "[]") as ROI[];
  } catch {
    return [];
  }
}

export function useRoiStore() {
  const [rois, setRois] = useState<ROI[]>(load);

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(rois));
  }, [rois]);

  const upsert = useCallback((roi: ROI) => {
    setRois((prev) => {
      const idx = prev.findIndex((r) => r.id === roi.id);
      logAction("roi_change", `${idx >= 0 ? "update" : "create"} ${roi.name}`);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = roi;
        return next;
      }
      return [...prev, roi];
    });
  }, []);

  const remove = useCallback((id: string) => {
    logAction("roi_change", `delete ${id}`);
    setRois((prev) => prev.filter((r) => r.id !== id));
  }, []);

  const rename = useCallback((id: string, name: string) => {
    setRois((prev) => prev.map((r) => (r.id === id ? { ...r, name } : r)));
  }, []);

  return { rois, upsert, remove, rename };
}
