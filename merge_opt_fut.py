import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import datetime
from typing import final
import option_list
import future_day_price
import option_list
import pandas as pd
from datetime import datetime as dt
from datetime import timedelta
import calendar
import os
from os import walk
import numpy as np
from scipy import stats as si
import pathlib
import csv


#current file location
in_path = str(pathlib.Path(__file__).parent.absolute())
if not os.path.isfile(in_path + '/future_missing.csv'):
    with open(in_path + '/future_missing.csv', "w") as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',')
        spamwriter.writerow(['Date','Option_code','Future_contact'])

def BS_call(S0,K,T,r,v):  ##  BS Call Option value
    d1 = (np.log(S0/K) + (r + 0.5*v**2)*T ) / (v*np.sqrt(T))
    d2 = d1 - (v*np.sqrt(T))
    c_value =S0*si.norm.cdf(d1) - K * np.exp(-r*T)*si.norm.cdf(d2)
    return c_value

def BS_put(S0,K,T,r,v):   ##  BS Put Option value
    d1 = (np.log(S0/K) + (r + 0.5*v**2)*T ) / (v*np.sqrt(T))
    d2 = d1 - (v*np.sqrt(T))
    p_value = K * np.exp(-r*T)*si.norm.cdf(-d2) -  S0*si.norm.cdf(-d1) 
    return p_value

def newton_vol_call(S, K, T, C, r, v):
    #S: spot price
    #K: strike price
    #T: time to maturity
    #C: Call value
    #r: interest rate
    #v: volatility of underlying asset
    high = 5
    low = 0
    sigma = v
    last_sig = v
    while True:
        fx = BS_call(S, K, T, r, sigma) - C
        if fx > 0:
            last_sig  = sigma
            high = sigma
            sigma = (sigma + low) / 2
        else:
            last_sig  = sigma
            low = sigma
            sigma = (sigma + high) / 2
        
        if abs(last_sig - sigma) < 0.00001:
            break
    return sigma

def newton_vol_put(S, K, T, P, r, v): 
    high = 5
    low = 0
    sigma = v
    last_sig = v
    while True:
        fx = BS_put(S, K, T, r, sigma) - P
        if fx > 0:
            last_sig  = sigma
            high = sigma
            sigma = (sigma + low) / 2
        else:
            last_sig  = sigma
            low = sigma
            sigma = (sigma + high) / 2
        
        if abs(last_sig - sigma) < 0.00001:
            break
    return sigma

