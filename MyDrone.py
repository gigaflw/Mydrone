import tkinter as tk
from pyardrone import ARDrone
import time
from math import *


class MyDrone(ARDrone):
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
        self.root.protocol("WM_DELETE_WINDOW", self.window_close)

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

    def window_close(self):
        self.close()
        self.root.destroy()
        print("Programme ends!")

    # UI-related functions
# ------------------------------------------------------
    def add_btn(self, text: str, func):
        tk.Button(self.root, text=text, command=func).pack(padx=10, pady=5)

    def add_ent(self, description: str, var):
        tk.Label(self.root, text=description).pack()
        tk.Entry(self.root, textvariable=var).pack(padx=10, pady=5)

    # Taking off and landing
# ------------------------------------------------------
    def takeoff(self):
        # Notice when 'Done' is printed,UAV is still in the process of taking off and
        # doesn't hover steadily
        print("Taking off...")
        while not self.state.fly_mask:
            super().takeoff()
        while True:
            # Here should goes the check of steady hover
            break
        print("Done")
        self.halt = False

    def land(self):
        # Similarly,when 'Done' is printed,UAV is not yet on the ground
        self.moving = False
        self.halt = True
        print("Landing...")
        while self.state.fly_mask:
            super().land()
        print("Done")

    # Basic moving
# ------------------------------------------------------
    def free_move(self, vx, vy, vz, w, ms_period, first_in=True):
        """The base moving method of my drone"""
        if first_in:
            self.moving = True
            self.memo = {"total_period": ms_period}

        super().move(forward=vy, right=vx, up=vz, cw=w)

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
                time.sleep(1.5)  # this is a pause make the UAV stable before next move
            self.root.after(200, seq[index])
            index += 1
            if index < len(seq):
                self.root.after(interval, lambda: self.move_seq(seq, interval, index, no_pause))

    def _arc_move(self, v, rad: float, ms_period: int, start_angle=0.0, vertical=False, first_in=True):
        """
        A internal function serves to let UAV move in a route of a circle
        It's in x-z plane if vertical,otherwise in x-y plane
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
        if vertical:
            vx = v * cos(cur_ang) * ccw_flag
            vz = 4 * v * sin(cur_ang) * ccw_flag
            # Multiplied by 4 because the max_v is about 4 times the max_v in vertical
            super().move(up=vz, right=vx)
        else:
            vx = v * cos(cur_ang) * ccw_flag
            vy = v * sin(cur_ang) * ccw_flag
            super().move(forward=vy, right=vx)

        ms_period -= 50
        if ms_period >= 0 and not self.halt:
            self.root.after(50, lambda: self._arc_move(v, rad, ms_period, start_angle, vertical, False))
        else:
            self.moving = False
            self.memo = {}
            print("Done")
            time.sleep(1)  # This is to make the UAV stable

    def arc_move(self, v, r, deg, start_angle=0, vertical=False):
        """
        A much more user-friendly arc_move

        If vertical, it flies in x-z plane,otherwise in x-y plane
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
        self._arc_move(v, deg, ms_period, start_angle, vertical)

    def function_move(self, f_vx, f_vy, f_vz, ms_period, first_in=True):
        """
        This function largely resembles the basic free_move
        But it takes three function instead of three velocity!
        Functions should be in the unit of (v_percentage)/s
        Low accuracy!
        """
        if first_in:
            self.moving = True
            self.memo = {"total_period": ms_period}

        t = self.memo["total_period"] - ms_period
        t /= 1000  # convert from ms to sec
        vx = f_vx(t)
        vy = f_vy(t)
        vz = f_vz(t)
        print("t:%fs,vx:%.3f,vy:%.3f,vz:%.3f" % (t, vx, vy, vz))

        super().move(forward=vy, right=vx, up=vz)

        ms_period -= 50
        if ms_period >= 0 and not self.halt:
            self.root.after(50, lambda: self.function_move(f_vx, f_vy, f_vz, ms_period, False))
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

    def circle(self, v=0.1, r=0.6, vertical=False):
        """
        Draw a circle clockwise.
        For mysterious reason,the trace is not circle enough.
        """
        print("Circle moving starts")
        self.arc_move(v, r, -380, 0, vertical)

    def two_circle(self, v=0.1, r=0.6, vertical=False):
        """
        This function split circle move into two half-circle move
        which improve the stability.
        """
        print("Circle moving starts")
        a = lambda: self.arc_move(v, r, -180, 0, vertical)
        b = lambda: self.arc_move(v, r, -200, 180, vertical)
        self.move_seq([a, b], no_pause=True)

    def number_eight(self):
        v = 0.1
        r = 0.6

        m_list = list()
        m_list.append(lambda: self.arc_move(v, r, -180, 0))
        m_list.append(lambda: self.arc_move(v, r, 180, 0))
        m_list.append(lambda: self.arc_move(v, r, 180, 180))
        m_list.append(lambda: self.arc_move(v, r, -200, 180))
        self.move_seq(m_list, no_pause=True)

    def spiral_up(self):
        v = 0.1
        r = 0.7
        total_t = 2 * pi * r / (self.max_v * v)  # This result is in ms
        total_t *= 4

        def fx(t):
            w = v * self.max_v * 1000 / r
            return -v * cos(w * t)

        def fz(t):
            return 0.1 if t/(total_t/1000) <= 0.5 else -0.1

        def fy(t):
            w = v * self.max_v * 1000 / r
            return v * sin(w * t)

        self.function_move(fx, fy, fz, total_t)

    def star(self):
        t = 1200
        v = 0.1
        a = radians(36)
        moving_list = list()
        moving_list.append(lambda: self.free_move(v*cos(2*a), v*sin(2*a), 0, 0, t))
        moving_list.append(lambda: self.free_move(v*cos(2*a), -v*sin(2*a), 0, 0, t))
        moving_list.append(lambda: self.free_move(-v*cos(a), v*sin(a), 0, 0, t))
        moving_list.append(lambda: self.free_move(v, 0, 0, 0, t))
        moving_list.append(lambda: self.free_move(-v*cos(a), -v*sin(a), 0, 0, t))
        self.move_seq(moving_list)

    def four_leaves(self):
        v = 0.1
        r = 0.8
        m_list = list()
        m_list.append(lambda: self.arc_move(v, r, 180, 0))
        m_list.append(lambda: self.arc_move(v, r, 180, -90))
        m_list.append(lambda: self.arc_move(v, r, 180, 180))
        m_list.append(lambda: self.arc_move(v, r, 200, 90))
        self.move_seq(m_list)

