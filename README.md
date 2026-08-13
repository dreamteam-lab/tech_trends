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

# Запуск Stack Overflow collector

Сбор вопросов с тегом python за 7 завершённых UTC-дней:

docker compose run --rm stack-overflow-collector --tag python --days 7 --page-size 100

Коллектор может работать без регистрации с ограниченной анонимной квотой.
# Запуск npm metadata collector

docker compose run --rm npm-collector --package react

Для scoped-пакета:

docker compose run --rm npm-collector --package "@nestjs/core"

# Запуск npm downloads collector

Сбор статистики за 7 завершённых дней:

docker compose run --rm npm-downloads-collector --package react --days 7

Для scoped-пакета:

docker compose run --rm npm-downloads-collector --package "@nestjs/core" --days 7
