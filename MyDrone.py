import tkinter as tk
from pyardrone import ARDrone, at
import time
from math import *

from PIDController import PIDController


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
        # self.navdata_ready.wait()
        # print("Navdata prepared.")
        self.root = tk.Tk()
        self.root.minsize(300, 300)

        self.halt = False
        self.moving = False
        self.memo = {}  # Do nothing but memorize something

        # I can't find a record from the doc of ARDrone,these data are estimated
        self.max_v = 0.01  # m/ms
        self.max_w = 0.12  # deg/ms

        # PID controller,
        # be cleared in _arc_move and move_seq,
        # be used in _arc_move and free_move
        self.vx_ctrl = PIDController()
        self.vy_ctrl = PIDController()
        self.vz_ctrl = PIDController()

        # enable navdata
        self.send(at.CONFIG('general:navdata_demo', True))

    def run(self):
        """Make everything begin"""
        print("Programme starts!")
        self.root.mainloop()
        # when windows is closed,close the drone.
        self.close()
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
        print("Landing...")
        while self.state.fly_mask:
            super().land()
        print("Done")
        self.halt = True

    # Basic moving
# ------------------------------------------------------
    def free_move(self, vx, vy, vz, w, ms_period, first_in=True):
        """The base moving method of my drone"""
        if first_in:
            self.moving = True
            self.clear_controller()
            self.memo = {"total_period": ms_period}

        # Calculate offset using PDI controller
        dx, dy, dz = self.speed_offset(vx, vy, vz)

        super().move(forward=vy+dy, right=vx+dx, up=vz+dz, cw=w)

        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.free_move(vx, vy, vz, w, ms_period, False))
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

    def move_seq(self, seq: list, interval=500, index=0):
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
            self.vx_ctrl.clear()
            self.vy_ctrl.clear()
            time.sleep(2)  # this is a pause make the UAV stable before next move
            self.root.after(200, seq[index])
            index += 1
            if index < len(seq):
                self.root.after(interval, lambda: self.move_seq(seq, interval, index))

    def _arc_move(self, v, deg: float, ms_period: int, start_angle=0.0, first_in=True):
        """
        A internal function serves to let UAV move in a route of a circle.
        deg and start_angle are in radians

        Radius r = (self.max_v*v) * ms_period / deg

        It directly call the super method because we need to change v for every AT command
        0 degree points to the South,and counterclockwise is positive

        But this function is NOT user-friendly,you had better use arc_move below
        """
        if first_in:
            self.clear_controller()
            print("Circle starts")
            self.memo = {"total_period": ms_period}

        self.moving = True

        cur_ang = deg * (1 - ms_period / self.memo["total_period"])
        cur_ang += start_angle

        ccw_flag = -1 if deg < 0 else 1
        vx = v * cos(cur_ang) * ccw_flag
        vy = v * sin(cur_ang) * ccw_flag

        # Calculate offset using PDI controller
        dx, dy, _ = self.speed_offset(vx, vy, 0)

        # super().move(forward=vy+dy, right=vx+dx)
        print("moving: %.2f %.2f" % (vx+dx, vy+dy))

        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self._arc_move(v, deg, ms_period, start_angle, False))
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
            self.clear_controller()
            self.memo = {"total_period": ms_period}

        t = self.memo["total_period"] - ms_period
        t /= 1000  # convert from ms to sec
        vx = f_vx(t)
        vy = f_vy(t)
        vz = f_vz(t)

        # Calculate offset using PDI controller
        dx, dy, dz = self.speed_offset(vx, vy, vz)
        # super().move(forward=vy+dy, right=vx+dx, up=vz+dz)
        print("moving: %.2f %.2f %.2f" % (vx+dx, vy+dy, vz+dz))

        ms_period -= 10
        if ms_period >= 0 and not self.halt:
            self.root.after(10, lambda: self.function_move(f_vx, f_vy, f_vz, ms_period, False))
        else:
            self.moving = False
            self.memo = {}
            print("Done")
            time.sleep(1.5)  # This is to make the UAV stable

    # NOT stable functions
    # def turn_by_degree(self, deg, w=None, ms_period=None):
    #     """
    #     You should control either by speed or by period
    #     This function is NOT STABLE,UAV will mysteriously drift around after the move
    #
    #     :param deg: The degree you want to turn,negative value means counterclockwise
    #     :param w: Angle speed percentage
    #     :param ms_period: The time you'd like to use to complete the move,only works when 'w' is not given
    #     """
    #     if w:
    #         ms_period = deg/(self.max_w * w)
    #     elif ms_period:
    #         w = deg / ms_period / self.max_w
    #     else:
    #         w = 0.1
    #         ms_period = deg/(self.max_w * w)
    #
    #     self.turn(w, ms_period)
    #
    # def move_by_distance(self, distance, v, ms_period=None):
    #     """Speed must be given,if period is given,recalculate speed without change its direction"""
    #     # You had better test the range of period first
    #     assert(len(v) == 3)
    #     vx, vy, vz = v
    #     if ms_period:
    #         v_magnitude = distance / ms_period / self.max_v
    #         vx /= v_magnitude
    #         vy /= v_magnitude
    #         vz /= v_magnitude
    #     else:
    #         v_magnitude = sqrt(vx**2 + vy**2 + vz**2)
    #         ms_period = distance / (self.max_v * v_magnitude)
    #
    #     print("distance:%dm,v:(%.2f,%.2f,%.2f)m/s,period:%.2fs" % (distance, vx, vy, vz, ms_period))
    #     self.free_move(vx, vy, vz, 0, ms_period)
    #
    # def smooth_move(self, vy, ms_period, first_in=True):
    #     """
    #     Moving smoothly,which means slow->fast>slow
    #     Only forward or backward available yet
    #
    #     Difference between normal and 'smooth' move is not obvious
    #     And when speed comes down,UAV will tilt to slow down automatically,which make it not smooth at all
    #     So it is not recommended before improved
    #     """
    #     if first_in:
    #         print("Move start!")
    #         self.memo = {"total_moving_period": ms_period}
    #
    #     def smooth_map(max_v, time_remain):
    #         """
    #         It returns the speed UAV should use according to the ratio of time_remain
    #         a map like '/\
    #         '"""
    #         # add 0.01 to prevent zero speed
    #         t = self.memo["total_moving_period"]
    #         k = 2*max_v/t
    #         return max_v-abs(k*(time_remain-t/2))+0.01
    #
    #     def smooth_map2(max_v, time_remain):
    #         """a map like '⋂'"""
    #         tr = time_remain
    #         t = self.memo["total_moving_period"]
    #         a = -4*max_v/t**2
    #         return a*tr*(tr-t)+0.01
    #
    #     def smooth_map3(max_v, time_remain):
    #         """a map using sin"""
    #         tr = time_remain
    #         t = self.memo["total_moving_period"]
    #
    #         return max_v * sin(pi/t*tr)
    #
    #     self.move(forward=smooth_map3(vy, ms_period))
    #     ms_period -= 10
    #     if ms_period >= 0 and not self.halt:
    #         self.root.after(10, lambda: self.smooth_move(vy, ms_period, False))
    #     else:
    #         self.memo = {}
    #         print("Moving ends.")

    # Shape moving
