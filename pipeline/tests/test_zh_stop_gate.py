"""hook 丙：回复漂成英文就打回一次。样本取自 bc794578 会话的真实回复（10-01 那两条漂成英文的）。"""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]

# 10-01 真实回复开头（漂成英文，占比 0.00）
ENGLISH = (
    "Each candidate now has one sentence. Preview v3 is published (09-29 close; open the "
    "Focus section at the bottom).\n\n**Action Plan**\n1. Read through the 27 sentences and "
    "tell me whether the style is right, which one reads worst, and how to change it. That's "
    "the only call I need from you. Once it's settled I'll make it run every day.\n"
    "skill-used: task-protocol · ruling recorded"
)
# 09-26 真实回复开头（中文夹英文术语，占比约 0.56）
CHINESE = (
    "**预览出了，真数据、六层逐层计数；ALEX 那单已开（T-0926-62）。**\n\n**Action Plan**\n"
    "1. 看预览挑毛病：点 ④ 的三个 setup 芯片，Focus 表跟着换。\n"
    "2. 一个字：这个骨架合不合（y / 改哪层）。合了我再做进 React 替掉 6 张卡。\n"
    "3. ALEX 单已派，两件事：数据有无盘点 + X/书稿/TraderLion 调研 screener 与 setup 怎么设计。\n"
    "skill-used: chart-for-andy · 无"
)


@pytest.fixture(scope="module")
def gate():
    p = ROOT / ".claude" / "hooks" / "zh_stop_gate.py"
    spec = importlib.util.spec_from_file_location("zh_stop_gate", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_blocks_the_real_english_drift(gate):
    v = gate.verdict({"last_assistant_message": ENGLISH, "stop_hook_active": False})
    assert v.get("decision") == "block" and "中文" in v["reason"]


def test_passes_chinese_with_english_terms(gate):
    assert gate.verdict({"last_assistant_message": CHINESE, "stop_hook_active": False}) == {}


def test_second_stop_always_passes(gate):
    # 打回过一次就放行：拦得住忘记，冻不死会话
    assert gate.verdict({"last_assistant_message": ENGLISH, "stop_hook_active": True}) == {}


def test_short_reply_not_checked(gate):
    assert gate.verdict({"last_assistant_message": "OK, pushed 5b47672d6.", "stop_hook_active": False}) == {}


def test_english_draft_in_quote_or_code_is_not_counted(gate):
    draft = "\n".join(["> " + ENGLISH.splitlines()[0]] * 6)
    code = "```bash\n" + ("git push origin HEAD:main && echo done\n" * 10) + "```"
    msg = f"草稿在下面，只清了语法，没加东西。\n{draft}\n命令：\n{code}\n你看哪句要改。"
    assert gate.verdict({"last_assistant_message": msg, "stop_hook_active": False}) == {}


@pytest.mark.parametrize("payload", [{}, {"last_assistant_message": None}, {"last_assistant_message": 3}])
def test_malformed_input_passes(gate, payload):
    assert gate.verdict(payload) == {}
