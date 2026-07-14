import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Plus, Video } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DataTable, type Column } from "@/components/common/DataTable";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useManagedCameras } from "@/hooks/api";
import { apiClient, unwrap } from "@/lib/api";
import type { CameraStatus, ManagedCamera } from "@/types";

interface CameraForm {
  code: string;
  name: string;
  rtsp_main: string;
  location: string;
}

/** Camera Management — danh sách + thêm camera (gọi Camera API). */
export function CameraManagementPage() {
  const { data: cameras, refetch } = useManagedCameras();
  const [open, setOpen] = useState(false);
  const { register, handleSubmit, reset } = useForm<CameraForm>({
    defaultValues: { code: "", name: "", rtsp_main: "", location: "" },
  });

  const onSubmit = async (values: CameraForm) => {
    try {
      const res = await apiClient.post("/cameras", {
        code: values.code.trim(),
        name: values.name.trim() || values.code.trim(),
        location: values.location.trim() || undefined,
        rtsp_main: values.rtsp_main.trim(),
        enabled: true,
      });
      const created = unwrap<ManagedCamera>(res.data);
      await apiClient.post(`/cameras/${created.id}/start`);
      toast.success("Đã thêm camera và bắt đầu stream RTSP");
      void refetch();
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Không thêm được camera. Kiểm tra RTSP URL và backend.";
      toast.error(msg);
    }
    reset();
    setOpen(false);
  };

  const columns: Column<CameraStatus>[] = [
    { key: "camera_id", header: "ID", render: (r) => `#${r.camera_id}` },
    { key: "name", header: "Tên camera", render: (r) => <span className="font-medium">{r.name}</span> },
    { key: "fps", header: "FPS", render: (r) => r.fps.toFixed(0) },
    {
      key: "status",
      header: "Trạng thái",
      render: (r) => (
        <Badge variant={r.status === "online" ? "success" : "destructive"}>{r.status}</Badge>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Camera Management"
        description="Quản lý danh sách camera giám sát"
        actions={
          <Button onClick={() => setOpen(true)}>
            <Plus className="h-4 w-4" /> Thêm Camera
          </Button>
        }
      />
      <Card>
        <CardContent className="pt-4">
          <DataTable columns={columns} rows={cameras ?? []} rowKey={(r) => String(r.camera_id)} />
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Video className="h-5 w-5" /> Thêm Camera
            </DialogTitle>
          </DialogHeader>
          <form className="space-y-3" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1">
              <Label>Mã camera</Label>
              <Input {...register("code", { required: true })} placeholder="CAM_110" />
            </div>
            <div className="space-y-1">
              <Label>Tên camera</Label>
              <Input {...register("name", { required: true })} placeholder="Office 01" />
            </div>
            <div className="space-y-1">
              <Label>RTSP URL (main stream)</Label>
              <Input {...register("rtsp_main", { required: true })} placeholder="rtsp://..." />
            </div>
            <div className="space-y-1">
              <Label>Vị trí</Label>
              <Input {...register("location")} placeholder="Tầng 3" />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Huỷ
              </Button>
              <Button type="submit">Thêm</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
