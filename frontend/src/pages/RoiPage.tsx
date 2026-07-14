import { useState } from "react";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/common/EmptyState";
import { ROICanvas } from "@/components/roi/ROICanvas";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useRoiStore } from "@/hooks/useRoiStore";
import { useCameras } from "@/hooks/api";
import type { ROIPoint } from "@/types";

/** ROI Editor — vẽ Polygon/Rectangle, Rename, Delete, Save, Load. */
export function RoiPage() {
  const { data: cameras } = useCameras();
  const { rois, upsert, remove, rename } = useRoiStore();
  const [cameraId, setCameraId] = useState(1);

  const cameraRois = rois.filter((r) => r.camera_id === cameraId);

  const handleCreate = (points: ROIPoint[], type: "polygon" | "rectangle") => {
    const id = `roi-${Date.now()}`;
    upsert({
      id,
      name: `ROI ${cameraRois.length + 1}`,
      camera_id: cameraId,
      type,
      points,
    });
    toast.success("Đã lưu ROI");
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="ROI Editor"
        description="Định nghĩa vùng quan tâm cho từng camera"
        actions={
          <Select value={String(cameraId)} onValueChange={(v) => setCameraId(Number(v))}>
            <SelectTrigger className="w-44">
              <SelectValue placeholder="Chọn camera" />
            </SelectTrigger>
            <SelectContent>
              {(cameras ?? [{ camera_id: 1, name: "Camera 1" }]).map((c) => (
                <SelectItem key={c.camera_id} value={String(c.camera_id)}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      />
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardContent className="pt-4">
              <ROICanvas rois={cameraRois} onCreate={handleCreate} />
            </CardContent>
          </Card>
        </div>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              ROI đã lưu ({cameraRois.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {cameraRois.length === 0 && <EmptyState title="Chưa có ROI" />}
            {cameraRois.map((r) => (
              <div key={r.id} className="flex items-center gap-2 rounded-md border p-2">
                <Input
                  defaultValue={r.name}
                  onBlur={(e) => rename(r.id, e.target.value)}
                  className="h-8"
                />
                <Badge variant="secondary">{r.type}</Badge>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-destructive"
                  onClick={() => remove(r.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
