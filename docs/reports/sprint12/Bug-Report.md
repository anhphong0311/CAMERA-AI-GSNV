# Bug Report — Release v1.0.0

## Summary

| Severity | Total | Fixed | Open |
|----------|------:|------:|-----:|
| Critical | 0 | 0 | 0 |
| High | 0 | 0 | 0 |
| Medium | 2 | 2 | 0 |
| Low | 3 | 3 | 0 |

## Fixed in Sprint 12

| ID | Severity | Module | Description | Resolution |
|----|----------|--------|-------------|------------|
| BUG-012-001 | Medium | QA | Coverage tooling not configured | Added `.coveragerc`, pytest-cov, CI gate |
| BUG-012-002 | Medium | Ops | Health version string stale | Updated to 1.0.0 |
| BUG-012-003 | Low | Tests | Watchdog mock async issue | Fixed MagicMock vs AsyncMock |
| BUG-012-004 | Low | Tests | TelegramConfig missing `enabled` | Fixed test fixtures |
| BUG-012-005 | Low | Docs | README showed Sprint 1 status | Updated to v1.0.0 |

## Known Issues (Accepted)

| ID | Severity | Description | Workaround |
|----|----------|-------------|------------|
| KNOWN-001 | Low | Stub routes `/employees`, `/alerts` | Use module APIs |
| KNOWN-002 | Low | Playwright E2E not in CI | Run manually: `npm run test:e2e` |
| KNOWN-003 | Low | Self-signed SSL browser warning | Use Let's Encrypt in production |

## Bug Tracking Process

```
Report → Triage (Severity/Priority) → Fix → Test → Close → Release Note
```

Template for future bugs:

```
ID: BUG-XXX-NNN
Severity: Critical|High|Medium|Low
Priority: P0|P1|P2|P3
Status: Open|In Progress|Fixed|Closed
Module: camera|ai|tracking|...
Description: ...
Steps to reproduce: ...
Expected: ...
Actual: ...
Resolution: ...
```
