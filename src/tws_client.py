from defines import *

from ibapi.client import EClient, Contract
from ibapi.contract import ContractDetails
from ibapi.utils import current_fn_name
from ibapi.wrapper import EWrapper, BarData
from ibapi.common import TickerId, TickAttrib, TagValueList, WshEventData
from ibapi.ticktype import TickTypeEnum, TickType
from threading import Event
import queue
from decimal import Decimal
from typing import Any, TypedDict
import re

FLOAT_UNSET = float(-1.0)

Underlying = TypedDict('Underlying',{'symbol': str,
                                     'current_price': float,
                                     'sma_200': float,
                                     'sma_50': float,
                                     'current_iv': float,
                                     'price_percentile_13': float,
                                     'price_percentile_52': float,
                                     'price_rank_13': float,
                                     'price_rank_52': float,
                                     'price_change_13': float,
                                     'price_change_52': float,
                                     'iv_percentile_13': float,
                                     'iv_percentile_52': float,
                                     'iv_rank_13': float,
                                     'iv_rank_52': float,
                                     'price_weeks_high_13': float,
                                     'price_weeks_high_52': float,
                                     'price_weeks_low_13': float,
                                     'price_weeks_low_52': float,
                                     'iv_weeks_high_13': float,
                                     'iv_weeks_high_52': float,
                                     'iv_weeks_low_13': float,
                                     'iv_weeks_low_52': float,
                                     'last_financial_data': str,
                                     }
                       )

