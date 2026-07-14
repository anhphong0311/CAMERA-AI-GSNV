"""
Unit tests — BenchmarkService tracking.
"""

from app.modules.tracking.benchmark.benchmark_service import BenchmarkService


class TestTrackingBenchmark:
    """Test benchmark tracking."""

    def test_benchmark_runs(self, tracking_config) -> None:
        """Benchmark trả FPS + số liệu hợp lệ."""
        bench = BenchmarkService(tracking_config)
        result = bench.run(frames=30, num_people=20, width=1280, height=720)
        assert result.frames == 30
        assert result.num_people == 20
        assert result.fps > 0
        assert result.final_active_tracks >= 1
        assert 0.0 <= result.track_stability <= 1.0

    def test_benchmark_stable_ids(self, tracking_config) -> None:
        """20 người di chuyển đều → ít ID switch, stability cao."""
        bench = BenchmarkService(tracking_config)
        result = bench.run(frames=50, num_people=20)
        # Người di chuyển tuyến tính → tracker phải giữ ổn định ID
        assert result.id_switches <= 5
        assert result.track_stability >= 0.7

    def test_benchmark_to_dict(self, tracking_config) -> None:
        """Serialize kết quả benchmark."""
        bench = BenchmarkService(tracking_config)
        d = bench.run(frames=10, num_people=5).to_dict()
        assert "fps" in d
        assert "id_switches" in d
        assert "track_stability" in d
