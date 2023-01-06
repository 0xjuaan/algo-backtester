# this is for development
from qfin.backtester import Algorithm, Backtester

data_folder_dir = r"C:\Users\isaac\Downloads\data"

backtester = Backtester(['AAPL', 'GOOG', 'IBM'],
                        data=data_folder_dir,  tests=20)


class ExampleAlgorithm(Algorithm):

    def __init__(self, lb):
        pass
        # self.set_indicator_params({
        #     "vol_difference": {
        #         "lookback": lb,
        #     }
        # })

    @Algorithm.indicator
    def vol_difference(data, lookback=100):
        return data['volume'].diff()

    def on_data(self, data, portfolio):

        # for _ in range(100):
        #     portfolio.buy('apple', 1, 0)

        # for _ in range(20):
        #     portfolio.sell('apple', 1, 0)
        # if 10 < 2:
        #     for i in range(100):
        #         1 + 2

        # for _ in range(5):
        #     portfolio.enter_position('long', 'apple', 10, 0)

        return


strategy = ExampleAlgorithm(50)
backtester.update_indicators(only=['volume_diff'])

results = backtester.backtest_strategy(strategy, cash=10000, fee=0.005)

print(results)

# results = backtester.backtest_straties(ExampleAlgorithm, {
#                                        'test': ['multi'], 'test2': ['multi2a', 'multi2b']}, cash=69, fee=0.005)
