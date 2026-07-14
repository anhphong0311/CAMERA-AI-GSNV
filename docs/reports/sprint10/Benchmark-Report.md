# Sprint 10 — Benchmark Report Template

Run via API:

```http
POST /api/v1/system/benchmark
Authorization: Bearer <token>
Content-Type: application/json

{
  "backends": ["pytorch", "onnx", "tensorrt"],
  "runs": 50,
  "warmup": 5,
  "image_size": 640
}
```

## Expected Output Structure

```json
{
  "data": {
    "runs": 50,
    "device": "cuda:0",
    "precision": "fp32",
    "results": [
      {
        "backend": "pytorch",
        "success": true,
        "avg_inference_ms": 12.5,
        "fps": 80.0,
        "gpu_percent": 45.0,
        "vram_mb": 1024.0
      },
      {
        "backend": "onnx",
        "success": true,
        "avg_inference_ms": 8.2,
        "fps": 122.0
      },
      {
        "backend": "tensorrt",
        "success": true,
        "avg_inference_ms": 5.1,
        "fps": 196.0
      }
    ],
    "best_backend": "tensorrt",
    "comparison": [
      {"backend": "pytorch", "fps": 80.0, "speedup_vs_pytorch": 1.0},
      {"backend": "onnx", "fps": 122.0, "speedup_vs_pytorch": 1.53},
      {"backend": "tensorrt", "fps": 196.0, "speedup_vs_pytorch": 2.45}
    ]
  }
}
```

## Half-Precision (FP16)

Set in `config/performance.yaml`:

```yaml
backend:
  precision: fp16
```

Re-run benchmark and compare accuracy/FPS/latency/VRAM across fp32 vs fp16.

## Notes

- Benchmark requires model weights at `detection.yaml → model.path`.
- ONNX/TRT may fail in CPU-only CI — API returns `success: false` + `error` per backend.
- Production: use TensorRT for lowest latency and VRAM on RTX 3060/4070/4080.
