from ibapi.client import EClient,Contract
import time
from threading import Thread, Event
from tws_client import TwsClient
from defines import *
from ibapi.scanner import ScannerSubscription
from ibapi.tag_value import TagValue

client_ready_ev: Event = Event()

if __name__ == '__main__':
    client = TwsClient(client_ready_ev)
    client.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    client_thread = Thread(target=client.run)
    client_thread.start()
    time.sleep(1)
    contract = Contract()
    contract.symbol = 'AMD'
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    what_to_show = 'Trades'

    subsc: ScannerSubscription = ScannerSubscription()
    subsc.instrument = 'STK'
    subsc.locationCode = 'STK.US.MAJOR'
    subsc.scanCode = 'WSH_NEXT_MAJOR_EVENT'
    scanner_options = []
    filter_options = [
        #TagValue('impVolatAbove','40'),
        TagValue('priceAbove','40'),
        TagValue('priceBelow','1000')
    ]
    client.reqScannerSubscription(reqId=3,
                                  subscription=subsc,
                                  scannerSubscriptionOptions=scanner_options,
                                  scannerSubscriptionFilterOptions=filter_options
                                  )
    #client.reqScannerParameters()
    while not client_ready_ev.wait():
        pass
    print(client.error_code)
    client_ready_ev.clear()
    client.disconnect()
    while not client_thread.is_alive():
        pass
    print(f'Main thread finished')