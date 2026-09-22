"""hook 丙：Andy 说像裁决的话，本轮没记进耐久处就拦一次（spec §6.3）。

只查「记没记」，不查记得对不对。失败模式一律放行——卡死交互会话（含 Andy 自己在用的
那个）比漏拦一次贵。
"""
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def gate():
    p = ROOT / ".claude" / "hooks" / "ruling_stop_gate.py"
    spec = importlib.util.spec_from_file_location("ruling_stop_gate", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _write_transcript(tmp_path: Path, user_texts, assistant_text="ok") -> Path:
    """造一份最小可用的 transcript.jsonl：若干条 user 消息 + 一条 assistant。"""
    p = tmp_path / "transcript.jsonl"
    lines = []
    for text in user_texts:
        lines.append(json.dumps({
            "type": "user",
            "isSidechain": False,
            "message": {"role": "user", "content": text},
        }, ensure_ascii=False))
    lines.append(json.dumps({
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": assistant_text}]},
    }, ensure_ascii=False))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


# ---------- 基本放行模式 ----------

def test_stop_hook_active_passes(gate):
    assert gate.verdict({"stop_hook_active": True}) == {}


def test_missing_field_passes(gate):
    assert gate.verdict({}) == {}


def test_bad_transcript_path_passes(gate):
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": "/does/not/exist.jsonl",
        "last_assistant_message": "干完了",
    })
    assert v == {}


# ---------- 不命中裁决词 ----------

def test_no_ruling_word_passes(gate, tmp_path):
    tp = _write_transcript(tmp_path, ["今天数据看起来不错，谢谢"])
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "干完了，收工。",
    })
    assert v == {}


# ---------- 命中裁决词、且没有任何留痕 → 拦 ----------

def test_ruling_word_without_receipt_blocks(gate, tmp_path):
    tp = _write_transcript(tmp_path, ["以后都这样做，写进去"])
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "好，收工。",
    })
    assert v.get("decision") == "block"
    assert "ruling-recorded" in v["reason"]


def test_last_user_message_direct_field(gate):
    """payload 里直接给了 last_user_message 时优先用它，不用去读 transcript。"""
    v = gate.verdict({
        "stop_hook_active": False,
        "last_user_message": "这个以后不要再犯了",
        "last_assistant_message": "收工。",
    })
    assert v.get("decision") == "block"


# ---------- 有 ruling-recorded / ruling-none → 放行 ----------

@pytest.mark.parametrize("line", [
    "ruling-recorded: T-0922-111",
    "ruling-recorded: remember",
    "ruling-none: 这只是他随口一句感慨，不是裁决",
])
def test_receipt_line_passes(gate, tmp_path, line):
    tp = _write_transcript(tmp_path, ["以后都这样办"])
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": f"已处理。\n{line}",
    })
    assert v == {}


# ---------- fluxus-ops 30 分钟内有 remember 提交 → 放行 ----------

def _init_fake_fluxus_ops(tmp_path: Path, subject: str) -> Path:
    repo = tmp_path / "fluxus-ops"
    bare = tmp_path / "fluxus-ops-bare.git"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    (repo / "f.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "f.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", subject], check=True)
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(bare)], check=True)
    subprocess.run(["git", "-C", str(repo), "push", "-q", "origin", "main"], check=True)
    subprocess.run(["git", "-C", str(repo), "fetch", "-q", "origin"], check=True)
    return repo


def test_recent_remember_commit_passes(gate, tmp_path, monkeypatch):
    repo = _init_fake_fluxus_ops(tmp_path, "memory: remember Andy 说以后都这样")
    monkeypatch.setattr(gate, "FLUXUS_OPS", repo)
    tp = _write_transcript(tmp_path, ["以后都这样办"])
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "已处理，没写留痕行也行因为有 commit。",
    })
    assert v == {}


def test_missing_fluxus_ops_dir_passes_to_block(gate, tmp_path, monkeypatch):
    """读不到 fluxus-ops：这一条放行理由不成立，但仍要拦（没有别的放行理由）。"""
    monkeypatch.setattr(gate, "FLUXUS_OPS", tmp_path / "does-not-exist")
    tp = _write_transcript(tmp_path, ["以后都这样办"])
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "收工。",
    })
    assert v.get("decision") == "block"


def test_git_timeout_passes_gate_check_but_still_blocks_without_receipt(gate, tmp_path, monkeypatch):
    """git 超时只影响这一条放行理由，不代表整个 hook 放行——总耗时仍在 5 秒超时内返回。"""
    def _boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="git", timeout=5)

    monkeypatch.setattr(subprocess, "run", _boom)
    repo_dir = tmp_path / "fluxus-ops"
    repo_dir.mkdir()
    monkeypatch.setattr(gate, "FLUXUS_OPS", repo_dir)
    tp = _write_transcript(tmp_path, ["以后都这样办"])
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "收工。",
    })
    assert v.get("decision") == "block"


def test_any_unexpected_exception_passes(gate, monkeypatch):
    """卡死会话比漏拦一次贵：verdict 内部任何异常都必须吞掉并放行。"""
    def _boom(_payload):
        raise RuntimeError("boom")

    monkeypatch.setattr(gate, "_last_user_message", _boom)
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": "/whatever",
        "last_assistant_message": "收工。",
    })
    assert v == {}
