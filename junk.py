# Here goes functions that failed

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

# def clear_controller(self):
#     """Clear the data of vx\vy\vz_ctrl"""
#     print("Controller cleared.")
#     self.vx_ctrl.clear()
#     self.vy_ctrl.clear()
#     self.vz_ctrl.clear()
#
# def speed_offset(self, vx, vy):
#     """
#     Call for PIDController to get the speed offset to rectify the current speed(in m/ms)
#     vz control is not included since ARDrone already has complete vz control
#     """
#     # data reported by UAV
#     real_vx = -self.navdata.demo.vx
#     real_vy = self.navdata.demo.vy  # convert from mm/s to m/ms
#
#     real_vx /= self.max_v
#     real_vy /= self.max_v
#
#     real_vx /= 1e6
#     real_vy /= 1e6  # convert from mm/s to m/ms
#
#     print("In speed_offset")
#     print("\treal_vx:%.4f,real_vy:%.4f" % (real_vx, real_vy))
#     print("\tvx:%.4f,vy:%.4f" % (vx, vy))
#
#     # Rectify speed
#     dx = self.vx_ctrl.delta(real_vx-vx)
#     dy = self.vy_ctrl.delta(real_vy-vy)
#
#     print("\tdelta_x:%.5f,delta_y:%.5f" % (dx, dy))
#
#     # return dx, dy
#     return 0, 0
