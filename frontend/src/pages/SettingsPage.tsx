import { useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTheme } from "@/contexts/ThemeContext";
import { logAction } from "@/lib/logger";

const KEY = "aems.settings";

interface Settings {
  telegramToken: string;
  telegramChatId: string;
  telegramEnabled: boolean;
  cameraRetry: number;
  aiConfidence: number;
  threshold: number;
  language: string;
  timezone: string;
}

const DEFAULTS: Settings = {
  telegramToken: "",
  telegramChatId: "",
  telegramEnabled: false,
  cameraRetry: 3,
  aiConfidence: 0.5,
  threshold: 0.6,
  language: "vi",
  timezone: "Asia/Ho_Chi_Minh",
};

function load(): Settings {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || "{}") };
  } catch {
    return DEFAULTS;
  }
}

/** Settings — Telegram, Camera, AI, Threshold, Theme, Language, Timezone. */
export function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [s, setS] = useState<Settings>(load);

  const update = <K extends keyof Settings>(k: K, v: Settings[K]) =>
    setS((prev) => ({ ...prev, [k]: v }));

  const save = () => {
    localStorage.setItem(KEY, JSON.stringify(s));
    logAction("settings_change", "cập nhật cấu hình");
    toast.success("Đã lưu cài đặt");
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Settings"
        description="Cấu hình hệ thống & giao diện"
        actions={<Button onClick={save}>Lưu thay đổi</Button>}
      />
      <Card>
        <CardContent className="pt-4">
          <Tabs defaultValue="telegram">
            <TabsList className="flex-wrap">
              <TabsTrigger value="telegram">Telegram</TabsTrigger>
              <TabsTrigger value="camera">Camera</TabsTrigger>
              <TabsTrigger value="ai">AI</TabsTrigger>
              <TabsTrigger value="threshold">Threshold</TabsTrigger>
              <TabsTrigger value="appearance">Giao diện</TabsTrigger>
            </TabsList>

            <TabsContent value="telegram" className="max-w-md space-y-3">
              <div className="flex items-center gap-2">
                <Switch
                  checked={s.telegramEnabled}
                  onCheckedChange={(v) => update("telegramEnabled", v)}
                />
                <Label className="font-normal">Bật thông báo Telegram</Label>
              </div>
              <div className="space-y-1">
                <Label>Bot Token</Label>
                <Input value={s.telegramToken} onChange={(e) => update("telegramToken", e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Chat ID</Label>
                <Input value={s.telegramChatId} onChange={(e) => update("telegramChatId", e.target.value)} />
              </div>
            </TabsContent>

            <TabsContent value="camera" className="max-w-md space-y-3">
              <div className="space-y-1">
                <Label>Số lần thử kết nối lại</Label>
                <Input
                  type="number"
                  value={s.cameraRetry}
                  onChange={(e) => update("cameraRetry", Number(e.target.value))}
                />
              </div>
            </TabsContent>

            <TabsContent value="ai" className="max-w-md space-y-3">
              <div className="space-y-1">
                <Label>Confidence tối thiểu ({s.aiConfidence})</Label>
                <Input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={s.aiConfidence}
                  onChange={(e) => update("aiConfidence", Number(e.target.value))}
                />
              </div>
            </TabsContent>

            <TabsContent value="threshold" className="max-w-md space-y-3">
              <div className="space-y-1">
                <Label>Ngưỡng cảnh báo ({s.threshold})</Label>
                <Input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={s.threshold}
                  onChange={(e) => update("threshold", Number(e.target.value))}
                />
              </div>
            </TabsContent>

            <TabsContent value="appearance" className="max-w-md space-y-3">
              <div className="space-y-1">
                <Label>Giao diện</Label>
                <Select value={theme} onValueChange={(v) => setTheme(v as "light" | "dark")}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light Mode</SelectItem>
                    <SelectItem value="dark">Dark Mode</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Ngôn ngữ</Label>
                <Select value={s.language} onValueChange={(v) => update("language", v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="vi">Tiếng Việt</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Múi giờ</Label>
                <Select value={s.timezone} onValueChange={(v) => update("timezone", v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Asia/Ho_Chi_Minh">Asia/Ho_Chi_Minh</SelectItem>
                    <SelectItem value="UTC">UTC</SelectItem>
                    <SelectItem value="Asia/Singapore">Asia/Singapore</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
