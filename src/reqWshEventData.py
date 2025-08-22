from ibapi.client import WshEventData
import time
from tws_client import TwsClient
from threading import Thread, Event
from defines import *

client_ready_ev = Event()

if __name__ == '__main__':
    client = TwsClient(client_ready_ev)
    client.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    cl_thread = Thread(target=client.run)
    cl_thread.start()
    time.sleep(1)
    wsh_event_data: WshEventData = WshEventData()
    wsh_event_data.conId = 'AMD'
    wsh_event_data.startDate = '20250101'
    wsh_event_data.endDate = '20250820'
    wsh_event_data.fillCompetitors = True
    wsh_event_data.fillWatchlist = True
    wsh_event_data.fillPortfolio = True
    client.reqWshMetaData(reqId=5)
    while not client_ready_ev.wait():
        pass
    client_ready_ev.clear()
    client.reqWshMetaData(1100)
    while not client_ready_ev.wait():
        pass
    client_ready_ev.clear()
    client.reqWshEventData(reqId=1100,wshEventData=wsh_event_data)
    while not client_ready_ev.wait():
        pass
    client_ready_ev.clear()
    print(f'Main thread finished')