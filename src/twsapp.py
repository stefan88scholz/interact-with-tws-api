import logging
from defines import DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID
import time
from threading import Thread
from tws_client import *
import datetime
import pandas as pd
import argparse as ap

client_ready_ev: Event = Event()

def execute_tws_app(df_input: pd.DataFrame, end_date_time: str) -> None:
    client: TwsClient = TwsClient(client_ready_ev)
    client.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    client_thread: Thread = Thread(target=client.run)
    client_thread.start()
    time.sleep(1)

    contract = Contract()
    df_input2: pd.DataFrame = pd.DataFrame(
        data={'Symbol': ['AMD', 'CEG'],
              'Name': ['Advanced Micro Devices Inc. Common Stock', 'Constellation Energy Corporation Common Stock '],
              'MarketCap': ['272248257267.00', '96895.71']}
    )
    for row in df_input.itertuples():
        contract.symbol = row.Symbol
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        what_to_show_trades = 'Trades'
        what_to_show_option_iv = 'OPTION_IMPLIED_VOLATILITY'

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
        client.underlying_dict['Market Cap'] = f'${(round((float(row.MarketCap) / 1000000), 2)):,.2f}M'
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
    df_underlying.to_csv('result.csv')

    client.disconnect()
    while not client_thread.is_alive():
        pass

def main() -> None:
    # logging.basicConfig(filename='twsapp.log', level=logging.DEBUG)
    parser = ap.ArgumentParser(description='Provide list of csv files with minimum columns Symbol=Ticker Symbol'
                                                 'Name= Company name and Market Cap ')
    parser.add_argument('csv_files', nargs='*', type=str, help='List of CSV files')
    args = parser.parse_args()

    if not len(args.csv_files):
        print('Error: No CSV file provided')
    else:
        try:
            df_input_list: list[pd.DataFrame] = [pd.read_csv(file) for file in args.csv_files]
            df_input: pd.DataFrame = pd.concat(df_input_list)
            df_input.columns = df_input.columns.str.replace(' ','')
            df_input_sorted: pd.DataFrame = df_input.sort_values('Symbol')

            yesterday: datetime.date = datetime.date.today() - datetime.timedelta(days=1)
            end_date_time: str = f'{yesterday.__str__().replace('-', '')} 15:59:00 US/Eastern'

            execute_tws_app(df_input_sorted, end_date_time)
        except Exception as error:
            print(error)

if __name__ == '__main__':
    now = time.time()
    main()
    end = time.time()
    print(f'Total time: {end - now} seconds')
