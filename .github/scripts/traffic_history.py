#!/usr/bin/env python3
"""Merge GitHub traffic API responses into the CSV history of the traffic-history branch.

The traffic API keeps 14 days. Each collection is merged by date: the newest
observation of a date wins, dates a collection does not report keep their
stored values, and nothing is summed across collections, so merging the same
collection twice changes nothing. Every response and every existing file is
validated before anything is written, so an invalid collection leaves the
history unchanged. After each merge the README badge files are rewritten from
the stored data.

The alert command compares the two latest snapshots and, when traffic spikes,
stars or forks increase, or a new referrer appears, writes the title and body
of one alert issue for the workflow to open (docs/TRAFFIC.md).

The merge rules (newest observation, idempotent merge, validation before
writing) and the alert's planning section were adapted from
danielep71/MyTemplate's tools/traffic_history.py (see NOTICE.md); the CSV
layout is this repository's own.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

SNAPSHOTS = "traffic.csv"
DAILY = "traffic_daily.csv"
REFERRERS = "referrers.csv"
PATHS = "popular_paths.csv"
HEADERS: dict[str, tuple[str, ...]] = {
    SNAPSHOTS: ("snapshot_date", "snapshot_datetime_utc", "views_14d", "unique_views_14d",
                "clones_14d", "unique_clones_14d", "stars", "forks", "watchers", "open_issues"),
    # observed_at: the collection that last reported the date's values.
    DAILY: ("date", "views", "unique_views", "clones", "unique_clones", "observed_at"),
    REFERRERS: ("snapshot_date", "rank", "referrer", "count", "uniques"),
    PATHS: ("snapshot_date", "rank", "path", "title", "count", "uniques"),
}
# Earlier layouts, read and rewritten with the current header on the next merge.
# A daily row without observed_at counts as older than any collection.
LEGACY_HEADERS: dict[str, tuple[tuple[str, ...], ...]] = {
    DAILY: (("date", "views", "unique_views", "clones", "unique_clones"),),
}
RESPONSES = ("views.json", "clones.json", "referrers.json", "paths.json", "repo.json")
REPOSITORY_COUNTS = {"stars": "stargazers_count", "forks": "forks_count",
                     "watchers": "subscribers_count", "open_issues": "open_issues_count"}
NUMERIC = {"views", "unique_views", "clones", "unique_clones", "views_14d", "unique_views_14d",
           "clones_14d", "unique_clones_14d", "rank", "count", "uniques", *REPOSITORY_COUNTS}
BADGE_COLOR = "217346"
# Alert thresholds: a spike doubles the 14-day count and adds at least this many.
SPIKE_GROWTH = {"views_14d": 100, "clones_14d": 10}
NEW_REFERRER_VIEWS = 5
ALERT_DAYS = 14
Row = dict[str, str]


class TrafficError(Exception):
    """An invalid response or history file; nothing has been written."""


def stamp(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat(timespec="seconds")


def parse_stamp(value: str, where: str) -> datetime:
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise TrafficError(f"{where}: invalid time {value!r}") from error
    if moment.tzinfo is None:
        raise TrafficError(f"{where}: time {value!r} has no time zone")
    return moment


def count(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TrafficError(f"{where}: expected a non-negative integer, found {value!r}")
    return value


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise TrafficError(f"{path.name}: {error}") from error


def parse_series(data: Any, key: str) -> tuple[int, int, dict[str, tuple[int, int]]]:
    """The 14-day count and uniques, and the per-day counts of a views or clones response."""
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        raise TrafficError(f"Unexpected {key} API response")
    days: dict[str, tuple[int, int]] = {}
    for item in data[key]:
        if not isinstance(item, dict):
            raise TrafficError(f"{key}: unexpected entry {item!r}")
        day = str(item.get("timestamp", ""))[:10]
        try:
            date.fromisoformat(day)
        except ValueError as error:
            raise TrafficError(f"{key}: invalid timestamp {item.get('timestamp')!r}") from error
        days[day] = (count(item.get("count"), f"{key} {day}"),
                     count(item.get("uniques"), f"{key} {day}"))
    return count(data.get("count"), key), count(data.get("uniques"), key), days


def parse_ranked(data: Any, name: str, fields: Sequence[str], day: str) -> list[Row]:
    if not isinstance(data, list):
        raise TrafficError(f"Unexpected {name} API response")
    rows = []
    for rank, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise TrafficError(f"{name}: unexpected entry {item!r}")
        row = {"snapshot_date": day, "rank": str(rank)}
        row.update({field: str(item.get(field, "")) for field in fields})
        row["count"] = str(count(item.get("count"), f"{name} {rank}"))
        row["uniques"] = str(count(item.get("uniques"), f"{name} {rank}"))
        rows.append(row)
    return rows


def read_history(path: Path) -> list[Row]:
    """Read a history file in its current or an earlier layout, validating every row."""
    if not path.exists():
        return []
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")))
    header = HEADERS[path.name]
    found = tuple(reader.fieldnames or ())
    if found not in (header, *LEGACY_HEADERS.get(path.name, ())):
        raise TrafficError(f"{path.name}: header is {list(found)}, expected {list(header)}")
    rows = []
    for number, raw in enumerate(reader, start=2):
        row = {key: raw.get(key) or "" for key in header}
        for key in header:
            value = row[key]
            if key in NUMERIC and not value.isdigit():
                raise TrafficError(f"{path.name} line {number}: {key} is {value!r}")
        key_field = "date" if path.name == DAILY else "snapshot_date"
        try:
            date.fromisoformat(row[key_field])
        except ValueError as error:
            raise TrafficError(f"{path.name} line {number}: invalid {key_field}") from error
        if row.get("snapshot_datetime_utc"):
            parse_stamp(row["snapshot_datetime_utc"], f"{path.name} line {number}")
        if row.get("observed_at"):
            parse_stamp(row["observed_at"], f"{path.name} line {number}")
        rows.append(row)
    return rows


def render(name: str, rows: Sequence[Mapping[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=HEADERS[name], lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def merge_daily(rows: list[Row], days: Mapping[str, Row], observed: str) -> list[Row]:
    """Each reported date takes this collection's values unless a newer one already reported it."""
    by_date = {row["date"]: row for row in rows}
    moment = parse_stamp(observed, "collection")
    for day, values in days.items():
        stored = by_date.get(day)
        if stored and stored["observed_at"] and parse_stamp(stored["observed_at"], day) > moment:
            continue
        by_date[day] = dict(values, date=day, observed_at=observed)
    return [by_date[day] for day in sorted(by_date)]


