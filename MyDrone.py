import tkinter as tk
from pyardrone import ARDrone
import time
import math


class MyDrone(ARDrone):
    """Extension for the default ardrone to add some characterized function"""
    def __init__(self):
        super().__init__()
        # self.navdata_ready.wait()

        self.root = tk.Tk()
        self.root.minsize(300, 300)

        self.halt = False
        self.memo = {}  # Do nothing but memorize something

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
    def turn(self, v, ms_period=1000):
        """Turing clockwise if v > 0,counterclockwise if v<0"""
        # I prefer to control it by angle instead of period.
        # Remain to be implemented
        self.move(cw=v)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.turn(v, ms_period))
        else:
            print("Turning ends.")

    def right(self, v, ms_period=1000):
        """Moving right if v >0,left if v < 0"""
        self.move(right=v)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.right(v, ms_period))
        else:
            print("Moving ends.")

    def forward(self, v=0.1, ms_period=1000):
        """Moving forward if v >0,backward if v < 0"""
        self.move(forward=v)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.forward(v, ms_period))
        else:
            print("Moving ends.")

    def climb(self, v, ms_period=1000):
        """Moving up if v >0,down if v < 0"""
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
    def free_move(self, v, ms_period):
        """Nearly the origin move method"""
        try:
            vx, vy, vz = v
        except ValueError:
            print("Invalid input")
            return

        super().move(forward=vy, right=vx, up=vz)
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.free_move(v, ms_period))
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

    def smooth_move(self, v, ms_period, first_in=True):
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

        self.move(forward=smooth_map(v, ms_period))
        # print("%.5f" % smooth_map(v, ms_period))
        # print("%.5f" % smooth_map2(v, ms_period))
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.smooth_move(v, ms_period, False))
        else:
            print("Moving ends.")

    def square2(self):
        """Square moving which only moves forward and make use of turning"""
        print("Square moving start")
        ang_t = 1000
        for i in range(4):
            self.root.after(200+i*(3000+ang_t+300), lambda: self.forward())
            self.root.after(3200+i*(3000+ang_t+300), lambda: self.turn(0.2, ang_t))

    def triangle(self):
        """Moving in the route of a square in the order of forward,right,backward,left"""
        print("Triangle moving start")
        self.root.after(200, lambda: self.free_move((0.1, 0.1*(3**0.5), 0), 500))
        self.root.after(3200, lambda: self.free_move((0.1, -0.1*(3**0.5), 0), 500))
        self.root.after(6200, lambda: self.free_move((-0.2, 0, 0), 500))

    def turn_degree(self, deg, v=0.1):
        max_v = 10  # degree pre second
        peri = 360/(max_v*v)
        self.turn(v, peri)


if __name__ == '__main__':
    d = MyDrone()
    d.add_btn("起飞", d.takeoff)
    d.add_btn("降落", d.land)
    d.add_btn("前进", lambda: d.forward(0.1))
    d.add_btn("后退", lambda: d.forward(0.1))
    d.add_btn("右移", lambda: d.right(-0.1))
    d.add_btn("左移", lambda: d.right(-0.1))
    d.add_btn("上升", lambda: d.climb(0.1))
    d.add_btn("下降", lambda: d.climb(-0.1))
    d.add_btn("顺时针旋转", lambda: d.turn(0.1))
    d.add_btn("逆时针旋转", lambda: d.turn(-0.1))
    d.add_btn("Square", lambda: d.square())

    a = lambda: d.turn(0.1, 1000)
    b = lambda: d.turn(-0.2, 500)
    c = lambda: d.forward(0.1, 500)
    d.add_btn("Move seq", lambda: d.move_seq([(a, 1000), (b, 500), (c, 500)]))

    d.add_btn("Smooth move", lambda: d.smooth_move(0.3, 1000))
    d.run()
