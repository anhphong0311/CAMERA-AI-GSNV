import { useState } from "react";
import { toast } from "sonner";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { Loading } from "@/components/Loading";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { RuleFormDialog } from "@/components/rule/RuleFormDialog";
import { useDeleteRule, useRules, useToggleRule } from "@/hooks/api";
import type { Rule } from "@/types";

/** Rule Management — CRUD rule, bật/tắt, priority, cooldown, threshold. */
export function RulesPage() {
  const { data: rules, isLoading } = useRules();
  const toggle = useToggleRule();
  const del = useDeleteRule();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Rule | null>(null);

  const openCreate = () => {
    setEditing(null);
    setDialogOpen(true);
  };
  const openEdit = (r: Rule) => {
    setEditing(r);
    setDialogOpen(true);
  };
  const remove = async (r: Rule) => {
    if (!confirm(`Xoá rule ${r.id}?`)) return;
    try {
      await del.mutateAsync(r.id);
      toast.success("Đã xoá rule");
    } catch {
      toast.error("Xoá thất bại");
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Rule Management"
        description="Quản lý luật phát hiện hành vi (CRUD)"
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" /> Thêm Rule
          </Button>
        }
      />
      <Card>
        <CardContent className="pt-4">
          {isLoading ? (
            <Loading />
          ) : (rules ?? []).length === 0 ? (
            <EmptyState title="Chưa có rule" description="Bấm Thêm Rule để tạo mới" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Bật</TableHead>
                  <TableHead>ID / Tên</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Cooldown</TableHead>
                  <TableHead className="text-right">Thao tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(rules ?? []).map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>
                      <Switch
                        checked={r.enabled}
                        onCheckedChange={(v) =>
                          toggle.mutate({ id: r.id, enabled: v })
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <p className="font-medium">{r.name ?? r.id}</p>
                      <p className="text-xs text-muted-foreground">{r.id}</p>
                    </TableCell>
                    <TableCell>
                      <SeverityBadge severity={r.severity} />
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">P{r.priority}</Badge>
                    </TableCell>
                    <TableCell>{r.cooldown ?? "—"}s</TableCell>
                    <TableCell className="text-right">
                      <Button size="sm" variant="ghost" onClick={() => openEdit(r)}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-destructive"
                        onClick={() => remove(r)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <RuleFormDialog open={dialogOpen} onOpenChange={setDialogOpen} rule={editing} />
    </div>
  );
}
