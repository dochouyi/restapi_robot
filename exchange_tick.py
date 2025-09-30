import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def parse_symbol_from_pair(pair: str) -> str:
    """
    支持 'GAS/USDT:USDT' 或 'BTC/USDT' 或 'BTC' 等格式，返回主币种名称
    """
    if ':' in pair:
        pair = pair.split(':')[0]
    if '/' in pair:
        symbol = pair.split('/')[0]
    else:
        symbol = pair
    return symbol.strip().upper()


class FuturesPriceFetcher:
    def __init__(self):
        self.proxies = {
            "http": "http://127.0.0.1:7890",
            "https": "http://127.0.0.1:7890"
        }

    def _format_symbol(self, symbol: str, exchange: str) -> str:
        base = symbol.upper()
        if 'USDT' not in base:
            base = base + 'USDT'
        if exchange == 'okx':
            return base.replace('USDT', '-USDT')
        else:
            return base

    def get_binance_futures_price(self, symbol: str) -> float:
        symbol = self._format_symbol(symbol, 'binance')
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
        resp = requests.get(url, proxies=self.proxies, timeout=10)
        data = resp.json()
        return float(data['price'])

    def get_bybit_futures_price(self, symbol: str) -> float:
        symbol = self._format_symbol(symbol, 'bybit')
        url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"
        resp = requests.get(url, proxies=self.proxies, timeout=10)
        data = resp.json()
        return float(data['result']['list'][0]['lastPrice'])

    def get_okx_futures_price(self, symbol: str) -> float:
        symbol = self._format_symbol(symbol, 'okx')
        okx_symbol = symbol + '-SWAP'
        url = f"https://www.okx.com/api/v5/market/ticker?instId={okx_symbol}"
        resp = requests.get(url, proxies=self.proxies, timeout=10)
        data = resp.json()
        return float(data['data'][0]['last'])


    def get_pair_prices(self, symbol: str, exchanges: list):
        """
        输入 symbol 和两个交易所名（如 ['binance', 'okx']），并发返回这两个交易所的价格。
        """
        # 交易所与对应获取价格的方法映射
        exchange_methods = {
            'binance': self.get_binance_futures_price,
            'bybit': self.get_bybit_futures_price,
            'okx': self.get_okx_futures_price
        }
        # 检查输入合法性
        assert len(exchanges) == 2, "只支持两个交易所"
        for ex in exchanges:
            assert ex in exchange_methods, f"不支持的交易所: {ex}"

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_exchange = {
                executor.submit(exchange_methods[ex], symbol): ex
                for ex in exchanges
            }
            price_dict = {}
            for future in as_completed(future_to_exchange):
                exchange = future_to_exchange[future]
                try:
                    price = future.result()
                except Exception as exc:
                    price = None
                price_dict[exchange] = price

        # 按输入顺序返回
        return price_dict


if __name__ == "__main__":
    fetcher = FuturesPriceFetcher()
    symbol = 'OMNI'  # 只需传入BTC
    prices = fetcher.get_pair_prices(symbol,['binance','bybit'])
    print(prices)
