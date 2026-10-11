# Binance Token Heatmap

小型前后端项目：后端定时拉取 Binance Spot 24hr ticker 数据，整理成交额前 100 token 及 24h 变化率；前端以类似股市热力图的大色块展示。

> 说明：Binance Spot 公共接口不直接提供流通市值/总市值字段。本项目默认使用 Binance `quoteVolume`（24h USDT 成交额）作为排序和色块面积的“市值风格展示”代理指标，并在 UI 中明确标注。
