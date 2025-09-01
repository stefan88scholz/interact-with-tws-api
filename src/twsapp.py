import logging
from defines import DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID
import time
from threading import Thread
from tws_client import *
from datetime import datetime
from pytz import timezone
import pandas as pd
from natsort import index_natsorted
import numpy as np
import argparse as ap

client_ready_ev: Event = Event()

def execute_tws_app(df_input: pd.DataFrame,
                    end_date_time: str,
                    ascending: bool,
                    min_price: float,
                    max_price: float,
                    above_sma200: bool,
                    above_sma50: bool,
                    min_iv: float,
                    min_market_cap: float) -> pd.DataFrame:
    client: TwsClient = TwsClient(client_ready_ev,
                                  ascending,
                                  min_price,
                                  max_price,
                                  above_sma200,
                                  above_sma50,
                                  min_iv)
    client.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    client_thread: Thread = Thread(target=client.run)
    client_thread.start()
    time.sleep(1)

    contract = Contract()
    df_input2: pd.DataFrame = pd.DataFrame(
        data={'Symbol': ['AMD', 'CEG'],
              'Name': ['Advanced Micro Devices Inc. Common Stock',
                       'Constellation Energy Corporation Common Stock '],
              'MarketCap': ['272248257267.00', '96895.71']}
    )
    for row in df_input.itertuples():
        contract.symbol = row.Symbol
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        what_to_show_trades = 'Trades'
        what_to_show_option_iv = 'OPTION_IMPLIED_VOLATILITY'

        if min_market_cap > row.MarketCap:
            client.error_code = f'Market Cap below ${min_market_cap}'
            print(f'{row.Symbol}: {client.error_code}')
            continue

        client.reqHistoricalData(
            5, contract, end_date_time, '52 W', '1 day', what_to_show_trades, True, 1, False, []
        )
        while not client_ready_ev.wait():
            pass
        client_ready_ev.clear()
        if client.error_code != '':
            print(client.error_code)
            continue

        client.reqHistoricalData(
            10, contract, end_date_time, '52 W', '1 day', what_to_show_option_iv, True, 1, False, []
        )
        while not client_ready_ev.wait():
            pass
        client_ready_ev.clear()
        if client.error_code != '':
            print(client.error_code)
            continue

        client.reqHistoricalData(
            20, contract, end_date_time, '13 W', '1 day', what_to_show_trades, True, 1, False, []
        )
        while not client_ready_ev.wait():
            pass
        client_ready_ev.clear()
        if client.error_code != '':
            print(client.error_code)
            continue

        client.reqHistoricalData(
            30, contract, end_date_time, '13 W', '1 day', what_to_show_option_iv, True, 1, False, []
        )
        while not client_ready_ev.is_set():
            pass
        client_ready_ev.clear()
        if client.error_code != '':
            print(client.error_code)
            continue
        # client.reqFundamentalData(reqId=100, contract=contract, reportType='ReportSnapshot', fundamentalDataOptions=[])
        # while not client_ready_ev.is_set():
        #    pass
        # client_ready_ev.clear()
        # if client.error_code != '':
        #    print(client.error_code)
        #    continue
        client.underlying_dict['Name'] = row.Name
        client.underlying_dict['Market Cap'] = row.MarketCap #f'${(round((float(row.MarketCap) / 1000000), 2)):,.2f}M'
        print(client.underlying_dict)
        client.underlying_list.append(client.underlying_dict.copy())

    #for underlying in client.underlying_list:
    #    print(underlying)

    df_underlying: pd.DataFrame = pd.DataFrame.from_records(client.underlying_list).drop(['Price Weeks High 13W',
                                                                                          'Price Weeks Low 13W',
                                                                                          'IV Weeks High 13W',
                                                                                          'IV Weeks Low 13W',
                                                                                          'Price Weeks High 52W',
                                                                                          'Price Weeks Low 52W',
                                                                                          'IV Weeks High 52W',
                                                                                          'IV Weeks Low 52W',
                                                                                          ], axis=1)
    client.disconnect()
    while not client_thread.is_alive():
        pass

    return df_underlying

