"""
Unit test — PoseAssociator (ghép pose ↔ track theo IoU).
"""

from __future__ import annotations

from app.modules.behavior.feature_engine import PoseAssociator
from tests.modules.behavior.conftest import make_pose, make_tracking_view


def test_associate_matches_overlapping():
    tv = make_tracking_view(1, 0, [(10, (100, 140, 180, 360))])
    poses = [make_pose((102, 142, 182, 362))]
    assoc = PoseAssociator(0.3).associate(tv.tracks, poses)
    assert 10 in assoc


def test_associate_skips_far_pose():
    tv = make_tracking_view(1, 0, [(10, (100, 140, 180, 360))])
    poses = [make_pose((900, 900, 980, 1100))]
    assoc = PoseAssociator(0.3).associate(tv.tracks, poses)
    assert assoc == {}


def test_associate_one_pose_per_track():
    tv = make_tracking_view(
        1, 0, [(1, (100, 140, 180, 360)), (2, (300, 140, 380, 360))]
    )
    poses = [make_pose((100, 140, 180, 360)), make_pose((300, 140, 380, 360))]
    assoc = PoseAssociator(0.3).associate(tv.tracks, poses)
    assert set(assoc.keys()) == {1, 2}
