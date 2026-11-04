"""Single run for Actions; never emit original account/API logs."""
import contextlib
import io
import json
import os
import sys
from pathlib import Path


TARGET_UID = ""  # Set the single streamer UID before running.


def run():
    if not TARGET_UID.isascii() or not TARGET_UID.isdecimal() or int(TARGET_UID) <= 0:
        print("A single streamer TARGET_UID must be configured before running.")
        return 1
    key = os.environ.pop("BILI_ACCESS_KEY", "").strip()
    if not key or any(c.isspace() for c in key):
        print("Missing or invalid BILI_ACCESS_KEY repository secret.")
        return 1
    failed = []
    try:
        import yaml
        from loguru import logger
        config = yaml.safe_load(Path(__file__).with_name("users.example.yaml").read_text())
        config.update(CRON=None, CRON_INDEX=0, STOPWATCHINGTIME=4500,
                      SENDKEY=None, MOREPUSH=None, PROXY=None,
                      WATCHINGLIVE=30, WATCHINGLIVE_CD=60,
                      LIKE_COUNT=0, DANMAKU_COUNT=1, DANMAKU_CD=60,
                      SIGNINGROUP_CD=-1, CUSTOMSIGNIN_CD=-1, WEARMEDAL=0)
        config["USERS"] = [{"access_key": key, "white_uid": TARGET_UID, "banned_uid": 0}]
        os.environ["USERS"] = json.dumps(config)
        # Import installs the project's verbose logger. Suppress all output here.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            import main
            logger.remove()
            def collect(message):
                if message.record["level"].no >= 40:
                    failed.append(True)
            logger.add(collect, level="ERROR", backtrace=False, diagnose=False)
            main.run()
        os.environ.pop("USERS", None)
    except BaseException:
        os.environ.pop("USERS", None)
        print("Run failed. Raw account/API details were withheld for privacy.")
        return 1
    if failed:
        print("Run reported errors; check credential validity or retry later. Raw details were withheld.")
        return 1
    print("Run completed without reported errors. Intimacy rewards are not independently verified.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
