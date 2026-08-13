"""Send a message to a Discord channel via bot."""
import os
import requests

DISCORD_API_BASE = "https://discord.com/api/v10"

NOTIFY_CHANNEL_ID = "1470332022881910966"


def send_channel_message(message: str, channel_id: str | None = None, bot_token: str | None = None) -> bool:
    """Send a message to a Discord channel. Splits long messages at 2000 chars. Returns True on success."""
    token = bot_token or os.environ["DISCORD_BOT_TOKEN"]
    channel = channel_id or NOTIFY_CHANNEL_ID
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

    # Split into chunks at line boundaries, respecting Discord's 2000 char limit
    chunks = _split_message(message, 1900)
    for chunk in chunks:
        resp = requests.post(
            f"{DISCORD_API_BASE}/channels/{channel}/messages",
            headers=headers,
            json={"content": chunk},
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"Failed to send message: {resp.status_code} {resp.text}")
            return False

    return True


def _split_message(text: str, max_len: int = 1900) -> list[str]:
    """Split text into chunks at line boundaries."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_len:
            chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "Test notification from Fluxus Reader"
    ok = send_channel_message(msg)
    print("Sent!" if ok else "Failed.")
