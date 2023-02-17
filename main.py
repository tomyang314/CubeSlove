import pyautogui
from command import *
from tools import Mouse, Screen, get_image
import webbrowser
import time
import re
from optimization import optimization


position = (960, 910)
path = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"  # 安装了魔方插件的chrome浏览器的路径

mouse = Mouse()
screen = Screen()


def run(execute_code: str):
    for val in re.split(r"[ ]+", execute_code):
        if val == "U":
            mouse.up(0)
        elif val == "U'":
            mouse.up(1)
        elif val == "U2":
            mouse.up(2)

        elif val == "D":
            mouse.down(0)
        elif val == "D'":
            mouse.down(1)
        elif val == "D2":
            mouse.down(2)

        elif val == "L":
            mouse.left(0)
        elif val == "L'":
            mouse.left(1)
        elif val == "L2":
            mouse.left(2)

        elif val == "R":
            mouse.right(0)
        elif val == "R'":
            mouse.right(1)
        elif val == "R2":
            mouse.right(2)

        elif val == "F":
            mouse.front(0)
        elif val == "F'":
            mouse.front(1)
        elif val == "F2":
            mouse.front(2)

        elif val == "B":
            mouse.behind(0)
        elif val == "B'":
            mouse.behind(1)
        elif val == "B2":
            mouse.behind(2)

        elif val == "X":
            mouse.x_axis(0)
        elif val == "X'":
            mouse.x_axis(1)
        elif val == "X2":
            mouse.x_axis(2)

        elif val == "Y":
            mouse.y_axis(0)
        elif val == "Y'":
            mouse.y_axis(1)
        elif val == "Y2":
            mouse.y_axis(2)

        elif val == "Z":
            mouse.z_axis(0)

        elif val == "Z'":
            mouse.z_axis(1)

        elif val == "Z2":
            mouse.z_axis(2)


def run_chrome():
    webbrowser.register("Chrome", None, webbrowser.BackgroundBrowser(path))
    webbrowser.get("Chrome").open('chrome-extension://dlabgdldanmcjlmnifgogbnffionmfki/index.html', new=1,
                                  autoraise=True)

    time.sleep(6)

    pyautogui.moveTo(position)
    pyautogui.doubleClick()

    time.sleep(6)


if __name__ == '__main__':
    run_chrome()

    get_image(mouse, screen)
    code = command()
    print(code)

    code_new = optimization(code)
    print(code_new)

    run(code_new)

