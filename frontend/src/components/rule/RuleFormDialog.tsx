import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateRule, useUpdateRule, type RulePayload } from "@/hooks/api";
import type { Rule } from "@/types";

const schema = z.object({
  id: z.string().min(1, "Nhập ID rule"),
  name: z.string().optional(),
  description: z.string().optional(),
  severity: z.string(),
  priority: z.coerce.number().int().min(1).max(5),
  cooldown: z.coerce.number().min(0).optional(),
  enabled: z.boolean(),
  conditions: z.string(),
});
type FormValues = z.infer<typeof schema>;

const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"];

/** Form tạo/sửa Rule (CRUD). */
export function RuleFormDialog({
  open,
  onOpenChange,
  rule,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  rule: Rule | null;
}) {
  const create = useCreateRule();
  const update = useUpdateRule();
  const editing = !!rule;

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      id: "",
      name: "",
      description: "",
      severity: "MEDIUM",
      priority: 3,
      cooldown: 60,
      enabled: true,
      conditions: "[]",
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        id: rule?.id ?? "",
        name: rule?.name ?? "",
        description: rule?.description ?? "",
        severity: String(rule?.severity ?? "MEDIUM"),
        priority: rule?.priority ?? 3,
        cooldown: rule?.cooldown ?? 60,
        enabled: rule?.enabled ?? true,
        conditions: "[]",
      });
    }
  }, [open, rule, reset]);

  const onSubmit = async (values: FormValues) => {
    let conditions: unknown;
    try {
      conditions = JSON.parse(values.conditions || "[]");
    } catch {
      toast.error("Conditions phải là JSON hợp lệ");
      return;
    }
    const payload: RulePayload = {
      id: values.id,
      name: values.name || values.id,
      description: values.description ?? "",
      severity: values.severity,
      priority: values.priority,
      cooldown: values.cooldown ?? null,
      enabled: values.enabled,
      actions: ["alert"],
      conditions: conditions as RulePayload["conditions"],
    };
    try {
      if (editing) await update.mutateAsync(payload);
      else await create.mutateAsync(payload);
      toast.success(editing ? "Đã cập nhật rule" : "Đã tạo rule");
      onOpenChange(false);
    } catch {
      toast.error("Lưu rule thất bại");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{editing ? "Sửa Rule" : "Tạo Rule mới"}</DialogTitle>
        </DialogHeader>
        <form className="space-y-3" onSubmit={handleSubmit(onSubmit)}>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>ID</Label>
              <Input {...register("id")} disabled={editing} placeholder="PHONE_USAGE" />
              {errors.id && <p className="text-xs text-destructive">{errors.id.message}</p>}
            </div>
            <div className="space-y-1">
              <Label>Tên</Label>
              <Input {...register("name")} placeholder="Sử dụng điện thoại" />
            </div>
          </div>
          <div className="space-y-1">
            <Label>Mô tả</Label>
            <Textarea rows={2} {...register("description")} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1">
              <Label>Severity</Label>
              <Select value={watch("severity")} onValueChange={(v) => setValue("severity", v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SEVERITIES.map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Priority (1-5)</Label>
              <Input type="number" {...register("priority")} />
            </div>
            <div className="space-y-1">
              <Label>Cooldown (s)</Label>
              <Input type="number" {...register("cooldown")} />
            </div>
          </div>
          <div className="space-y-1">
            <Label>Conditions (JSON)</Label>
            <Textarea rows={3} {...register("conditions")} className="font-mono text-xs" />
          </div>
          <div className="flex items-center gap-2">
            <Switch checked={watch("enabled")} onCheckedChange={(v) => setValue("enabled", v)} />
            <Label className="font-normal">Kích hoạt rule</Label>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Huỷ
            </Button>
            <Button type="submit" disabled={create.isPending || update.isPending}>
              {editing ? "Cập nhật" : "Tạo"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
