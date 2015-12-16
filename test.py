import tkinter as tk
import time
from math import *


class MyDrone():
    """
    Extension for the default ardrone to add some characterized function
    Focus on fly in a specific route.

    Notes:
    * All speeds ('v' or 'w') denote the percentage of max speed,which ranges from -1 to 1
    * All time ('period') are in millisecond
    """
    def __init__(self):
        super().__init__()
        self.root = tk.Tk()
        self.root.minsize(300, 300)

        self.halt = False
        self.moving = False
        self.memo = {}  # Do nothing but memorize something

        # I can't find a record from the doc of ARDrone,these data are estimated
        self.max_v = 0.01  # m/ms
        self.max_w = 0.12  # deg/ms

    def run(self):
        """Make everything begin"""
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
        """The base moving method of my drone"""
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
        """
        Turning clockwise if v > 0,counterclockwise if v < 0
        """
        assert(-1 <= w <= 1)
        self.free_move(0, 0, 0, w, ms_period)

    def right(self, v, ms_period=1000):
        """Moving right if v >0,left if v < 0"""
        assert(-1 <= v <= 1)
        self.free_move(v, 0, 0, 0, ms_period)

    def forward(self, v=0.1, ms_period=1000):
        """Moving forward if v >0,backward if v < 0"""
        assert(-1 <= v <= 1)
        self.free_move(0, v, 0, 0, ms_period)

    def climb(self, v, ms_period=1000):
        """Moving up if v >0,down if v < 0"""
        assert(-1 <= v <= 1)
        self.free_move(0, 0, v, 0, ms_period)

    def move_seq(self, seq: list, interval=200, index=0, no_pause=False):
        """
        Handle a sequence of move command
        Every 'interval' milliseconds,this function will be called and check self.moving to see if UAV is moving,
        i.e. if the UAV is ready to do the next move,until all commands have been done.

        :param seq: The list of the function
        :param interval: The interval between two calls
        :param index: Should not be implemented by user,it is used as a pointer when function is recalled
        :param no_pause: Whether there is a pause between two moves
        """
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
        """
        A internal function serves to let UAV move in a route of a circle in x-z plane
        deg and start_angle are in radians

        Radius r = (self.max_v*v) * ms_period / deg

        It directly call the super method because we need to change v for every AT command
        0 degree points to the South,and counterclockwise is positive

        But this function is NOT user-friendly,you had better use arc_move below
        """
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
        """
        A much more user-friendly arc_move

        UAV is supposed at the place of 6 o'clock at default
        i.e.
        6 o'clock -> 0 degree
        3 o'clock -> 90 degree or -270
        9 o'clock -> -90 degree or 270
        12 o'clock -> 180 degree
        The sign of deg stands for counterclockwise(+)/clockwise(-) move

        Examples:
        To move UAV from 6 o'clock to 3 o'clock counterclockwise with 10% speed,1m radius
        drone.arc_move(0.1, 1, 90, 0)

        To move UAV from 6 o'clock to 9 o'clock clockwise with 10% speed,1m radius
        drone.arc_move(0.1, 1, -90, 0)

        To move UAV from 6 o'clock to 9 o'clock counterclockwise with 10% speed,1m radius
        drone.arc_move(0.1, 1, 270, 0)

        To move UAV from 9 o'clock to 6 o'clock counterclockwise with 10% speed,1m radius
        drone.arc_move(0.1, 1, 90, -90)

        To move UAV from 8 o'clock to 5 o'clock counterclockwise with 10% speed,1m radius
        drone.arc_move(0.1, 1, 90, -60)

        To move 2 rounds
        drone.arc_move(0.1, 1, 720, 0)
        """
        deg = pi * deg/180
        start_angle = pi * start_angle/180
        ms_period = abs(r * deg / (v * self.max_v))
        self._arc_move(v, deg, ms_period, start_angle)

    def function_move(self, f_vx, f_vy, f_vz, ms_period, first_in=True):
        """
        This function largely resembles the basic free_move
        But it takes three function instead of three velocity!
        Functions should be in the unit of (v_percentage)/s
        """
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
        """
        Moving in the route of a square in horizontal plane in the order of forward,right,backward,left

        :param v: speed percentage
        :param ms_period: time to cover one side
        """
        print("Square moving start")

        t = ms_period

        move_list = list()
        move_list.append(lambda: self.forward(v, t))
        move_list.append(lambda: self.right(v, t))
        move_list.append(lambda: self.forward(-v, t))
        move_list.append(lambda: self.right(-v, t))
        self.move_seq(move_list)

    def triangle(self, v=0.2, ms_period=800):
        """
        Moving in the route of a triangle in horizontal plane in the order of forward,backward,left

        :param v: Speed percentage
        :param ms_period: Time to cover one side
        """
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
        """
        Draw a circle counterclockwise.
        """
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
        """
        Draw a number '8' clockwise,
        in which the curve upward and downward is a 2/3 circle,
        which implies the sloping angle of the middle 'X' is 60 degree
        """
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

    # d.add_btn("前进(默认1s,下同）", lambda: d.forward(0.1))
    # d.add_btn("后退", lambda: d.forward(-0.1))
    # d.add_btn("右移", lambda: d.right(0.1))
    # d.add_btn("左移", lambda: d.right(-0.1))
    # d.add_btn("上升", lambda: d.climb(0.1))
    # d.add_btn("下降", lambda: d.climb(-0.1))
    # d.add_btn("顺时针旋转", lambda: d.turn(0.1))
    # d.add_btn("逆时针旋转", lambda: d.turn(-0.1))

    d.add_btn("Square", lambda: d.square())
    d.add_btn("Triangle", lambda: d.triangle())
    d.add_btn("Circle", lambda: d.circle())
    d.add_btn("Circle", lambda: d.function_circle())
    d.add_btn("8", lambda: d.number_eight())
    d.add_btn("8", lambda: d.function_eight())

    d.run()
