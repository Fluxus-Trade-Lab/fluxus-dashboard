"""Finviz 的每个查询只给前 1000 行——抓法必须绕过它，而不是撞它。

2026-09-30 实测（三个不同网络、两个 GitHub runner、一台本机）：

    全新会话的**第一个**请求   r=981  -> 200      r=1001 -> 403
    全新会话的**第一个**请求   r=1021 -> 403      r=3001 -> 403

403 带 `Cf-Mitigated: challenge`。第一个请求就能复现，所以不是限流；三个
网络都能复现，所以不是 IP 封禁。边界是行偏移——那是每个查询的行数上限，
**退避重试碰的还是同一面墙**。当天两班正班各只抓到 1000/5613 行。

这份测试里的假 Finviz 照这个形状拒绝：`r > ROW_CAP` 一律 403。所以任何
「加个重试再撞一次」的写法在这里必然红，而正确的写法——把市场按板块切成
每块都够小的查询，块本身超过 1000 行时再从反向排序补尾巴——必然绿。
"""
import re

import pandas as pd
import pytest
import requests

from pipeline.adapters import finviz_adapter as fa
from pipeline.adapters.finviz_adapter import ROW_CAP, SECTOR_FILTERS, FinvizAdapter

HEADERS = ["No.", "Ticker", "Company", "Sector", "Industry", "Country",
           "Market Cap", "P/E", "Price", "Change", "Volume"]


def _ticker(sector_idx: int, n: int) -> str:
    """板块内单调递增的合成代码，好让升序/降序能被断言。"""
    return f"S{sector_idx}T{n:05d}"


class FakeFinviz:
    """按真实形状回答的假 Finviz：r > ROW_CAP 一律 403。"""

    def __init__(self, sizes: dict[str, int]):
        self.sizes = sizes
        self.headers: dict = {}
        self.requested: list[tuple[str, int, str | None]] = []
        # 每块的代码表只造一次。按请求重造会让这份测试从 3 秒变成 100 秒。
        order = sorted(sizes)
        self._names = {s: [_ticker(order.index(s), i) for i in range(1, n + 1)]
                       for s, n in sizes.items()}
        self._all = [_ticker(99, i) for i in range(1, sum(sizes.values()) + 1)]

    # requests.Session 的最小面
    def get(self, url, params=None, timeout=None):
        params = params or {}
        f = params.get("f", "")
        r = int(params.get("r", 1))
        order = params.get("o")
        self.requested.append((f, r, order))

        if r > ROW_CAP:
            raise requests.HTTPError(f"403 Client Error: Forbidden for url {url}?r={r}")

        sector = next((s for s in self.sizes if s in f), None)
        names = self._names[sector] if sector else self._all
        if order == "-ticker":
            names = names[::-1]
        page = names[r - 1: r - 1 + 20]
        return FakeResponse(_html(len(names), page))


class FakeResponse:
    def __init__(self, text):
        self.text = text
        self.status_code = 200
        self.headers = {}

    def raise_for_status(self):
        return None


def _html(total: int, tickers: list[str]) -> str:
    head = "".join(f"<td>{h}</td>" for h in HEADERS)
    rows = ""
    for i, t in enumerate(tickers, 1):
        cells = [str(i), t, f"{t} Inc", "Technology", "Software", "USA",
                 "1.00B", "20", "10.00", "1.00%", "100000"]
        tds = "".join(
            f'<td data-boxover-ticker="{t}">X{t}</td>' if j == 1 else f"<td>{c}</td>"
            for j, c in enumerate(cells))
        rows += f"<tr>{tds}</tr>"
    return (f"<html><body><div>#1 / {total:,} Total</div>"
            f'<table class="screener_table"><tr>{head}</tr>{rows}</table>'
            f"</body></html>")


