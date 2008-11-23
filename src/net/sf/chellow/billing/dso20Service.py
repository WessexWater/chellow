from net.sf.chellow.billing import BillElement
from java.util import GregorianCalendar, TimeZone, Locale, Calendar

def totalElement(account, startDate, finishDate):
    totalElement = BillElement("total", 103, "Dso cost")
    return totalElement

class LlfCalculator:
    def __init__(self, voltage_level, is_substation):
        self.cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
        self.cal_ct = GregorianCalendar(TimeZone.getTimeZone("BST"), Locale.UK)
        self.voltage_level = voltage_level
        self.is_substation = is_substation
        self.rate_script = None

    def find_rate_script(self, date):
        if self.rate_script == None or self.rate_script.getStartDate().getDate().after(date.getDate()) or (self.rate_script.getFinishDate() is not None and self.rate_script.getFinishDate().getDate().before(date.getDate())):
            self.rate_script = service.rateScripts(date, date)[0]
        return self.rate_script 

    def llf(self, date, year = None, month = None, day = None, day_of_week = None, hour = None, minute = None, decimal_hour = None, year_ct = None, month_ct = None, day_ct = None, day_of_week_ct = None, hour_ct = None, minute_ct = None, decimal_hour_ct = None):
        if year == None:
            self.cal.setTime(date.getDate())
            year = self.cal.get(Calendar.YEAR)
            month = self.cal.get(Calendar.MONTH)
            day = self.cal.get(Calendar.DAY_OF_MONTH)
            day_of_week = self.cal.get(Calendar.DAY_OF_WEEK)
            hour = self.cal.get(Calendar.HOUR_OF_DAY)
            minute = self.cal.get(Calendar.MINUTE)
            decimal_hour = hour + minute / 60
            self.cal_ct.setTime(date.getDate())
            year_ct = self.cal_ct.get(Calendar.YEAR)
            month_ct = self.cal_ct.get(Calendar.MONTH)
            day_ct = self.cal_ct.get(Calendar.DAY_OF_MONTH)
            day_of_week_ct = self.cal_ct.get(Calendar.DAY_OF_WEEK)
            hour_ct = self.cal_ct.get(Calendar.HOUR_OF_DAY)
            minute_ct = self.cal_ct.get(Calendar.MINUTE)
            decimal_hour_ct = hour_ct + minute_ct / 60            
        rate_script = self.find_rate_script(date)
        if decimal_hour_ct > 0.5 and decimal_hour_ct <= 7.5:
            if self.voltage_level == "HV":
                return rate_script.getRate('night_hv')
            elif self.voltage_level == "LV":
                return rate_script.getRate('night_lv')
        elif day_of_week_ct < 5 and decimal_hour_ct > 16 and decimal_hour_ct <= 19 and (month_ct > 10 or month_ct < 3):
            if self.voltage_level == "HV":
                return rate_script.getRate('peak_hv')
            elif self.voltage_level == "LV":
                return rate_script.getRate('peak_lv')
        elif day_of_week_ct < 5 and ((decimal_hour_ct > 7.5 and decimal_hour_ct <= 16) or (decimal_hour_ct > 19 and decimal_hour_ct <= 20)) and (month_ct > 10 or month_ct < 3):
            if self.voltage_level == "HV":
                return rate_script.getRate('winter_weekday_hv')
            elif self.voltage_level == "LV":
                return rate_script.getRate('winter_weekday_lv')
        else:
            if self.voltage_level == "HV":
                return rate_script.getRate('other_hv')
            if self.voltage_level == "LV":
                return rate_script.getRate('other_lv')

def llf_calculator(voltage_level, is_substation):
    return LlfCalculator(voltage_level, is_substation)