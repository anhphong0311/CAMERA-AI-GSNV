param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Protect", "Unprotect")]
    [string]$Mode,

    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [Parameter(Mandatory = $true)]
    [string]$KeyPath
)

$ErrorActionPreference = "Stop"

$magic = [System.Text.Encoding]::ASCII.GetBytes("AEMSBK01")
$nonceSize = 12
$tagSize = 16

function Assert-OutputDoesNotExist([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        throw "Output already exists: $Path"
    }

    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
}

if ($Mode -eq "Protect") {
    Assert-OutputDoesNotExist $OutputPath
    Assert-OutputDoesNotExist $KeyPath

    $plain = [System.IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $InputPath))
    $key = [byte[]]::new(32)
    $nonce = [byte[]]::new($nonceSize)
    $tag = [byte[]]::new($tagSize)
    $cipher = [byte[]]::new($plain.Length)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($key)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($nonce)

    $aes = [System.Security.Cryptography.AesGcm]::new($key, $tagSize)
    try {
        $aes.Encrypt($nonce, $plain, $cipher, $tag, $magic)
    }
    finally {
        $aes.Dispose()
    }

    $stream = [System.IO.File]::Create($OutputPath)
    try {
        $stream.Write($magic)
        $stream.Write($nonce)
        $stream.Write($tag)
        $stream.Write($cipher)
    }
    finally {
        $stream.Dispose()
    }

    [System.IO.File]::WriteAllText($KeyPath, [Convert]::ToBase64String($key))
    Write-Output "Encrypted backup: $OutputPath"
    Write-Output "Recovery key (keep off GitHub): $KeyPath"
    exit 0
}

Assert-OutputDoesNotExist $OutputPath
$payload = [System.IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $InputPath))
if ($payload.Length -lt ($magic.Length + $nonceSize + $tagSize)) {
    throw "Invalid AEMS backup: file is too short."
}

$storedMagic = $payload[0..($magic.Length - 1)]
if ([Convert]::ToHexString($storedMagic) -ne [Convert]::ToHexString($magic)) {
    throw "Invalid AEMS backup header."
}

$keyText = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $KeyPath)).Trim()
$key = [Convert]::FromBase64String($keyText)
if ($key.Length -ne 32) {
    throw "Invalid recovery key length."
}

$nonceStart = $magic.Length
$tagStart = $nonceStart + $nonceSize
$cipherStart = $tagStart + $tagSize
$nonce = $payload[$nonceStart..($tagStart - 1)]
$tag = $payload[$tagStart..($cipherStart - 1)]
$cipher = $payload[$cipherStart..($payload.Length - 1)]
$plain = [byte[]]::new($cipher.Length)

$aes = [System.Security.Cryptography.AesGcm]::new($key, $tagSize)
try {
    $aes.Decrypt($nonce, $cipher, $tag, $plain, $magic)
}
finally {
    $aes.Dispose()
}

[System.IO.File]::WriteAllBytes($OutputPath, $plain)
Write-Output "Decrypted backup: $OutputPath"
