from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.strategies.m_strategy1 import (
    MStragety1,
)
from datetime import datetime

engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="CU88.SHFE",
    interval="1m",
    start=datetime(2019, 1, 1),
    end=datetime(2019, 4, 30),
    rate=0.3 / 10000,
    slippage=0.2,
    size=300,
    pricetick=0.2,
    capital=1_000_000,
)

engine.add_strategy(MStragety1, {})

engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()

