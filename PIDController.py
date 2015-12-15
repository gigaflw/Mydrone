import random


class PIDController:
    def __init__(self):
        self.error_sum = 0
        self.last_error = 0
        self.p_const = - 1
        self.i_const = - 0.5
        self.d_const = - 0.2

    def delta(self, error):
        p = error * self.p_const
        i = self.error_sum * self.i_const
        d = (error - self.last_error) * self.d_const
        # print("p:%.4f,i:%.4f,d:%.4f," % (p, i, d))
        self.error_sum += error
        self.last_error = error
        return p + i + d

    def clear(self):
        self.error_sum = 0
        self.last_error = 0

if __name__ == '__main__':
    pid = PIDController()
    real_v = 10
    v = 10
    for i in range(100):
        real_v += random.random() * 2 - 1
        error = real_v - v
        dv = pid.delta(error)
        real_v += dv
        print("In turn %d:\nerror:%.2f\tdv:%.2f\nreal_v:%.2f\n" % (i, error, dv, real_v))
