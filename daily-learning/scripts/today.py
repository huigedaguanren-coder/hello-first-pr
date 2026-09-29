#!/usr/bin/env python3
"""Work out which lesson to teach on a given date.

The schedule is derived from the date alone, so no progress file is needed:
  Mon/Wed -> track A (贸易合规与实务)
  Tue/Thu -> track B (半导体产业结构)
  Fri     -> weekly review of that week's Mon-Thu lessons
  Sat/Sun -> no new lesson

Usage:
  python today.py                  # today, Asia/Shanghai
  python today.py --date 2026-10-12
  python today.py --lesson A5      # a specific lesson (catch-up / 补课)
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

START = date(2026, 9, 29)  # first lesson day
TRACK_DAYS = {"A": (0, 2), "B": (1, 3)}  # Monday = 0
WEEKDAY_CN = "一二三四五六日"

CURRICULUM = json.loads(
    (Path(__file__).resolve().parent.parent / "references" / "curriculum.json").read_text(encoding="utf-8")
)["tracks"]


def lesson_info(track, count):
    """count is 1-based across rounds; round 2+ revisits the list at greater depth."""
    lessons = CURRICULUM[track]["lessons"]
    idx = (count - 1) % len(lessons)
    return {
        "track": track,
        "track_name": CURRICULUM[track]["name"],
        "number": idx + 1,
        "total": len(lessons),
        "round": (count - 1) // len(lessons) + 1,
        "title": lessons[idx]["title"],
        "points": lessons[idx]["points"],
    }


def count_for(track, d):
    """How many track days fall in [START, d]."""
    n, cur = 0, START
    while cur <= d:
        if cur.weekday() in TRACK_DAYS[track]:
            n += 1
        cur += timedelta(days=1)
    return n


def plan_for(d):
    base = {"date": d.isoformat(), "weekday": "周" + WEEKDAY_CN[d.weekday()]}
    if d < START:
        return {**base, "mode": "before_start", "first_day": START.isoformat()}
    wd = d.weekday()
    for track, days in TRACK_DAYS.items():
        if wd in days:
            return {**base, "mode": "lesson", **lesson_info(track, count_for(track, d))}
    if wd == 4:
        monday = d - timedelta(days=4)
        week = []
        for i in range(4):
            day = monday + timedelta(days=i)
            if day < START:
                continue
            track = next(t for t, ds in TRACK_DAYS.items() if day.weekday() in ds)
            week.append({"date": day.isoformat(), **lesson_info(track, count_for(track, day))})
        return {**base, "mode": "review", "lessons": week}
    return {**base, "mode": "weekend"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD, default: today in Asia/Shanghai")
    ap.add_argument("--lesson", help="e.g. A5 or B12")
    args = ap.parse_args()

    if args.lesson:
        track, num = args.lesson[0].upper(), args.lesson[1:]
        if track not in CURRICULUM or not num.isdigit() or not 1 <= int(num) <= len(CURRICULUM[track]["lessons"]):
            sys.exit(f"unknown lesson: {args.lesson}")
        out = {"mode": "lesson", "requested": True, **lesson_info(track, int(num))}
    else:
        d = date.fromisoformat(args.date) if args.date else datetime.now(ZoneInfo("Asia/Shanghai")).date()
        out = plan_for(d)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