if __name__ == '__main__':
    d = MyDrone()

    d.add_btn("起飞", d.takeoff)
    d.add_btn("降落", d.land)
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
    # d.add_btn("Circle", lambda: d.circle(vertical=True))
    d.add_btn("Two-part Circle in x-y", lambda: d.two_circle())
    # d.add_btn("Two-part Circle in x-z", lambda: d.two_circle(vertical=True))
    d.add_btn("Number-8 in x-y", lambda: d.number_eight())
    d.add_btn("Spiral Up", lambda: d.spiral_up())
    d.add_btn("Star", lambda: d.star())
    d.add_btn("Four_leaves", lambda: d.four_leaves())

    # arc_move with PID
    deg = tk.IntVar()
    d0 = tk.IntVar()
    r = tk.DoubleVar()
    d.add_ent("角度", deg)
    d.add_ent("初始角度", d0)
    d.add_ent("半径", r)
    deg.set(180)
    r.set(0.7)
    d.add_btn("arc_move", lambda: d.arc_move(0.1, r.get(), deg.get(), d0.get()))

    d.root.bind_all('<Up>', lambda e: d.move(forward=0.1))
    d.root.bind_all('<Down>', lambda e: d.move(backward=0.1))
    d.root.bind_all('<Left>', lambda e: d.move(left=0.1))
    d.root.bind_all('<Right>', lambda e: d.move(right=0.1))
    d.root.bind_all('<Z>', lambda e: d.move(up=0.1))
    d.root.bind_all('<X>', lambda e: d.move(down=0.1))
    d.root.bind_all('<A>', lambda e: d.move(ccw=0.1))
    d.root.bind_all('<S>', lambda e: d.move(cw=0.1))
    d.root.bind_all('<T>', lambda e: d.takeoff())
    d.root.bind_all('<L>', lambda e: d.land())

    d.run()
