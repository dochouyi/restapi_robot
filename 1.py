from freqtrade_client import FtRestClient

class FreqtradeManager:
    def __init__(self, server_url="http://127.0.0.1:8080", username="freqtrader", password="123456"):
        self.client = FtRestClient(server_url, username, password)



if __name__ == "__main__":
    binance_bot = FreqtradeManager(server_url="http://127.0.0.1:8080")

    result=binance_bot.client.stop()
    # print(result)

    # result=binance_bot.client.stopbuy()
    # print(result)

    # result=binance_bot.client.reload_config()
    # print(result)
    #

    # result=binance_bot.client.balance()
    # print(result)

    # result=binance_bot.client.start()
    # print(result)