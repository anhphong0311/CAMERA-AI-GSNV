"""Unit test — Service layer admin (users/roles/config/models/backup/storage)."""

from __future__ import annotations

import pytest

from app.exceptions.base import ConflictError, NotFoundError, ValidationError
from app.modules.admin.repositories.memory import (
    InMemoryAuditRepository,
    InMemoryBackupRepository,
    InMemoryModelRepository,
)
from app.modules.admin.services import (
    AuditService,
    BackupService,
    ModelService,
    RestoreService,
)


# ---------- Users ----------
def test_user_create_and_duplicate(container):
    user = container.users.create(username="alice", password="Str0ng@Pass", role="viewer")
    assert user.username == "alice"
    with pytest.raises(ConflictError):
        container.users.create(username="alice", password="Str0ng@Pass")


def test_user_weak_password_rejected(container):
    with pytest.raises(ValidationError):
        container.users.create(username="bob", password="weak")


def test_user_invalid_role_rejected(container):
    with pytest.raises(ValidationError):
        container.users.create(username="bob", password="Str0ng@Pass", role="ghost")


def test_cannot_delete_last_admin(container):
    admin = container.users.list()[0]
    with pytest.raises(ConflictError):
        container.users.delete(admin.id)


def test_reset_password_updates_hash(container):
    u = container.users.create(username="carl", password="Str0ng@Pass")
    old = u.password_hash
    container.users.reset_password(u.id, "N3w@Password")
    assert container.users.get(u.id).password_hash != old


# ---------- Roles ----------
def test_role_crud_and_system_protection(container):
    container.roles.create("auditor", "Audit role", ["audit:read"])
    assert container.roles.get("auditor").description == "Audit role"
    with pytest.raises(ConflictError):
        container.roles.delete("admin")  # system role
    container.roles.delete("auditor")
    with pytest.raises(NotFoundError):
        container.roles.get("auditor")


def test_role_invalid_permission(container):
    with pytest.raises(ValidationError):
        container.roles.create("x", "", ["not:a:perm"])


# ---------- Config ----------
def test_config_seed_and_policy(container):
    assert container.config.get_value("system.company_name") == "AEMS"
    policy = container.config.password_policy()
    assert policy.min_length >= 8


def test_config_set_and_get(container):
    container.config.set_value("system.company_name", "ACME", updated_by="tester")
    assert container.config.get_value("system.company_name") == "ACME"


# ---------- Models ----------
def test_model_switch_and_rollback():
    audit = AuditService(InMemoryAuditRepository())
    svc = ModelService(InMemoryModelRepository(), audit)
    m1 = svc.register(name="yolo", version="1.0", path="/m/1.pt")
    m2 = svc.register(name="yolo", version="2.0", path="/m/2.pt")
    svc.switch(m1.id)
    assert svc.get(m1.id).is_active
    svc.switch(m2.id)
    assert svc.get(m2.id).is_active and not svc.get(m1.id).is_active
    rolled = svc.rollback("yolo")
    assert rolled.id == m1.id and rolled.is_active


def test_model_cannot_delete_active():
    audit = AuditService(InMemoryAuditRepository())
    svc = ModelService(InMemoryModelRepository(), audit)
    m = svc.register(name="yolo", version="1.0", path="/m/1.pt")
    svc.switch(m.id)
    with pytest.raises(ConflictError):
        svc.delete(m.id)


# ---------- Backup / Restore ----------
def test_backup_and_restore_config(tmp_path):
    audit = AuditService(InMemoryAuditRepository())
    repo = InMemoryBackupRepository()
    store = {"system.company_name": "AEMS"}
    backup = BackupService(
        repo, audit, base_dir=str(tmp_path),
        providers={"config": lambda: dict(store)},
    )
    applied = {}
    restore = RestoreService(
        repo, audit, handlers={"config": lambda data: applied.update(data) or {"n": len(data)}}
    )
    record = backup.create_backup("config", actor="tester")
    assert record.id is not None and record.status == "completed"
    summary = restore.restore(record.id, actor="tester")
    assert summary["applied"] is True
    assert applied["system.company_name"] == "AEMS"


def test_restore_database_blocked(tmp_path):
    audit = AuditService(InMemoryAuditRepository())
    repo = InMemoryBackupRepository()
    backup = BackupService(repo, audit, base_dir=str(tmp_path))
    rec = backup.create_backup("database")
    restore = RestoreService(repo, audit)
    with pytest.raises(ValidationError):
        restore.restore(rec.id)


# ---------- Storage ----------
def test_storage_retention_and_cleanup(container):
    retention = container.storage.retention()
    assert retention["video_days"] >= 1
    # cleanup trên thư mục không tồn tại → an toàn, 0 file
    result = container.storage.cleanup("video", actor="tester")
    assert result["removed"] == 0


# ---------- Audit ----------
def test_audit_logging(container):
    container.audit.log("test", "unit", username="tester", target="x")
    rows = container.audit.query(module="unit")
    assert any(r.action == "test" for r in rows)
