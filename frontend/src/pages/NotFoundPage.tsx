import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Trang 404 — route không tồn tại.
 */
export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <CardTitle className="text-6xl font-bold text-primary">404</CardTitle>
          <CardDescription>Trang bạn tìm kiếm không tồn tại.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link to="/">Về Dashboard</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
