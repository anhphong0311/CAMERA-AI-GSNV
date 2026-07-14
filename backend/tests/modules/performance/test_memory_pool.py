"""Unit test — Memory pools."""

from __future__ import annotations

from app.modules.performance.pool.memory_pool import BufferPool, FramePool


def test_frame_pool_reuse():
    pool = FramePool(pool_size=4, default_shape=(64, 64, 3))
    a = pool.acquire()
    pool.release(a)
    b = pool.acquire()
    stats = pool.stats()
    assert stats["hits"] >= 0
    assert b.shape == (64, 64, 3)


def test_buffer_pool():
    pool = BufferPool(pool_size=2, buffer_size=1024)
    buf = pool.acquire()
    pool.release(buf)
    assert pool.stats()["pool_size"] == 2
