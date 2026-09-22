"""data/growth/scripts/fetch_whop_members.py 的测试（Whop API 全部 mock，不联网）。"""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "data" / "growth" / "scripts" / "fetch_whop_members.py"
spec = importlib.util.spec_from_file_location("fetch_whop_members", SCRIPT)
fw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fw)

FAKE_KEY = "sk_test_FAKEKEY_do_not_leak_1234567890"
PREMIUM = "prod_JP6vlypnDQTNk"
PPNEW = "prod_lqtg4j5LTtBVh"
MASTER = fw.MASTERCLASS_PRODUCT


def m(uid, status, product=PREMIUM, cape=False):
    return {"user_id": uid, "status": status, "product_id": product, "plan_id": "plan_x",
            "cancel_at_period_end": cape}


class Resp:
    def __init__(self, body, code=200):
        self._b, self.status_code = body, code

    def json(self):
        return self._b


class FakeSession:
    """按 after 游标返回预置的页；记录每次调用的参数。"""

    def __init__(self, pages_by_path, code=200):
        self.pages, self.code, self.calls = pages_by_path, code, []

    def get(self, url, headers=None, params=None, timeout=None):
        path = url.rsplit("/", 1)[-1]
        self.calls.append((path, dict(params or {}), headers))
        if self.code != 200:
            return Resp({"error": f"bad token {FAKE_KEY}"}, self.code)
        pages = self.pages[path]
        idx = 0 if not params.get("after") else int(params["after"].split("_")[1])
        last = idx == len(pages) - 1
        return Resp({"data": pages[idx],
                     "page_info": {"has_next_page": not last,
                                   "end_cursor": None if last else f"cur_{idx + 1}"}})


THREE_PAGES = [
    [m("u1", "active"), m("u1", "completed", MASTER), m("u2", "active", cape=True),
     m("u3", "trialing")],
    [m("u4", "past_due"), m("u5", "canceled"), m("u6", "expired"), m("u7", "canceling")],
    [m("u8", "active", PPNEW), m("u9", "completed", MASTER), m("u10", "unresolved"),
     m("u11", "drafted"), m("u2", "active", PPNEW)],
]
MEMBERS = [[{"access_level": "customer", "status": "joined"},
            {"access_level": "admin", "status": "joined"},
            {"access_level": "no_access", "status": "left"},
            {"access_level": "customer", "status": "left"}]]


def test_reads_all_three_pages_via_cursor():
    s = FakeSession({"memberships": THREE_PAGES})
    rows, pages = fw.fetch_all(s, "memberships", FAKE_KEY)
    assert pages == 3 and len(rows) == 13
    assert [c[1].get("after") for c in s.calls] == [None, "cur_1", "cur_2"]
    assert all("offset" not in c[1] and "limit" not in c[1] for c in s.calls)
    assert all(c[1]["first"] == fw.PAGE_SIZE for c in s.calls)


def test_short_first_page_is_not_treated_as_last():
    # v1 的 bug：第一页 20 < limit 100 就停。这里每页都很短，也必须读到 has_next_page=false
    s = FakeSession({"memberships": [[m("a", "active")], [m("b", "active")], [m("c", "active")]]})
    rows, pages = fw.fetch_all(s, "memberships", FAKE_KEY)
    assert (len(rows), pages) == (3, 3)


def test_summarize_all_statuses_and_candidates():
    rows, _ = fw.fetch_all(FakeSession({"memberships": THREE_PAGES}), "memberships", FAKE_KEY)
    s = fw.summarize(rows, MEMBERS[0])
    assert s["status"] == {"active": 4, "completed": 2, "trialing": 1, "past_due": 1, "canceled": 1,
                           "expired": 1, "canceling": 1, "unresolved": 1, "drafted": 1}
    # active|past_due 且订阅产品，按 user 去重：u1 u2 u4 u8（u2 两条合一）
    assert s["cand_A_paid_sub_users"] == 4
    assert s["cand_A_of_which_cancel_at_period_end"] == 1
    assert s["trialing_users"] == 1
    assert s["masterclass_completed_users"] == 2
    assert s["users_all"] == 11
    assert s["by_product"][MASTER] == {"completed": 2}
    assert s["cand_B_customer_joined"] == 1


def test_non_subscription_active_not_counted_in_A():
    s = fw.summarize([m("x", "active", "prod_other"), m("y", "active")])
    assert s["cand_A_paid_sub_users"] == 1


def test_http_error_is_masked():
    with pytest.raises(fw.WhopError) as e:
        fw.fetch_all(FakeSession({}, code=401), "memberships", FAKE_KEY)
    assert FAKE_KEY not in str(e.value) and "401" in str(e.value)


def test_network_exception_is_masked():
    class Boom:
        def get(self, *a, **k):
            raise ConnectionError(f"failed with header Bearer {FAKE_KEY}")
    with pytest.raises(fw.WhopError) as e:
        fw.fetch_all(Boom(), "memberships", FAKE_KEY)
    assert FAKE_KEY not in str(e.value) and "***" in str(e.value)


def test_key_unavailable_prints_empty_week(capsys, tmp_path):
    csv_path = tmp_path / "metrics.csv"
    csv_path.write_text("date,whop_members,notes\n")
    assert fw.main(["--write", "--csv", str(csv_path), "--date", "2026-09-28"],
                   session=FakeSession({}), key_getter=lambda: None) == 0
    assert fw.KEY_UNAVAILABLE in capsys.readouterr().out
    assert csv_path.read_text() == "date,whop_members,notes\n"


def test_keychain_failure_returns_none():
    class R:
        returncode, stdout = 44, ""
    assert fw.get_api_key(runner=lambda *a, **k: R()) is None


def test_write_leaves_whop_members_blank_and_no_key_or_comma(tmp_path, capsys):
    csv_path = tmp_path / "metrics.csv"
    csv_path.write_text("date,x_followers,whop_members,notes\n2026-09-21,285,,old\n")
    sess = FakeSession({"memberships": THREE_PAGES, "members": MEMBERS})
    assert fw.main(["--write", "--csv", str(csv_path), "--date", "2026-09-21"],
                   session=sess, key_getter=lambda: FAKE_KEY) == 0
    out = capsys.readouterr().out
    text = csv_path.read_text()
    lines = text.strip().split("\n")
    assert len(lines) == 2
    row = lines[1].split(",")
    assert row[:3] == ["2026-09-21", "285", ""] and len(row) == 4  # notes 无半角逗号
    assert "候选A" in row[3] and "=4" in row[3]
    assert FAKE_KEY not in text and FAKE_KEY not in out


def test_write_appends_new_date_row(tmp_path):
    csv_path = tmp_path / "metrics.csv"
    csv_path.write_text("date,whop_members,notes\n2026-09-21,,old\n")
    fw.main(["--write", "--csv", str(csv_path), "--date", "2026-09-28"],
            session=FakeSession({"memberships": THREE_PAGES, "members": MEMBERS}),
            key_getter=lambda: FAKE_KEY)
    lines = csv_path.read_text().strip().split("\n")
    assert len(lines) == 3 and lines[1] == "2026-09-21,,old" and lines[2].startswith("2026-09-28,,")
