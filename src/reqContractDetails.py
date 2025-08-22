from ibapi.client import EClient,Contract
import time
from tws_client import TwsClient
from defines import *
from threading import Thread, Event

req_finished = Event()

if __name__ == '__main__':
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
    client.reqContractDetails(reqId=4,contract=contract)