class TwsClient(EWrapper, EClient):
    def __init__(self, event: Event):
        EClient.__init__(self,self)
        self.data_queue = queue.Queue()
        self.event = event
        self.error_code = ''
        self.weeks_high: float = FLOAT_UNSET
        self.weeks_low: float = FLOAT_UNSET
        self.percentile: float = FLOAT_UNSET
        self.rank: float = FLOAT_UNSET
        self.what_to_show: str = ''
        self.duration_str: str = ''
        # An asset's closing price. The last level at which it was traded on any given day
        self.close_list: list[float] = list()
        self.underlying_symbol: str = ''
        self.underlying_dict: Underlying = {'symbol': 'na',
                                            'current_price': FLOAT_UNSET,
                                            'current_iv': FLOAT_UNSET,
                                            'sma_200': FLOAT_UNSET,
                                            'sma_50': FLOAT_UNSET,
                                            'price_percentile_13': FLOAT_UNSET,
                                            'price_percentile_52': FLOAT_UNSET,
                                            'price_rank_13': FLOAT_UNSET,
                                            'price_rank_52': FLOAT_UNSET,
                                            'price_change_13': FLOAT_UNSET,
                                            'price_change_52': FLOAT_UNSET,
                                            'iv_percentile_13': FLOAT_UNSET,
                                            'iv_percentile_52': FLOAT_UNSET,
                                            'iv_rank_13': FLOAT_UNSET,
                                            'iv_rank_52': FLOAT_UNSET,
                                            'price_weeks_high_13': FLOAT_UNSET,
                                            'price_weeks_high_52': FLOAT_UNSET,
                                            'price_weeks_low_13': FLOAT_UNSET,
                                            'price_weeks_low_52': FLOAT_UNSET,
                                            'iv_weeks_high_13': FLOAT_UNSET,
                                            'iv_weeks_high_52': FLOAT_UNSET,
                                            'iv_weeks_low_13': FLOAT_UNSET,
                                            'iv_weeks_low_52': FLOAT_UNSET,
                                            'last_financial_data': ''
                                            }
        self.underlying_list: list[Underlying] = list()

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
            self.error_code = f'{reqId = }; Error {errorCode}: {self.underlying_dict['symbol']}; {errorString}'
            self.event.set()


    def reqHistoricalData(
        self,
        reqId: TickerId,
        contract: Contract,
        endDateTime: str,
        durationStr: str,
        barSizeSetting: str,
        whatToShow: str,
        useRTH: int,
        formatDate: int,
        keepUpToDate: bool,
        chartOptions: TagValueList,
    ) -> Any:
        self.error_code = ''
        self.what_to_show = whatToShow
        self.duration_str = durationStr
        self.weeks_low = FLOAT_UNSET
        self.weeks_high = FLOAT_UNSET
        self.close_list.clear()
        self.underlying_dict['symbol'] = contract.symbol
        
        super().reqHistoricalData(reqId,
                                  contract,
                                  endDateTime,
                                  durationStr,
                                  barSizeSetting,
                                  whatToShow,
                                  useRTH,
                                  formatDate,
                                  keepUpToDate,
                                  chartOptions
                                  )

    def historicalData(self, req_id, bar: BarData):
        """returns the requested historical data bars"""

        self.close_list.insert(0,bar.close)
        if self.weeks_low == FLOAT_UNSET:
            self.weeks_low = bar.low
        elif self.weeks_low > bar.low:
            self.weeks_low = bar.low

        if self.weeks_high == FLOAT_UNSET:
            self.weeks_high = bar.high
        elif self.weeks_high < bar.high:
            self.weeks_high = bar.high


        #t = datetime.datetime.fromtimestamp(int(bar.date))

        # Create bar dictionary for each bar received
        # data = {
        #     'date': t,
        #     'open': bar.open,
        #     'high': bar.high,
        #     'low': bar.low,
        #     'close': bar.close,
        #     'volume': int(bar.volume)
        # }
        #print(data)
        # Put the data into the queue
        #self.data_queue.put(data)

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """ Callback when all historical data has been received """
        #print(f'end of data {reqId}; {start}; {end}')
        #print(f'Number of values: {len(self.close_list)}')
        #print(f'Highest value: {self.weeks_high}')
        #print(f'Lowest value: {self.weeks_low}')
        last_closing: float = self.close_list[0]
        #print(f'Last closing: {last_closing}')
        count_lower_last_closing: int = sum(1 for x in self.close_list if x < last_closing)
        self.percentile = (count_lower_last_closing / len(self.close_list) * 100)
        self.rank = ((last_closing - self.weeks_low) / (self.weeks_high - self.weeks_low)) * 100
        #print(f'Stock price percentile: {self.percentile:.2f}%')
        #print(f'Stock price rank: {self.rank:.2f} ')

        if self.duration_str == '52 W':
            if self.what_to_show == 'Trades':
                self.underlying_dict['current_price'] = self.close_list[0]
                self.underlying_dict['price_weeks_high_52'] = round(self.weeks_high,2)
                self.underlying_dict['price_weeks_low_52'] = round(self.weeks_low,2)
                self.underlying_dict['price_percentile_52'] = round(self.percentile,2)
                self.underlying_dict['price_rank_52'] = round(self.rank,2)
                self.underlying_dict['price_change_52'] = round(((self.close_list[0] / self.close_list[-1]) - 1) * 100,2)
                #Calculate SMA 200 and SMA 50
                self.underlying_dict['sma_200'] = round(sum([price for idx,price in enumerate(self.close_list) if idx < 200]) / 200,2)
                self.underlying_dict['sma_50'] = round(sum([price for idx,price in enumerate(self.close_list) if idx < 50]) / 50,2)

                cur_price = self.underlying_dict['current_price']
                if cur_price <= 40:
                    self.error_code = f'{self.underlying_dict['symbol']}: Current price under 40 US Dollar'
                elif cur_price >= 1000:
                    self.error_code = f'{self.underlying_dict['symbol']}: Current price above 1000 US Dollar'
                elif cur_price < self.underlying_dict['sma_200']:
                    self.error_code = f'{self.underlying_dict['symbol']}: Current price below SMA 200'

            elif self.what_to_show == 'OPTION_IMPLIED_VOLATILITY':
                self.underlying_dict['current_iv'] = round(self.close_list[0],2) * 100
                self.underlying_dict['iv_weeks_high_52'] = round(self.weeks_high,2) * 100
                self.underlying_dict['iv_weeks_low_52'] = round(self.weeks_low,2) * 100
                self.underlying_dict['iv_percentile_52'] = round(self.percentile,2)
                self.underlying_dict['iv_rank_52'] = round(self.rank,2)
                
                cur_iv = self.underlying_dict['current_iv']
                if cur_iv < 40.0:
                    self.error_code = f'{self.underlying_dict['symbol']}: IV under 40'

        elif self.duration_str == '13 W':
            if self.what_to_show == 'Trades':
                self.underlying_dict['price_weeks_high_13'] = round(self.weeks_high,2)
                self.underlying_dict['price_weeks_low_13'] = round(self.weeks_low,2)
                self.underlying_dict['price_percentile_13'] = round(self.percentile,2)
                self.underlying_dict['price_rank_13'] = round(self.rank,2)
                self.underlying_dict['price_change_13'] = round(((self.close_list[0] / self.close_list[-1]) - 1) * 100,2)
            elif self.what_to_show == 'OPTION_IMPLIED_VOLATILITY':
                self.underlying_dict['iv_weeks_high_13'] = round(self.weeks_high,2) * 100
                self.underlying_dict['iv_weeks_low_13'] = round(self.weeks_low,2) * 100
                self.underlying_dict['iv_percentile_13'] = round(self.percentile,2)
                self.underlying_dict['iv_rank_13'] = round(self.rank,2)

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
        super().fundamentalData(reqId,data)
        #print(f'Function name: {current_fn_name()}')
        #print(f'reqId: {reqId}')
        #print(f'data: {data}')
        self.underlying_dict['last_financial_data'] = re.findall(r'"Financial Summary"\slastModified="([0-9-]+)', data)[0]
        print(f'Function name: {current_fn_name()}')
        print(f'reqId: {reqId}')
        self.event.set()

    def wshMetaData(self, reqId: int, dataJson: str) -> None:
        super().wshMetaData(reqId, dataJson)
        print(f'{reqId}' + f'{dataJson}',sep=';')
        self.event.set()

    def wshEventData(self, reqId: int, dataJson: str) -> None:
        super().wshEventData(reqId, dataJson)
        print(f'{reqId}' + f'{dataJson}',sep=';')
        self.event.set()
