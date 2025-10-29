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


def place_limit_then_market_entry(client: FreqtradeClient, pair: str, stake_amount: float, wait_seconds: int = 2):
    """
    先限价入场，等待 wait_seconds，如未成交则撤销并用市价入场。
    """
    side = "long"

    client.force_enter_order(pair=pair, side=side, order_type="market", stake_amount=stake_amount, leverage=1)

    # # 1) 限价入场
    # client.force_enter_order(pair=pair, side=side, order_type="limit", stake_amount=stake_amount, leverage=1)
    #
    # # 2) 等待成交
    time.sleep(wait_seconds)
    #
    # # 3) 检查是否成交
    # if client.is_latest_order_open():
    #     # 未成交则撤单并用市价入场
    #     client.cancel_latest_open_order()
    #     client.force_enter_order(pair=pair, side=side, order_type="market", stake_amount=stake_amount, leverage=1)
    # else:
    #     print("限价入场已成交。")



def place_limit_then_market_exit_10_percent(client: FreqtradeClient, pair: str, wait_seconds: int = 10):
    """
    先限价出场 10% 仓位，等待 wait_seconds，如未成交则撤销并用市价出场。
    注意：force_exit_order 的 amount 语义需与你的 API 保持一致（此处假设为币的数量）。
    """

    total_amount = client.trade(client.get_current_open_trade_id())['amount']

    exit_amount = round(total_amount * 0.10, 0)

    client.force_exit_order(order_type="limit", amount=exit_amount)

    # 2) 等待成交
    time.sleep(wait_seconds)

    if client.is_latest_order_open():
        # 未成交则撤单并用市价出场
        client.cancel_latest_open_order()
        client.force_exit_order(order_type="market", amount=exit_amount)
    else:
        print("限价出场已成交。")



def run_sequence(client: FreqtradeClient, pair: str):
    """
    依次入场 10 次，每次 200 金额；然后依次出场 10 次，每次 10% 仓位。
    每次都先限价，10 秒未成交则改市价。
    """
    # 入场 10 次
    # for i in range(20):
    #     print(f"第 {i+1} 次入场开始")
    #     place_limit_then_market_entry(client, pair=pair, stake_amount=1000, wait_seconds=10)
    #     print(f"第 {i+1} 次入场结束")
        # 可根据需要在连续入场之间短暂等待，防止触发频率限制

    # 出场 10 次
    for j in range(10):
        print(f"第 {j+1} 次出场开始")
        place_limit_then_market_exit_10_percent(client, pair=pair, wait_seconds=3)
        print(f"第 {j+1} 次出场结束")



if __name__ == "__main__":
    pair = 'BTC/USDT:USDT'
    client = FreqtradeClient()
    # client.get_current_open_trade_id()

    run_sequence(client, pair)
