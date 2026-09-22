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


# ================= 09-22 复核第 1 轮 FAIL 两条必修 =================

# ---------- 必修①：词表换正则，误拦 0 / 漏判 0 ----------

DAILY_SENTENCES_NOT_RULINGS = [
    "批量改一下",
    "以后再说吧",
    "你记住这个链接了吗",
    "批注版 PDF",
    "这个不做空了",
    "写进 word 里存着",
    "这次就先这样吧",
    "不要这么急",
    "都不知道该怎么办",
    "记着点这件事",
]

TRUE_RULINGS = [
    "以后都这样做",
    "都这样办",  # 09-22 第 2 轮：「都这样」要求带具体动作，原「都这样吧」不再命中，换用例
    "写进规矩里",
    "记住，以后都要这样",  # 09-22 第 2 轮：「记住」收紧为句首 `记住[:：，]`，原「记住这个规则」不再命中，换用例
    "这个就定了",
    "不要再犯同样的错误",
    "都批了，去合吧",
    "这个不做了",
    "今后一律先问我",
    "别再写这个了",  # 09-22 第 2 轮：「别再」要求跟具体动词，原「别再问这个了」不再命中，换用例
]

# ================= 09-22 复核第 2 轮 FAIL 两条必修 =================

# ---------- 必修①续：复核员新造的 5 句日常话，全部要求放行；第 1 轮那 20 句结果不变 ----------

DAILY_SENTENCES_ROUND2 = [
    "以后就知道了，先看看",
    "别再下雨就好了",
    "这个定了多少价格？",
    "我记住了，不用再说",
    "他们都这样说，不一定对",
]


@pytest.mark.parametrize("text", DAILY_SENTENCES_ROUND2)
def test_daily_sentence_round2_is_not_a_ruling_word_hit(gate, text):
    assert gate._hits_ruling_word(text) is False


@pytest.mark.parametrize("text", DAILY_SENTENCES_ROUND2)
def test_daily_sentence_round2_end_to_end_passes(gate, tmp_path, text):
    tp = _write_transcript(tmp_path, [text])
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "好的。",
    })
    assert v == {}


@pytest.mark.parametrize("text", DAILY_SENTENCES_NOT_RULINGS)
def test_daily_sentence_is_not_a_ruling_word_hit(gate, text):
    assert gate._hits_ruling_word(text) is False


@pytest.mark.parametrize("text", TRUE_RULINGS)
def test_true_ruling_is_a_ruling_word_hit(gate, text):
    assert gate._hits_ruling_word(text) is True


@pytest.mark.parametrize("text", DAILY_SENTENCES_NOT_RULINGS)
def test_daily_sentence_end_to_end_passes(gate, tmp_path, text):
    tp = _write_transcript(tmp_path, [text])
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "好的。",
    })
    assert v == {}


@pytest.mark.parametrize("text", TRUE_RULINGS)
def test_true_ruling_end_to_end_blocks(gate, tmp_path, text):
    tp = _write_transcript(tmp_path, [text])
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "好的，收工。",
    })
    assert v.get("decision") == "block"


# ---------- 必修②：只认真人消息，跳过注入/合成消息；content 是 list 也要能读 ----------

def _entry(**kw) -> str:
    return json.dumps(kw, ensure_ascii=False)


def _user_entry(content, origin=None, is_meta=None, is_compact=None, is_sidechain=False):
    d = {"type": "user", "isSidechain": is_sidechain, "message": {"role": "user", "content": content}}
    if origin is not None:
        d["origin"] = origin
    if is_meta is not None:
        d["isMeta"] = is_meta
    if is_compact is not None:
        d["isCompactSummary"] = is_compact
    return _entry(**d)


def test_origin_human_is_used(gate, tmp_path):
    tp = tmp_path / "t.jsonl"
    tp.write_text(_user_entry("以后都这样办", origin={"kind": "human"}) + "\n", encoding="utf-8")
    assert gate._last_user_message(str(tp)) == "以后都这样办"


def test_origin_peer_is_skipped_even_though_it_hits_ruling_words(gate, tmp_path):
    """跨会话消息 origin.kind=peer，即便文字命中裁决词也不能算 Andy 说的。"""
    lines = [
        _user_entry("以后都这样办，这是我真正说的话", origin={"kind": "human"}),
        _user_entry(
            "按错门了，这里不归我管，以后都这样处理吧",
            origin={"kind": "peer", "from": "uds:/tmp/cc-socks/1.sock"},
            is_meta=True,
        ),
    ]
    tp = tmp_path / "t.jsonl"
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert gate._last_user_message(str(tp)) == "以后都这样办，这是我真正说的话"


def test_stop_hook_feedback_is_skipped_falls_back_to_real_message(gate, tmp_path):
    lines = [
        _user_entry("好，以后都这样，写进去", origin={"kind": "human"}),
        _user_entry("Stop hook feedback:\n收工前补一行", is_meta=True),
    ]
    tp = tmp_path / "t.jsonl"
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert gate._last_user_message(str(tp)) == "好，以后都这样，写进去"


