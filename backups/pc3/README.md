# PC3 migration backup

`aems-pc3-20260927.zip.aes` is an AES-256-GCM encrypted migration snapshot.

- Source commit: `13a37ca`
- Encrypted SHA-256: `0E25A3763C4DD079D0CDE227DF1F3F9657BF6C0FB05A128D86CEC09D403D9026`
- Decrypted ZIP SHA-256: `C34E6C7E26A439067222B98F0D674A54F004365C9B836D85182A526F889D218B`
- Recovery key: intentionally not stored in Git or GitHub

Decrypt on PC3 with PowerShell 7:

```powershell
.\deploy\scripts\backup-crypto.ps1 `
  -Mode Unprotect `
  -InputPath .\backups\pc3\aems-pc3-20260927.zip.aes `
  -OutputPath .\aems-pc3-20260927.zip `
  -KeyPath <path-to-AEMS-PC3-20260927.backup-key.txt>
```

The ZIP contains the PostgreSQL dump, `.env`, application configuration,
evidence files, runtime state, and the source machine's model directory.
Follow `RESTORE-PC3.md` inside the decrypted ZIP to restore the system.
