import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate, useLocation } from "react-router-dom";
import { ShieldCheck, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";

const schema = z.object({
  username: z.string().min(1, "Nhập tên đăng nhập"),
  password: z.string().min(1, "Nhập mật khẩu"),
  remember: z.boolean(),
});
type FormValues = z.infer<typeof schema>;

/**
 * Trang đăng nhập — JWT + Remember Login + Role Permission (suy từ tài khoản).
 */
export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { username: "admin", password: "admin", remember: true },
  });

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/";

  const onSubmit = async (values: FormValues) => {
    setSubmitting(true);
    try {
      await login(values.username, values.password, values.remember);
      toast.success("Đăng nhập thành công");
      navigate(from, { replace: true });
    } catch {
      toast.error("Đăng nhập thất bại");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
      <Card className="w-full max-w-md border-slate-700 bg-card/95 shadow-2xl backdrop-blur">
        <CardHeader className="space-y-2 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary/15">
            <ShieldCheck className="h-7 w-7 text-primary" />
          </div>
          <CardTitle className="text-2xl">AEMS</CardTitle>
          <CardDescription>AI Operation Center — Đăng nhập quản trị</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-2">
              <Label htmlFor="username">Tên đăng nhập</Label>
              <Input id="username" autoComplete="username" {...register("username")} />
              {errors.username && (
                <p className="text-xs text-destructive">{errors.username.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Mật khẩu</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-xs text-destructive">{errors.password.message}</p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="remember"
                checked={watch("remember")}
                onCheckedChange={(v) => setValue("remember", Boolean(v))}
              />
              <Label htmlFor="remember" className="text-sm font-normal">
                Ghi nhớ đăng nhập
              </Label>
            </div>
            <Button className="w-full" type="submit" disabled={submitting}>
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Đăng nhập
            </Button>
            <p className="text-center text-xs text-muted-foreground">
              Vai trò suy theo tài khoản: <b>admin</b> · <b>supervisor</b> · <b>viewer</b>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
