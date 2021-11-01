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
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


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
    
    d1 = (np.log(S / K) + (r - 0.5 * v ** 2) * T) / (v * np.sqrt(T))
    d2 = (np.log(S / K) + (r - 0.5 * v ** 2) * T) / (v * np.sqrt(T))
    
    fx = S * si.norm.cdf(d1, 0.0, 1.0) - K * np.exp(-r * T) * si.norm.cdf(d2, 0.0, 1.0) - C
    
    vega = (1 / np.sqrt(2 * np.pi)) * S * np.sqrt(T) * np.exp(-(si.norm.cdf(d1, 0.0, 1.0) ** 2) * 0.5)
    
    tolerance = 0.000001
    x0 = v
    xnew  = x0
    xold = x0 - 1
        
    while abs(xnew - xold) > tolerance:
    
        xold = xnew
        xnew = (xnew - fx - C) / vega
        
    return abs(xnew)

def newton_vol_put(S, K, T, P, r, v):
    
    d1 = (np.log(S / K) + (r - 0.5 * v ** 2) * T) / (v * np.sqrt(T))
    d2 = (np.log(S / K) + (r - 0.5 * v ** 2) * T) / (v * np.sqrt(T))
    
    fx = K * np.exp(-r * T) * si.norm.cdf(-d2, 0.0, 1.0) - S * si.norm.cdf(-d1, 0.0, 1.0) - P
    
    vega = (1 / np.sqrt(2 * np.pi)) * S * np.sqrt(T) * np.exp(-(si.norm.cdf(d1, 0.0, 1.0) ** 2) * 0.5)
    
    tolerance = 0.000001
    x0 = v
    xnew  = x0
    xold = x0 - 1
        
    while abs(xnew - xold) > tolerance:
    
        xold = xnew
        xnew = (xnew - fx - P) / vega
        
    return abs(xnew)

if __name__ == '__main__':
    # 分析選擇權代碼
    # option_list.option_code()
    if os.path.isfile(in_path + '/options.csv'):
        option_df = pd.read_csv(in_path + '/options.csv')
        option_df = option_df.set_index('Code')
    else:
        print('error: file options.csv not found.')
        print('program closing...')
        exit(1)

    #更新期貨資料和歷史波動度
    # future_day_price.future_day_price()
    # future_day_price.hist_vol()

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
    for root,dirs,files in walk('/home/user/Naspublic/Option_Data/Price'):
        for d in dirs:
            if len(d) == 8:
                existed.append(d)
    opt_list = ['TXO']
    for opt in opt_list:
        fut = 'TXF'
        for d in dir_list:
            date = dt.strftime(d,'%Y%m%d')
            if date in existed:
                continue
            for root,dirs,files in walk(f'/home/user/NasHistoryData/OptionCT/{date}'):
                for f in files:
                    if opt in f:
                        print('Processing option')
                        opt_code = f.split('.')[0]
                        # get k and delivery date
                        opt_crnt = option_df.loc[opt_code]
                        opt_df = pd.read_csv(opt_path + f'/{date}/{opt_code}.csv')

                        c = 0
                        while c < 5:
                            try:
                                c+=1
                                opt_last = pd.read_csv(opt_path + f'/{opt_crnt[2]}/{opt_code}.csv')
                                opt_last = opt_last[opt_last['Last'] !=0]
                                clearing_price = opt_last.tail(1)['Last'].values[0]
                                break
                            except:
                                opt_crnt[2] = dt.strftime(dt.strptime(str(opt_crnt[2]),'%Y%m%d') - timedelta(days=1),'%Y%m%d')
                        if c == 5:
                            print('Clearing price not found')
                            continue
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
                        if not os.path.isfile(f'/home/user/NasHistoryData/FutureCT/{date}/{fut_code}.csv'):
                            print('for option',opt_code + ',','future price data is missing.')
                            with open(in_path + '/future_missing.csv', "w") as csvfile:
                                spamwriter = csv.writer(csvfile, delimiter=',')
                                spamwriter.writerow([date,opt_code,fut_code])
                            continue
                        fut_df = pd.read_csv(f'/home/user/NasHistoryData/FutureCT/{date}/{fut_code}.csv')
                        fut_his_v = pd.read_csv(f'/home/user/Future_OHLC/{fut}.csv',dtype={"Date": str})
                        fut_his_v = fut_his_v.set_index('Date')
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
                        merge_df = opt_df.merge(fut_df_60,how='outer',on='Time').fillna(method='ffill')
                        merge_df = merge_df[merge_df['Last'] !=0]
                        merge_df = merge_df[merge_df['Future_last'] != 0]
                        merge_df = merge_df[merge_df['Tick'] != 0]
                        merge_df['K'] = opt_crnt[1]
                        t_delta = dt.strptime(str(opt_crnt[2]),'%Y%m%d') - d
                        merge_df['T'] = t_delta.days/360
                        merge_df['V'] = fut_his_v.loc[date,'hist_vol']
                        merge_df['S'] = (merge_df['BID1'] + merge_df['ASK1'])/2
                        merge_df = merge_df.reset_index(drop=True)
                        for i in range(len(merge_df)):
                            value = merge_df.iloc[i]
                            if opt_crnt[0] == 'call':
                                merge_df.loc[i,'Option_Price'] = BS_call(value[2],value[3],value[4],0.03,value[5])
                                merge_df.loc[i,'Implied_Volatility'] = newton_vol_call(value[6],value[3],value[4],merge_df.loc[i,'Option_Price'],0.03,value[5])
                            else:
                                merge_df.loc[i,'Option_Price'] = BS_put(value[2],value[3],value[4],0.03,value[5])
                                merge_df.loc[i,'Implied_Volatility'] = newton_vol_put(value[6],value[3],value[4],merge_df.loc[i,'Option_Price'],0.03,value[5])
                        if len(merge_df) == 0:
                            continue
                        merge_df['Clearing_price'] = clearing_price
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
