import pandas as pd
from os import walk, path, mkdir
from os.path import join
import calendar
from datetime import datetime as dt
import datetime
import pathlib
import csv
import os
in_path = str(pathlib.Path(__file__).parent.absolute())
with open(in_path + '/options.csv', "w") as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',')
    spamwriter.writerow(['Code','Type','Execution_price','Expiry_date'])
# option code to expiry_date
info_list = {'code': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X'], 'type': ['call', 'call', 'call', 'call', 'call', 'call', 'call', 'call', 'call', 'call', 'call', 'call', 'put', 'put', 'put', 'put', 'put', 'put', 'put', 'put', 'put', 'put', 'put', 'put'], 'expiry_month': ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']}
c = calendar.Calendar(firstweekday=calendar.SUNDAY)
def option_code():
    print('Processing option basic information data...')
    info_df = pd.DataFrame(info_list)
    info_df = info_df.set_index('code')
    code_list = []
    option_df = pd.DataFrame(columns=['Code','Type','Execution_price','Expiry_date'])
    for root,dirs,files in walk('/home/user/NasHistoryData/OptionCT'):
        for f in files:
            if 'TXO' in f:
                code = f.split('.')[0]
                if code not in code_list:
                    print(code)
                    code_list.append(code)
                    price = int(code[3:8])
                    month = int(info_df.loc[code[8],'expiry_month'])
                    tpe = info_df.loc[code[8],'type']
                    year = int('202'+code[9])
                    monthcal = c.monthdatescalendar(year,month)
                    third_wed = [day for week in monthcal for day in week if day.weekday() == calendar.WEDNESDAY and day.month == month][2]
                    exp_date = dt.strftime(third_wed,'%Y%m%d')
                    with open(in_path + '/options.csv', "a") as csvfile:
                        spamwriter = csv.writer(csvfile, delimiter=',')
                        spamwriter.writerow([code,tpe,price,exp_date])
                    option_df = option_df.append({'Code':code,'Type':tpe,'Execution_price':price,'Expiry_date':exp_date},ignore_index=True)
    return option_df
# if __name__ == '__main__':
#     option_code()