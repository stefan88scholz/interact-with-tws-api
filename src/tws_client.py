from defines import *

from ibapi.client import EClient, Contract
from ibapi.contract import ContractDetails
from ibapi.utils import current_fn_name
from ibapi.wrapper import EWrapper
from ibapi.common import TickerId, TickAttrib
from ibapi.ticktype import TickTypeEnum, TickType
from threading import Event
import time, datetime
import queue
import pandas as pd
from decimal import Decimal



class TwsClient(EWrapper, EClient):
    def __init__(self, event: Event):
        EClient.__init__(self,self)
        self.data_queue = queue.Queue()
        self.event = event
        self.fifthytwo_weeks_high = float(SHARE_PRICE_UNSET)
        self.fifthytwo_weeks_low = float(SHARE_PRICE_UNSET)
        self.price_percentile_fifthytwo = 0.0
        self.price_rank_fifthytwo = 0.0
        self.what_to_show = ''
        self.bar_close = list()

    def error(
            self,
            reqId: TickerId,
            errorTime: int,
            errorCode: int,
            errorString: str,
            advancedOrderRejectJson="",
    ):
        if errorCode in [2104, 2106, 2158]:
            print(errorString)
        else:
            print(f'Error {errorCode}: {errorString}')

    def historicalData(self, req_id, bar):
        """returns the requested historical data bars"""
        #print(bar)
        self.bar_close.append(bar.close)
        if float(self.fifthytwo_weeks_low).__eq__(SHARE_PRICE_UNSET):
            self.fifthytwo_weeks_low = bar.low
        elif float(self.fifthytwo_weeks_low).__gt__(bar.low):
            self.fifthytwo_weeks_low = bar.low

        if float(self.fifthytwo_weeks_high).__eq__(SHARE_PRICE_UNSET):
            self.fifthytwo_weeks_high = bar.high
        elif float(self.fifthytwo_weeks_high).__lt__(bar.high):
            self.fifthytwo_weeks_high = bar.high


        t = datetime.datetime.fromtimestamp(int(bar.date))

        # Create bar dictionary for each bar received
        data = {
            'date': t,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': int(bar.volume)
        }
        #print(data)
        # Put the data into the queue
        self.data_queue.put(data)

    def historicalDataEnd(self, req_id, start, end):
        """ Callback when all historical data has been received """
        print(f'end of data {start} {end}')
        print(f'Highest value: {self.fifthytwo_weeks_high}')
        print(f'Lowest value: {self.fifthytwo_weeks_low}')
        last_value = self.bar_close[-1]
        print(f'Last Value {last_value}')
        count = sum(1 for x in self.bar_close if x < last_value)
        self.price_percentile_fifthytwo = (count / len(self.bar_close) * 100)
        self.price_rank_fifthytwo = ((last_value - self.fifthytwo_weeks_low) / (self.fifthytwo_weeks_high - self.fifthytwo_weeks_low)) * 100
        print(f'Stock price percentile: {self.price_percentile_fifthytwo}%')
        print(f'Stock price rank: {self.price_rank_fifthytwo}%')
        self.event.set()

    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        print(f'reqId: {reqId}, tickType: {tickType}, value: {value}')

    def tickSize(self, reqId: TickerId, tickType: TickType, size: Decimal):
        print(f'reqId: {reqId}, tickType: {tickType}, size: {size}')

    def tickPrice(
            self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib
    ):
        print(f'reqId: {reqId}, tickType: {tickType}, price: {price}, attrib: {attrib}')

    def tickGeneric(self, reqId: TickerId, tickType: TickType, value: float):
        print(f'reqId: {reqId}, tickType: {tickType}, value: {value}')

    def tickOptionComputation(self,
        reqId: TickerId,
        tickType: TickType,
        tickAttrib: int,
        impliedVol: float,
        delta: float,
        optPrice: float,
        pvDividend: float,
        gamma: float,
        vega: float,
        theta: float,
        undPrice: float
    ):
        print(f'reqId: {reqId}, tickType: {tickType}, tickAttrib: {tickAttrib},'
              f'impliedVol: {impliedVol}, delta: {delta}, optPrice: {optPrice},'
              f'pvDividend: {pvDividend}, gamma: {gamma}, vega: {vega},'
              f'theta: {theta}, undPrice: {undPrice}')

    def contractDetailsEnd(self, reqId: int):
        print(f'Function name: {current_fn_name()}')
        print(f'Parameter: reqId={reqId}')

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        print(f'Function name: {current_fn_name()}')
        print(f'Parameter: reqId={reqId}, contractDetails={contractDetails.__str__()}')
        print(f'marketName={contractDetails.marketName}')
        print(f'minTick={contractDetails.minTick}')
        print(f'orderTypes={contractDetails.validExchanges}')
        print(f'priceMagnifier={contractDetails.priceMagnifier}')
        print(f'underConId={contractDetails.underConId}')
        print(f'longName={contractDetails.longName}')
        print(f'contractMonth={contractDetails.contractMonth}')
        print(f'industry={contractDetails.industry}')
        print(f'category={contractDetails.category}')
        print(f'subcategory={contractDetails.subcategory}')
        print(f'timeZoneId={contractDetails.timeZoneId}')
        print(f'tradingHours={contractDetails.tradingHours}')
        print(f'liquidHours={contractDetails.liquidHours}')
        print(f'evRule={contractDetails.evRule}')
        print(f'evMultiplier={contractDetails.evMultiplier}')
        print(f'underSymbol={contractDetails.underSymbol}')
        print(f'underSecType={contractDetails.underSecType}')
        print(f'marketRuleIds={contractDetails.marketRuleIds}')
        print(f'aggGroup={contractDetails.aggGroup}')
        print(f'secIdList={contractDetails.secIdList}')
        print(f'realExpirationDate={contractDetails.realExpirationDate}')
        print(f'stockType={contractDetails.stockType}')
        print(f'cusip={contractDetails.cusip}')
        print(f'ratings={contractDetails.ratings}')
        print(f'descAppend={contractDetails.descAppend}')
        print(f'bondType={contractDetails.bondType}')
        print(f'couponType={contractDetails.couponType}')
        print(f'callable={contractDetails.callable}')
        print(f'putable={contractDetails.putable}')
        print(f'coupon={contractDetails.coupon}')
        print(f'convertible={contractDetails.convertible}')
        print(f'maturity={contractDetails.maturity}')
        print(f'issueDate={contractDetails.issueDate}')
        print(f'nextOptionDate={contractDetails.nextOptionDate}')
        print(f'nextOptionType={contractDetails.nextOptionType}')
        print(f'nextOptionPartial={contractDetails.nextOptionPartial}')
        print(f'notes={contractDetails.notes}')
        print(f'minSize={contractDetails.minSize}')
        print(f'sizeIncrement={contractDetails.sizeIncrement}')
        print(f'suggestedSizeIncrement={contractDetails.suggestedSizeIncrement}')
        print(f'ineligibilityReasonList={contractDetails.ineligibilityReasonList}')

    def fundamentalData(self, reqId: TickerId, data: str):
        print(f'Function name: {current_fn_name()}')
        print(f'reqId: {reqId}')
        print(f'data: {data}')