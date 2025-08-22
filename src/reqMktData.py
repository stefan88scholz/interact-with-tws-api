from ibapi.client import EClient,Contract
import time
from threading import Thread, Event
from tws_client import TwsClient
from defines import *

client_ready_ev: Event = Event()

if __name__ == '__main__':
    client = TwsClient(client_ready_ev)
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
    client.reqMktData(reqId=3,
                      contract=contract,
                      genericTickList='258, 411, 165',
                      snapshot=False,
                      regulatorySnapshot=False,
                      mktDataOptions=[])