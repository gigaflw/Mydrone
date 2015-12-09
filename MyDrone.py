import tkinter as tk
from pyardrone import ARDrone, at
import time
from math import *

# 下次测试：
# 方形运动的神秘微动
# 图形运动的速度被调高了
# arc_move2
# nav_data
#  e.g. drone.navdata.demo.vx

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
        self.navdata_ready.wait()

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
        self.close()
        print("Programme ends!")

    # UI-related functions
# ------------------------------------------------------
    def add_btn(self, text, func):
        tk.Button(self.root, text=text, command=func).pack(padx=10, pady=5)

    def add_ent(self, description, var):
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
        print("Landing...")
        while self.state.fly_mask:
            super().land()
        print("Done")
        self.halt = True

    # Basic moving
# ------------------------------------------------------
    def free_move(self, vx, vy, vz, w, ms_period):
        """The base moving method of my drone"""
        self.moving = True
        super().move(forward=vy, right=vx, up=vz, cw=w)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.free_move(vx, vy, vz, w, ms_period))
        else:
            self.moving = False
            print("Done")
            time.sleep(1.5)  # This is to make the UAV stable

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

    def move_seq(self, seq, interval=500, index=0):
        """
        Handle a sequence of move command
        Every 'interval' milliseconds,this function will be called and check self.moving to see if UAV is moving,
        i.e. if the UAV is ready to do the next move,until all commands have been done.

        :param seq: The list of the function
        :param interval: The interval between two calls
        :param index: Should not be implemented by user,it is used as a pointer when function is recalled
        """
        if self.moving:
            self.root.after(interval, lambda: self.move_seq(seq, interval, index))
        else:
            self.root.after(200, seq[index])
            index += 1
            if index < len(seq):
                self.root.after(interval, lambda: self.move_seq(seq, interval, index))

    def arc_move(self, v, deg, ms_period, first_in=True):
        """
        This function let UAV move in a route of circle counterclockwise
        Radius r = v * ms_period / (deg/180*pi)
        It directly call the super method because we need to change v for every AT command
        :param v:speed percentage
        :param deg: The center angle
        :param ms_period: Total time to cover
        """
        if first_in:
            print("Circle starts")
            self.memo = {"total_moving_period": ms_period}

        self.moving = True
        a = 2 * pi * deg/360 * (1 - ms_period / self.memo["total_moving_period"])
        vx = v * cos(a)
        vy = v * sin(a)
        super().move(right=vx, forward=vy)

        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.arc_move(v, deg, ms_period, False))
        else:
            self.moving = False
            print("Done")
            time.sleep(1.5)  # This is to make the UAV stable

    def arc_move2(self, v, deg, r):
        """
        A more user-friendly arc_move
        :param v:speed percentage
        :param deg: The center angle
        """
        ms_period = r * (deg/180*pi) / (v * self.max_v)
        self.arc_move(v, deg, ms_period)

    def turn_by_degree(self, deg, w=None, ms_period=None):
        """
        You should control either by speed or by period
        This function is NOT STABLE,UAV will mysteriously drift around after the move

        :param deg: The degree you want to turn,negative value means counterclockwise
        :param w: Angle speed percentage
        :param ms_period: The time you'd like to use to complete the move,only works when 'w' is not given
        """
        if w:
            ms_period = deg/(self.max_w * w)
        elif ms_period:
            w = deg / ms_period / self.max_w
        else:
            w = 0.1
            ms_period = deg/(self.max_w * w)

        self.turn(w, ms_period)

    def move_by_distance(self, distance, v, ms_period=None):
        """Speed must be given,if period is given,recalculate speed without change its direction"""
        # You had better test the range of period first
        assert(len(v) == 3)
        vx, vy, vz = v
        if ms_period:
            v_magnitude = distance / ms_period / self.max_v
            vx /= v_magnitude
            vy /= v_magnitude
            vz /= v_magnitude
        else:
            v_magnitude = sqrt(vx**2 + vy**2 + vz**2)
            ms_period = distance / (self.max_v * v_magnitude)

        print("distance:%dm,v:(%.2f,%.2f,%.2f)m/s,period:%.2fs" % (distance, vx, vy, vz, ms_period))
        self.free_move(vx, vy, vz, 0, ms_period)

    def smooth_move(self, vy, ms_period, first_in=True):
        """
        Moving smoothly,which means slow->fast>slow
        Only forward or backward available yet

        Difference between normal and 'smooth' move is not obvious
        And when speed comes down,UAV will tilt to slow down automatically,which make it not smooth at all
        So it is not recommended before improved
        """
        if first_in:
            print("Move start!")
            self.memo = {"total_moving_period": ms_period}

        def smooth_map(max_v, time_remain):
            """
            It returns the speed UAV should use according to the ratio of time_remain
            a map like '/\
            '"""
            # add 0.01 to prevent zero speed
            t = self.memo["total_moving_period"]
            k = 2*max_v/t
            return max_v-abs(k*(time_remain-t/2))+0.01

        def smooth_map2(max_v, time_remain):
            """a map like '⋂'"""
            tr = time_remain
            t = self.memo["total_moving_period"]
            a = -4*max_v/t**2
            return a*tr*(tr-t)+0.01

        def smooth_map3(max_v, time_remain):
            """a map using sin"""
            tr = time_remain
            t = self.memo["total_moving_period"]

            return max_v * sin(pi/t*tr)

        self.move(forward=smooth_map(vy, ms_period))
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.smooth_move(vy, ms_period, False))
        else:
            self.memo = {}
            print("Moving ends.")

    # Shape moving
