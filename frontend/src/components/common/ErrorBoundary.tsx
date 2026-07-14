import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { AlertOctagon } from "lucide-react";

interface Props {
  children: ReactNode;
}
interface State {
  hasError: boolean;
  message?: string;
}

/**
 * ErrorBoundary — chặn lỗi render, hiển thị UI dự phòng thay vì màn hình trắng.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("UI error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[300px] flex-col items-center justify-center gap-3 text-center">
          <AlertOctagon className="h-10 w-10 text-destructive" />
          <p className="font-semibold">Đã xảy ra lỗi hiển thị</p>
          <p className="max-w-md text-sm text-muted-foreground">{this.state.message}</p>
          <Button onClick={() => this.setState({ hasError: false })}>Thử lại</Button>
        </div>
      );
    }
    return this.props.children;
  }
}
