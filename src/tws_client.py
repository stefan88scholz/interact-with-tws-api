from ibapi.client import EClient, Contract
from ibapi.contract import ContractDetails
from ibapi.utils import current_fn_name
from ibapi.wrapper import EWrapper, BarData
from ibapi.common import TickerId, TickAttrib, TagValueList, WshEventData
from ibapi.ticktype import TickType
from threading import Event
import queue
from decimal import Decimal
from typing import Any, TypedDict
import re

FLOAT_UNSET = float(-1.0)

Underlying = TypedDict('Underlying',{'Symbol': str,
                                     'Name': str,
                                     'Current Price': str,
                                     'SMA200': str,
                                     'SMA50': str,
                                     'Current IV': str,
                                     'Price Percentile 13W': str,
                                     'Price Percentile 52W': str,
                                     'Price Rank 13W': str,
                                     'Price Rank 52W': str,
                                     'Price Change 13W': str,
                                     'Price Change 52W': str,
                                     'IV Percentile 13W': str,
                                     'IV Percentile 52W': str,
                                     'IV Rank 13W': str,
                                     'IV Rank 52W': str,
                                     'Price Weeks High 13W': str,
                                     'Price Weeks High 52W': str,
                                     'Price Weeks Low 13W': str,
                                     'Price Weeks Low 52W': str,
                                     'IV Weeks High 13W': str,
                                     'IV Weeks High 52W': str,
                                     'IV Weeks Low 13W': str,
                                     'IV Weeks Low 52W': str,
                                     'Market Cap': str,
                                     }
                       )