# ------------------------------------------------------
    def square(self, v=0.2, ms_period=400):
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

    def triangle(self, v=0.2, ms_period=400):
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

    def circle(self, v=0.1, r=1):
        """
        Draw a circle counterclockwise.
        """
        print("Circle moving start")
        deg = 360
        # ms_period = r * (deg/180*pi) / (self.max_v * v)
        m_list = list()
        m_list.append(lambda: self.arc_move(v, r, 90, 0))
        m_list.append(lambda: self.arc_move(v, r, 90, 90))
        m_list.append(lambda: self.arc_move(v, r, 90, 180))
        m_list.append(lambda: self.arc_move(v, r, 90, 270))
        self.move_seq(m_list)

    def number_eight(self):
        """
        Draw a number '8' clockwise,
        in which the curve upward and downward is a 2/3 circle,
        which implies the sloping angle of the middle 'X' is 60 degree
        """
        v = 0.1
        a = 180  # The angle of curve
        # t = 1000
        b = 60 # The angle of slope
        a = radians(a)
        b = radians(b)
        # r = (self.max_v*v) * t / (a/180*pi)  # The radius,see docstring of arc_move
        r = 1

        forward_len = 2*r/cos(b)
        forward_len /= 3  # crazy modify

        moving_list = list()
        moving_list.append(lambda: self.free_move(v*cos(b), v*sin(b), 0, 0, 2000))
        moving_list.append(lambda: self.arc_move(v, r, 180, 90))
        moving_list.append(lambda: self.free_move(v*cos(b), -v*sin(b), 0, 0, 2000))
        moving_list.append(lambda: self.arc_move(v, r, -180, 90))
        self.move_seq(moving_list)

    # def to_center_circle(self, v, deg, ms_period, first_in=True):
    #     """
    #     Remain to be tested
    #     """
    #     if first_in:
    #         print("To-point Circle starts")
    #         self.memo = {"total_moving_period": ms_period}
    #
    #     self.moving = True
    #     w = 2 * pi / (self.max_w * self.memo["total_moving_period"])
    #     if w > 1:
    #         print("w is too high!")
    #         w = 1
    #
    #     # super().move(right=v, ccw=w)
    #     super().move(ccw=w)
    #
    #     ms_period -= 10
    #     if ms_period >= 0 and not self.halt:
    #         self.root.after(10, lambda: self.to_center_circle(v, deg, ms_period, False))
    #     else:
    #         self.moving = False
    #         print("Done")
    #         time.sleep(1.5)  # This is to make the UAV stable

    # def spiral_up(self, v, max_r, first_in=True):
    #     """
    #     Remain to be tested
    #     """
    #     pass

    # def curve_move(self, x, y, z, ms_period):
    #     """
    #     x,y,z are three parameter functions of time
    #     so that at time t,UAV will be at the coordinate (x,y,z)
    #     """
    #     steps = 1000
    #     dt = ms_period / steps
    #     for t in range(0, ms_period, steps):
    #         dx = x(t+dt) - x(t)
    #         dy = y(t+dt) - y(t)
    #         dz = z(t+dt) - z(t)
    #         desti = (dx, dy, dz)
    #         self.move_by_vector(desti, dt)

    # def show_navdata(self):
    #     self.send(at.CONFIG('general:navdata_demo', True))
    #     print(self.state)

    def clear_controller(self):
        """Clear the data of vx\vy\vz_ctrl"""
        print("Controller cleared.")
        self.vx_ctrl.clear()
        self.vy_ctrl.clear()
        self.vz_ctrl.clear()

    def speed_offset(self, vx, vy, vz):
        """Call for PIDController to get the speed offset to rectify the current speed(in m/ms)"""
        # data reported by UAV
        # real_vx = self.navdata.demo.vx / 1000 / 1000
        # real_vy = self.navdata.demo.vy / 1000 / 1000
        # real_vz = self.navdata.demo.vz / 1000 / 1000  # convert from mm/s to m/ms
        real_vx, real_vy, real_vz = 0, 0, 0

        print("In speed_offset")
        print("\tdelta_x:%.5f,vx:%.4f" % (self.vx_ctrl.delta(real_vx-vx), vx))
        print("\tdelta_y:%.5f,vy:%.4f" % (self.vy_ctrl.delta(real_vy-vy), vy))
        print("\tdelta_z:%.5f,vz:%.4f" % (self.vz_ctrl.delta(real_vz-vz), vz))

        # Rectify speed
        vx2 = self.vx_ctrl.delta(real_vx-vx)
        vy2 = self.vy_ctrl.delta(real_vy-vy)
        vz2 = self.vz_ctrl.delta(real_vz-vz)

        return vx2, vy2, vz2