if __name__ == '__main__':
    # 分析選擇權代碼
    # option_list.option_code()

    #更新期貨資料和歷史波動度
    # future_day_price.future_day_price()
    future_day_price.hist_vol()

    print('merging future and option price data...')
    #merge選擇權資料和現貨價格
    info_list = {'code': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'], 'expiry_month': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]}
    info_df = pd.DataFrame(info_list)
    info_df = info_df.set_index('expiry_month')
    opt_path = '/home/user/NasHistoryData/OptionCT'
    existed = []
    dir_list = []
    for root,dirs,files in walk('/home/user/NasHistoryData/OptionCT'):
        for d in dirs:
            if len(d) == 8:
                dir_list.append(dt.strptime(d,'%Y%m%d'))
    for root,dirs,files in walk('/home/user/NasPublic/Option_Data/Price'):
        for d in dirs:
            if len(d) == 8:
                existed.append(d)
    # opt_list = ['CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'CJ', 'CK', 'CL', 'CM', 'CN', 'CQ', 'CR', 'CS', 'CZ', 'DC', 'DE', 'DF', 'DG', 'DH', 'DJ', 'DK', 'DL', 'DN', 'DO', 'DP', 'DQ', 'DS', 'DV', 'DW', 'DX', 'GI', 'GX', 'HC', 'IJ', 'LO', 'NY', 'NZ', 'OA', 'OB', 'OC', 'OJ', 'OK', 'OO', 'OZ', 'QB', 'TX', 'TE', 'TF']
    opt_list = ['TX']
    for opt in opt_list:
        fut = opt + 'F'
        opt = opt + 'O'
        for d in dir_list:
            date = dt.strftime(d,'%Y%m%d')
            if date in existed:
                continue
            for root,dirs,files in walk(f'/home/user/NasHistoryData/OptionCT/{date}'):
                for f in files:
                    if opt in f:
                        print('Processing option',f,date)
                        if os.path.isfile(in_path + f'/option_codes/{opt}.csv'):
                            option_df = pd.read_csv(in_path + f'/option_codes/{opt}.csv')
                            option_df = option_df.set_index('Code')
                        else:
                            print('error: file options.csv not found.')
                            print('program closing...')
                            exit(1)
                        opt_code = f.split('.')[0]
                        # get k and delivery date
                        opt_crnt = option_df.loc[opt_code]
                        opt_df = pd.read_csv(opt_path + f'/{date}/{opt_code}.csv')
                        opt_df = opt_df[opt_df['Tick']!=0]
                        if len(opt_df) == 0:
                            print('Option no transaction on',date)
                            continue
                        # 先做call option
                        # if opt_crnt[0] == 'put':
                        #     continue
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
                        if not os.path.isfile(f'/home/user/NasHistoryData/FutureCT/{date}/{fut_code}.csv'):
                            print('for option',opt_code + ',','future price data is missing.')
                            with open(in_path + '/future_missing.csv', "w") as csvfile:
                                spamwriter = csv.writer(csvfile, delimiter=',')
                                spamwriter.writerow([date,opt_code,fut_code])
                            continue
                        fut_df = pd.read_csv(f'/home/user/NasHistoryData/FutureCT/{date}/{fut_code}.csv')
                        fut_his_v = pd.read_csv(f'/home/user/Future_OHLC/{fut}_vol.csv',dtype={"Date": str})
                        fut_his_v = fut_his_v.set_index('Date')
    
                        # calculate theoretical settlement price from future data
                        t_year = int(str(opt_crnt[2])[0:4])
                        t_month = int(str(opt_crnt[2])[4:6])
                        t_day = int(str(opt_crnt[2])[6:8])
                        monthcal = c.monthdatescalendar(t_year,t_month)
                        third_wed = [day for week in monthcal for day in week if day.weekday() == calendar.WEDNESDAY and day.month == t_month][2]
                        fut_code ='{}{}{}'.format(fut,info_df.loc[t_month,'code'],str(t_year)[3])
                        print('loading future settlement price from date', opt_crnt[2], fut_code)
                        if not os.path.isfile(f'/home/user/NasHistoryData/FutureCT/{opt_crnt[2]}/{fut_code}.csv'):
                            print('for option',opt_code + ',','settlement future price data is missing.')
                            continue
                        else:
                            settle_df = pd.read_csv(f'/home/user/NasHistoryData/FutureCT/{date}/{fut_code}.csv')
                            final_s = int(settle_df.tail(1)['Last'])

                        #merge option and future price; record future price every 60 ticks
                        step = 60
                        fut_df_60 = pd.DataFrame(columns=fut_df.columns)
                        for i in range(0,len(fut_df),step):
                            fut_df_60 = fut_df_60.append(fut_df.iloc[i],ignore_index=True)
                        fut_df_60 = fut_df_60.drop(['Vol','BIDSZ1', 'BID2', 'BIDSZ2', 'BID3',
                            'BIDSZ3', 'BID4', 'BIDSZ4', 'BID5', 'BIDSZ5', 'ASKSZ1', 'ASK2',
                            'ASKSZ2', 'ASK3', 'ASKSZ3', 'ASK4', 'ASKSZ4', 'ASK5', 'ASKSZ5', 'Tick',
                            'Volume', 'LastTime'],axis=1)
                        opt_df = opt_df.drop(['Vol', 'BID1', 'BIDSZ1', 'BID2', 'BIDSZ2', 'BID3',
                            'BIDSZ3', 'BID4', 'BIDSZ4', 'BID5', 'BIDSZ5', 'ASK1', 'ASKSZ1', 'ASK2',
                            'ASKSZ2', 'ASK3', 'ASKSZ3', 'ASK4', 'ASKSZ4', 'ASK5', 'ASKSZ5',
                            'Volume', 'LastTime'],axis=1)
                        fut_df_60 = fut_df_60.rename(columns={'Last':'Future_last'})
                        fut_df_60 = fut_df_60.sort_values(by=['Time'])
                        opt_df = opt_df.sort_values(by=['Time'])
                        merge_df = pd.merge(opt_df,fut_df_60,how='left',on='Time').fillna(method='ffill')
                        merge_df = merge_df.dropna(axis = 0)
                        merge_df = merge_df.dropna(axis = 0)
                        merge_df['K'] = opt_crnt[1]
                        t_delta = dt.strptime(str(opt_crnt[2]),'%Y%m%d') - d
                        merge_df['T'] = t_delta.days/252
                        merge_df['V'] = fut_his_v.loc[date,'hist_vol']
                        merge_df['S'] = (merge_df['BID1'] + merge_df['ASK1'])/2
                        merge_df = merge_df.reset_index(drop=True)
                        for i in range(len(merge_df)):
                            value = merge_df.iloc[i]
                            if opt_crnt[0] == 'call':
                                merge_df.loc[i,'Option_Price'] = BS_call(value[4],value[6],value[7],0.03,value[8])
                                merge_df.loc[i,'Clearing_price'] = max(final_s - opt_crnt[1],0)
                                merge_df.loc[i,'Implied_Volatility'] = newton_vol_call(value[9],value[6],value[7],merge_df.loc[i,'Last'],0.03,value[8])
                            else:
                                merge_df.loc[i,'Option_Price'] = BS_put(value[4],value[6],value[7],0.03,value[8])
                                merge_df.loc[i,'Clearing_price'] = max(opt_crnt[1] - final_s,0)
                                merge_df.loc[i,'Implied_Volatility'] = newton_vol_put(value[9],value[6],value[7],merge_df.loc[i,'Last'],0.03,value[8])
                        if len(merge_df) == 0:
                            continue
                        merge_df['Last-Clearing'] = merge_df['Last'] - merge_df['Clearing_price']
                        merge_df['Option_Price-Clearing'] = merge_df['Option_Price'] - merge_df['Clearing_price']
                        
                        # output merge file
                        output_folder = '/home/user/NasPublic/Option_Data/Price'
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
                        output_path = output_folder + f'/{opt_code}.csv'
                        merge_df.to_csv(output_path,index=False)
                        print('Output:',output_path)
