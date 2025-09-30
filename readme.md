# RestAPI控制多个机器人
已经支持的交易所
- binance
- bybit
- okx

采用的dry_run模式
交易所秘钥没有添加


定下来以下IP地址和交易所的对应关系
- "http://127.0.0.1:8080",
- "http://127.0.0.1:8081",
- "http://127.0.0.1:8082"

CORS_origins每一条后面不能加斜线



main文件中是同时控制多个机器人的代码

![image-20250805171451047](https://pkuxiaohou.oss-cn-beijing.aliyuncs.com/img/202508051714142.png)

![image-20250805171458808](https://pkuxiaohou.oss-cn-beijing.aliyuncs.com/img/202508051714881.png)



docker使用命令
docker compose up -d

docker compose down

代理配置
容器中的代理配置和外部host一致，docker的network_mode: host



docker容器如下

![image-20250805172213328](https://pkuxiaohou.oss-cn-beijing.aliyuncs.com/img/202508051722377.png)







