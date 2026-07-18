import os
import re
from pathlib import Path

from command import command
from config import (
    BROWSER_WINDOW_HEIGHT,
    BROWSER_WINDOW_WIDTH,
    CAPTURE_FALLBACK_OFFSET_Y,
    CAPTURE_SIZE,
    CHROME_PATH,
    EXTENSION_CRX_PATH,
    KEEP_BROWSER_OPEN,
    MOVE_DURATION_MS,
    PAGE_TIMEOUT_SECONDS,
)
from optimization import optimization
from tools import Screen, get_image
from web_cube import ChromeCubeController, CubeControlError, MoveSyntaxError


def run(execute_code: str, controller: ChromeCubeController):
    """Send the complete solution to the page without moving the mouse."""

    return controller.execute_solution(execute_code)


def run_chrome() -> ChromeCubeController:
    controller = ChromeCubeController(
        chrome_path=CHROME_PATH,
        extension_crx_path=EXTENSION_CRX_PATH,
        move_duration_ms=MOVE_DURATION_MS,
        keep_browser_open=KEEP_BROWSER_OPEN,
        page_timeout_seconds=PAGE_TIMEOUT_SECONDS,
        window_width=BROWSER_WINDOW_WIDTH,
        window_height=BROWSER_WINDOW_HEIGHT,
    )
    engine = controller.open()
    print("本地网页控制接口已连接：{}；正在自动开始并随机打乱…".format(engine))
    controller.start_game()
    print("网页已自动开始，随机打乱完成（无需双击）")
    return controller


def main():
    # command.py intentionally remains unchanged and reads ./Image/*.jpg.
    os.chdir(str(Path(__file__).resolve().parent))
    controller = run_chrome()
    try:
        screen = Screen(
            controller,
            cube_side=CAPTURE_SIZE,
            fallback_offset_y=CAPTURE_FALLBACK_OFFSET_Y,
        )

        # The four views are now rotated and captured inside Chrome. command.py's
        # colour recognition and two-phase solving logic remain unchanged.
        get_image(controller, screen)
        code = command()
        print(code + '\t', len(re.split(r"\s+", code.strip())))

        code_new = optimization(code)
        print(code_new + '\t', len(re.split(r"\s+", code_new.strip())))

        # Execute the solver's exact sequence. optimization.py was written for
        # old screen-coordinate gestures (its X/Y/Z substitutions are view
        # changes), whereas the page API addresses intrinsic cube faces.
        report = run(code_new, controller)
        print(
            "网页端执行完成：{} 步（{} 个 90° 动作），耗时 {:.3f} 秒".format(
                report.moves, report.quarter_turns, report.elapsed_seconds
            )
        )
    finally:
        if not KEEP_BROWSER_OPEN:
            controller.close()


if __name__ == '__main__':
    try:
        main()
    except (CubeControlError, MoveSyntaxError) as exc:
        raise SystemExit("网页魔方控制失败：{}".format(exc))
