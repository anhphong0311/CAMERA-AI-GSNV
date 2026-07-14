import { Brain, Cpu, Database, LineChart, Play, RefreshCw } from "lucide-react";
import { useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { LineChartCard } from "@/components/charts/Charts";
import {
  useTrainingDashboard,
  useTrainingJobs,
  useDatasetStatistics,
  useStartTraining,
} from "@/hooks/mlPlatform";

/** ML Training Platform Dashboard — Sprint 13 / v2.0 */
export function TrainingDashboardPage() {
  const { data: overview, refetch } = useTrainingDashboard();
  const { data: jobs } = useTrainingJobs();
  const { data: dsStats } = useDatasetStatistics();
  const startTraining = useStartTraining();
  const [starting, setStarting] = useState(false);

  const lossCurve = overview?.loss_curve ?? [];
  const accCurve = overview?.accuracy_curve ?? [];

  const handleStartDemo = async () => {
    setStarting(true);
    try {
      await startTraining.mutateAsync();
      refetch();
    } finally {
      setStarting(false);
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="AI Training Platform"
        description="Dataset · Annotation · Training · Model Registry · Deployment (v2.0)"
        actions={
          <Button size="sm" onClick={() => refetch()} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh
          </Button>
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Database className="h-4 w-4" /> Datasets
            </div>
            <p className="text-2xl font-bold">{dsStats?.datasets ?? 0}</p>
            <p className="text-xs text-muted-foreground">
              {dsStats?.annotated_items ?? 0}/{dsStats?.total_items ?? 0} annotated (
              {dsStats?.annotation_rate ?? 0}%)
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Cpu className="h-4 w-4" /> Active Jobs
            </div>
            <p className="text-2xl font-bold">{overview?.active_jobs ?? 0}</p>
            <p className="text-xs text-muted-foreground">{overview?.total_jobs ?? 0} total</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Brain className="h-4 w-4" /> Active Learning
            </div>
            <p className="text-2xl font-bold">{overview?.active_learning?.queued ?? 0}</p>
            <p className="text-xs text-muted-foreground">queued for review</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <LineChart className="h-4 w-4" /> FP/FN Open
            </div>
            <p className="text-2xl font-bold">{overview?.fp_fn_open ?? 0}</p>
            <p className="text-xs text-muted-foreground">cases pending</p>
          </CardContent>
        </Card>
      </div>

      {overview?.latest_job && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Latest Training Job</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">{overview.latest_job.name}</span>
              <Badge variant={overview.latest_job.status === "completed" ? "default" : "secondary"}>
                {overview.latest_job.status}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {overview.latest_job.architecture}
              </span>
            </div>
            <Progress value={overview.latest_job.progress ?? 0} />
            <p className="text-xs text-muted-foreground">
              Epoch {overview.latest_job.current_epoch}/{overview.latest_job.total_epochs}
            </p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <LineChartCard title="Train Loss" data={lossCurve} xKey="epoch" yKey="loss" />
        <LineChartCard title="mAP50" data={accCurve} xKey="epoch" yKey="map50" />
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Training Jobs</CardTitle>
          <Button size="sm" disabled={starting} onClick={handleStartDemo}>
            <Play className="mr-2 h-4 w-4" />
            {starting ? "Starting..." : "Quick Demo Train"}
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {(jobs ?? []).slice(0, 8).map((job) => (
              <div
                key={job.id}
                className="flex items-center justify-between rounded border p-2 text-sm"
              >
                <span>{job.name}</span>
                <Badge variant="outline">{job.status}</Badge>
                <span className="text-muted-foreground">{job.architecture}</span>
                <span>{job.progress ?? 0}%</span>
              </div>
            ))}
            {!jobs?.length && (
              <p className="text-sm text-muted-foreground">No training jobs yet.</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
