"""
DTO — trạng thái vòng đời track.
"""

from enum import Enum


class TrackState(str, Enum):
    """
    Trạng thái vòng đời của một track.

    NEW: Vừa được tạo (frame đầu tiên).
    TRACKING: Đang được theo dõi liên tục.
    LOST: Tạm mất (chưa match frame này, còn trong buffer).
    RECOVERED: Vừa tìm lại sau khi LOST.
    REMOVED: Bị xóa (mất quá lâu).
    """

    NEW = "NEW"
    TRACKING = "TRACKING"
    LOST = "LOST"
    RECOVERED = "RECOVERED"
    REMOVED = "REMOVED"
