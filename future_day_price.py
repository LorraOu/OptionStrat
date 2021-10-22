import pandas as pd
from os import walk, path, mkdir
from os.path import join
import calendar
from datetime import datetime as dt
import pathlib
import csv
import os
in_path = str(pathlib.Path(__file__).parent.absolute())

def future_day_price():
    out_path = '/home/user/Future_OHLC'
    info_list = {'code': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'], 'expiry_month': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]}
    info_df = pd.DataFrame(info_list)
    info_df = info_df.set_index('expiry_month')

    dir_list = []
    for root,dirs,files in walk('/home/user/NasHistoryData/FutureCT'):
        for d in dirs:
            if len(d) == 8:
                dir_list.append(dt.strptime(d,'%Y%m%d'))
    for d in dir_list:
        c = calendar.Calendar(firstweekday=calendar.SUNDAY)
        monthcal = c.monthdatescalendar(d.year,d.month)
        third_wed = [day for week in monthcal for day in week if day.weekday() == calendar.WEDNESDAY and day.month == d.month][2]
        if d.day > third_wed.day:
            if d.month == 12:
                code ='TXF{}{}'.format(info_df.loc[1,'code'],str(d.year+1)[3]) #換月
            else:
                code ='TXF{}{}'.format(info_df.loc[d.month+1,'code'],str(d.year)[3])
        else:
            code ='TXF{}{}'.format(info_df.loc[d.month,'code'],str(d.year)[3]) #使用結算日當天契約價格當作現貨價格
        with open(out_path + f'/{code[:-2]}.csv', "w") as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            spamwriter.writerow(['Date','Open','High','Low','Close'])
        date = dt.strftime(d,'%Y%m%d')
        path = f'/home/user/NasHistoryData/FutureCT/{date}/{code}.csv'
        if os.path.isfile(path):
            df1 = pd.read_csv(path)
            opn = 0
            high = 0
            low = 0
            close = 0
            first_trade = 0
            for i in range(0,len(df1),60):
                value = df1.iloc[i]
                if i == 0:
                    if value[1] != 0 and first_trade == 0:
                        opn = value[1]
                        first_trade = 1
                        high = value[1]
                        low = value[1]
                if value[1] > high:
                    high = value[1]
                elif value[1] < low and value[1] != 0:
                    low = value[1]
                last = value[1]
            close = last
            with open(out_path + f'/{code[:-2]}.csv', "a") as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=',')
                spamwriter.writerow([date,opn,high,low,close])
            print(date,opn,high,low,close)
# option_df.to_csv(in_path+'/options.csv',index=False)
if __name__ == '__main__':
    future_day_price()