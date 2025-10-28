from freqtrade_client import FtRestClient
from exchange_tick import parse_symbol_from_pair,FuturesPriceFetcher
import time
from delete_all_db import clean_directories

class FreqtradeManager:
    def __init__(self, server_url="http://127.0.0.1:8080", username="freqtrader", password="123456"):
        self.client = FtRestClient(server_url, username, password)

    def get_current_trades(self):
        """获取当前所有开放交易"""
        try:
            trades = self.client.status()
            return trades or []
        except Exception as e:
            print(f"获取交易状态失败: {e}")
            return []

    def force_enter_order(self, pair, side="long", price=None, stake_amount=None, leverage=3, order_type="limit"):
        """
        强制进入交易函数
        """
        try:
            result = self.client.forceenter(
                pair=pair,
                side=side,
                price=price,
                order_type= order_type,
                stake_amount=stake_amount,
                enter_tag="force_entry",
                leverage=leverage
            )
            print(f"强制进入 {pair} ({side}) 的结果:", result)
            return result
        except Exception as e:
            print(f"强制进入失败: {e}")
            return None

    def force_exit_order(self, pair):
        """
        强制退出指定交易对的所有交易
        """
        trades = self.get_current_trades()
        found_trades = False

        for trade in trades:
            if trade.get("pair") == pair:
                found_trades = True
                trade_id = trade.get("trade_id")
                try:
                    result = self.client.forceexit(trade_id, ordertype="market")
                    print(f"退出交易 {trade_id} 的结果:", result)
                except Exception as e:
                    print(f"退出交易 {trade_id} 失败: {e}")

        if not found_trades:
            print(f"未找到交易对 {pair} 的开放交易")

    def cancel_open_order(self, trade_id):
        """取消未成交订单"""
        try:
            result = self.client.cancel_open_order(trade_id)
            print(f"取消订单 {trade_id} 的结果:", result)
            return result
        except Exception as e:
            print(f"取消订单失败: {e}")
            return None

    def check_connection(self):
        """检查与机器人的连接状态"""
        try:
            ping_result = self.client.ping()
            print("连接状态:", ping_result)
            return ping_result
        except Exception as e:
            print(f"连接检查失败: {e}")
            return None

    def start_bot(self):
        """启动机器人"""
        try:
            result = self.client.start()
            return result
        except Exception as e:
            print(f"启动机器人失败: {e}")
            return None

    def stop_bot(self):
        """停止机器人"""
        try:
            result = self.client.stop()
            return result
        except Exception as e:
            print(f"停止机器人失败: {e}")
            return None

    def get_trade_status(self, pair):
        """返回指定交易对的所有订单状态列表"""
        trades = self.get_current_trades()
        trade_status=None
        for trade in trades:
            if trade.get("pair") == pair:
                trade_status={
                    "trade_id": trade.get("trade_id"),
                    "status": trade['orders'][0].get("status"),  # 例如 open, filled, closed, partial
                }
        return trade_status

class ArbitrageManager:
    def __init__(self):
        self.binance_bot = FreqtradeManager(server_url="http://127.0.0.1:8080")
        self.bybit_bot = FreqtradeManager(server_url="http://127.0.0.1:8081")
        self.okx_bot = FreqtradeManager(server_url="http://127.0.0.1:8082")

    def start_all_bot(self):
        self.binance_bot.start_bot()
        self.bybit_bot.start_bot()
        self.okx_bot.start_bot()

    def close_all_bot(self):
        self.binance_bot.stop_bot()
        self.bybit_bot.stop_bot()
        self.okx_bot.stop_bot()

    def enter_order(self, pair):
        self.binance_bot.force_enter_order(pair, side="short", stake_amount=1000, leverage=3)
        self.bybit_bot.force_enter_order(pair, side="short", stake_amount=1000, leverage=3)
        self.okx_bot.force_enter_order(pair, side="short", stake_amount=1000, leverage=3)

    def exit_order(self, pair):
        self.binance_bot.force_exit_order(pair)
        self.bybit_bot.force_exit_order(pair)
        self.okx_bot.force_exit_order(pair)

    def enter_arbitrage(self, pair, long_bot_name, short_bot_name, stake_amount, leverage, max_wait=1000, interval=1):

        fetcher = FuturesPriceFetcher()

        prices = fetcher.get_pair_prices(parse_symbol_from_pair(pair), [long_bot_name, short_bot_name])
        long_price=prices[long_bot_name]+1
        short_price=prices[short_bot_name]+1

        print(f"限价做多({long_bot_name}): {long_price}，限价做空({short_bot_name}): {short_price}")

        long_bot = getattr(self, f"{long_bot_name}_bot")
        short_bot = getattr(self, f"{short_bot_name}_bot")

        long_bot.force_enter_order(pair, side="long", stake_amount=stake_amount, leverage=leverage,
                                   order_type="limit")
        short_bot.force_enter_order(pair, side="short", stake_amount=stake_amount, leverage=leverage,
                                    order_type="limit")

        # 轮询成交状态
        for _ in range(max_wait):
            long_filled = long_bot.get_trade_status(pair)
            short_filled = short_bot.get_trade_status(pair)

            if long_filled and not short_filled:
                print(f"{long_bot_name} 完全成交，{short_bot_name} 未完全成交，市价补齐")
                self.fill_unfilled(short_bot, pair, side="short", stake_amount=stake_amount, leverage=leverage)
                break
            elif short_filled and not long_filled:
                print(f"{short_bot_name} 完全成交，{long_bot_name} 未完全成交，市价补齐")
                self.fill_unfilled(long_bot, pair, side="long", stake_amount=stake_amount, leverage=leverage)
                break
            elif long_filled and short_filled:
                print("两边都已完全成交")
                break
            time.sleep(interval)


    def fill_unfilled(self, bot, pair, side, stake_amount, leverage):
        """
        取消未成交订单并用市价单补齐
        """
        trade_status = bot.get_trade_status(pair)
        # 取消未成交订单
        bot.cancel_open_order(trade_status['trade_id'])
        # 用市价单补齐
        bot.force_enter_order(pair, side=side, stake_amount=stake_amount, leverage=leverage,order_type="market")



if __name__ == "__main__":

    dirs_to_clean = [
        'binance_robot/db',
        'bybit_robot/db',
        'okx_robot/db'
    ]
    clean_directories(dirs_to_clean)

    pair = 'GAS/USDT:USDT'
    long_bot_name = 'binance'
    short_bot_name = 'bybit'
    manager = ArbitrageManager()
    manager.start_all_bot()
    manager.enter_arbitrage(pair, long_bot_name, short_bot_name, stake_amount=100, leverage=1)
    # manager.exit_order(pair)
    # manager.close_all_bot()
