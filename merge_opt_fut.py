import option_list
import future_day_price
import option_list
import pandas as pd
from datetime import datetime as dt
import calendar
import os
from os import walk
import numpy as np
from scipy import stats
import pathlib

#current file location
in_path = str(pathlib.Path(__file__).parent.absolute())

def BS_call(S0,K,T,r,v):  ##  BS Call Option value
    d1 = (np.log(S0/K) + (r + 0.5*v**2)*T ) / (v*np.sqrt(T))
    d2 = d1 - (v*np.sqrt(T))
    c_value =S0*stats.norm.cdf(d1) - K * np.exp(-r*T)*stats.norm.cdf(d2)
    return c_value

def BS_put(S0,K,T,r,v):   ##  BS Put Option value
    d1 = (np.log(S0/K) + (r + 0.5*v**2)*T ) / (v*np.sqrt(T))
    d2 = d1 - (v*np.sqrt(T))
    p_value = K * np.exp(-r*T)*stats.norm.cdf(-d2) -  S0*stats.norm.cdf(-d1) 
    return p_value

if __name__ == '__main__':
    print('merging future and option price data...')
    # 分析選擇權代碼
    option_list.option_code()
    if os.path.isfile(in_path + '/options.csv'):
        option_df = pd.read_csv()
        option_df = option_df.set_index('Code')
    else:
        print('error: file options.csv not found.')
        print('program closing...')
        exit(1)

    #更新期貨資料和歷史波動度
    future_day_price.future_day_price()
    future_day_price.hist_vol()

    #merge選擇權資料和現貨價格
    info_list = {'code': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'], 'expiry_month': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]}
    info_df = pd.DataFrame(info_list)
    info_df = info_df.set_index('expiry_month')
    opt_path = '/home/user/NasHistoryData/OptionCT'
    dir_list = []
    for root,dirs,files in walk('/home/user/NasHistoryData/OptionCT'):
        for d in dirs:
            if len(d) == 8:
                dir_list.append(dt.strptime(d,'%Y%m%d'))
    opt_list = ['TXO']
    for opt in opt_list:
        fut = 'TXF'
        for d in dir_list:
            date = dt.strftime(d,'%Y%m%d')
            for root,dirs,files in walk(f'/home/user/NasHistoryData/OptionCT/{date}'):
                for f in files:
                    if opt in f:
                        opt_code = f.split('.')[0]
                        # get k and delivery date
                        opt_crnt = option_df.loc[opt_code]
                        opt_df = pd.read_csv(opt_path + f'/{opt_code}.csv')
                        # 先做call option
                        if opt_crnt[0] == 'put':
                            continue
                        # import corresponding future price information and historical volatility
                        c = calendar.Calendar(firstweekday=calendar.SUNDAY)
                        monthcal = c.monthdatescalendar(d.year,d.month)
                        third_wed = [day for week in monthcal for day in week if day.weekday() == calendar.WEDNESDAY and day.month == d.month][2]
                        if d.day > third_wed.day:
                            if d.month == 12:
                                fut_code ='{}{}{}'.format(fut,info_df.loc[1,'code'],str(d.year+1)[3]) #換月
                            else:
                                fut_code ='{}{}{}'.format(fut,info_df.loc[d.month+1,'code'],str(d.year)[3])
                        else:
                            fut_code ='{}{}{}'.format(fut,info_df.loc[d.month,'code'],str(d.year)[3])
                        fut_df = pd.read_csv(f'/home/user/NasHistoryData/FutureCT/{date}/{fut_code}.csv')
                        fut_his_v = pd.read_csv(f'/home/user/Future_OHLC/{fut}.csv')
                        fut_his_v = fut_his_v.set_index('Date')
                        #merge option and future price; record future prrice every 60 ticks
                        step = 60
                        fut_df_60 = pd.DataFrame(columns=fut_df.columns)
                        for i in range(0,len(fut_df),step):
                            fut_df_60 = fut_df_60.append(fut_df.iloc[i],ignore_index=True)
                        fut_df_60 = fut_df_60.drop(['Vol', 'BID1', 'BIDSZ1', 'BID2', 'BIDSZ2', 'BID3',
                            'BIDSZ3', 'BID4', 'BIDSZ4', 'BID5', 'BIDSZ5', 'ASK1', 'ASKSZ1', 'ASK2',
                            'ASKSZ2', 'ASK3', 'ASKSZ3', 'ASK4', 'ASKSZ4', 'ASK5', 'ASKSZ5', 'Tick',
                            'Volume', 'LastTime'],axis=1)
                        opt_df = opt_df.drop(['Vol', 'BID1', 'BIDSZ1', 'BID2', 'BIDSZ2', 'BID3',
                            'BIDSZ3', 'BID4', 'BIDSZ4', 'BID5', 'BIDSZ5', 'ASK1', 'ASKSZ1', 'ASK2',
                            'ASKSZ2', 'ASK3', 'ASKSZ3', 'ASK4', 'ASKSZ4', 'ASK5', 'ASKSZ5', 'Tick',
                            'Volume', 'LastTime'],axis=1)
                        fut_df_60 = fut_df_60.rename(columns={'Last':'Future_last'})
                        merge_df = opt_df.merge(fut_df_60,how='outer',on
                        ='Time').fillna(method='ffill')
                        merge_df = merge_df[merge_df.Last !=0]
                        merge_df['K'] = opt_crnt[1]
                        t_delta = dt.strptime(opt_crnt[2],'%Y%m%d') - d
                        merge_df['T'] = t_delta.days/360
                        merge_df['sigma'] = fut_his_v.loc[date]
                        for i in range(len(merge_df)):
                            value = merge_df.iloc[i]
                            merge_df.iloc[i]['Option_Price'] = BS_call(value[2],value[3],value[4],0.03,value[5])

                        # output merge file
                        output_folder = '/home/user/Option_val'
                        try:
                            if os.path.isdir(output_folder):
                                print('Folder exist: ' + output_folder)
                            else:
                                print('Create folder: ' + output_folder)
                                os.mkdir(output_folder)
                        except OSError:
                            print('Creation of the directory {} failed'.format(output_folder))
                            exit(1)
                        output_folder = output_folder + f'/{date}'
                        try:
                            if os.path.isdir(output_folder):
                                print('Folder exist: ' + output_folder)
                            else:
                                print('Create folder: ' + output_folder)
                                os.mkdir(output_folder)
                        except OSError:
                            print('Creation of the directory {} failed'.format(output_folder))
                            exit(1)
                        output_path = output_folder + f'{opt_code}.csv'
                        merge_df.to_csv(output_path)
                        print('Output:',output_folder)