@pytest.fixture(autouse=True)
def _no_politeness_sleep(monkeypatch):
    """页间 0.2s 是给真 Finviz 的礼貌，不是给假 Finviz 的——不跳过就是 100 秒。"""
    monkeypatch.setattr(fa.time, "sleep", lambda _s: None)


@pytest.fixture
def adapter():
    return FinvizAdapter()


# --------------------------------------------------------------------------
#  阳性对照①：假 Finviz 真的会拒 —— 先证这把尺子能报出阳性，再信它的阴性
# --------------------------------------------------------------------------
def test_the_fake_refuses_past_the_cap_like_the_real_one():
    fake = FakeFinviz({"sec_technology": 5000})
    fake.get("u", params={"f": "sec_technology", "r": ROW_CAP - 19})  # 通
    with pytest.raises(requests.HTTPError):
        fake.get("u", params={"f": "sec_technology", "r": ROW_CAP + 1})


# --------------------------------------------------------------------------
#  一个查询：不许请求越过上限，能拿到的就是上限那么多
# --------------------------------------------------------------------------
def test_a_single_query_never_asks_past_the_cap(adapter):
    """一个 5000 行的查询只该抓回 ROW_CAP 行，且一次都不许去撞 403。

    撞一次就返回 `[], None`（`page == 1` 之外是 break），宇宙会静默变短——
    2026-09-30 那两班正是这个形状：1000 行、零 error、quality ok。
    """
    fake = FakeFinviz({"sec_technology": 5000})
    rows, headers = adapter._scrape_one_direction(
        fake, "111", {"f": "sec_technology"}, max_pages=600)
    assert len(rows) == ROW_CAP
    assert max(r for _f, r, _o in fake.requested) <= ROW_CAP
    assert rows[0]["Ticker"] == _ticker(0, 1)
    assert rows[-1]["Ticker"] == _ticker(0, ROW_CAP)


def test_the_ticker_comes_from_the_attribute_not_the_logo_text(adapter):
    """Finviz 的代码格里塞了 logo <img>，get_text() 会多一个字符。"""
    fake = FakeFinviz({"sec_technology": 40})
    rows, _ = adapter._scrape_one_direction(
        fake, "111", {"f": "sec_technology"}, max_pages=600)
    assert all(not r["Ticker"].startswith("X") for r in rows)


# --------------------------------------------------------------------------
#  头尾两趟：超过上限但不到两倍的查询，靠反向排序补齐
# --------------------------------------------------------------------------
def test_a_slice_over_the_cap_is_completed_from_the_other_end(adapter):
    """1123 行（2026-09-30 真实的 sec_financial 大小）必须一行不缺。"""
    fake = FakeFinviz({"sec_financial": 1123})
    df, claimed = adapter._scrape_pages(
        fake, "111", {"f": "sec_financial"}, max_pages=600)
    assert claimed == 1123
    got = set(df["Ticker"])
    assert len(got) == 1123, f"缺 {1123 - len(got)} 行"
    assert got == {_ticker(0, i) for i in range(1, 1124)}
    assert max(r for _f, r, _o in fake.requested) <= ROW_CAP


def test_the_tail_pass_only_fetches_the_overflow(adapter):
    """尾巴只需要溢出的那部分，不该再抓一整个 ROW_CAP。"""
    fake = FakeFinviz({"sec_financial": 1123})
    adapter._scrape_pages(fake, "111", {"f": "sec_financial"}, max_pages=600)
    desc_pages = [r for _f, r, o in fake.requested if o == "-ticker"]
    # 123 行溢出 = 7 页；留一页余量，但绝不能是 50 页
    assert 6 <= len(desc_pages) <= 9, desc_pages


def test_a_query_over_twice_the_cap_says_the_middle_is_unreachable(adapter, caplog):
    """头尾各 1000 行也盖不住 2500 行——中间那段必须报出来，不许静默变短。"""
    fake = FakeFinviz({"sec_financial": 2500})
    with caplog.at_level("ERROR"):
        df, _ = adapter._scrape_pages(
            fake, "111", {"f": "sec_financial"}, max_pages=600)
    assert "cannot be read at all" in caplog.text
    assert len(df) < 2500


