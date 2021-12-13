import pandas as pd
from os import walk, path, mkdir
from os.path import join
import calendar
from datetime import datetime as dt
import datetime
import pathlib
import csv
import os
# option_code()的用途為解析選擇權檔案名稱，建立選擇權基本資料表

def option_code():
    in_path = str(pathlib.Path(__file__).parent.absolute()) + '/option_codes'
    if not os.path.isdir(in_path):
        os.mkdir(in_path)
    info_list = {'code': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X'], 'type': ['call', 'call', 'call', 'call', 'call', 'call', 'call', 'call', 'call', 'call', 'call', 'call', 'put', 'put', 'put', 'put', 'put', 'put', 'put', 'put', 'put', 'put', 'put', 'put'], 'expiry_month': ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']}
    option_list = ['CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'CJ', 'CK', 'CL', 'CM', 'CN', 'CQ', 'CR', 'CS', 'CZ', 'DC', 'DE', 'DF', 'DG', 'DH', 'DJ', 'DK', 'DL', 'DN', 'DO', 'DP', 'DQ', 'DS', 'DV', 'DW', 'DX', 'GI', 'GX', 'HC', 'IJ', 'LO', 'NY', 'NZ', 'OA', 'OB', 'OC', 'OJ', 'OK', 'OO', 'OZ', 'QB', 'TX', 'TE', 'TF']
    c = calendar.Calendar(firstweekday=calendar.SUNDAY)

    print('Processing option basic information data...')
    info_df = pd.DataFrame(info_list)
    info_df = info_df.set_index('code')
    for opt in option_list:
        opt = opt + 'O'
        # 匯入舊有資料或建立新資料
        if os.path.isfile(in_path + f'/{opt}.csv'):
            df1 = pd.read_csv(in_path + f'/{opt}.csv')
            code_list = list(df1['Code'])
        else:
            code_list = []
            with open(in_path + f'/{opt}.csv', "w") as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=',')
                spamwriter.writerow(['Code','Type','Execution_price','Expiry_date'])

        for root,dirs,files in walk('/home/user/NasHistoryData/OptionCT'):
            for f in files:
                if opt in f:
                    code = f.split('.')[0]
                    if code not in code_list:
                        print('processing',code)
                        code_list.append(code)
                        price = int(code[3:8])
                        month = int(info_df.loc[code[8],'expiry_month'])
                        tpe = info_df.loc[code[8],'type']
                        year = int('202'+code[9])
                        monthcal = c.monthdatescalendar(year,month)
                        third_wed = [day for week in monthcal for day in week if day.weekday() == calendar.WEDNESDAY and day.month == month][2]
                        exp_date = dt.strftime(third_wed,'%Y%m%d')
                        with open(in_path + f'/{opt}.csv', "a") as csvfile:
                            spamwriter = csv.writer(csvfile, delimiter=',')
                            spamwriter.writerow([code,tpe,price,exp_date])
                    else:
                        print(code,'exists.')
# if __name__ == '__main__':
#     option_code()