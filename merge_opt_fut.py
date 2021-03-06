import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from typing import final
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
import multiprocessing as mp
from workalendar.asia import Taiwan
cal = Taiwan()
# merge_opt_fut.py為主程式，執行時會自動帶入另外兩個涵式庫
# create_file() 會處理指定日期的選擇權資料

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

def BS_call_delta(S0,K,T,r,v):
    d1 = (np.log(S0/K) + (r + 0.5*v**2)*T ) / (v*np.sqrt(T))
    return si.norm.cdf(d1)

def BS_put_delta(S0,K,T,r,v):
    d1 = (np.log(S0/K) + (r + 0.5*v**2)*T ) / (v*np.sqrt(T))
    return -si.norm.cdf(-d1) 

def newton_vol_call(S, K, T, C, r, v): ## 隱含波動度
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
        
        if abs(last_sig - sigma) < 0.0001:
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
        
        if abs(last_sig - sigma) < 0.0001:
            break
    return sigma

def create_file(date):
    print('merging future and option price data...')
    #merge選擇權資料和現貨價格
    info_list = {'code': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'], 'expiry_month': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]}
    info_df = pd.DataFrame(info_list)
    info_df = info_df.set_index('expiry_month')
    opt_path = '/home/user/NasHistoryData/OptionCT'
    # opt_list = ['CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'CJ', 'CK', 'CL', 'CM', 'CN', 'CQ', 'CR', 'CS', 'CZ', 'DC', 'DE', 'DF', 'DG', 'DH', 'DJ', 'DK', 'DL', 'DN', 'DO', 'DP', 'DQ', 'DS', 'DV', 'DW', 'DX', 'GI', 'GX', 'HC', 'IJ', 'LO', 'NY', 'NZ', 'OA', 'OB', 'OC', 'OJ', 'OK', 'OO', 'OZ', 'QB', 'TX', 'TE', 'TF']
    opt_list = ['TX', 'TE', 'TF','CE', 'CF', 'CG', 'CH', 'CJ', 'CK', 'CL', 'CM', 'CN', 'CQ', 'CR', 'CS', 'CZ', 'DC', 'DE', 'DF', 'DG', 'DH', 'DJ', 'DK', 'DL', 'DN', 'DO', 'DP', 'DQ', 'DS', 'DV', 'DW', 'DX', 'GI', 'GX', 'HC', 'IJ', 'LO', 'NY', 'NZ', 'OA', 'OB', 'OC', 'OJ', 'OK', 'OO', 'OZ', 'QB']
    for opt in opt_list:
        if opt == 'TE':
            fut = 'EXF'
            opt = opt + 'O'
        elif opt == 'TF':
            fut = 'FXF'
            opt = opt + 'O'
        else:
            fut = opt + 'F'
            opt = opt + 'O'
        d = dt.strptime(date,'%Y%m%d')
        # 排除非工作天的日期
        if not cal.is_working_day(d):
            continue
        for root,dirs,files in walk(f'/home/user/NasHistoryData/OptionCT/{date}'):
            for f in files:
                if opt in f:
                    # 檢查選擇權資料是否存在
                    if os.path.isfile(in_path + f'/option_codes/{opt}.csv'):
                        option_df = pd.read_csv(in_path + f'/option_codes/{opt}.csv')
                        option_df = option_df.set_index('Code')
                    else:
                        print('error: file options.csv not found.')
                        print('program closing...')
                        exit(1)
                    
                    # 取得選擇權名稱作為檢索值
                    opt_code = f.split('.')[0]
                    # 取得選擇權基本資料
                    opt_crnt = option_df.loc[opt_code]
                    print('Processing option',f,date,'expire on',opt_crnt[2])
                    opt_df = pd.read_csv(opt_path + f'/{date}/{opt_code}.csv')
                    opt_df = opt_df[opt_df['Tick']!=0]
                    # 如果之前有做過就跳過
                    if os.path.isfile(f'/home/user/NasPublic/Option_Data/Price/{date}/{opt_code}_{date[0:4]}-{date[4:6]}-{date[6:8]}.csv'):
                        continue
                    # 若當日該選擇權並無交易則直接略過
                    if len(opt_df) == 0:
                        print('Option no transaction on',date)
                        continue
                    # 匯入對應之期貨價格和歷史波動度
                    y = str(opt_crnt[2])[3]
                    m = int(str(opt_crnt[2])[4:6])
                    fut_code ='{}{}{}'.format(fut,info_df.loc[m,'code'],y)
                    print('Get future price from contract',fut_code)
                    if not os.path.isfile(f'/home/user/NasHistoryData/FutureCT/{date}/{fut_code}.csv'):
                        print('for option',opt_code + ',','future price data is missing.')
                        with open(in_path + '/future_missing.csv', "w") as csvfile:
                            spamwriter = csv.writer(csvfile, delimiter=',')
                            spamwriter.writerow([date,opt_code,fut_code])
                        continue
                    fut_df = pd.read_csv(f'/home/user/NasHistoryData/FutureCT/{date}/{fut_code}.csv')
                    fut_his_v = pd.read_csv(f'/home/user/Future_OHLC/{fut}_vol.csv',dtype={"Date": str})
                    fut_his_v = fut_his_v.set_index('Date')
                    # 去除試搓價格
                    mask = (fut_df['Time'] >= 84500000000)
                    fut_df = fut_df[mask]

                    # 合併選擇權和期貨資料，期貨因交易量大所以每30筆做subsample
                    fut_df_60 = pd.DataFrame(columns=fut_df.columns)
                    step = 30
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
                    merge_df = pd.merge(opt_df,fut_df_60,how='outer',sort=True,on='Time').fillna(method='ffill')
                    merge_df['Time'] = merge_df['Time'].astype(int)
                    # 去除合併後非選擇權原本時間的資料
                    opt_time_l = list(opt_df['Time'])
                    for i in merge_df.index:
                        if merge_df.loc[i,'Time'] not in opt_time_l:
                            merge_df = merge_df.drop(i,axis=0)
                    # 調整履約價格，由option_list得到的履約價有可能不是真正履約價（系統會預留小數點位置）
                    print('calculate option price')
                    while opt_crnt[1]/fut_df_60.tail(1)['Future_last'].values[0] > 2:
                            opt_crnt[1] = opt_crnt[1]/10
                    merge_df['K'] = opt_crnt[1]
                    t_delta = dt.strptime(str(opt_crnt[2]),'%Y%m%d') - d
                    # 調整剩餘到期日精確到秒
                    for i in merge_df.index:
                        tmp = str(merge_df.loc[i,'Time'])
                        tmp_d = dt(d.year,d.month,d.day,13,45) - dt(d.year,d.month,d.day,int(tmp[:-10]),int(tmp[-10:-8]))
                        merge_df.loc[i,'T'] = t_delta.days/252 + tmp_d.seconds/21772800
                    
                    # 紀錄期貨在結算當天收盤價
                    try:
                        final_s = fut_his_v.loc[str(opt_crnt[2]),'Close']
                    except:
                        print('Future settlement price not found.')
                        continue
                    # 得到對應的歷史波動度資料
                    t_d = d
                    t_date = date
                    while True:
                        try:
                            # 若當日無資料就會往前搜索
                            merge_df['V'] = fut_his_v.loc[t_date,'hist_vol']
                            break
                        except:
                            t_d = t_d - timedelta(days=1)
                            t_date = dt.strftime(t_d,'%Y%m%d')
                    # 計算隱含波動度之現貨價格(S)及實際結算價格(S*)
                    merge_df['S'] = (merge_df['BID1'] + merge_df['ASK1'])/2
                    merge_df['S*'] = final_s
                    merge_df = merge_df.reset_index(drop=True)

                    # 計算選擇權的理論價格、結算價、隱含波動度以及Delta
                    for i in range(len(merge_df)):
                        value = merge_df.iloc[i]
                        if opt_crnt[0] == 'call':
                            sigma_i = newton_vol_call(value[9],value[6],value[7],value[1],0.03,value[8])
                            merge_df.loc[i,'Option_Price'] = BS_call(value[3],value[6],value[7],0.03,value[8])
                            merge_df.loc[i,'Clearing_price'] = max(final_s - opt_crnt[1],0)
                            merge_df.loc[i,'Implied_Volatility'] = sigma_i
                            merge_df.loc[i,'Delta'] = BS_call_delta(value[3],value[6],value[7],0.03,sigma_i)
                        else:
                            sigma_i = newton_vol_put(value[9],value[6],value[7],value[1],0.03,value[8])
                            merge_df.loc[i,'Option_Price'] = BS_put(value[3],value[6],value[7],0.03,value[8])
                            merge_df.loc[i,'Clearing_price'] = max(opt_crnt[1] - final_s,0)
                            merge_df.loc[i,'Implied_Volatility'] = sigma_i
                            merge_df.loc[i,'Delta'] = BS_put_delta(value[3],value[6],value[7],0.03,sigma_i)
                    if len(merge_df) == 0:
                        print('Discard',opt_code,'because no effective transaction is recorded (very likely due to missing values)')
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
                    output_path = output_folder + f'/{opt_code}_{date[0:4]}-{date[4:6]}-{date[6:8]}.csv'
                    merge_df.to_csv(output_path,index=False)
                    print('Output:',output_path)

if __name__ == '__main__':
    # 分析選擇權代碼
    option_list.option_code()

    # 更新期貨資料和歷史波動度
    future_day_price.future_day_price()
    future_day_price.hist_vol()

    # 建立資料所需日期
    date_list = []
    c = calendar.Calendar(firstweekday=calendar.SUNDAY)
    for year in range(2020,2022,1):
        for month in range(1,13,1):
            monthcal = c.monthdatescalendar(year,month)
            third_wed = [day for week in monthcal for day in week if day.weekday() == calendar.WEDNESDAY and day.month == month][2]
            date_list.append(third_wed)
    data_date = []
    for d in date_list:
        data_date.append(d.strftime('%Y%m%d'))
    # 因歷史波動度是rolling 15 天，所以前面幾筆資料會無法計算價格
    data_date = data_date[3:]

    # 平行化運算
    pool = mp.Pool()
    res = pool.map(create_file, data_date)
    print(res)
    

    
