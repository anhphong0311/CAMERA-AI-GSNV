#!/usr/bin/env python3
"""
Script tiện ích — sinh SECRET_KEY ngẫu nhiên cho .env

Chạy: python scripts/generate_secret.py
"""

import secrets


def main() -> None:
    """In ra hex secret 64 ký tự — dùng cho JWT SECRET_KEY."""
    print(secrets.token_hex(32))


if __name__ == "__main__":
    main()
