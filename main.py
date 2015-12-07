import tkinter as tk
from pyardrone import ARDrone
from pyardrone.navdata import NavData

# 如果飞机活动状态进行drone.close()会怎样？
# 到什么程度fly_mask被置1？
# 用循环来控制时间不是个好主意，因为这个时候无法响应别的事情，有没有什么好的替代方案？
# 输出一个指令后，这个指令的有效期是多久？直到接受下个命令嘛？还是只有一瞬间。


def takeoff(drone):
    print("开始起飞")
    while not drone.state.fly_mask:
        drone.takeoff()
    print("起飞完毕")


def land(drone):
    global halt
    halt = True
    print("开始降落")
    while drone.state.fly_mask:
        drone.land()
    print("降落完毕")
    drone.close()


def turn_right(drone, root, period, speed):
    drone.move(cw=speed)
    period -= 10
    if period >= 0 and not halt:
        root.after(10, lambda: turn_right(drone, root, period, speed))
    else:
        print("旋转终了")


def move(drone, root, period, speed):
    forw, left, cw = speed
    drone.move(forward=forw, left=left, cw=cw)
    period -= 10
    if period >= 0 and not halt:
        root.after(10, lambda: move(drone, root, period, speed))
    else:
        print("运动终了")

if __name__ == '__main__':
    d = ARDrone()
    d.navdata_ready.wait()
    print("Navdata prepared.")
    r = tk.Tk()
    r.minsize(200, 300)

    halt = False
    tk.Button(r, text="起飞", command=lambda: takeoff(d)).pack()
    tk.Button(r, text="降落", command=lambda: land(d)).pack()
    # tk.Button(r, text="开始输出Navdata", command=lambda: navdata(d)).pack()
    tk.Button(r, text="0.1倍速度 d顺时针旋转0.7s", command=lambda: turn_right(d, r, 700, 0.1)).pack()

    r.mainloop()
    d.close()
