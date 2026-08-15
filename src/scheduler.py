"""Gate hourly GitHub workflow runs using the interval in ``config.json``."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import PROJECT_ROOT, load_config


DEFAULT_STATE_PATH = PROJECT_ROOT / "data" / "run_state.json"


def load_last_completed_at(
    path: Path = DEFAULT_STATE_PATH,
) -> datetime | None:
    """Return the last successful run time, or ``None`` for a new tracker."""

    if not path.exists() or path.stat().st_size == 0:
        return None

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in scheduler state: {path}") from error

    if not isinstance(data, dict) or not data.get("last_completed_at"):
        return None

    try:
        completed_at = datetime.fromisoformat(data["last_completed_at"])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid last_completed_at value in {path}") from error

    if completed_at.tzinfo is None:
        raise ValueError(f"last_completed_at must include a timezone in {path}")
    return completed_at.astimezone(timezone.utc)


def is_run_due(
    every_hours: int,
    *,
    now: datetime | None = None,
    path: Path = DEFAULT_STATE_PATH,
) -> bool:
    """Return whether the configured interval has elapsed."""

    current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    last_completed_at = load_last_completed_at(path)
    if last_completed_at is None:
        return True
    return current_time >= last_completed_at + timedelta(hours=every_hours)


def mark_run_completed(
    path: Path = DEFAULT_STATE_PATH,
    completed_at: datetime | None = None,
) -> None:
    """Record a successful email report so the next interval starts now."""

    timestamp = (completed_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump({"last_completed_at": timestamp.isoformat()}, file, indent=2)
        file.write("\n")
    temporary_path.replace(path)


def main() -> None:
    """Expose the due decision as a GitHub Actions step output."""

    config = load_config()
    force_run = os.getenv("FORCE_RUN", "").lower() == "true"
    should_run = force_run or is_run_due(config.schedule.every_hours)

    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write(f"should_run={str(should_run).lower()}\n")

    if force_run:
        print("Manual run requested; the flight search will run now.")
    elif should_run:
        print("The configured interval has elapsed; the flight search will run.")
    else:
        print("The configured interval has not elapsed; skipping this hourly check.")


if __name__ == "__main__":
    main()
