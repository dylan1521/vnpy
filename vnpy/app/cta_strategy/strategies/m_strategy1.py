from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from datetime import datetime as dt
from loguru import logger
import numpy as np


class MStragety1(CtaTemplate):
    author = "mc"

    fast_window = 10
    slow_window = 20

    fast_ma0 = 0.0
    fast_ma1 = 0.0

    slow_ma0 = 0.0
    slow_ma1 = 0.0
    count = 0
    signal_count = 99999999
    last_trade_price = 0
    parameters = ["fast_window", "slow_window"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        self.close_time = "1450"  # 下午1450之后平仓
        self.open_time = "0900"  # 早上9点开始交易，只做白盘

    def trade_status(self, bar):
        if bar.datetime.time().strftime("%H%M") > self.close_time:
            return "end"
        elif bar.datetime.time().strftime("%H%M") > self.open_time:
            return "start"
        else:
            return "hold"

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.count += 1
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        trade_status = self.trade_status(bar)
        if trade_status == "end" and self.pos>0:
            self.cut(bar.close_price, self.pos)
        if trade_status == "hold":
            if self.pos != 0:
                logger.warning("夜盘持仓，仓位为{}".format(self.pos))
                self.cut(bar.close_price, self.pos)
        if trade_status == "start":
            high = am.high
            low = am.low
            low_diff1 = low[-2] - low[-3]
            low_diff2 = low[-2] - low[-1]
            high_diff1 = high[-2] - high[-3]
            high_diff2 = high[-2] - high[-1]

            ema_20 = am.ema(20, array=True)[-1]

            long_signal = low_diff1 < 0 and low_diff2 < 0 and high_diff1 < 0 and high_diff2 < 0 and bar.close_price > ema_20
            short_signal = low_diff1 > 0 and low_diff2 > 0 and high_diff1 > 0 and high_diff2 > 0 and bar.close_price < ema_20

            if long_signal:
                self.signal_count = self.count
                if self.pos == 0:
                    self.buy(bar.close_price, 1)
                elif self.pos < 0:
                    self.cover(bar.close_price, self.pos)
                    self.buy(bar.close_price, 1)
                self.last_trade_price = bar.close_price
            elif short_signal:
                self.signal_count = self.count
                if self.pos == 0:
                    self.short(bar.close_price, 1)
                elif self.pos > 0:
                    self.sell(bar.close_price, self.pos)
                    self.short(bar.close_price, 1)
                self.last_trade_price = bar.close_price
            else:
                if self.pos > 0:
                    ret = bar.close_price - self.last_trade_price
                    if ret >= 10:
                        self.cut(bar.close_price, self.pos)
                    elif ret <= -5:
                        self.cut(bar.close_price, self.pos)
                    # 2分钟未盈利，止损
                    if self.count - self.signal_count >= 2:
                        if bar.close_price <= self.last_trade_price:
                            self.cut(bar.close_price, self.pos)
        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