def compact(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M".replace(".0M", "M")
    if value >= 1000:
        return f"{value / 1000:.1f}k".replace(".0k", "k")
    return str(value)


def badge(label: str, value: int) -> str:
    return json.dumps({"schemaVersion": 1, "label": label, "message": compact(value),
                       "color": BADGE_COLOR}) + "\n"


def merge(raw: Path, data: Path, collected_at: datetime) -> dict[str, str]:
    """Merge one collection; return the files written, relative to ``data``."""
    responses = {name: load_json(raw / name) for name in RESPONSES}
    views, unique_views, view_days = parse_series(responses["views.json"], "views")
    clones, unique_clones, clone_days = parse_series(responses["clones.json"], "clones")
    repository = responses["repo.json"]
    if not isinstance(repository, dict):
        raise TrafficError("Unexpected repository metadata API response")
    counts = {key: count(repository.get(field), field) for key, field in REPOSITORY_COUNTS.items()}
    day = collected_at.astimezone(UTC).date().isoformat()
    observed = stamp(collected_at)
    referrers = parse_ranked(responses["referrers.json"], "referrers", ("referrer",), day)
    paths = parse_ranked(responses["paths.json"], "popular paths", ("path", "title"), day)
    history = {name: read_history(data / name) for name in HEADERS}

    snapshots = history[SNAPSHOTS]
    stored = next((row for row in snapshots if row["snapshot_date"] == day), None)
    newest = stored is None or parse_stamp(stored["snapshot_datetime_utc"], day) <= collected_at
    if newest:
        snapshot = {"snapshot_date": day, "snapshot_datetime_utc": observed,
                    "views_14d": str(views), "unique_views_14d": str(unique_views),
                    "clones_14d": str(clones), "unique_clones_14d": str(unique_clones),
                    **{key: str(value) for key, value in counts.items()}}
        snapshots = sorted([row for row in snapshots if row["snapshot_date"] != day] + [snapshot],
                           key=lambda row: row["snapshot_date"])
        for name, new in ((REFERRERS, referrers), (PATHS, paths)):
            kept = [row for row in history[name] if row["snapshot_date"] != day]
            history[name] = sorted(kept + new, key=lambda row: (row["snapshot_date"], int(row["rank"])))
    days: dict[str, Row] = {}
    for reported, key in ((view_days, "views"), (clone_days, "clones")):
        for when, (total, uniques) in reported.items():
            values = days.setdefault(when, {"views": "0", "unique_views": "0",
                                            "clones": "0", "unique_clones": "0"})
            values[key], values[f"unique_{key}"] = str(total), str(uniques)
    daily = merge_daily(history[DAILY], days, observed)

    latest = max(snapshots, key=lambda row: row["snapshot_date"])
    contents = {
        SNAPSHOTS: render(SNAPSHOTS, snapshots),
        DAILY: render(DAILY, daily),
        REFERRERS: render(REFERRERS, history[REFERRERS]),
        PATHS: render(PATHS, history[PATHS]),
        # README badges: total recorded clones (CI and maintainer clones included),
        # cumulative daily unique visitors, and unique visitors over the latest 14 days.
        "badges/clones.json": badge("clones", sum(int(row["clones"]) for row in daily)),
        "badges/visits.json": badge("visits", sum(int(row["unique_views"]) for row in daily)),
        "badges/visitors.json": badge("visitors (14d)", int(latest["unique_views_14d"])),
    }
    for name, text in contents.items():
        path = data / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")
    return contents


def alert(data: Path, milestone_due: str | None) -> dict[str, str] | None:
    """The alert issue for the latest snapshot, or None when nothing stands out."""
    snapshots = sorted(read_history(data / SNAPSHOTS), key=lambda row: row["snapshot_date"])
    if len(snapshots) < 2:
        return None
    previous, current = snapshots[-2], snapshots[-1]
    day = current["snapshot_date"]
    reasons = []
    for key, growth in SPIKE_GROWTH.items():
        before, now = int(previous[key]), int(current[key])
        if now >= max(before * 2, before + growth):
            reasons.append(f"{key.removesuffix('_14d').capitalize()} spike")
    for key in ("stars", "forks"):
        if int(current[key]) > int(previous[key]):
            reasons.append(f"{key.capitalize()} increased")
    referrers = read_history(data / REFERRERS)
    known = {row["referrer"] for row in referrers if row["snapshot_date"] < day}
    today = [row for row in referrers if row["snapshot_date"] == day]
    new = [row for row in today
           if row["referrer"] and row["referrer"] not in known
           and int(row["count"]) >= NEW_REFERRER_VIEWS]
    if new:
        reasons.append("New referrer")
    if not reasons:
        return None
    paths = [row for row in read_history(data / PATHS) if row["snapshot_date"] == day]

    def ranked(rows: Sequence[Row], label: str) -> list[str]:
        top = sorted(rows, key=lambda row: int(row["count"]), reverse=True)[:10]
        return [f"- {row[label]}: {row['count']} views, {row['uniques']} unique"
                for row in top] or ["- None reported."]

    def compared(key: str, name: str) -> str:
        return f"| {name} | {current[key]} | {previous[key]} |"

    # Issue triage requires a target end date before the milestone's due date.
    target = date.fromisoformat(day) + timedelta(days=ALERT_DAYS)
    if milestone_due:
        target = min(target, date.fromisoformat(milestone_due) - timedelta(days=1))
    body = [
        "## 🎯 Objective", "",
        f"Find out what drove the traffic recorded on {day}: " + ", ".join(reasons).lower() + ".", "",
        "## 📦 Context", "",
        "Opened by the **Daily traffic export** workflow (docs/TRAFFIC.md).", "",
        f"| 14-day snapshot | {day} | {previous['snapshot_date']} |", "| --- | --- | --- |",
        compared("views_14d", "Views"), compared("unique_views_14d", "Unique visitors"),
        compared("clones_14d", "Clones"), compared("unique_clones_14d", "Unique cloners"),
        compared("stars", "Stars"), compared("forks", "Forks"), "",
        f"**New referrers** (at least {NEW_REFERRER_VIEWS} views):", "", *ranked(new, "referrer"), "",
        "**Top referrers:**", "", *ranked(today, "referrer"), "",
        "**Popular paths:**", "", *ranked(paths, "path"), "",
        "## 🏁 Acceptance criteria", "",
        "- [ ] The sources are checked in **Insights → Traffic**: which referrer (a blog, "
        "forum, newsletter or another project) and which page drew the visits.",
        "- [ ] What was found, and any follow-up issue, is recorded in a Resolution.", "",
        "## 🔗 Dependencies and blocking status", "", "None.", "",
        "## 🗓️ Planning", "",
        f"- Target end date: {target.isoformat()} (Europe/Rome)",
        f"- Milestone due date: {milestone_due or 'not set'}",
    ]
    return {"title": f"Traffic alert: {day}", "body": "\n".join(body) + "\n"}


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    merging = commands.add_parser("merge", help="merge one collection into the history")
    merging.add_argument("--raw", type=Path, required=True, help="directory of API responses")
    merging.add_argument("--data", type=Path, required=True, help="history directory")
    merging.add_argument("--collected-at", required=True, help="collection time, ISO 8601 UTC")
    alerting = commands.add_parser("alert", help="write the alert issue, if one is due")
    alerting.add_argument("--data", type=Path, required=True)
    alerting.add_argument("--milestone-due", help="due date YYYY-MM-DD of the alert milestone")
    alerting.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "merge":
            collected_at = parse_stamp(args.collected_at, "--collected-at")
            for name in merge(args.raw, args.data, collected_at):
                print(f"Wrote {args.data / name}")
            return 0
        if args.milestone_due:
            date.fromisoformat(args.milestone_due)
        issue = alert(args.data, args.milestone_due)
    except (TrafficError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if issue is None:
        print("No traffic alert is due.")
        return 0
    args.output.write_text(json.dumps(issue) + "\n", encoding="utf-8")
    print(f"Alert due: {issue['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
