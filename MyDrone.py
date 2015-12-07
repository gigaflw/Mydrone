import tkinter as tk
from pyardrone import ARDrone
import time


class MyDrone(ARDrone):
    """Extension for the default ardrone to add some characterized function"""
    def __init__(self):
        super().__init__()
        self.navdata_ready.wait()

        self.root = tk.Tk()
        self.root.minsize(300, 300)

        self.halt = False

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

    def x_move(self, v, ms_period=1000):
        """Moving right if v >0,left if v < 0"""
        self.move(right=v)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.x_move(v, ms_period))
        else:
            print("Moving ends.")

    def y_move(self, v=, ms_period=1000):
        """Moving forward if v >0,backward if v < 0"""
        self.move(forward=v)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.x_move(v, ms_period))
        else:
            print("Moving ends.")

    def z_move(self, v, ms_period=1000):
        """Moving up if v >0,down if v < 0"""
        self.move(up=v)
        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.x_move(v, ms_period))
        else:
            print("Moving ends.")

    def square(self):
        """Moving in the route of a square in the order of forward,right,backward,left"""
        print("Square moving start")
        # Here should leave enough time for UAV to counteract inertia automatically
        # No less than 3(remain to be examine) seconds
        self.root.after(200, lambda: self.y_move(0.1, 1000))
        self.root.after(3200, lambda: self.x_move(0.1, 1000))
        self.root.after(6200, lambda: self.y_move(-0.1, 1000))
        self.root.after(9200, lambda: self.x_move(-0.1, 1000))


if __name__ == '__main__':
    d = MyDrone()
    d.add_btn("起飞", d.takeoff)
    d.add_btn("降落", d.land)
    d.add_btn("前进", d.y_move(0.1))
    d.add_btn("后退", d.y_move(0.1))
    d.add_btn("右移", d.x_move(-0.1))
    d.add_btn("左移", d.x_move(-0.1))
    d.add_btn("上升", d.z_move(0.1))
    d.add_btn("下降", d.z_move(-0.1))
    d.add_btn("顺时针旋转", d.turn(0.1))
    d.add_btn("逆时针旋转", d.turn(-0.1))
    d.add_btn("Square", lambda: d.square())
    d.run()