class TwsClient(EWrapper, EClient):
    def __init__(self,
                 event: Event,
                 ascending: bool,
                 min_price: float,
                 max_price: float,
                 above_sma200: bool,
                 above_sma50: bool,
                 min_iv: float):
        EClient.__init__(self,self)
        self.data_queue = queue.Queue()
        self.event: Event = event
        self.ascending: bool = ascending
        self.min_price: float = min_price
        self.max_price: float = max_price
        self.above_sma200: bool = above_sma200
        self.above_sma50: bool = above_sma50
        self.min_iv: float = min_iv
        self.error_code: str = ''
        self.weeks_high: float = FLOAT_UNSET
        self.weeks_low: float = FLOAT_UNSET
        self.percentile: float = FLOAT_UNSET
        self.rank: float = FLOAT_UNSET
        self.what_to_show: str = ''
        self.duration_str: str = ''
        # An asset's closing price. The last level at which it was traded on any given day
        self.close_list: list[float] = list()
        self.underlying_symbol: str = ''
        self.underlying_dict: Underlying = {'Symbol': '',
                                            'Name': '',
                                            'Current Price': '',
                                            'Current IV': '',
                                            'SMA200': '',
                                            'SMA50': '',
                                            'Price Percentile 13W': '',
                                            'Price Percentile 52W': '',
                                            'Price Rank 13W': '',
                                            'Price Rank 52W': '',
                                            'Price Change 13W': '',
                                            'Price Change 52W': '',
                                            'IV Percentile 13W': '',
                                            'IV Percentile 52W': '',
                                            'IV Rank 13W': '',
                                            'IV Rank 52W': '',
                                            'Price Weeks High 13W': '',
                                            'Price Weeks High 52W': '',
                                            'Price Weeks Low 13W': '',
                                            'Price Weeks Low 52W': '',
                                            'IV Weeks High 13W': '',
                                            'IV Weeks High 52W': '',
                                            'IV Weeks Low 13W': '',
                                            'IV Weeks Low 52W': '',
                                            'Market Cap': ''
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
            self.error_code = f'{reqId = }; Error {errorCode}: {self.underlying_dict['Symbol']}; {errorString}'
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
        self.underlying_dict['Symbol'] = contract.symbol
        
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
        self.percentile = (count_lower_last_closing / len(self.close_list))
        self.rank = ((last_closing - self.weeks_low) / (self.weeks_high - self.weeks_low)) * 100
        #print(f'Stock price percentile: {self.percentile:.2f}%')
        #print(f'Stock price rank: {self.rank:.2f} ')

        if self.duration_str == '52 W':
            if self.what_to_show == 'Trades':
                curr_price = self.close_list[0]
                self.underlying_dict['Current Price'] = f'${curr_price:.2f}'
                self.underlying_dict['Price Weeks High 52W'] = f'${round(self.weeks_high,2):.2f}'
                self.underlying_dict['Price Weeks Low 52W'] = f'${round(self.weeks_low,2):.2f}'
                self.underlying_dict['Price Percentile 52W'] = f'{round(self.percentile,2):.2%}'
                self.underlying_dict['Price Rank 52W'] = f'{round(self.rank,2):.2f}'
                self.underlying_dict['Price Change 52W'] = f'{round(((self.close_list[0] / self.close_list[-1]) - 1),2):.2%}'
                #Calculate SMA 200 and SMA 50
                sma200: float = round(sum([price for idx,price in enumerate(self.close_list) if idx < 200]) / 200,2)
                sma50: float = round(sum([price for idx,price in enumerate(self.close_list) if idx < 50]) / 50,2)
                self.underlying_dict['SMA200'] = f'${sma200:.2f}'
                self.underlying_dict['SMA50'] = f'${sma50:.2f}'

                if curr_price < self.min_price:
                    self.error_code = f'{self.underlying_dict['Symbol']}: Current price smaller than ${self.min_price}'
                elif curr_price > self.max_price:
                    self.error_code = f'{self.underlying_dict['Symbol']}: Current price greater than ${self.max_price}'
                elif self.above_sma200 and curr_price < sma200:
                    self.error_code = f'{self.underlying_dict['Symbol']}: Current price smaller than SMA 200'
                elif self.above_sma50 and curr_price < sma50:
                    self.error_code = f'{self.underlying_dict['Symbol']}: Current price smaller than SMA 200'

            elif self.what_to_show == 'OPTION_IMPLIED_VOLATILITY':
                cur_iv = round(self.close_list[0],2) * 100
                self.underlying_dict['Current IV'] = f'{cur_iv:.2f}'
                self.underlying_dict['IV Weeks High 52W'] = f'{round(self.weeks_high,2) * 100:.2f}'
                self.underlying_dict['IV Weeks Low 52W'] = f'{round(self.weeks_low,2) * 100:.2f}'
                self.underlying_dict['IV Percentile 52W'] = f'{round(self.percentile,2):.2%}'
                self.underlying_dict['IV Rank 52W'] = f'{round(self.rank,2):.2f}'

                if cur_iv < self.min_iv:
                    self.error_code = f'{self.underlying_dict['Symbol']}: IV smaller than {self.min_iv}'

        elif self.duration_str == '13 W':
            if self.what_to_show == 'Trades':
                self.underlying_dict['Price Weeks High 13W'] = f'${round(self.weeks_high,2):.2f}'
                self.underlying_dict['Price Weeks Low 13W'] = f'${round(self.weeks_low,2):.2f}'
                self.underlying_dict['Price Percentile 13W'] = f'{round(self.percentile,2):.2%}'
                self.underlying_dict['Price Rank 13W'] = f'{round(self.rank,2):.2f}'
                self.underlying_dict['Price Change 13W'] = f'{round(((self.close_list[0] / self.close_list[-1]) - 1),2):.2%}'
            elif self.what_to_show == 'OPTION_IMPLIED_VOLATILITY':
                self.underlying_dict['IV Weeks High 13W'] = f'{round(self.weeks_high,2) * 100:.2f}'
                self.underlying_dict['IV Weeks Low 13W'] = f'{round(self.weeks_low,2) * 100:.2f}'
                self.underlying_dict['IV Percentile 13W'] = f'{round(self.percentile,2):.2%}'
                self.underlying_dict['IV Rank 13W'] = f'{round(self.rank,2):.2f}'

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

    def scannerParameters(self, xml: str):
        print(f'Function name: {current_fn_name()}')
        open('scannerParam.txt', 'w',errors='backslashreplace').write(xml)
        print("Scanner parameters received!")

    def scannerDataEnd(self, reqId: int):
        print(f'Function name: {current_fn_name()}')
        print(f'{reqId = }')
        self.event.set()

    def scannerData(
        self,
        reqId: int,
        rank: int,
        contractDetails: ContractDetails,
        distance: str,
        benchmark: str,
        projection: str,
        legsStr: str,
    ):
        print(f'{reqId = }',end=';')
        print(f'{rank = }')
        print(f'{contractDetails.__str__() = }')
        print(f'{contractDetails.contract.__str__()}')
        print(f'{distance = }', end=';')
        print(f'{benchmark = }')
        print(f'{projection = }', end=';')
        print(f'{legsStr = }')