import pandas as pd
from os import walk, path, mkdir
from os.path import join
import calendar
from datetime import datetime as dt
import datetime
import pathlib
import csv
import os
from workalendar.asia import Taiwan
cal = Taiwan()
in_path = str(pathlib.Path(__file__).parent.absolute())

def future_day_price():
    print('Processing future daily price data...')
    out_path = '/home/user/Future_OHLC'
    info_list = {'code': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'], 'expiry_month': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]}
    info_df = pd.DataFrame(info_list)
    info_df = info_df.set_index('expiry_month')

    dir_list = []
    for root,dirs,files in walk('/home/user/NasHistoryData/FutureCT'):
        for d in dirs:
            if len(d) == 8:
                dir_list.append(dt.strptime(d,'%Y%m%d'))
    fut_list = ['CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'CJ', 'CK', 'CL', 'CM', 'CN', 'CQ', 'CR', 'CS', 'CZ', 'DC', 'DE', 'DF', 'DG', 'DH', 'DJ', 'DK', 'DL', 'DN', 'DO', 'DP', 'DQ', 'DS', 'DV', 'DW', 'DX', 'GI', 'GX', 'HC', 'IJ', 'LO', 'NY', 'NZ', 'OA', 'OB', 'OC', 'OJ', 'OK', 'OO', 'OZ', 'QB', 'TX', 'TE', 'TF']
    for fut in fut_list:
        if fut == 'TE':
            fut = 'EXF'
        elif fut == 'TF':
            fut = 'FXF'
        else:
            fut = fut + 'F'
        print(fut)
        #從之前的檔案列出最後更新日期
        if  not os.path.isfile(out_path + f'/{fut}.csv'):
            with open(out_path + f'/{fut}.csv', "w") as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=',')
                spamwriter.writerow(['Date','Open','High','Low','Close'])
            last_date = datetime.datetime(1999,1,1)
        else:
            in_path = '/home/user/Future_OHLC/'+f'{fut}.csv'
            fut_df = pd.read_csv(in_path)
            l_d = str(fut_df.loc[len(fut_df)-1,'Date'])
            last_date = dt.strptime(l_d,'%Y%m%d')
        for d in dir_list:
            if d > last_date and cal.is_working_day(d):
                c = calendar.Calendar(firstweekday=calendar.SUNDAY)
                monthcal = c.monthdatescalendar(d.year,d.month)
                third_wed = [day for week in monthcal for day in week if day.weekday() == calendar.WEDNESDAY and day.month == d.month][2]
                if d.day > third_wed.day:
                    if d.month == 12:
                        code ='{}{}{}'.format(fut,info_df.loc[1,'code'],str(d.year+1)[3]) #換月
                    else:
                        code ='{}{}{}'.format(fut,info_df.loc[d.month+1,'code'],str(d.year)[3])
                else:
                    code ='{}{}{}'.format(fut,info_df.loc[d.month,'code'],str(d.year)[3]) #使用結算日當天契約價格當作現貨價格
                date = dt.strftime(d,'%Y%m%d')
                path = f'/home/user/NasHistoryData/FutureCT/{date}/{code}.csv'
                if os.path.isfile(path):
                    df1 = pd.read_csv(path)
                    mask = (df1['Time'] >= 84500000000)
                    df1 = df1[mask]
                    opn = 0
                    high = 0
                    low = 0
                    close = 0
                    last = 0
                    first_trade = 0
                    for i in range(len(df1)):
                        value = df1.iloc[i]
                        if opn == 0:
                            if value[1] != 0 and first_trade == 0:
                                opn = value[1]
                                first_trade = 1
                                high = value[1]
                                low = value[1]
                        if value[1] > high:
                            high = value[1]
                        elif value[1] < low and value[1] != 0:
                            low = value[1]
                        if value[1] != 0:
                            last = value[1]
                    close = last
                    with open(out_path + f'/{fut}.csv', "a") as csvfile:
                        spamwriter = csv.writer(csvfile, delimiter=',')
                        spamwriter.writerow([date,opn,high,low,close])
                    print(date,opn,high,low,close)
def hist_vol():
    import math
    fut_list = ['CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'CJ', 'CK', 'CL', 'CM', 'CN', 'CQ', 'CR', 'CS', 'CZ', 'DC', 'DE', 'DF', 'DG', 'DH', 'DJ', 'DK', 'DL', 'DN', 'DO', 'DP', 'DQ', 'DS', 'DV', 'DW', 'DX', 'GI', 'GX', 'HC', 'IJ', 'LO', 'NY', 'NZ', 'OA', 'OB', 'OC', 'OJ', 'OK', 'OO', 'OZ', 'QB', 'TX', 'TE', 'TF']
    for fut in fut_list:
        if fut == 'TE':
            code = 'EXF'
        elif fut == 'TF':
            code = 'FXF'
        else:
            code = fut + 'F'
        in_path = '/home/user/Future_OHLC/'+f'{code}.csv'
        fut_df = pd.read_csv(in_path)
        # sort all rows by date
        fut_df = fut_df.sort_values(by=['Date'])
        fut_df = fut_df.drop_duplicates(subset=['Date'])
        fut_df = fut_df[fut_df['Low']!=0]
        fut_df = fut_df.reset_index(drop=True)
        for i in range(len(fut_df)):
            try:
                value = fut_df.loc[i]
                fut_df.loc[i,'r_hl_2'] = math.pow(math.log(value[2]/value[3]),2)
            except:
                fut_df.loc[i,'r_hl_2'] = 0
        fut_df['sum_r'] = fut_df['r_hl_2'].rolling(15).sum()
        for i in range(len(fut_df)):
            value = fut_df.loc[i]
            fut_df.loc[i,'hist_vol'] = math.sqrt(value[6]/(60*math.log(2)))*math.sqrt(252)
        fut_df = fut_df.drop(['r_hl_2','sum_r'],axis=1)
        fut_df.to_csv('/home/user/Future_OHLC/'+f'{code}_vol.csv',index=False)
