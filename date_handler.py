from datetime import date

class Date_Handler:
    def __init__(self, 
                suspense_period_start = 0, 
                suspense_period_end = 0, 
                TODAY = date.today()):
        self.suspense_period_start = suspense_period_start
        self.suspense_period_end = suspense_period_end
        self.TODAY = TODAY

    # human readable date formatter
    def date_formatter(date):
        return date.strftime("%b-%d-%Y")

    def get_suspense_period_start(self):
        return self.suspense_period_start

    def get_suspense_period_end(self):
        return self.suspense_period_end

    def get_today(self):
        return self.TODAY

    def set_suspense_period_start(self, x):
        self.suspense_period_start = x
    
    def set_suspense_period_end(self, x):
        self.suspense_period_end = x


