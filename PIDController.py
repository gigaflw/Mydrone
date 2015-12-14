class PIDController:
    def __init__(self):
        self.error_sum = 0
        self.last_error = 0
        self.p_const = - 0.2
        self.i_const = - 0.1
        self.d_const = - 0.1

    def delta(self, error):
        p = error * self.p_const
        i = self.error_sum * self.i_const
        d = (error - self.last_error) * self.d_const
        print("p:%.4f,i:%.4f,d:%.4f," % (p, i, d))
        self.error_sum += error
        self.last_error = error
        return p + i + d

    def clear(self):
        self.error_sum = 0
        self.last_error = 0