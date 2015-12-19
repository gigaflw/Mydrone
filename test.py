"""
This file serves for test when hardware is unavailable.
It is a simplified copy of main file except for
whenever a 'move' command is to be sent,
paras will be printed instead of let the UAV move.
"""

import tkinter as tk
import time
from math import *


class MyDrone():
    def __init__(self):
        super().__init__()
        self.root = tk.Tk()
        self.root.minsize(300, 300)

        self.halt = False
        self.moving = False
        self.memo = {}  # Do nothing but memorize something

        self.max_v = 0.01  # m/ms
        self.max_w = 0.12  # deg/ms

    def run(self):
        print("Programme starts!")
        self.root.mainloop()
        # when windows is closed,close the drone.
        print("Programme ends!")

    # UI-related functions
# ------------------------------------------------------
    def add_btn(self, text: str, func):
        tk.Button(self.root, text=text, command=func).pack(padx=10, pady=5)

    def add_ent(self, description: str, var):
        tk.Label(self.root, text=description).pack()
        tk.Entry(self.root, textvariable=var).pack(padx=10, pady=5)

    # Basic moving
# ------------------------------------------------------
    def free_move(self, vx, vy, vz, w, ms_period, first_in=True):
        if first_in:
            self.moving = True
            self.memo = {"total_period": ms_period}

        print("t:%dms\tvx:%.3f\tvy:%.3f\tvz:%.3f" % (self.memo["total_period"]-ms_period, vx, vy, vz))

        ms_period -= 50
        if ms_period >= 0 and not self.halt:
            self.root.after(50, lambda: self.free_move(vx, vy, vz, w, ms_period, False))
        else:
            self.moving = False
            self.memo = {}
            print("Done")
            # time.sleep(1.5)  # This is to make the UAV stable

    def turn(self, w, ms_period=1000):
        assert(-1 <= w <= 1)
        self.free_move(0, 0, 0, w, ms_period)

    def right(self, v, ms_period=1000):
        assert(-1 <= v <= 1)
        self.free_move(v, 0, 0, 0, ms_period)

    def forward(self, v=0.1, ms_period=1000):
        assert(-1 <= v <= 1)
        self.free_move(0, v, 0, 0, ms_period)

    def climb(self, v, ms_period=1000):
        assert(-1 <= v <= 1)
        self.free_move(0, 0, v, 0, ms_period)

    def move_seq(self, seq: list, interval=200, index=0, no_pause=False):
        if self.moving:
            self.root.after(interval, lambda: self.move_seq(seq, interval, index))
        else:
            if not no_pause:
                time.sleep(1)  # this is a pause make the UAV stable before next move
            self.root.after(200, seq[index])
            index += 1
            if index < len(seq):
                self.root.after(interval, lambda: self.move_seq(seq, interval, index, no_pause))

    def _arc_move(self, v, rad: float, ms_period: int, start_angle=0.0, first_in=True):
        if first_in:
            print("Circle starts")
            self.memo = {"total_period": ms_period}
            print("Will take %.3fms" % ms_period)

        self.moving = True

        cur_ang = rad * (1 - ms_period / self.memo["total_period"])
        cur_ang += start_angle

        ccw_flag = -1 if rad < 0 else 1
        vx = v * cos(cur_ang) * ccw_flag
        vz = 4 * v * sin(cur_ang) * ccw_flag
        # Multiplied by 4 because the max_v is about 4 times the max_v in vertical

        print("t:%dms\tvx:%.3f\tvz:%.3f" % (self.memo["total_period"]-ms_period, vx, vz))

        ms_period -= 100
        if ms_period >= 0 and not self.halt:
            self.root.after(100, lambda: self._arc_move(v, rad, ms_period, start_angle, False))
        else:
            self.moving = False
            self.memo = {}
            print("Done")
            time.sleep(1)  # This is to make the UAV stable

    def arc_move(self, v, r, deg, start_angle=0):
        deg = pi * deg/180
        start_angle = pi * start_angle/180
        ms_period = abs(r * deg / (v * self.max_v))
        self._arc_move(v, deg, ms_period, start_angle)

    def function_move(self, f_vx, f_vy, f_vz, ms_period, first_in=True):
        if first_in:
            self.moving = True
            self.memo = {"total_period": ms_period}

        t = self.memo["total_period"] - ms_period
        t /= 1000  # convert from ms to sec
        vx = f_vx(t)
        vy = f_vy(t)
        vz = f_vz(t)

        print("t:%dms\tvx:%.3f\tvy:%.3d\tvz:%.3f" % (self.memo["total_period"]-ms_period, vx, vy, vz))

        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.function_move(f_vx, f_vy, f_vz, ms_period, False))
        else:
            self.moving = False
            self.memo = {}
            print("Done")
            time.sleep(1.5)  # This is to make the UAV stable

    # Shape moving
