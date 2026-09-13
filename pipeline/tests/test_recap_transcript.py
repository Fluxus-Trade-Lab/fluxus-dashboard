"""fetch_transcript: VTT rolling-duplicate removal + which upload is the daily."""
from pipeline.content.recap.fetch_transcript import dedupe_vtt, is_daily_title, pick_daily

# Shape copied from a real YouTube auto-caption file (2026-09-11 daily):
# tagged cue, 10ms transition cue repeating it, next cue repeating line 1.
VTT = """WEBVTT
Kind: captions
Language: en

00:00:00.880 --> 00:00:04.390 align:start position:0%

Hello<00:00:02.000><c> investors,</c><00:00:03.200><c> welcome</c>

00:00:04.390 --> 00:00:04.400 align:start position:0%
Hello investors, welcome


00:00:04.400 --> 00:00:07.829 align:start position:0%
Hello investors, welcome
to<00:00:05.040><c> the</c><00:00:05.759><c> daily</c><00:00:06.240><c> market</c>

00:00:07.829 --> 00:00:07.839 align:start position:0%
to the daily market


00:01:10.000 --> 00:01:12.000 align:start position:0%
to the daily market
insight.<00:01:11.000><c> Today</c><00:01:11.500><c> is</c><00:01:11.700><c> Friday.</c>
"""


def test_dedupe_keeps_each_line_once_in_order():
    paras = dedupe_vtt(VTT, para_seconds=60)
    text = " ".join(p for _, p in paras)
    assert text == "Hello investors, welcome to the daily market insight. Today is Friday."
    assert text.count("Hello investors") == 1


def test_dedupe_splits_paragraphs_by_time():
    paras = dedupe_vtt(VTT, para_seconds=60)
    assert [t for t, _ in paras] == [0, 70]


def test_dedupe_positive_control_duplicates_exist_in_raw():
    # the raw file really does repeat lines — otherwise the test above is vacuous
    assert VTT.count("Hello investors, welcome") == 2


CHANNEL = [  # newest first, as the flat playlist returns it
    {"id": "wk", "title": "WEEKEND REVIEW $DELL $HPE SHOW LEADERSHIP", "duration": 1901},
    {"id": "d11", "title": "SELECT LEADERS STANDOUT AS INDEXES SNAP BACK", "duration": 2915},
    {"id": "pod", "title": "OIL TOPS $100! | Your Money Podcast Ep. 607", "duration": 2860},
    {"id": "d10", "title": "HOT PPI AND HIGHER YIELDS LEAD TO FURTHER WEAKNESS", "duration": 851},
    {"id": "d09", "title": "OIL, YIELDS, AND GEOPOLITICAL TENSIONS", "duration": 886},
]
UPLOADS = {"wk": "20260912", "d11": "20260911", "pod": "20260911", "d10": "20260910", "d09": "20260909"}


def test_title_rule():
    assert not is_daily_title("OIL TOPS $100! | Your Money Podcast Ep. 607")
    assert not is_daily_title("9/5 Weekend Review $DELL")
    assert is_daily_title("HOT PPI AND HIGHER YIELDS LEAD TO FURTHER WEAKNESS")


def test_pick_daily_excludes_podcast_same_day():
    # the podcast was uploaded the same day and is nearly as long — title rule must drop it
    got = pick_daily(CHANNEL, "2026-09-11", UPLOADS.get)
    assert got["id"] == "d11"


def test_pick_daily_older_session():
    assert pick_daily(CHANNEL, "2026-09-10", UPLOADS.get)["id"] == "d10"


def test_weekend_date_has_no_daily():
    assert pick_daily(CHANNEL, "2026-09-12", UPLOADS.get) is None


def test_pick_daily_positive_control_without_title_rule_would_be_wrong():
    # if titles were not filtered, 09-12 would pick the weekend show — proves the rule does work
    no_filter = [dict(e, title="x") for e in CHANNEL]
    assert pick_daily(no_filter, "2026-09-12", UPLOADS.get)["id"] == "wk"


def test_pick_daily_stops_after_walking_past_date():
    calls = []
    def ud(vid):
        calls.append(vid)
        return UPLOADS[vid]
    pick_daily(CHANNEL, "2026-09-11", ud)
    assert "d09" not in calls