if __name__ == '__main__':
    d = MyDrone()

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
    d.add_btn("8", lambda: d.number_eight())

    # free_move
    d.add_btn("free_move with pdi", lambda: d.free_move(0.1, 0, 0, 0, 1000))
    d.add_btn("free_move with pdi", lambda: d.free_move(0, 0.1, 0, 0, 1000))
    d.add_btn("free_move with pdi", lambda: d.free_move(-0.3, 0.3, 0, 0, 1000))

    # arc_move with PID
    deg = tk.IntVar()
    d0 = tk.IntVar()
    r = tk.IntVar()
    d.add_ent("角度", deg)
    d.add_ent("初始角度", d0)
    d.add_ent("半径", r)
    d.add_btn("arc_move", lambda: d.arc_move(0.1, r.get(), deg.get(), d0.get()))

    # function_move
    d.add_btn("function_move_test", lambda: d.function_move(lambda t: 0, lambda t: 0.1, lambda t: 0, 1000))

    def fx(t):
        v = 0.1
        r = 1
        w = v / r
        return v * cos(w * t)
    def fy(t):
        v = 0.1
        r = 1
        w = v / r
        return v * sin(w * t)
    def fz(t):
        return 0.1
    d.add_btn("spiral_up", lambda: d.function_move(fx, fy, fz, 2000))

    # nav_data
    #  e.g. drone.navdata.demo.vx

    d.run()
