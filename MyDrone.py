import tkinter as tk
from pyardrone import ARDrone, at
import time
from math import *

# 下次测试目标
#     free_move
#     move_seq
#
#     turn_degree
#     move_distance
#     smooth_move
#     arc_move

#     triangle
#     square2


# 如果freemove可用，将forward，right，up全部改写
# 之后，为freemove添加操控self.moving的部分，测试move_seq2
# 如果move_seq2可用，将所有的shape_fly改写为基于move_seq2

class MyDrone(ARDrone):
    """Extension for the default ardrone to add some characterized function"""
    def __init__(self):
        super().__init__()
        # self.navdata_ready.wait()

        self.root = tk.Tk()
        self.root.minsize(300, 300)

        self.halt = False
        self.moving = False
        self.memo = {}  # Do nothing but memorize something

        self.max_w = 10  # deg/s
        self.max_v = 10  # m/s

    def run(self):
        """Make everything begin"""
        print("Programme starts!")
        self.root.mainloop()
        # when windows is closed,close the drone.
        self.close()
        print("Programme ends!")

    # UI-related functions
    def add_btn(self, text, func):
        tk.Button(self.root, text=text, command=func).pack(padx=10, pady=5)

    def add_ent(self, des, var):
        tk.Label(self.root, text=des).pack()
        tk.Entry(self.root, textvariable=var).pack(padx=10, pady=5)

    # Taking off and landing
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

    # Moving
    def turn(self, w, ms_period=1000):
        """Turing clockwise if v > 0,counterclockwise if v < 0"""
        # I prefer to control it by angle instead of period.
        # Remain to be implemented
        assert(-1 <= w <= 1)

        self.move(cw=w)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.turn(w, ms_period))
        else:
            print("Turning ends.")

    def right(self, v, ms_period=1000):
        """Moving right if v >0,left if v < 0"""
        assert(-1 <= v <= 1)

        self.move(right=v)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.right(v, ms_period))
        else:
            print("Moving ends.")

    def forward(self, v=0.1, ms_period=1000):
        """Moving forward if v >0,backward if v < 0"""
        assert(-1 <= v <= 1)

        self.move(forward=v)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.forward(v, ms_period))
        else:
            print("Moving ends.")

    def climb(self, v, ms_period=1000):
        """Moving up if v >0,down if v < 0"""
        assert(-1 <= v <= 1)

        self.move(up=v)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.climb(v, ms_period))
        else:
            print("Moving ends.")

    def square(self):
        """Moving in the route of a square in the order of forward,right,backward,left"""
        print("Square moving start")
        # Here should leave enough time for UAV to counteract inertia automatically
        # No less than 3(remain to be examine) seconds
        self.root.after(200, lambda: self.forward(0.1, 1000))
        self.root.after(3200, lambda: self.right(0.1, 1000))
        self.root.after(6200, lambda: self.forward(-0.1, 1000))
        self.root.after(9200, lambda: self.right(-0.1, 1000))

    # functions not tested yet
    def free_move(self, vx, vy, vz, ms_period):
        """The base moving method of my drone"""

        super().move(forward=vy, right=vx, up=vz)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.free_move(vx, vy, vz, ms_period))
        else:
            print("Moving ends.")

    def move_seq(self, seq, interval=1000):
        """Do all moving in the seq which should be list of (func, period)"""
        sum_per = 0
        for func, peri in seq:
            # print("Move performed:", func)
            self.root.after(sum_per+200, func)
            sum_per += peri
            sum_per += interval

    def move_seq2(self, seq, interval=1000, index=0):
        """Do all moving in the seq which should be list of func"""
        if self.moving:
            self.root.after(interval, self.move_seq2(seq, interval, index))
        else:
            self.root.after(200, seq[index])
            self.root.after(interval, self.move_seq2(seq, interval, index+1))

    def smooth_move(self, vy, ms_period, first_in=True):
        """Moving smoothly,which means slow->fast>slow"""
        if first_in:
            print("Move start!")
            self.memo = {"total_moving_period": ms_period}

        def smooth_map(max_v, time_remain):
            """a map like '/\'"""
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

        self.move(forward=smooth_map(vy, ms_period))
        # print("%.5f" % smooth_map(v, ms_period))
        # print("%.5f" % smooth_map2(v, ms_period))
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.smooth_move(vy, ms_period, False))
        else:
            self.memo = {}
            print("Moving ends.")

    def square2(self):
        """Square moving which only moves forward and make use of turning"""
        print("Square moving start")
        ang_t = 1000
        for i in range(4):
            self.root.after(200+i*(3000+ang_t+300), lambda: self.forward())
            self.root.after(3200+i*(3000+ang_t+300), lambda: self.turn(0.2, ang_t))

    def square3(self):
        ang_t = 1000
        for i in range(4):
            self.root.after(200+i*(3000+ang_t+300), lambda: self.forward())
            self.root.after(3200+i*(3000+ang_t+300), lambda: self.turn_by_degree(90, sec_period=ang_t/1000))

    def square4(self):
        ang_t = 1000
        for i in range(4):
            self.root.after(200+i*(3000+ang_t+300), lambda: self.forward())
            self.root.after(3200+i*(3000+ang_t+300), lambda: self.turn_by_degree(90, sec_period=ang_t/1000))

    def triangle(self):
        print("Triangle moving start")
        self.root.after(200, lambda: self.free_move((0.1, 0.1*(3**0.5), 0), 500))
        self.root.after(3200, lambda: self.free_move((0.1, -0.1*(3**0.5), 0), 500))
        self.root.after(6200, lambda: self.free_move((-0.2, 0, 0), 500))

    def turn_by_degree(self, deg, w=None, sec_period=None):
        """You should control either by speed or by period"""
        if sec_period:
            w = deg / sec_period / self.max_w
            self.turn(w, sec_period)
        elif w:
            sec_period = deg/(self.max_w * abs(w))
            self.turn(w, sec_period)

    def move_by_distance(self, distance, v, sec_period=None):
        """Speed must be given,if period is given,recalculate speed without change its direction"""
        # You had better test the range of period first
        assert(len(v) == 3)
        vx, vy, vz = v
        if sec_period:
            v_magnitude = distance / sec_period / self.max_v
            vx /= v_magnitude
            vy /= v_magnitude
            vz /= v_magnitude
        else:
            v_magnitude = math.sqrt(vx**2 + vy**2 + vz**2)
            sec_period = distance / v_magnitude

        self.free_move(vx, vy, vz, ms_period=sec_period*1000)

    def arc_move(self, v, w, ms_period):
        """radius:max_v/max_w * v/w * 180/pi, center of circle:(r,0)"""
        self.forward(v, ms_period)
        self.turn(w, ms_period)

    def circle(self, radius, degree):
        r = radius
        v = 0.1
        w = self.max_v/self.max_w * v/r * 180/math.pi  # see docstring of arc_move
        t = degree/(w * self.max_w)
        if degree < 0:
            w *= -1
            t *= -1
        print(w, t)
        # self.arc_move(v, w, t)

    def number_eight(self):
        """Rely on move_seq"""
        r = 1
        a = 135
        self.turn_by_degree(-90, 0.1)
        self.circle(r, a)
        self.move_by_distance(2*r*tan(180-a), (0, 0.1, 0))
        self.circle(r, -a*2)
        self.move_by_distance(2*r*tan(180-a), (0, 0.1, 0))
        self.circle(r, a)
        self.turn_by_degree(90, 0.1)

    def show_navdata(self):
        self.send(at.CONFIG('general:navdata_demo', True))
        print(self.state)


