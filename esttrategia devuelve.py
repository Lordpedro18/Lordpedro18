# -*- coding: utf-8 -*-
"""
Created on Sat Jun 22 01:46:23 2024

@author: pedro
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

top_stocks = {
    'US': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'BRK-B', 'JNJ', 'NVDA', 'V'],
    'UK': ['HSBC', 'RIO', 'ULVR', 'GSK', 'BP', 'AAL', 'BATS', 'SHEL', 'VOD', 'LLOY'],
    'France': ['OR.PA', 'AIR.PA', 'BN.PA', 'SAN.PA', 'SGO.PA', 'LR.PA', 'CAP.PA', 'HO.PA', 'DG.PA', 'MC.PA'],
    'Japan': ['7203.T', '6758.T', '9984.T', '8306.T', '8035.T', '9432.T', '6367.T', '6954.T', '6952.T', '7201.T'],
    'China': ['BABA', 'TCEHY', 'JD', 'PDD', 'BIDU', 'NIO', 'XPEV', 'LI', 'BEKE', 'ZTO'],
    'Mexico': ['AMXL.MX', 'FEMSAUBD.MX', 'GMEXICOB.MX', 'WALMEX.MX', 'CEMEXCPO.MX', 'GFNORTEO.MX', 'TLEVISACPO.MX', 'GFINBURO.MX', 'PE&OLES.MX'],
    'Brazil': ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'B3SA3.SA', 'ABEV3.SA', 'ITSA4.SA', 'BBAS3.SA', 'WEGE3.SA', 'SUZB3.SA'],
    'Chile': ['SQM', 'COPEC', 'BSANTANDER', 'FALABELLA.SN', 'CMPC.SN', 'ENELCHILE.SN', 'CCU.SN', 'CENCOSUD.SN', 'ANTARCHILE.SN', 'CAP.SN'],
    'Peru': ['BAP', 'BVN', 'CREDICORP', 'FERREYCORP.LM', 'SCCO', 'CASAGRANDE.LM', 'RELAPAC1.LM', 'CPACASC1.LM', 'VOLCANB.LM', 'MILPOI1.LM'],
    'Colombia': ['EC', 'PFAVAL', 'CNEC', 'GRUPOSURA', 'NUTRESA', 'AVAL', 'BOGOTA', 'ICOLCAP', 'GRUPOARGOS', 'CEMARGOS']
}

# Function to fetch historical data for stocks
def fetch_stock_data(stock_symbols, start_date, end_date):
    stock_data = {}
    for symbol in stock_symbols:
        try:
            stock_data[symbol] = yf.download(symbol, start=start_date, end=end_date)
            stock_data[symbol].index = pd.to_datetime(stock_data[symbol].index)  # Ensure datetime index
        except Exception as e:
            print(f"Error downloading data for {symbol}: {e}")
    return stock_data

def backtest_strategy(stock_data, buy_threshold, sell_threshold, initial_investment=100):
    results = {}
    mean_profit_per_operation = {}
    all_data_with_signals = {}
    annual_operation_counts = {}

    for symbol, data in stock_data.items():
        if data.empty:
            continue  
        data['Rentability'] = data['Close'].pct_change() * 100
        data['Signal'] = 0
        data['Signal'][data['Rentability'] <= -buy_threshold] = 1  
        data['Signal'][data['Rentability'] >= sell_threshold] = -1 

        # Backtesting
        position = 0 
        total_profit = 0
        operation_count = 0
        operation_profits = []
        operations = []

        for i in range(1, len(data) - 1): 
            if data['Signal'].iloc[i] == 1 and position == 0:
                position = 1
                buy_price = data['Close'].iloc[i + 1]  
                shares = initial_investment / buy_price
                operations.append((data.index[i + 1], 'Buy'))
            elif data['Signal'].iloc[i] == -1 and position == 1:
                position = 0
                sell_price = data['Close'].iloc[i + 1] 
                profit = shares * (sell_price - buy_price)
                total_profit += profit
                operation_profits.append(profit)
                operation_count += 1
                operations.append((data.index[i + 1], 'Sell'))

        if operation_count > 0:
            mean_profit_per_operation[symbol] = np.mean(operation_profits)
        else:
            mean_profit_per_operation[symbol] = 0

        results[symbol] = total_profit
        all_data_with_signals[symbol] = data 

        df_operations = pd.DataFrame(operations, columns=['Date', 'Operation'])
        df_operations['Date'] = pd.to_datetime(df_operations['Date'])
        df_operations['Year'] = df_operations['Date'].dt.year
        annual_counts = df_operations.groupby(['Year', 'Operation']).size().unstack(fill_value=0)
        annual_operation_counts[symbol] = annual_counts

    return results, mean_profit_per_operation, all_data_with_signals, annual_operation_counts

end_date = datetime.now()
start_date = datetime(2000, 1, 1)  

thresholds = [2, 3, 4, 5]

stocks_with_country = [f"{country}_{stock}" for country, stocks in top_stocks.items() for stock in stocks]
result_table = pd.DataFrame(index=stocks_with_country, columns=thresholds)
mean_profit_table = pd.DataFrame(index=stocks_with_country, columns=thresholds)
price_data_dict = {} 
annual_operations_dict = {} 

for country, symbols in top_stocks.items():
    stock_data = fetch_stock_data(symbols, start_date, end_date)
    
    for threshold in thresholds:
        buy_threshold = threshold
        sell_threshold = threshold
        results, mean_profit_per_operation, all_data_with_signals, annual_operation_counts = backtest_strategy(stock_data, buy_threshold, sell_threshold)
        
        for stock, profit in results.items():
            result_table.at[f"{country}_{stock}", threshold] = profit
            mean_profit_table.at[f"{country}_{stock}", threshold] = mean_profit_per_operation[stock]
            if f"{country}_{stock}" not in price_data_dict:
                price_data_dict[f"{country}_{stock}"] = all_data_with_signals[stock]  
                annual_operations_dict[f"{country}_{stock}"] = annual_operation_counts[stock] 

file_path = r"C:\Users\pedro\OneDrive\Escritorio\Estrategia trading\resultados.xlsx"

with pd.ExcelWriter(file_path) as writer:
    result_table.to_excel(writer, sheet_name='Total_Profit_Table')
    mean_profit_table.to_excel(writer, sheet_name='Mean_Profit_per_Operation')
    
    for stock, data in price_data_dict.items():
        data.to_excel(writer, sheet_name=f'{stock}_Price_Data')
    
    for stock, data in annual_operations_dict.items():
        data.to_excel(writer, sheet_name=f'{stock}_Operations')

print(f"Results saved successfully to {file_path}")
