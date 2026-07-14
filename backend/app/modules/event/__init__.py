"""
Module Event Processing & Notification Center (Sprint 7).

Trung tâm xử lý mọi BehaviorEvent: nhận → validate → lưu → snapshot → video
evidence → notification queue → Telegram (retry/dedup/cooldown).

KHÔNG chứa logic AI Detect / Tracking / Pose / Rule / Dashboard.
"""
