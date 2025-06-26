import logging
import threading
import time
from threading import Thread, Event
from lightweight_charts import Chart

from defines import *
from tws_client import *

req_finished = Event()

if __name__ == '__main__':
    # logging.basicConfig(filename='twsapp.log', level=logging.DEBUG)
    now = time.time()
    client = TwsClient(req_finished)
    client.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    cl_thread = Thread(target=client.run)
    cl_thread.start()
    time.sleep(1)
    contract = Contract()
    contract.symbol = 'AMD'
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    what_to_show = 'Trades'
    #what_to_show = 'OPTION_IMPLIED_VOLATILITY'

    client.reqHistoricalData(
        2, contract, '20250618 15:59:00 US/Eastern', '52 W', '1 day', what_to_show, True, 1, False, []
    )
    while not req_finished.is_set():
        pass
    print(f'Request historical data finished')
    client.disconnect()
    print(f'{cl_thread.is_alive()}')
    while not cl_thread.is_alive():
        pass
    print(f'{cl_thread.is_alive()}')
    print(f'Main thread finished')
    end = time.time()
    print(f'Total time: {end-now}')
