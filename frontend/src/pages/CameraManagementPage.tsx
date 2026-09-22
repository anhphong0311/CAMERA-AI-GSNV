import { useState } from "react";
import axios from "axios";
import { useForm } from "react-hook-form";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, Pencil, Plus, RefreshCw, Trash2, Video } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DataTable, type Column } from "@/components/common/DataTable";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { apiClient, unwrap } from "@/lib/api";
import type { ManagedCamera } from "@/types";

interface CameraForm {
  code: string;
  name: string;
  rtsp_main: string;
  rtsp_sub: string;
  location: string;
  enabled: boolean;
}

const emptyForm: CameraForm = {
  code: "", name: "", rtsp_main: "", rtsp_sub: "", location: "", enabled: true,
};

function errorMessage(err: unknown): string {
  const response = axios.isAxiosError(err)
    ? (err.response?.data as { error?: { message?: string } } | undefined)
    : undefined;
  return response?.error?.message?.replace(
    /^Camera code '(.+)' đã tồn tại\.$/,
    "Mã camera '$1' đã tồn tại. Hãy nhập mã khác."
  ) ?? "Không thực hiện được. Vui lòng thử lại.";
}

/** Quản lý camera: thêm, sửa thông tin/luồng RTSP và xóa có xác nhận. */
export function CameraManagementPage() {
  const queryClient = useQueryClient();
  const { data: cameras, error, isError, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["managed-camera-records"],
    queryFn: async () => unwrap<ManagedCamera[]>((await apiClient.get("/cameras")).data),
    refetchInterval: 10000,
  });
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<ManagedCamera | null>(null);
  const [deleting, setDeleting] = useState<ManagedCamera | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteBusy, setDeleteBusy] = useState(false);
  const { register, handleSubmit, reset } = useForm<CameraForm>({ defaultValues: emptyForm });

  const refreshCameras = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["managed-camera-records"] }),
      queryClient.invalidateQueries({ queryKey: ["managed-cameras"] }),
    ]);
  };

  const openCreate = () => {
    setEditing(null);
    reset(emptyForm);
    setFormOpen(true);
  };

  const openEdit = (camera: ManagedCamera) => {
    setEditing(camera);
    reset({
      code: camera.code,
      name: camera.name ?? "",
      location: camera.location ?? "",
      rtsp_main: camera.rtsp_main,
      rtsp_sub: camera.rtsp_sub ?? "",
      enabled: camera.enabled,
    });
    setFormOpen(true);
  };

  const onSubmit = async (values: CameraForm) => {
    setSaving(true);
    try {
      const payload = {
        code: values.code.trim(),
        name: values.name.trim(),
        location: values.location.trim() || null,
        rtsp_main: values.rtsp_main.trim(),
        rtsp_sub: values.rtsp_sub.trim() || null,
        enabled: values.enabled,
      };
      if (editing) {
        await apiClient.put(`/cameras/${editing.id}`, payload, { timeout: 30000 });
        toast.success("Đã cập nhật camera");
      } else {
        const res = await apiClient.post("/cameras", payload);
        const created = unwrap<ManagedCamera>(res.data);
        if (created.enabled) {
          try {
            await apiClient.post(`/cameras/${created.id}/start`, undefined, { timeout: 30000 });
            toast.success("Đã thêm camera và bắt đầu stream RTSP");
          } catch {
            toast.warning("Đã lưu camera nhưng chưa khởi động được luồng RTSP. Kiểm tra lại kết nối.");
          }
        } else {
          toast.success("Đã thêm camera ở trạng thái tắt");
        }
      }
      setFormOpen(false);
      reset(emptyForm);
      await refreshCameras();
    } catch (err: unknown) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const deleteCamera = async () => {
    if (!deleting) return;
    setDeleteBusy(true);
    try {
      await apiClient.delete(`/cameras/${deleting.id}`, { timeout: 30000 });
      toast.success(`Đã xóa camera ${deleting.name ?? deleting.code}`);
      setDeleting(null);
      await refreshCameras();
    } catch (err: unknown) {
      toast.error(errorMessage(err));
    } finally {
      setDeleteBusy(false);
    }
  };

  const columns: Column<ManagedCamera>[] = [
    { key: "id", header: "ID", render: (r) => `#${r.id}` },
    { key: "code", header: "Mã camera" },
    { key: "name", header: "Tên camera", render: (r) => <span className="font-medium">{r.name ?? r.code}</span> },
    { key: "fps", header: "FPS", render: (r) => r.fps.toFixed(0) },
    {
      key: "status", header: "Trạng thái",
      render: (r) => (
        <Badge variant={!r.enabled ? "secondary" : r.status === "online" ? "success" : "destructive"}>
          {!r.enabled ? "Đã tắt" : r.status}
        </Badge>
      ),
    },
    {
      key: "actions", header: "Thao tác",
      render: (r) => (
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => openEdit(r)} aria-label={`Sửa camera ${r.name ?? r.code}`}>
            <Pencil className="h-3.5 w-3.5" /> Sửa
          </Button>
          <Button type="button" variant="destructive" size="sm" onClick={() => setDeleting(r)} aria-label={`Xóa camera ${r.name ?? r.code}`}>
            <Trash2 className="h-3.5 w-3.5" /> Xóa
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Camera Management"
        description="Quản lý danh sách camera giám sát"
        actions={<Button onClick={openCreate}><Plus className="h-4 w-4" /> Thêm Camera</Button>}
      />
      <Card>
        <CardContent className="pt-4">
          {isLoading ? (
            <div className="flex min-h-40 items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" /> Đang tải danh sách camera...
            </div>
          ) : isError ? (
            <div className="flex min-h-40 flex-col items-center justify-center gap-3 text-center">
              <p className="text-sm text-destructive">Không tải được danh sách camera. Dữ liệu đã lưu vẫn được giữ nguyên.</p>
              <p className="max-w-xl text-xs text-muted-foreground">{error instanceof Error ? error.message : "Không thể kết nối tới backend."}</p>
              <Button type="button" variant="outline" onClick={() => void refetch()}><RefreshCw className="h-4 w-4" /> Thử lại</Button>
            </div>
          ) : (
            <div className="space-y-2">
              {isFetching && <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3.5 w-3.5 animate-spin" /> Đang cập nhật trạng thái...</div>}
              <DataTable columns={columns} rows={cameras ?? []} rowKey={(r) => String(r.id)} emptyMessage="Chưa có camera nào được lưu" />
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={formOpen} onOpenChange={(open) => { if (!saving) setFormOpen(open); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Video className="h-5 w-5" /> {editing ? `Sửa camera ${editing.name ?? editing.code}` : "Thêm Camera"}</DialogTitle>
          </DialogHeader>
          <form className="space-y-3" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1"><Label htmlFor="camera-code">Mã camera</Label><Input id="camera-code" {...register("code", { required: true })} placeholder="CAM_110" /></div>
            <div className="space-y-1"><Label htmlFor="camera-name">Tên camera</Label><Input id="camera-name" {...register("name", { required: true })} placeholder="Office 01" /></div>
            <div className="space-y-1"><Label htmlFor="camera-rtsp-main">RTSP URL (main stream)</Label><Input id="camera-rtsp-main" {...register("rtsp_main", { required: true })} placeholder="rtsp://..." /></div>
            <div className="space-y-1"><Label htmlFor="camera-rtsp-sub">RTSP URL (sub stream, nếu có)</Label><Input id="camera-rtsp-sub" {...register("rtsp_sub")} placeholder="rtsp://..." /></div>
            <div className="space-y-1"><Label htmlFor="camera-location">Vị trí</Label><Input id="camera-location" {...register("location")} placeholder="Tầng 3" /></div>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="h-4 w-4" {...register("enabled")} /> Bật camera</label>
            <DialogFooter>
              <Button type="button" variant="outline" disabled={saving} onClick={() => setFormOpen(false)}>Huỷ</Button>
              <Button type="submit" disabled={saving}>{saving && <Loader2 className="h-4 w-4 animate-spin" />}{editing ? "Lưu thay đổi" : "Thêm"}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={deleting !== null} onOpenChange={(open) => { if (!open && !deleteBusy) setDeleting(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Xóa camera {deleting?.name ?? deleting?.code}?</DialogTitle>
            <DialogDescription>
              Camera sẽ bị dừng và xóa khỏi danh sách. Dữ liệu cảnh báo, theo dõi và vùng giám sát liên kết với camera cũng sẽ bị xóa.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" variant="outline" disabled={deleteBusy} onClick={() => setDeleting(null)}>Huỷ</Button>
            <Button type="button" variant="destructive" disabled={deleteBusy} onClick={() => void deleteCamera()}>
              {deleteBusy && <Loader2 className="h-4 w-4 animate-spin" />} Xác nhận xóa
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
