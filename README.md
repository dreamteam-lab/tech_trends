# TechTrend Monitor

Сбор и аналитика данных о популярности IT-технологий.

## Проверка окружения

```
docker compose build
docker compose run --rm collector
```

# Запуск hacker_news collector

docker compose run --rm collector --technology rust --days 14 --page-size 100

# Запуск github collector

docker compose run --rm github-collector --technology clickhouse --days 30 --page-size 5

# Запуск pypi-collector

docker compose run --rm pypi-collector --package pandas

# Запуск pypi-downloads-collector

docker compose run --rm pypi-downloads-collector --package pandas --days 1
