#!/usr/bin/env python3
"""Fetch Whop active paid members count and update metrics.csv"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
import requests


def get_api_key():
    """Retrieve Whop API key from macOS keychain (in memory only)"""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-a", "fluxus", "-s", "whop-readonly-key", "-w"],
            capture_output=True,
            text=True,
            check=True
        )
        key = result.stdout.strip()
        if not key:
            raise ValueError("Keychain key is empty")
        return key
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to retrieve Whop API key from keychain") from e


def fetch_active_members(api_key):
    """
    Fetch active (paid) members from Whop API.
    Returns count of active members (status=active), excluding trial users.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    try:
        url = "https://api.whop.com/api/v1/memberships"
        all_members = []
        offset = 0
        limit = 100

        while True:
            params = {"offset": offset, "limit": limit}
            resp = requests.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

            if "data" not in data:
                break

            members = data.get("data", [])
            if not members:
                break

            all_members.extend(members)
            offset += limit

            if len(members) < limit:
                break

        active_count = sum(1 for m in all_members if m.get("status") == "active")
        return active_count, len(all_members)

    except requests.RequestException as e:
        raise ValueError(f"Whop API request failed: {e}") from e


def update_metrics_csv(member_count):
    """Update data/growth/metrics.csv with today's active member count"""
    csv_path = Path(__file__).parent.parent / "metrics.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"metrics.csv not found at {csv_path}")

    with open(csv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    from pipeline.marketcal import market_today
    today_date = market_today().isoformat()

    import pytz
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.now(jst).strftime("%Y-%m-%dT%H:%M:%S%z")

    found_today = False
    new_lines = []

    for i, line in enumerate(lines):
        if i == 0:
            new_lines.append(line)
        elif line.strip() and not line.startswith("#"):
            parts = line.split(",")
            if parts[0] == today_date:
                found_today = True
                parts[5] = str(member_count)
                parts[7] = f"Whop API memberships · status=active · 取数 {now_jst}\n"
                new_lines.append(",".join(parts))
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if not found_today:
        new_row = [
            today_date,
            "",
            "",
            "",
            "",
            str(member_count),
            "",
            f"Whop API memberships · status=active · 取数 {now_jst}\n"
        ]
        if new_lines and new_lines[-1].strip() == "":
            new_lines.insert(-1, ",".join(new_row))
        else:
            new_lines.append(",".join(new_row))

    with open(csv_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return today_date, member_count


def main():
    try:
        api_key = get_api_key()
        active_count, total_count = fetch_active_members(api_key)
        date, count = update_metrics_csv(active_count)
        print(f"Success: Updated whop_members to {count} for {date}")
        print(f"(Total memberships: {total_count}, Active: {active_count})")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
