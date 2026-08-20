"""The Library index groups by the article's own `page`, never by filename."""
from __future__ import annotations

import json

import pytest

from pipeline.content import library_index as LI


def _write(d, name, **doc):
    (d / name).write_text(json.dumps(doc))


def test_every_page_key_is_present_even_when_empty(tmp_path):
    index, problems = LI.build(tmp_path)
    assert set(index) == set(LI.PAGES)
    assert all(v == [] for v in index.values())
    assert problems == []


def test_groups_by_the_page_field_not_the_filename(tmp_path):
    # Filename says offense, the article says defense. The article wins --
    # a prefix parse would file this under the wrong page silently.
    _write(tmp_path, "offense_mislabeled.json", page="defense", title="x")
    index, problems = LI.build(tmp_path)
    assert index["defense"] == ["offense_mislabeled.json"]
    assert index["offense"] == []
    assert problems == []


def test_hyphenated_page_is_not_split_on_the_underscore(tmp_path):
    _write(tmp_path, "portfolio-management_heat.json",
           page="portfolio-management", title="x")
    index, _ = LI.build(tmp_path)
    assert index["portfolio-management"] == ["portfolio-management_heat.json"]


def test_an_unknown_or_missing_page_is_reported_not_guessed(tmp_path):
    _write(tmp_path, "orphan.json", title="no page field")
    _write(tmp_path, "typo.json", page="offence", title="x")
    index, problems = LI.build(tmp_path)
    assert all(v == [] for v in index.values()), "a bad page was guessed into a bucket"
    assert len(problems) == 2
    assert any("orphan.json" in p for p in problems)
    assert any("offence" in p for p in problems)


def test_unparsable_file_does_not_take_the_index_down(tmp_path):
    (tmp_path / "broken.json").write_text("{not json")
    _write(tmp_path, "offense_good.json", page="offense", title="x")
    index, problems = LI.build(tmp_path)
    assert index["offense"] == ["offense_good.json"]
    assert any("broken.json" in p for p in problems)


def test_the_index_never_lists_itself(tmp_path):
    _write(tmp_path, "offense_a.json", page="offense", title="x")
    LI.write(tmp_path)
    index, problems = LI.build(tmp_path)   # second pass, index.json now on disk
    assert index["offense"] == ["offense_a.json"]
    assert problems == []


def test_write_round_trips(tmp_path):
    _write(tmp_path, "news_a.json", page="news", title="x")
    written = LI.write(tmp_path)
    on_disk = json.loads((tmp_path / "index.json").read_text())
    assert on_disk == written
    assert on_disk["news"] == ["news_a.json"]


def test_the_shipped_library_indexes_cleanly():
    """The real directory must have no orphans -- an unfiled article is invisible."""
    from pathlib import Path
    if not LI.LIBRARY_DIR.exists():
        pytest.skip("library dir not present in this checkout")
    index, problems = LI.build(LI.LIBRARY_DIR)
    assert problems == [], f"articles the index could not place: {problems}"
    assert sum(len(v) for v in index.values()) >= 1


def test_write_creates_the_directory_when_there_are_no_articles_yet(tmp_path):
    """Caught by the run_all smoke: a missing library dir threw inside the
    orchestrator's try/except, i.e. failed silently in production shape."""
    target = tmp_path / "does" / "not" / "exist"
    index = LI.write(target)
    assert (target / "index.json").exists()
    assert index == {p: [] for p in LI.PAGES}
