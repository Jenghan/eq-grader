#!/usr/bin/env python3
"""Headless screenshots for docs/teacher-guide.md (run from repo root)."""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("TEACHER_GUIDE_BASE_URL", "https://eq-grader.metaengine.org").rstrip("/")
OUT = Path(__file__).resolve().parent.parent / "docs" / "images"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        page.goto(f"{BASE}/", wait_until="networkidle")
        page.screenshot(path=str(OUT / "01-student-home-login.png"), full_page=True)

        page.goto(f"{BASE}/questionnaire/emotion_abc", wait_until="networkidle")
        page.screenshot(path=str(OUT / "02-questionnaire-emotion-abc.png"), full_page=True)

        # 未登入時進入 /teacher 或 /login 皆會導向 Google 帳號頁
        page.goto(f"{BASE}/login", wait_until="networkidle")
        page.screenshot(path=str(OUT / "03-google-sign-in.png"), full_page=True)

        browser.close()
    print("Wrote:", list(OUT.glob("*.png")))


if __name__ == "__main__":
    main()