# ------------------------------------------------------
    def square(self, v=0.2, ms_period=600):
        print("Square moving start")

        t = ms_period

        move_list = list()
        move_list.append(lambda: self.forward(v, t))
        move_list.append(lambda: self.right(v, t))
        move_list.append(lambda: self.forward(-v, t))
        move_list.append(lambda: self.right(-v, t))
        self.move_seq(move_list)

    def triangle(self, v=0.2, ms_period=800):
        print("Triangle moving start")
        t = ms_period
        a1 = radians(60)
        moving_list = list()
        moving_list.append(lambda: self.free_move(v*cos(a1), v*sin(a1), 0, 0, t))
        moving_list.append(lambda: self.free_move(v*cos(a1), -v*sin(a1), 0, 0, t))
        # This is because my UAV has something wrong with flying backward right
        moving_list.append(lambda: self.free_move(-v, 0, 0, 0, t))
        self.move_seq(moving_list)

    def circle(self, v=0.1, r=1):
        print("Circle moving starts")
        self.arc_move(v, r, -180, 180)

    def two_circle(self, v=0.1, r=1):
        print("Circle moving starts")
        m_list = list()
        m_list.append(lambda: self.arc_move(v, r, -180, 0))
        m_list.append(lambda: self.arc_move(v, r, -180, 180))
        self.move_seq(m_list, no_pause=True)

    def function_circle(self):
        r = 1
        v = 0.1

        def fx(t):
            w = v * self.max_v * 1000 / r
            return - v * cos(w * t)

        def fy(t):
            return 0

        def fz(t):
            w = v * self.max_v * 1000 / r
            return v * sin(w * t)

        t = 2 * pi * r / (self.max_v * v)  # This result is in ms
        self.function_move(fx, fy, fz, t)

    def number_eight(self):
        v = 0.1
        r = 0.6

        m_list = list()
        m_list.append(lambda: self.arc_move(v, r, -180, 0))
        m_list.append(lambda: self.arc_move(v, r, 180, 0))
        m_list.append(lambda: self.arc_move(v, r, 180, 180))
        m_list.append(lambda: self.arc_move(v, r, -180, 180))
        self.move_seq(m_list, no_pause=True)

    def function_eight(self):
        v = 0.1
        r = 0.6
        total_t = 2 * pi * r / (self.max_v * v)  # This result is in ms
        total_t *= 2  # number '8' has 2 circle

        def fx(t):
            w = v * self.max_v * 1000 / r
            return -v * cos(w * t)

        def fy(t):
            return 0

        def fz(t):
            w = v * self.max_v * 1000 / r
            ret = v * sin(w * t)
            if total_t/4 <= t <= total_t*3/4:
                ret *= -1
            return ret

        self.function_move(fx, fy, fz, total_t)

if __name__ == '__main__':
    d = MyDrone()

    d.add_btn("Square", lambda: d.square())
    d.add_btn("Triangle", lambda: d.triangle())
    d.add_btn("Circle", lambda: d.circle())
    d.add_btn("Circle", lambda: d.function_circle())
    d.add_btn("8", lambda: d.number_eight())
    d.add_btn("8", lambda: d.function_eight())

    d.run()