if __name__ == '__main__':
    d = MyDrone()
    d.add_btn("起飞", d.takeoff)
    d.add_btn("降落", d.land)
    d.add_btn("前进(默认1s,下同）", lambda: d.forward(0.1))
    d.add_btn("后退", lambda: d.forward(0.1))
    d.add_btn("右移", lambda: d.right(-0.1))
    d.add_btn("左移", lambda: d.right(-0.1))
    d.add_btn("上升", lambda: d.climb(0.1))
    d.add_btn("下降", lambda: d.climb(-0.1))
    d.add_btn("顺时针旋转", lambda: d.turn(0.1))
    d.add_btn("逆时针旋转", lambda: d.turn(-0.1))
    d.add_btn("Square", lambda: d.square())

    vx = tk.StringVar()
    vy = tk.StringVar()
    vz = tk.StringVar()
    d.add_ent("vx", vx)
    d.add_ent("vy", vy)
    d.add_ent("vz", vz)
    d.add_btn("Free move", lambda: d.free_move(float(vx.get()), float(vy.get()), float(vz.get()), 1000))

    a = lambda: d.free_move(0.1, 0, 0, 1000)
    b = lambda: d.free_move(0, 0.1, 0, 1000)
    c = lambda: d.free_move(0, 0, 0.1, 1000)
    d.add_btn("Sequence move", lambda: d.move_seq2([a, b, c]))

    d.add_btn("Smooth move", lambda: d.smooth_move(0.3, 1000))
    d.run()
