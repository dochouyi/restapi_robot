from freqtrade_client import FtRestClient
import time
from typing import Optional

class FreqtradeClient(FtRestClient):
    def __init__(self, serverurl="http://127.0.0.1:8090", username="freqtrader", password="123456"):
        super().__init__(serverurl, username=username, password=password)

    def force_enter_order(self, pair, side="long", price=None, order_type="limit", stake_amount=None, leverage=1):
        """
        强制进入交易函数
        """
        result = self.forceenter(
            pair=pair,
            side=side,
            price=price,
            order_type=order_type,
            stake_amount=stake_amount,
            enter_tag="force_entry",
            leverage=leverage
        )
        print(f"强制进入 {pair} ({side}) 的结果:", result)
        return result

    def force_exit_order(self, order_type="limit", amount=None):
        """
        强制退出交易
        """
        trade_id = self.get_current_open_trade_id()
        result = self.forceexit(trade_id, ordertype=order_type, amount=amount)
        print(f"退出交易 {trade_id} 的结果:", result)
        return result

    def cancel_latest_open_order(self):
        """取消未成交订单"""
        trade_id = self.get_current_open_trade_id()
        result = self.cancel_open_order(trade_id)
        print(f"取消订单 {trade_id} 的结果:", result)
        return result

    # 返回当前开放 trade 的 trade id
    def get_current_open_trade_id(self):
        current_trade = self.status()[0]  # 系统默认只能有一个 open trade，并且一定是 open 的状态
        return current_trade['trade_id']

    # 获取当前开放 trade 的最近的一次 order 对象
    def get_latest_order(self):
        current_trade = self.trade(self.get_current_open_trade_id())
        current_order = max(current_trade['orders'], key=lambda order: order['order_timestamp'])
        return current_order

    # true 表示还没有成交；false 表示已经成交
    def is_latest_order_open(self):
        order = self.get_latest_order()
        state = order['is_open']
        if state:
            print("没有成交")
        else:
            print("已经成交")
        return state


if __name__ == "__main__":
    pair = 'BTC/USDT:USDT'

    client=FreqtradeClient()

    l=client.locks()
    print(l)



    # client.force_enter_order(pair,stake_amount=1000)
    #
    client.cancel_latest_open_order()
    # result=client.is_latest_order_open()

    client.force_exit_order(order_type="market",)