def main() -> None:
    # logging.basicConfig(filename='twsapp.log', level=logging.DEBUG)
    parser = ap.ArgumentParser(description='Provide list of csv files with minimum columns Symbol=Ticker Symbol'
                                                 'Name= Company name and Market Cap ')
    parser.add_argument('csv_files',
                        nargs='*',
                        type=str,
                        help='List of CSV files')
    parser.add_argument('--column',
                        type=str,
                        choices=['Symbol', 'Name', 'Current Price', 'Current IV', 'SMA200', 'SMA50',
                                'Price Percentile 13W', 'Price Percentile 52W', 'Price Rank 13W',
                                'Price Rank 52W', 'Price Change 13W', 'Price Change 52W', 'IV Percentile 13W',
                                'IV Percentile 52W', 'IV Rank 13W', 'IV Rank 52W', 'Market Cap'],
                        default='Symbol',
                        help='''Provide column to sort. Default=Symbol. Possible Values:
                                "Symbol", "Name", "Current Price", "Current IV", "SMA200", "SMA50",
                                "Price Percentile 13W", "Price Percentile 52W", "Price Rank 13W",
                                "Price Rank 52W", "Price Change 13W", "Price Change 52W", "IV Percentile 13W",
                                "IV Percentile 52W", "IV Rank 13W", "IV Rank 52W", "Market Cap" ''',
                        )
    parser.add_argument('--ascending',
                        action='store_true',
                        help='''Order column ascending or descending. Possible values: True(=Ascending), False(=Descending).
                                Default=True''')
    parser.add_argument('--min_price',
                        type=float,
                        default=40.0,
                        help='Store results for stocks with current price greater than min_price in USD. Default $40.')
    parser.add_argument('--max_price',
                        type=float,
                        default=1000.0,
                        help='Store results for stocks with current price smaller than max_price in USD. Default $1000.')
    parser.add_argument('--above_sma200',
                        action='store_true',
                        help='''Store results for stocks with current price greater than than SMA200.
                                Possible values: True(=ignore stocks below SMA200), False(=consider all stocks). Default=True''')
    parser.add_argument('--above_sma50',
                        action='store_false',
                        help='''Store results for stocks with current price greater than than SMA50.
                                Possible values: True(=ignore stocks below SMA200), False(=consider all stocks). Default=False''')
    parser.add_argument('--min_iv',
                        type=float,
                        default=40.0,
                        help='Store results for stocks with current IV greater than than min_iv. Default=40')
    parser.add_argument('--min_market_cap',
                        type=float,
                        default=0.0,
                        help='Store results for stocks with Market Cap greater than min_market_cap. Default=0')
    args = parser.parse_args()

    if not len(args.csv_files):
        print('Error: No CSV file provided')
    else:
        try:
            df_input_list: list[pd.DataFrame] = [pd.read_csv(file) for file in args.csv_files]
            df_input: pd.DataFrame = pd.concat(df_input_list)
            df_input.columns = df_input.columns.str.replace(' ','')
            df_input_sorted: pd.DataFrame = df_input.sort_values('Symbol')

            end_date_time: str = f'{datetime.now(timezone('US/Eastern')).__str__().split('.')[0]} US/Eastern'
            end_date_time = end_date_time.replace('-','')
            print(f'Get data at {end_date_time}')
            df_underlying: pd.DataFrame = execute_tws_app(df_input=df_input_sorted,
                                                          end_date_time=end_date_time,
                                                          ascending= args.ascending,
                                                          min_price=args.min_price,
                                                          max_price=args.max_price,
                                                          above_sma200=args.above_sma200,
                                                          above_sma50=args.above_sma50,
                                                          min_iv=args.min_iv,
                                                          min_market_cap=args.min_market_cap)
            df_underlying_sorted: pd.DataFrame = df_underlying.sort_values(by=args.column,
                          key=lambda x: np.argsort(index_natsorted(df_underlying[args.column])),
                          ascending=(not args.ascending))
            df_underlying_sorted.to_csv('result.csv')
        except Exception as error:
            print(error)

if __name__ == '__main__':
    now = time.time()
    main()
    end = time.time()
    print(f'Total time: {(end - now):.2f} seconds')
