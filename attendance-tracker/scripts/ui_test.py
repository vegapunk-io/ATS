"""UI smoke test: login as admin, walk through every view, take screenshots."""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

BASE = "http://localhost:8000"
SHOTS = Path("/home/user/attendance-tracker/screenshots")
SHOTS.mkdir(exist_ok=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1360, "height": 900})
        errors = []

        async def on_error(e):
            errors.append(f"pageerror at {page.url}:\n{e}\n{e.stack}")
        page.on("pageerror", lambda e: asyncio.ensure_future(on_error(e)))
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)

        # 1. Unauthenticated visit should land on /login
        await page.goto(BASE, wait_until="domcontentloaded")
        await page.wait_for_url("**/login", timeout=8000)
        assert "/login" in page.url, f"expected /login, got {page.url}"
        print("✅ unauthenticated visit redirects to /login")

        # 2. Login as admin
        await page.fill("#username", "admin")
        await page.fill("#password", "admin123")
        await page.click("button[type=submit]")
        await page.wait_for_url(BASE + "/", timeout=10000)
        await page.wait_for_selector("#hero", timeout=10000)
        print("✅ admin login → dashboard")
        await page.screenshot(path=str(SHOTS / "1-dashboard.png"))

        # 3. Nav shows admin-only items
        nav_text = await page.locator(".nav").inner_text()
        assert all(v in nav_text for v in ["Dashboard", "Attendance", "People", "Users", "Reports"]), nav_text
        print("✅ admin nav shows all sections")

        # 4. People view
        await page.click('[data-view="people"]')
        await page.wait_for_selector("#people-table table", timeout=10000)
        body = await page.locator("#people-table").inner_text()
        assert "Aarav Shah" in body, "expected seeded people"
        print("✅ People view renders seeded people")
        await page.screenshot(path=str(SHOTS / "2-people.png"))

        # 5. Users view
        await page.click('[data-view="users"]')
        await page.wait_for_selector("#users-table table", timeout=10000)
        body = await page.locator("#users-table").inner_text()
        assert "aarav" in body and "admin" in body
        print("✅ Users view renders accounts")
        await page.screenshot(path=str(SHOTS / "3-users.png"))

        # 6. Reports view
        await page.click('[data-view="reports"]')
        await page.wait_for_selector("#reports-table table", timeout=15000)
        body = await page.locator("#reports-table").inner_text()
        assert "Aarav Shah" in body and "%" in body
        print("✅ Reports view renders summary with attendance rates")
        await page.screenshot(path=str(SHOTS / "4-reports.png"))

        # 7. Records view
        await page.click('[data-view="records"]')
        await page.wait_for_selector("#records-table table", timeout=15000)
        body = await page.locator("#records-table").inner_text()
        assert "Present" in body
        print("✅ Records view renders filtered records")
        await page.screenshot(path=str(SHOTS / "5-records.png"))

        # 8. Dashboard again — hero shows today state
        await page.click('[data-view="home"]')
        await page.wait_for_timeout(1200)
        await page.screenshot(path=str(SHOTS / "6-dashboard-again.png"))
        print("✅ dashboard refresh ok")

        # 9. Logout → back to /login
        await page.click("#logout-btn")
        await page.wait_for_url("**/login", timeout=8000)
        print("✅ logout returns to /login")

        await browser.close()

        if errors:
            print("\n⚠ Browser errors captured:")
            for e in errors[:10]:
                print("  ", e)
        else:
            print("\n✅ No console/page errors")
        return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
