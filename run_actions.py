"""Produce a single daily fans medal report from offline data."""
import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from tempfile import NamedTemporaryFile
from pathlib import Path


CHINA_TIME = timezone(timedelta(hours=8))
DEMO = {"level": 12, "intimacy": 830, "watch_minutes": 15}
FIELDS = {"level", "intimacy", "watch_minutes"}


def report(snapshot, day, source):
    if type(snapshot) is not dict or set(snapshot) != FIELDS:
        raise ValueError
    level, intimacy, minutes = (snapshot[key] for key in ("level", "intimacy", "watch_minutes"))
    if type(level) is not int or not 1 <= level <= 120:
        raise ValueError
    if type(intimacy) is not int or intimacy < 0:
        raise ValueError
    if minutes is not None and (type(minutes) is not int or minutes < 0):
        raise ValueError
    return {
        "date": day,
        "source": source,
        "level": level,
        "intimacy": intimacy,
        "watch_minutes": minutes,
        "watch_base_points_estimate": None if minutes is None else min(minutes // 5, 5) * 6,
        "platform_operations": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=date.fromisoformat)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("daily-reports"))
    args = parser.parse_args()
    day = (args.date or datetime.now(CHINA_TIME).date()).isoformat()
    source = "manual" if args.snapshot is not None else "mock"
    try:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8")) if args.snapshot else DEMO
        result = report(snapshot, day, source)
        args.output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = args.output_dir / f"{source}-{day}.json"
        # Publish the complete file atomically without replacing an existing report.
        with NamedTemporaryFile(dir=args.output_dir, mode="w", encoding="utf-8") as output:
            json.dump(result, output, indent=2)
            output.write("\n")
            output.flush()
            path.hardlink_to(output.name)
    except FileExistsError:
        print("今日报告已存在，跳过。")
        return 0
    except (OSError, ValueError, RecursionError):
        print("报告生成失败，请检查快照格式及输出目录。", file=sys.stderr)
        return 1
    print(json.dumps(result) if source == "mock" else "已保存今日手动快照报告。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
