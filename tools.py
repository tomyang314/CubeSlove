import pyautogui
import cv2 as cv
import numpy as np
import time


class Mouse:
    def __init__(self):
        self.offset = 120
        self.size = tuple(pyautogui.size())
        self.x, self.y = self.size[0] / 2, self.size[1] / 2 + self.offset

    def up_turning(self):
        pyautogui.moveTo((self.x - 400, self.y + 100))
        pyautogui.dragRel(50, -300, duration=0.25)

    def down_turning(self):
        pyautogui.moveTo((self.x - 400, self.y - 300))
        pyautogui.dragRel(-100, 300, duration=0.25)

    def right_turning(self):
        pyautogui.moveTo((self.x - 100, self.y + 300))
        pyautogui.dragRel(300, 0, duration=0.25)

    def up(self, mode):
        offset_x = 50
        offset_y = 10

        if mode == 0:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(-200, 0, duration=0.25)
        elif mode == 1:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(200, 0, duration=0.25)
        elif mode == 2:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(1000, -200, duration=0.4)

    def down(self, mode):
        offset_x = 50
        offset_y = 170

        if mode == 0:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(200, 0, duration=0.25)
        elif mode == 1:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(-200, 0, duration=0.25)
        elif mode == 2:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(-600, 50, duration=0.45)

    def left(self, mode):
        offset_x = 200
        offset_y = 90

        if mode == 0:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(0, 200, duration=0.25)
        elif mode == 1:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(0, -200, duration=0.25)
        elif mode == 2:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(900, -550, duration=0.45)

    def right(self, mode):
        offset_x = 50
        offset_y = 10

        if mode == 0:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(0, -200, duration=0.25)
        elif mode == 1:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(0, 200, duration=0.25)
        elif mode == 2:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(950, -600, duration=0.45)

    def front(self, mode):
        offset_x = 20
        offset_y = -60

        if mode == 0:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(0, 200, duration=0.25)
        elif mode == 1:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(0, -200, duration=0.25)
        elif mode == 2:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(-800, -400, duration=0.45)

    def behind(self, mode):
        offset_x = 0
        offset_y = -250

        if mode == 0:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(-200, -15, duration=0.25)
        elif mode == 1:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(200, 10, duration=0.25)
        elif mode == 2:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(900, 400, duration=0.45)
    def x_axis(self, mode):
        offset_x = 120
        offset_y = -50

        if mode == 0:
            pyautogui.moveTo((self.x + offset_x, self.y + offset_y))
            pyautogui.dragRel(-15, 200, duration=0.25)
        elif mode == 1:
            pyautogui.moveTo((self.x + offset_x, self.y + offset_y))
            pyautogui.dragRel(-15, -200, duration=0.25)
        elif mode == 2:
            pyautogui.moveTo((self.x + offset_x, self.y + offset_y))
            pyautogui.dragRel(-1000, -600, duration=0.45)

    def y_axis(self, mode):
        offset_x = -120
        offset_y = -50

        if mode == 0:
            pyautogui.moveTo((self.x + offset_x, self.y + offset_y))
            pyautogui.dragRel(-15, -200, duration=0.25)
        elif mode == 1:
            pyautogui.moveTo((self.x + offset_x, self.y + offset_y))
            pyautogui.dragRel(-15, 200, duration=0.25)
        elif mode == 2:
            pyautogui.moveTo((self.x + offset_x, self.y + offset_y))
            pyautogui.dragRel(1000, -600, duration=0.45)

    def z_axis(self, mode):
        offset_x = -50
        offset_y = 100

        if mode == 0:
            pyautogui.moveTo((self.x + offset_x, self.y + offset_y))
            pyautogui.dragRel(-200, 0, duration=0.25)
        elif mode == 1:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(200, 0, duration=0.25)
        elif mode == 2:
            pyautogui.moveTo((self.x - offset_x, self.y + offset_y))
            pyautogui.dragRel(-1000, 200, duration=0.4)


class Screen:
    def __init__(self):
        self.cube_side = 600
        self.offset = 120
        self.size = tuple(pyautogui.size())
        self.x, self.y = self.size[0] / 2 - self.cube_side / 2, self.size[1] / 2 - self.cube_side / 2 + self.offset

    def screen_shot(self, index):
        img = pyautogui.screenshot(region=[self.x, self.y, self.cube_side, self.cube_side])
        img = cv.cvtColor(np.asarray(img), cv.COLOR_RGB2BGR)

        cv.imwrite("./Image/{}.jpg".format(index), img)


def get_image(mouse, screen):
    screen.screen_shot(0)
    mouse.up_turning()
    time.sleep(0.5)
    screen.screen_shot(1)
    mouse.down_turning()
    mouse.right_turning()
    time.sleep(0.5)
    screen.screen_shot(2)
    mouse.right_turning()
    time.sleep(0.5)
    screen.screen_shot(3)
    mouse.right_turning()
    mouse.right_turning()