def test_another_claude_cross_session_message_is_skipped(gate, tmp_path):
    lines = [
        _user_entry("好，都定了", origin={"kind": "human"}),
        _user_entry(
            "Another Claude session sent a message:\n<cross-session-message>正文</cross-session-message>",
            origin={"kind": "peer", "from": "x"},
            is_meta=True,
        ),
    ]
    tp = tmp_path / "t.jsonl"
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert gate._last_user_message(str(tp)) == "好，都定了"


def test_system_reminder_prefixed_content_is_skipped(gate, tmp_path):
    lines = [
        _user_entry("以后都这样", origin={"kind": "human"}),
        _user_entry("<system-reminder>某某提醒</system-reminder>"),
    ]
    tp = tmp_path / "t.jsonl"
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert gate._last_user_message(str(tp)) == "以后都这样"


def test_compact_summary_is_skipped(gate, tmp_path):
    lines = [
        _user_entry("好，都这样定了", origin={"kind": "human"}),
        _user_entry(
            "This session is being continued from a previous conversation...",
            is_compact=True,
        ),
    ]
    tp = tmp_path / "t.jsonl"
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert gate._last_user_message(str(tp)) == "好，都这样定了"


def test_tool_result_list_content_is_skipped(gate, tmp_path):
    """content 是 list 但里面全是 tool_result（工具回填），不是人打的字。"""
    lines = [
        _user_entry("这个就定了", origin={"kind": "human"}),
        _user_entry([{"type": "tool_result", "tool_use_id": "x", "content": "42"}]),
    ]
    tp = tmp_path / "t.jsonl"
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert gate._last_user_message(str(tp)) == "这个就定了"


def test_image_plus_text_list_content_is_read_and_can_be_a_ruling(gate, tmp_path):
    """带图说的裁决：content 是 [image块, text块]，之前整条被跳过，现在要能读出 text 块。"""
    lines = [
        _user_entry([
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AAAA"}},
            {"type": "text", "text": "这张图我看完了，以后都这样标注"},
        ], origin={"kind": "human"}),
    ]
    tp = tmp_path / "t.jsonl"
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert gate._last_user_message(str(tp)) == "这张图我看完了，以后都这样标注"
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "收工。",
    })
    assert v.get("decision") == "block"


def test_sidechain_is_skipped(gate, tmp_path):
    lines = [
        _user_entry("这条不算裁决", origin={"kind": "human"}),
        _user_entry("子 agent 岔出去说的：以后都这样", origin={"kind": "human"}, is_sidechain=True),
    ]
    tp = tmp_path / "t.jsonl"
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert gate._last_user_message(str(tp)) == "这条不算裁决"


def test_reverse_reader_matches_forward_line_order(gate, tmp_path):
    """倒着读大文件时，行的相对顺序（哪条在后）不能错。"""
    lines = [f"line-{i}" for i in range(50)]
    tp = tmp_path / "big.jsonl"
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert list(gate._iter_lines_reverse(tp)) == list(reversed(lines))


# ---------- 必修②续：origin.kind=="human" 的真消息不做 INJECTED_PREFIXES 排除，
# 只剥附件/引用标记再判断；判的必须是最新一条，不能退回上一条 ----------

def test_human_message_with_attach_marker_is_a_ruling_and_blocks(gate, tmp_path):
    lines = [
        _user_entry("<!-- attach -->以后都这样画", origin={"kind": "human"}),
    ]
    tp = tmp_path / "t.jsonl"
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert gate._last_user_message(str(tp)) == "以后都这样画"
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "收工。",
    })
    assert v.get("decision") == "block"


def test_human_message_with_attach_marker_non_ruling_passes_and_judges_latest_not_prior(gate, tmp_path):
    """上一句是真裁决「以后都这样做」，这一句带附件标记但不是裁决——必须放行，
    且判的是这一句（最新），不能退回去判上一句。"""
    lines = [
        _user_entry("以后都这样做", origin={"kind": "human"}),
        _user_entry("<!-- reply -->这是今天的截图，你看一下", origin={"kind": "human"}),
    ]
    tp = tmp_path / "t.jsonl"
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert gate._last_user_message(str(tp)) == "这是今天的截图，你看一下"
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "好的。",
    })
    assert v == {}


# ---------- 必修③：拦截提示语必须写清楚「不是裁决就写 ruling-none」这条安全阀 ----------

def test_block_reason_tells_user_ruling_none_escape_hatch(gate, tmp_path):
    tp = _write_transcript(tmp_path, ["以后都这样做"])
    v = gate.verdict({
        "stop_hook_active": False,
        "transcript_path": str(tp),
        "last_assistant_message": "收工。",
    })
    assert v.get("decision") == "block"
    assert "ruling-none" in v["reason"]
    assert "不是裁决" in v["reason"]
