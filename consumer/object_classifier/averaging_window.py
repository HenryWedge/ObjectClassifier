class AveragingWindow:

    def __init__(self, window_size):
        self.values = []
        self.window_size = window_size

    def append_value(self, value: float):
        self.values.append(value)

    def get_average(self):
        last_n_elements = self.values[max(0, len(self.values) - self.window_size):]
        return sum(last_n_elements) / min(self.window_size, len(self.values))
