from ibapi.client import EClient,Contract
import time

from tws_client import TwsClient
from defines import *

if __name__ == '__main__':
    client = TwsClient(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    time.sleep(1)
    contract = Contract()
    contract.symbol = 'TSLA'
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    what_to_show = 'Trades'
    client.reqMktData(reqId=3,
                      contract=contract,
                      genericTickList='258, 411',
                      snapshot=False,
                      regulatorySnapshot=False,
                      mktDataOptions=[])