# ------------------------------------------------------
    def square(self, v=0.3, ms_period=500):
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

    def triangle(self, v=0.3, ms_period=500):
        """
        Moving in the route of a triangle in horizontal plane in the order of forward,backward,left

        :param v: Speed percentage
        :param ms_period: Time to cover one side
        """
        print("Triangle moving start")
        t = ms_period
        a = pi / 3
        moving_list = list()
        moving_list.append(lambda: self.free_move(v*cos(a), v*sin(a), 0, 0, t))
        moving_list.append(lambda: self.free_move(v*cos(a), -v*sin(a), 0, 0, t))
        moving_list.append(lambda: self.free_move(-v, 0, 0, 0, t))
        self.move_seq(moving_list)

    def circle(self, v=0.2, ms_period=10000):
        """
        Draw a circle counterclockwise.
        :param v: Speed percentage
        :param ms_period: Total time
        """
        print("Circle moving start")
        self.arc_move(v, 360, ms_period)

    def number_eight(self):
        """
        Draw a number '8' clockwise,
        in which the curve upward and downward is a 2/3 circle,
        which implies the sloping angle of the middle 'X' is 60 degree
        """
        v = 0.1
        a = 120  # The angle of curve
        t = 2000
        b = 180 - a  # The angle of slope
        r = v * t / (a/180*pi)  # The radius,see docstring of arc_move

        moving_list = list()
        moving_list.append(lambda: self.arc_move(v, -a, t))
        moving_list.append(lambda: self.move_by_distance(2*r*tan(b), (v*cos(b), v*sin(b), 0)))
        moving_list.append(lambda: self.arc_move(v, 2*a, t))
        moving_list.append(lambda: self.move_by_distance(2*r*tan(b), (-v*cos(b), -v*sin(b), 0)))
        moving_list.append(lambda: self.arc_move(v, -a, t))

    def to_center_circle(self, v, deg, ms_period, first_in=True):
        """
        Remain to be tested
        """
        if first_in:
            print("To-point Circle starts")
            self.memo = {"total_moving_period": ms_period}

        self.moving = True
        w = 2 * pi / (self.max_w * self.memo["total_moving_period"])
        if w > 1:
            print("w is too high!")
            w = 1

        super().move(right=v, ccw=w)

        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.to_center_circle(v, deg, ms_period, False))
        else:
            self.moving = False
            print("Done")
            time.sleep(1.5)  # This is to make the UAV stable

    def spiral_up(self, v, max_r, first_in=True):
        """
        Remain to be tested
        """
        pass

    #
    # def show_navdata(self):
    #     self.send(at.CONFIG('general:navdata_demo', True))
    #     print(self.state)


if __name__ == '__main__':
    d = MyDrone()
    d.add_btn("起飞", d.takeoff)
    d.add_btn("降落", d.land)
    d.add_btn("前进(默认1s,下同）", lambda: d.forward(0.1))
    d.add_btn("后退", lambda: d.forward(0.1))
    d.add_btn("右移", lambda: d.right(0.2))
    d.add_btn("左移", lambda: d.right(-0.2))
    d.add_btn("上升", lambda: d.climb(0.1))
    d.add_btn("下降", lambda: d.climb(-0.1))
    d.add_btn("顺时针旋转", lambda: d.turn(0.1))
    d.add_btn("逆时针旋转", lambda: d.turn(-0.1))
    d.run()
