import logging
import threading
import time
from threading import Thread, Event
from lightweight_charts import Chart
from defines import *
from tws_client import *
import pandas as pd

END_DATE_TIME = '20250821 15:59:00 US/Eastern'


client_ready_ev: Event = Event()

if __name__ == '__main__':
    # logging.basicConfig(filename='twsapp.log', level=logging.DEBUG)
    now = time.time()
    df_underlying: pd.DataFrame = pd.read_csv(r'..\data\nasdaq_screener_usa_nasdaq.csv')
    underlying_symbol: list[str] = [symbol for symbol in df_underlying['Symbol']]
    client: TwsClient = TwsClient(client_ready_ev)
    client.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    client_thread: Thread = Thread(target=client.run)
    client_thread.start()
    time.sleep(1)

    contract = Contract()
    underlying_symbol2 = ['GEV','AMD']#GNRC','SMCI']
    for symbol in underlying_symbol:
        contract.symbol = symbol
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        what_to_show_trades = 'Trades'
        what_to_show_option_iv = 'OPTION_IMPLIED_VOLATILITY'

        client.reqHistoricalData(
             5, contract, END_DATE_TIME, '52 W', '1 day', what_to_show_trades, True, 1, False, []
         )
        while not client_ready_ev.wait():
            pass
        client_ready_ev.clear()
        if client.error_code != '':
            print(client.error_code)
            continue

        #time.sleep(1)
        client.reqHistoricalData(
            10, contract, END_DATE_TIME, '52 W', '1 day', what_to_show_option_iv, True, 1, False, []
        )
        while not client_ready_ev.wait():
            pass
        client_ready_ev.clear()
        if client.error_code != '':
            print(client.error_code)
            continue

        #time.sleep(1)
        client.reqHistoricalData(
            20, contract, END_DATE_TIME, '13 W', '1 day', what_to_show_trades, True, 1, False, []
        )
        while not client_ready_ev.wait():
            pass
        client_ready_ev.clear()
        if client.error_code != '':
            print(client.error_code)
            continue

        #time.sleep(1)
        client.reqHistoricalData(
            30, contract, END_DATE_TIME, '13 W', '1 day', what_to_show_option_iv, True, 1, False, []
        )
        while not client_ready_ev.is_set():
            pass
        client_ready_ev.clear()
        if client.error_code != '':
            print(client.error_code)
            continue
        #client.reqFundamentalData(reqId=100, contract=contract, reportType='ReportSnapshot', fundamentalDataOptions=[])
        #while not client_ready_ev.is_set():
        #    pass
        #client_ready_ev.clear()
        #if client.error_code != '':
        #    print(client.error_code)
        #    continue

        print(client.underlying_dict)
        client.underlying_list.append(client.underlying_dict.copy())

    for underlying in client.underlying_list:
        print(underlying)

    df_underlying: pd.DataFrame = pd.DataFrame.from_records(client.underlying_list).drop(['price_weeks_high_13',
                        'price_weeks_low_13',
                        'iv_weeks_high_13',
                        'iv_weeks_low_13',
                        'price_weeks_high_52',
                        'price_weeks_low_52',
                        'iv_weeks_high_52',
                        'iv_weeks_low_52',
                        ],axis=1)
    df_underlying.to_csv('result_usa_nasdaq.csv')

    client.disconnect()
    while not client_thread.is_alive():
        pass
    end = time.time()
    print(f'Total time: {end-now}')
    print(f'Main thread finished')