# --------------------------------------------------------------------------
#  整个市场：板块切分必须穷尽，且对账要自己核
# --------------------------------------------------------------------------
def test_the_whole_universe_survives_the_cap(adapter, monkeypatch):
    """5613 行的市场，切成 11 个板块后一行不缺——这是 09-30 那两班该有的结果。

    真实大小（2026-09-30 现场量的，Σ = 5613 = 未切分时的 claim）。
    """
    real = {"sec_basicmaterials": 292, "sec_communicationservices": 255,
            "sec_consumercyclical": 529, "sec_consumerdefensive": 241,
            "sec_energy": 252, "sec_financial": 1123, "sec_healthcare": 1052,
            "sec_industrials": 719, "sec_realestate": 247,
            "sec_technology": 796, "sec_utilities": 107}
    assert set(real) == set(SECTOR_FILTERS)
    assert sum(real.values()) == 5613

    fake = FakeFinviz(real)
    monkeypatch.setattr(fa.requests, "Session", lambda: fake)

    df = adapter._fetch_html_screener()
    assert len(df) == 5613
    assert df["Ticker"].nunique() == 5613
    # claimed_total 必须是整个市场的数，不是各块之和——切分本身漏了一块时，
    # 自洽的和会正好把要报的那个故障藏住。
    assert adapter.claimed_total == 5613
    assert max(r for _f, r, _o in fake.requested) <= ROW_CAP


def test_a_sector_falling_out_of_the_partition_is_reported(adapter, monkeypatch, caplog):
    """阳性对照②「改了但接错」：Finviz 加一个板块时必须报不对账。

    假 Finviz 声明的整体是各块之和 + 40，于是 11 块加起来对不上整体。
    对账写成「各块之和 vs 各块之和」的话这条必然绿——所以它在这里必须红。
    """
    sizes = {s: 100 for s in SECTOR_FILTERS}
    fake = FakeFinviz(sizes)
    # 未切分的查询（f 里没有任何 sec_）多声明 40 行：一个不在 11 块里的板块。
    orig_get = fake.get

    def get(url, params=None, timeout=None):
        resp = orig_get(url, params=params, timeout=timeout)
        if not any(s in (params or {}).get("f", "") for s in SECTOR_FILTERS):
            resp.text = re.sub(r"#1 / [\d,]+ Total", "#1 / 1,140 Total", resp.text)
        return resp

    fake.get = get
    monkeypatch.setattr(fa.requests, "Session", lambda: fake)

    with caplog.at_level("ERROR"):
        df = adapter._fetch_html_screener()
    assert "does not reconcile" in caplog.text
    assert "missing 40" in caplog.text
    assert len(df) == 1100
    assert adapter.claimed_total == 1140


def test_the_index_membership_helper_keeps_its_contract(adapter):
    """`fetch_index_members` 靠 `_scrape_view` 拿 DataFrame——拆函数不许改这个约定。

    它本体在本套件里被 conftest 的 `_no_vendor_network` 整体打桩（一条测试
    偷偷联网，比一条慢测试更坏），所以这里盯的是它唯一的依赖：`_scrape_view`
    仍然只返回 DataFrame（不是 `_scrape_pages` 那个二元组），且带 Ticker 列。
    指数成分 503 名在上限之下，一趟就够，不触发尾巴那条路。
    """
    fake = FakeFinviz({"idx_sp500": 503})
    df = adapter._scrape_view(fake, "111", {"f": "idx_sp500"}, max_pages=60)
    assert isinstance(df, pd.DataFrame)
    assert "Ticker" in df.columns
    assert len(df) == 503
    assert not any(o for _f, _r, o in fake.requested), "503 名不该走反向那一趟"
