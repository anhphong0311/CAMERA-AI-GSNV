import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient, unwrap } from "@/lib/api";

async function get<T>(url: string): Promise<T> {
  const res = await apiClient.get(url);
  return unwrap<T>(res.data);
}

async function post<T>(url: string, body?: unknown): Promise<T> {
  const res = await apiClient.post(url, body);
  return unwrap<T>(res.data);
}

export interface TrainingJob {
  id: string;
  name: string;
  status: string;
  architecture: string;
  progress?: number;
  current_epoch?: number;
  total_epochs?: number;
  metrics?: Record<string, number>;
}

export interface DatasetStats {
  datasets: number;
  total_items: number;
  annotated_items: number;
  annotation_rate: number;
}

export interface TrainingDashboard {
  dataset_stats: DatasetStats;
  active_jobs: number;
  total_jobs: number;
  latest_job: TrainingJob | null;
  loss_curve: { epoch: number; loss: number; val_loss: number }[];
  accuracy_curve: { epoch: number; map50: number; map50_95: number }[];
  active_learning: { queued: number; reviewed: number; threshold: number };
  fp_fn_open: number;
}

export function useTrainingDashboard() {
  return useQuery({
    queryKey: ["training", "dashboard"],
    queryFn: () => get<TrainingDashboard>("/training/dashboard/overview"),
    refetchInterval: 5000,
  });
}

export function useTrainingJobs() {
  return useQuery({
    queryKey: ["training", "jobs"],
    queryFn: () => get<TrainingJob[]>("/training"),
    refetchInterval: 5000,
  });
}

export function useDatasetStatistics() {
  return useQuery({
    queryKey: ["dataset", "statistics"],
    queryFn: () => get<DatasetStats>("/dataset/statistics"),
  });
}

/** Quick demo: create dataset + version + job + start */
export function useStartTraining() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const ds = await post<{ id: string }>("/dataset", {
        name: `demo-${Date.now()}`,
        source_type: "snapshot",
      });
      await post(`/dataset/${ds.id}/import`, { paths: ["/demo/img1.jpg", "/demo/img2.jpg"] });
      const ver = await post<{ id: string }>(`/dataset/${ds.id}/versions`, { version: "v1" });
      const job = await post<TrainingJob>("/training", {
        name: `train-${Date.now()}`,
        dataset_version_id: ver.id,
        architecture: "yolo11",
        config: { epochs: 5 },
      });
      await post(`/training/${job.id}/start?simulate=true`, {});
      return job;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["training"] });
      qc.invalidateQueries({ queryKey: ["dataset"] });
    },
  });
}

export function useModelRegistry() {
  return useQuery({
    queryKey: ["model", "registry"],
    queryFn: () => get<Record<string, unknown>[]>("/model"),
  });
}

export function useAnnotationLabels() {
  return useQuery({
    queryKey: ["annotation", "labels"],
    queryFn: () => get<string[]>("/annotation/labels"),
  });
}
