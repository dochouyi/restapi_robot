from rest_api.ft_rest_client import FtRestClient
import time
from typing import Optional

class FreqtradeClient(FtRestClient):
    def __init__(self, serverurl="http://127.0.0.1:8090", username="freqtrader", password="123456"):
        super().__init__(serverurl, username=username, password=password)
        self.current_trade_id=None
        self.current_trade_stake_amount=0
        self.previous_trade_stake_amount=0

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
        if order_type=="limit":
            # 根据结果返回订单是否成功，不意味着成交，而是订单是否有问题
            if "error" not in result:
                print("限价入场")
                self.current_trade_id=result['trade_id']
                return True
            else:
                print("限价入场失败:",result)
                return False
        else:
            # 根据结果返回订单是否成功，不意味着成交，而是订单是否有问题
            if "error" not in result:
                print("市价入场")
                self.current_trade_id=result['trade_id']
                return True
            else:
                print("市价入场订单失败:",result)
                return False

    def force_exit_order(self, order_type="limit", amount=None):
        """
        强制退出交易
        """
        result = self.forceexit(self.current_trade_id, ordertype=order_type, amount=amount)

        if order_type=="limit":
            # 根据结果返回订单是否成功，不意味着成交，而是订单是否有问题
            if "error" not in result:
                print("限价出场")
                return True
            else:
                print("限价出场订单失败:",result)
                return False
        else:
            # 根据结果返回订单是否成功，不意味着成交，而是订单是否有问题
            if "error" not in result:
                print("市价出场")
                return True
            else:
                print("市价出场订单失败:",result)
                return False

    def get_current_open_trade(self):
        current_trade = self.trade(self.current_trade_id)
        return current_trade
    def get_current_open_trade_orders(self):
        orders=self.get_current_open_trade()['orders']
        return orders


    def cancel_latest_open_order(self):
        """取消未成交开放订单"""
        result = self.cancel_open_order(self.current_trade_id)
        if "error" not in result:
            print("取消开放订单")
        else:
            print("取消开放订单失败:",result)


    # 获取当前开放 trade 的最近的一次 order 对象
    def get_latest_order(self):
        current_order = max(self.get_current_open_trade_orders(), key=lambda order: order['order_timestamp'])
        return current_order

    # true 表示还没有成交；false 表示已经成交
    def is_latest_order_open(self):
        order = self.get_latest_order()
        state = order['is_open']
        return state

    def get_free_usdt(self):
        balance = self.balance()
        usdt_free = next(item['free'] for item in balance['currencies'] if item['currency'] == 'USDT')
        print("剩余USDT金额：",usdt_free)
        return usdt_free

    def get_trade_stake_amount(self):
        current_trade_total_stake_amount = self.get_current_open_trade()['stake_amount']
        return current_trade_total_stake_amount

    def have_trade_opened(self):
        state=self.trade(trade_id=self.current_trade_id)['is_open']
        return state



def place_limit_then_market_entry_2_exchange(client_1: FreqtradeClient, client_2: FreqtradeClient, pair: str, stake_amount: float, wait_seconds: float = 2):
    """
    先限价入场，等待 wait_seconds，如未成交则撤销并用市价入场。
    """
    side_1 = "long"
    side_2 = "short"
    # 1) 限价入场
    flag_1=client_1.force_enter_order(pair=pair, side=side_1, order_type="limit", stake_amount=stake_amount, leverage=10)
    flag_2=client_2.force_enter_order(pair=pair, side=side_2, order_type="limit", stake_amount=stake_amount, leverage=10)

    if flag_1!=True:
        print("flag_1出现问题，入场失败，可能是资金量不够")
        return
    if flag_2!=True:
        print("flag_2出现问题，入场失败，可能是资金量不够")
        return
    while(True):
        # # 2) 等待成交
        time.sleep(wait_seconds)
        open_flag_1=client_1.is_latest_order_open()
        open_flag_2=client_1.is_latest_order_open()
        if open_flag_1==True and open_flag_2==True:
            continue
        elif open_flag_1==True and open_flag_2==False:
            pass
        elif open_flag_1==False and open_flag_2==True:
            pass
        elif open_flag_1==False and open_flag_2==False:
            break

    # # 3) 检查是否成交
    if client_1.is_latest_order_open():
        client.cancel_latest_open_order()
        time.sleep(0.1)
        try:
            if client.get_trade_stake_amount() == client.previous_trade_stake_amount:
                client.force_enter_order(pair=pair, side=side, order_type="market", stake_amount=stake_amount, leverage=10)
        except:
            client.force_enter_order(pair=pair, side=side, order_type="market", stake_amount=stake_amount,leverage=10)

    else:
        print("限价入场已成交。")

    client.previous_trade_stake_amount = client.get_trade_stake_amount()
    print('当前持仓：',client.previous_trade_stake_amount)

def place_limit_then_market_exit_2_exchange(client_1: FreqtradeClient, client_2: FreqtradeClient, amount: None, wait_seconds: float = 5):

    flag=client.force_exit_order(order_type="limit", amount=amount)
    if flag==True:
        # 2) 等待成交
        time.sleep(wait_seconds)
        # # 3) 检查是否成交
        if client.is_latest_order_open():
            client.cancel_latest_open_order()
            time.sleep(0.1)
            try:
                if client.get_trade_stake_amount() == client.previous_trade_stake_amount:
                    client.force_exit_order(order_type="market", amount=amount)
            except:
                client.force_exit_order(order_type="market", amount=amount)
        else:
            print("限价出场已成交。")
    else:
        print("出现问题，出场失败")
    if amount is not None:
        client.previous_trade_stake_amount = client.get_trade_stake_amount()
        print('当前持仓：',client.previous_trade_stake_amount)
    else:
        if not client.have_trade_opened():
            print('当前持仓：',0)



def run_2_exchange(client_1: FreqtradeClient, client_2: FreqtradeClient, pair: str):


    num=5
    time_seconds=0.5
    for i in range(num):
        print(f"第 {i+1} 次入场#############################")
        place_limit_then_market_entry(client, pair=pair, stake_amount=500, wait_seconds=time_seconds)




    total_amount = client.trade(client.current_trade_id)['amount']

    # 出场 10 次
    for j in range(num):
        print(f"第 {j+1} 次出场#############################")
        if j!=(num-1):
            place_limit_then_market_exit_10_percent(client, amount=total_amount/num, wait_seconds=time_seconds)
        else:
            place_limit_then_market_exit_10_percent(client, amount=None, wait_seconds=time_seconds)



if __name__ == "__main__":
    pair = 'DOGE/USDT:USDT'
    client_biannce = FreqtradeClient(serverurl="http://127.0.0.1:8090")
    client_bybit = FreqtradeClient(serverurl="http://127.0.0.1:8091")



    # client.get_current_open_trade_id()
    # client.get_free_usdt()

    # client.get_trade_amount()
    run_sequence(client, pair)

    # client.force_exit_order(order_type="market", amount=1)

