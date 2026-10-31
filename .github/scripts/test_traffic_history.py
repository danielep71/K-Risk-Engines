"""Tests for the traffic history merge and alert (.github/scripts/traffic_history.py)."""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import traffic_history as traffic  # noqa: E402

LEGACY_DAILY = "date,views,unique_views,clones,unique_clones\r\n2026-10-07,1,1,5,2\r\n2026-10-20,9,9,9,9\r\n"
SNAPSHOT_HEADER = ",".join(traffic.HEADERS[traffic.SNAPSHOTS]) + "\r\n"


def moment(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)


def responses(days: dict[str, tuple[int, int, int, int]], *, referrers: tuple[tuple[str, int], ...] = (),
              stars: int = 0, views_14d: int = 0, clones_14d: int = 0) -> dict[str, Any]:
    return {
        "views.json": {"count": views_14d, "uniques": 1, "views": [
            {"timestamp": f"{day}T00:00:00Z", "count": v, "uniques": uv}
            for day, (v, uv, _, _) in days.items()]},
        "clones.json": {"count": clones_14d, "uniques": 1, "clones": [
            {"timestamp": f"{day}T00:00:00Z", "count": c, "uniques": uc}
            for day, (_, _, c, uc) in days.items()]},
        "referrers.json": [{"referrer": name, "count": n, "uniques": 1} for name, n in referrers],
        "paths.json": [{"path": "/o/r", "title": "Overview", "count": 3, "uniques": 2}],
        "repo.json": {"stargazers_count": stars, "forks_count": 0, "subscribers_count": 0,
                      "open_issues_count": 2},
    }


class Workspace:
    def __init__(self, directory: str) -> None:
        self.root = Path(directory)
        self.raw, self.data = self.root / "raw", self.root / "data"
        self.raw.mkdir()
        self.data.mkdir()

    def collect(self, at: str, payload: dict[str, Any]) -> dict[str, str]:
        for name, value in payload.items():
            (self.raw / name).write_text(json.dumps(value), encoding="utf-8")
        return traffic.merge(self.raw, self.data, moment(at))

    def rows(self, name: str) -> list[dict[str, str]]:
        return traffic.read_history(self.data / name)

    def snapshot(self) -> dict[str, bytes]:
        return {str(path.relative_to(self.data)): path.read_bytes()
                for path in sorted(self.data.rglob("*")) if path.is_file()}


class MergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.space = Workspace(self.directory.name)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_merging_the_same_collection_twice_changes_nothing(self) -> None:
        payload = responses({"2026-10-30": (3, 1, 7, 2)})
        self.space.collect("2026-10-31T06:17:00Z", payload)
        first = self.space.snapshot()
        self.space.collect("2026-10-31T06:17:00Z", payload)
        self.assertEqual(self.space.snapshot(), first)

    def test_newest_observation_of_a_date_wins(self) -> None:
        self.space.collect("2026-10-31T06:17:00Z", responses({"2026-10-30": (3, 1, 7, 2)}))
        self.space.collect("2026-11-01T06:17:00Z", responses({"2026-10-30": (5, 2, 8, 3)}))
        row = self.space.rows(traffic.DAILY)[0]
        self.assertEqual((row["views"], row["clones"], row["observed_at"]),
                         ("5", "8", "2026-11-01T06:17:00+00:00"))

    def test_an_older_collection_replayed_later_does_not_overwrite(self) -> None:
        self.space.collect("2026-11-01T06:17:00Z", responses({"2026-10-30": (5, 2, 8, 3)}, views_14d=9))
        self.space.collect("2026-11-01T05:00:00Z", responses({"2026-10-30": (1, 1, 1, 1)}, views_14d=1))
        self.assertEqual(self.space.rows(traffic.DAILY)[0]["views"], "5")
        snapshot = self.space.rows(traffic.SNAPSHOTS)[0]
        self.assertEqual((snapshot["views_14d"], snapshot["snapshot_datetime_utc"]),
                         ("9", "2026-11-01T06:17:00+00:00"))

    def test_a_later_collection_the_same_day_replaces_the_snapshot(self) -> None:
        self.space.collect("2026-11-01T06:17:00Z", responses({}, referrers=(("a.example", 1),)))
        self.space.collect("2026-11-01T09:00:00Z", responses({}, referrers=(("b.example", 2),)))
        self.assertEqual(len(self.space.rows(traffic.SNAPSHOTS)), 1)
        self.assertEqual([row["referrer"] for row in self.space.rows(traffic.REFERRERS)], ["b.example"])

    def test_unreported_dates_keep_their_stored_values(self) -> None:
        self.space.collect("2026-10-31T06:17:00Z", responses({"2026-10-17": (4, 4, 4, 4)}))
        self.space.collect("2026-11-01T06:17:00Z", responses({"2026-10-31": (1, 1, 1, 1)}))
        self.assertEqual([(row["date"], row["views"]) for row in self.space.rows(traffic.DAILY)],
                         [("2026-10-17", "4"), ("2026-10-31", "1")])

    def test_legacy_daily_file_is_read_and_rewritten_with_observation_times(self) -> None:
        (self.space.data / traffic.DAILY).write_bytes(LEGACY_DAILY.encode())
        self.space.collect("2026-11-01T06:17:00Z", responses({"2026-10-20": (2, 2, 3, 3)}))
        rows = self.space.rows(traffic.DAILY)
        self.assertEqual(rows[0], {"date": "2026-10-07", "views": "1", "unique_views": "1",
                                   "clones": "5", "unique_clones": "2", "observed_at": ""})
        self.assertEqual((rows[1]["views"], rows[1]["observed_at"]), ("2", "2026-11-01T06:17:00+00:00"))
        header = (self.space.data / traffic.DAILY).read_bytes().split(b"\r\n")[0]
        self.assertEqual(header.decode(), ",".join(traffic.HEADERS[traffic.DAILY]))

    def test_badges_are_rebuilt_from_the_stored_history(self) -> None:
        (self.space.data / traffic.DAILY).write_bytes(LEGACY_DAILY.encode())
        self.space.collect("2026-11-01T06:17:00Z", responses({"2026-10-31": (1, 1, 1000, 1)}))
        badge = json.loads((self.space.data / "badges/clones.json").read_text())
        self.assertEqual(badge, {"schemaVersion": 1, "label": "clones", "message": "1k",
                                 "color": traffic.BADGE_COLOR})
        visits = json.loads((self.space.data / "badges/visits.json").read_text())
        self.assertEqual(visits["message"], "11")

    def test_an_invalid_response_writes_nothing(self) -> None:
        self.space.collect("2026-10-31T06:17:00Z", responses({"2026-10-30": (3, 1, 7, 2)}))
        before = self.space.snapshot()
        broken = responses({"2026-10-31": (1, 1, 1, 1)})
        broken["clones.json"]["clones"][0]["count"] = -1
        with self.assertRaises(traffic.TrafficError):
            self.space.collect("2026-11-01T06:17:00Z", broken)
        self.assertEqual(self.space.snapshot(), before)

    def test_an_unexpected_history_file_writes_nothing(self) -> None:
        (self.space.data / traffic.SNAPSHOTS).write_text("day,views\r\n2026-10-30,1\r\n")
        with self.assertRaisesRegex(traffic.TrafficError, "header"):
            self.space.collect("2026-11-01T06:17:00Z", responses({}))
        self.assertFalse((self.space.data / traffic.DAILY).exists())


class AlertTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.space = Workspace(self.directory.name)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_no_alert_without_two_snapshots_or_a_change(self) -> None:
        self.assertIsNone(traffic.alert(self.space.data, "2026-12-31"))
        self.space.collect("2026-10-31T06:17:00Z", responses({}))
        self.assertIsNone(traffic.alert(self.space.data, "2026-12-31"))
        self.space.collect("2026-11-01T06:17:00Z", responses({}))
        self.assertIsNone(traffic.alert(self.space.data, "2026-12-31"))

    def test_spikes_stars_and_new_referrers_raise_one_alert(self) -> None:
        self.space.collect("2026-10-31T06:17:00Z", responses({}, referrers=(("old.example", 9),)))
        self.space.collect("2026-11-01T06:17:00Z", responses(
            {}, referrers=(("old.example", 9), ("new.example", 5), ("small.example", 4)),
            stars=1, views_14d=100, clones_14d=10))
        issue = traffic.alert(self.space.data, "2026-12-31")
        assert issue is not None
        self.assertEqual(issue["title"], "Traffic alert: 2026-11-01")
        body = issue["body"]
        self.assertIn("views spike, clones spike, stars increased, new referrer", body)
        new = body.split("**New referrers**", 1)[1].split("**Top referrers:**", 1)[0]
        self.assertIn("new.example", new)
        self.assertNotIn("small.example", new)
        self.assertNotIn("old.example", new)

    def test_alert_body_passes_issue_triage(self) -> None:
        self.space.collect("2026-10-31T06:17:00Z", responses({}))
        self.space.collect("2026-11-01T06:17:00Z", responses({}, stars=2))
        for due, target in (("2026-12-31", "2026-11-15"), ("2026-11-10", "2026-11-09"),
                            (None, "2026-11-15")):
            with self.subTest(due=due):
                issue = traffic.alert(self.space.data, due)
                assert issue is not None
                # The planning line and the dependency section issue triage reads.
                self.assertRegex(issue["body"], rf"(?m)^- Target end date: {target} \(Europe/Rome\)$")
                self.assertRegex(issue["body"], r"(?m)^## .*Dependencies and blocking status\n\nNone\.$")


class MainTests(unittest.TestCase):
    def test_merge_and_alert_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            space = Workspace(directory)
            for name, value in responses({}).items():
                (space.raw / name).write_text(json.dumps(value), encoding="utf-8")
            output = space.root / "alert.json"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                code = traffic.main(["merge", "--raw", str(space.raw), "--data", str(space.data),
                                     "--collected-at", "2026-11-01T06:17:00Z"])
                self.assertEqual(code, 0)
                code = traffic.main(["alert", "--data", str(space.data), "--milestone-due",
                                     "2026-12-31", "--output", str(output)])
            self.assertEqual(code, 0)
            self.assertFalse(output.exists())
            self.assertTrue(re.search(r"No traffic alert is due", stdout.getvalue()))

    def test_invalid_input_exits_with_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stderr(io.StringIO()):
            space = Workspace(directory)
            code = traffic.main(["merge", "--raw", str(space.raw), "--data", str(space.data),
                                 "--collected-at", "2026-11-01T06:17:00Z"])
            self.assertEqual(code, 2)
            code = traffic.main(["alert", "--data", str(space.data), "--milestone-due", "soon",
                                 "--output", str(space.root / "a.json")])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
