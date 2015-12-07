import tkinter as tk
from pyardrone import ARDrone


class MyDrone(ARDrone):
    def __init__(self):
        super().__init__()
        self.navdata_ready.wait()
        print("Navdata prepared.")

        self.view = tk.Tk()
        self.view.minsize(300, 300)

        self.halt = False

    def takeoff(self):
        print("开始起飞")
        super().takeoff()
        print("起飞完毕")

    def land(self):
        self.halt = True
        print("开始降落")
        while self.state.fly_mask:
            super().land()
        print("降落完毕")
        self.close()

    def turn_right(self, period, speed):
        print("继续旋转%dms" % period)
        self.move(cw=speed)
        period -= 10
        if period >= 0 and not self.halt:
            self.view.after(10, lambda: self.turn_right(period, speed))
        else:
            print("旋转终了")

    def my_move(self, period, speed):
        print("运动剩余%dms" % period)
        forw, left, cw = speed
        self.move(forward=forw, left=left, cw=cw)
        period -= 10
        if period >= 0 and not self.halt:
            self.view.after(10, lambda: self.my_move(period, speed))
        else:
            print("运动终了")

    def run(self):
        print("启动")
        self.view.mainloop()
        self.close()
        print("结束")

    def add_btn(self, text, func):
        tk.Button(self.view, text=text, command=func).pack()

if __name__ == '__main__':
    d = MyDrone()
    d.add_btn("起飞", d.takeoff)
    d.add_btn("降落", d.land)
    d.add_btn("0.1倍速度 d顺时针旋转1s", lambda: d.turn_right(0.1, 1000))
    d.run()
