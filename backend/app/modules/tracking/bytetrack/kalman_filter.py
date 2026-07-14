"""
Kalman Filter cho ByteTrack — mô hình vận tốc không đổi 8 chiều.

State: [x, y, a, h, vx, vy, va, vh]
  x, y: tâm bbox; a: tỉ lệ w/h; h: chiều cao.

Cài đặt thuần numpy (KHÔNG scipy) để không thêm dependency nặng.
"""

from __future__ import annotations

import numpy as np


class KalmanFilter:
    """Kalman filter theo dõi bbox trong không gian ảnh (chuẩn ByteTrack/SORT)."""

    def __init__(self) -> None:
        ndim, dt = 4, 1.0
        self._motion_mat = np.eye(2 * ndim, 2 * ndim)
        for i in range(ndim):
            self._motion_mat[i, ndim + i] = dt
        self._update_mat = np.eye(ndim, 2 * ndim)
        self._std_weight_position = 1.0 / 20
        self._std_weight_velocity = 1.0 / 160

    def initiate(self, measurement: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Khởi tạo track từ đo lường [x, y, a, h].

        Returns:
            (mean 8-dim, covariance 8x8).
        """
        mean_pos = measurement
        mean_vel = np.zeros_like(mean_pos)
        mean = np.r_[mean_pos, mean_vel]
        std = [
            2 * self._std_weight_position * measurement[3],
            2 * self._std_weight_position * measurement[3],
            1e-2,
            2 * self._std_weight_position * measurement[3],
            10 * self._std_weight_velocity * measurement[3],
            10 * self._std_weight_velocity * measurement[3],
            1e-5,
            10 * self._std_weight_velocity * measurement[3],
        ]
        covariance = np.diag(np.square(std))
        return mean, covariance

    def predict(
        self, mean: np.ndarray, covariance: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Dự đoán bước kế tiếp (prediction step)."""
        std_pos = [
            self._std_weight_position * mean[3],
            self._std_weight_position * mean[3],
            1e-2,
            self._std_weight_position * mean[3],
        ]
        std_vel = [
            self._std_weight_velocity * mean[3],
            self._std_weight_velocity * mean[3],
            1e-5,
            self._std_weight_velocity * mean[3],
        ]
        motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))
        mean = self._motion_mat @ mean
        covariance = self._motion_mat @ covariance @ self._motion_mat.T + motion_cov
        return mean, covariance

    def project(
        self, mean: np.ndarray, covariance: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Chiếu state về không gian đo lường."""
        std = [
            self._std_weight_position * mean[3],
            self._std_weight_position * mean[3],
            1e-1,
            self._std_weight_position * mean[3],
        ]
        innovation_cov = np.diag(np.square(std))
        mean = self._update_mat @ mean
        covariance = self._update_mat @ covariance @ self._update_mat.T
        return mean, covariance + innovation_cov

    def update(
        self, mean: np.ndarray, covariance: np.ndarray, measurement: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Cập nhật state với đo lường mới (correction step)."""
        projected_mean, projected_cov = self.project(mean, covariance)
        # Kalman gain: giải hệ tuyến tính bằng numpy (thay cho scipy cholesky)
        kalman_gain = covariance @ self._update_mat.T @ np.linalg.inv(projected_cov)
        innovation = measurement - projected_mean
        new_mean = mean + innovation @ kalman_gain.T
        new_covariance = covariance - kalman_gain @ projected_cov @ kalman_gain.T
        return new_mean, new_covariance

    def multi_predict(
        self, means: np.ndarray, covariances: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Dự đoán hàng loạt (loop đơn giản cho rõ ràng)."""
        for i in range(len(means)):
            means[i], covariances[i] = self.predict(means[i], covariances[i])
        return means, covariances
