"""--fetch-only 与 --generate 两个模式（2026-09-10 管道拆分：CI 拉取、云会话生成）。"""
import json
import sys
from unittest import mock

import pytest

from pipeline.content import discord_to_thread as d2t


FAKE_MSGS = [
    {"content": "MU leading memory again", "timestamp": "2026-09-09T15:00:00.000000+00:00"},
    {"content": "", "timestamp": "2026-09-09T15:05:00.000000+00:00"},
    {"content": "split tape, trade the theme", "timestamp": "2026-09-09T16:00:00.000000+00:00"},
]


@pytest.fixture
def threads_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(d2t, "THREADS_DIR", tmp_path)
    monkeypatch.setattr(d2t, "STATE_PATH", tmp_path / ".run_state.json")
    return tmp_path


def _run(argv, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["discord_to_thread"] + argv)
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "t")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "c")
    monkeypatch.setenv("DISCORD_USER_ID", "u")
    d2t.main()


def test_fetch_only_writes_messages_json_and_no_draft(threads_dir, monkeypatch):
    with mock.patch.object(d2t, "fetch_messages", return_value=FAKE_MSGS), \
         mock.patch.object(d2t, "filter_by_author_and_date", return_value=FAKE_MSGS), \
         mock.patch.object(d2t, "process_to_thread") as gen:
        _run(["--fetch-only", "--date", "2026-09-09"], monkeypatch)
    out = threads_dir / "2026-09-09"
    saved = json.loads((out / "messages.json").read_text())
    assert [m["content"] for m in saved] == [m["content"] for m in FAKE_MSGS]
    assert not (out / "draft.txt").exists()
    gen.assert_not_called()  # fetch-only 永不碰 Claude


def test_fetch_only_backfill_does_not_advance_watermark(threads_dir, monkeypatch):
    with mock.patch.object(d2t, "fetch_messages", return_value=FAKE_MSGS), \
         mock.patch.object(d2t, "filter_by_author_and_date", return_value=FAKE_MSGS):
        _run(["--fetch-only", "--date", "2026-09-09"], monkeypatch)
    assert d2t.read_watermark() is None


def test_fetch_only_rolling_advances_watermark(threads_dir, monkeypatch):
    with mock.patch.object(d2t, "fetch_messages", return_value=FAKE_MSGS), \
         mock.patch.object(d2t, "filter_since", return_value=FAKE_MSGS):
        _run(["--fetch-only"], monkeypatch)
    wm = d2t.read_watermark("c")  # per-channel since 2026-09-10
    assert wm is not None and wm.isoformat().startswith("2026-09-09T16:00")


def test_multi_channel_fetch_tags_and_separate_watermarks(threads_dir, monkeypatch):
    """DISCORD_CHANNEL_IDS: 每频道独立水位线,消息带 channel 标签,时间序合并。"""
    monkeypatch.setenv("DISCORD_CHANNEL_IDS", "111:live-commentary, 222:互帮互助")
    by_chan = {
        "111": [dict(FAKE_MSGS[0])],                       # 15:00
        "222": [dict(FAKE_MSGS[2]), {"content": "early Q", # 16:00 + 14:00
                 "timestamp": "2026-09-09T14:00:00.000000+00:00"}],
    }
    with mock.patch.object(d2t, "fetch_messages", side_effect=lambda cid, tok: by_chan[cid]), \
         mock.patch.object(d2t, "filter_since", side_effect=lambda msgs, uid, since: list(msgs)):
        _run(["--fetch-only"], monkeypatch)
    out = json.loads(next(threads_dir.glob("*/messages.json")).read_text())
    assert [m["channel"] for m in out] == ["互帮互助", "live-commentary", "互帮互助"]  # 14:00,15:00,16:00
    assert d2t.read_watermark("111").isoformat().startswith("2026-09-09T15:00")
    assert d2t.read_watermark("222").isoformat().startswith("2026-09-09T16:00")


def test_legacy_single_watermark_file_still_read(threads_dir, monkeypatch):
    (threads_dir / ".run_state.json").write_text(
        json.dumps({"last_message_utc": "2026-09-08T12:00:00+00:00"}))
    wm = d2t.read_watermark("anychan")
    assert wm is not None and wm.isoformat().startswith("2026-09-08T12:00")


def test_generate_reads_messages_json_and_writes_draft(threads_dir, monkeypatch):
    folder = threads_dir / "2026-09-09"
    folder.mkdir()
    (folder / "messages.json").write_text(json.dumps(FAKE_MSGS))
    with mock.patch.object(d2t, "process_to_thread",
                           return_value=["1/ MU leads", "2/ theme over index"]) as gen:
        _run(["--generate", "2026-09-09"], monkeypatch)
    assert (folder / "draft.txt").read_text() == "1/ MU leads\n\n2/ theme over index"
    # 空 content 的消息被过滤掉
    assert gen.call_args.args[0] == ["MU leading memory again", "split tape, trade the theme"]


def test_generate_missing_folder_exits_nonzero(threads_dir, monkeypatch):
    with pytest.raises(SystemExit) as e:
        _run(["--generate", "2026-01-01"], monkeypatch)
    assert e.value.code == 1


def test_qa_mode_attaches_member_question_anonymously(threads_dir, monkeypatch):
    """qa 模式:Andy 的 reply 带上被回复的会员提问,匿名;own 模式不带。"""
    monkeypatch.setenv("DISCORD_CHANNEL_IDS", "111:live:own, 222:互帮互助:qa")
    reply = {"content": "Size down and wait for the retest.",
             "timestamp": "2026-09-09T17:00:00.000000+00:00",
             "referenced_message": {"content": "How do I size this breakout?",
                                    "author": {"id": "member42", "username": "SECRET"}}}
    by_chan = {"111": [dict(reply)], "222": [dict(reply)]}
    with mock.patch.object(d2t, "fetch_messages", side_effect=lambda cid, tok: by_chan[cid]), \
         mock.patch.object(d2t, "filter_since", side_effect=lambda msgs, uid, since: list(msgs)):
        _run(["--fetch-only"], monkeypatch)
    out = json.loads(next(threads_dir.glob("*/messages.json")).read_text())
    qa = [m for m in out if m["channel"] == "互帮互助"][0]
    own = [m for m in out if m["channel"] == "live"][0]
    assert qa["question"] == "How do I size this breakout?"
    assert "question" not in own
    assert "SECRET" not in json.dumps(out)  # 会员名永不入库


def test_qa_mode_ignores_self_reply(threads_dir, monkeypatch):
    monkeypatch.setenv("DISCORD_CHANNEL_IDS", "222:互帮互助:qa")
    monkeypatch.setenv("DISCORD_USER_ID", "u")
    self_reply = {"content": "adding to my earlier point",
                  "timestamp": "2026-09-09T17:00:00.000000+00:00",
                  "referenced_message": {"content": "my own earlier msg",
                                         "author": {"id": "u"}}}
    with mock.patch.object(d2t, "fetch_messages", return_value=[self_reply]), \
         mock.patch.object(d2t, "filter_since", side_effect=lambda msgs, uid, since: list(msgs)):
        _run(["--fetch-only"], monkeypatch)
    out = json.loads(next(threads_dir.glob("*/messages.json")).read_text())
    assert "question" not in out[0]
