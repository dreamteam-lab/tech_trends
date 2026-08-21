# Модель данных Silver-слоя

## Назначение Silver-слоя

Silver содержит очищенные и структурированные данные, полученные из исходных JSON Bronze-слоя.

Поток данных:

API → Bronze JSON → Spark → Silver Parquet → ClickHouse

В Silver:

- данные приводятся к единому формату;
- даты преобразуются в UTC;
- числовые поля получают правильные типы;
- удаляются дубликаты;
- записи связываются с технологиями;
- сохраняются поля, необходимые для аналитики;
- исходные JSON при этом остаются в Bronze.

Silver хранится в S3-совместимом хранилище SeaweedFS:

```text
s3://tech-trends-silver/{dataset}/year={YYYY}/month={MM}/day={DD}/part-*.parquet
```

## Общие правила

- Все даты и время хранятся в UTC.
- `technology_id` связывает запись со справочником технологий в PostgreSQL.
- `fetched_at` показывает время получения данных из внешнего источника.
- Повторная обработка одного периода не должна создавать дубликаты.
- Для хранения используется формат Parquet.
- Партиции `year`, `month` и `day` определяются по дате метрики или времени получения данных.

## Таблицы Silver для MVP

### 1. github_repositories

Одна строка представляет состояние одного GitHub-репозитория на момент сбора.

```text
s3://tech-trends-silver/github_repositories/year={YYYY}/month={MM}/day={DD}/
```

Логический уникальный ключ:
snapshot_date + technology_id + repository_id

| Поле                    | Тип            | Обязательное | Описание                         |
| ----------------------- | -------------- | -----------: | -------------------------------- |
| `snapshot_date`         | DATE           |           да | Дата снимка                      |
| `technology_id`         | BIGINT         |           да | Идентификатор технологии         |
| `repository_id`         | BIGINT         |           да | Идентификатор репозитория GitHub |
| `owner`                 | STRING         |           да | Владелец репозитория             |
| `name`                  | STRING         |           да | Название репозитория             |
| `full_name`             | STRING         |           да | Полное имя `owner/name`          |
| `description`           | STRING         |          нет | Описание                         |
| `language`              | STRING         |          нет | Основной язык                    |
| `stars`                 | BIGINT         |           да | Количество звёзд                 |
| `forks`                 | BIGINT         |           да | Количество форков                |
| `open_issues`           | BIGINT         |           да | Количество открытых issues       |
| `topics`                | ARRAY\<STRING> |          нет | Темы репозитория                 |
| `license`               | STRING         |          нет | Лицензия                         |
| `is_archived`           | BOOLEAN        |           да | Признак архивного репозитория    |
| `repository_created_at` | TIMESTAMP      |           да | Дата создания репозитория        |
| `repository_updated_at` | TIMESTAMP      |           да | Дата последнего обновления       |
| `repository_pushed_at`  | TIMESTAMP      |          нет | Дата последнего push             |
| `url`                   | STRING         |           да | URL репозитория                  |
| `fetched_at`            | TIMESTAMP      |           да | Время получения данных           |

### 2. package_metadata

Одна строка представляет состояние npm- или PyPI-пакета на момент сбора.

```text
s3://tech-trends-silver/package_metadata/year={YYYY}/month={MM}/day={DD}/
```

Поле requires_python заполняется только для PyPI.

Логический уникальный ключ:
snapshot_date + technology_id + ecosystem + package_name

| Поле              | Тип       | Обязательное | Описание                         |
| ----------------- | --------- | -----------: | -------------------------------- |
| `snapshot_date`   | DATE      |           да | Дата снимка                      |
| `technology_id`   | BIGINT    |           да | Идентификатор технологии         |
| `ecosystem`       | STRING    |           да | Экосистема: `npm` или `pypi`     |
| `package_name`    | STRING    |           да | Название пакета                  |
| `latest_version`  | STRING    |          нет | Последняя версия                 |
| `description`     | STRING    |          нет | Краткое описание                 |
| `license`         | STRING    |          нет | Лицензия                         |
| `homepage_url`    | STRING    |          нет | Домашняя страница                |
| `repository_url`  | STRING    |          нет | Репозиторий исходного кода       |
| `requires_python` | STRING    |          нет | Требуемая версия Python          |
| `version_count`   | BIGINT    |          нет | Количество опубликованных версий |
| `fetched_at`      | TIMESTAMP |           да | Время получения данных           |

### 3. package_downloads_daily

Одна строка представляет количество скачиваний одного пакета за один день.

В этот набор объединяются данные:

- npm downloads;
- PyPI downloads.

```text
s3://tech-trends-silver/package_downloads_daily/year={YYYY}/month={MM}/day={DD}/
```

Логический уникальный ключ:
date + technology_id + ecosystem + package_name

| Поле            | Тип       | Обязательное | Описание                 |
| --------------- | --------- | -----------: | ------------------------ |
| `date`          | DATE      |           да | Дата скачиваний          |
| `technology_id` | BIGINT    |           да | Идентификатор технологии |
| `ecosystem`     | STRING    |           да | `npm` или `pypi`         |
| `package_name`  | STRING    |           да | Название пакета          |
| `downloads`     | BIGINT    |           да | Количество скачиваний    |
| `fetched_at`    | TIMESTAMP |           да | Время получения данных   |

### 4. hacker_news_stories

Одна строка представляет одну публикацию Hacker News, найденную по запросу технологии.

```text
s3://tech-trends-silver/hacker_news_stories/year={YYYY}/month={MM}/day={DD}/
```

Логический уникальный ключ:
technology_id + story_id

| Поле               | Тип       | Обязательное | Описание                  |
| ------------------ | --------- | -----------: | ------------------------- |
| `story_id`         | STRING    |           да | Идентификатор публикации  |
| `technology_id`    | BIGINT    |           да | Идентификатор технологии  |
| `title`            | STRING    |          нет | Заголовок                 |
| `author`           | STRING    |          нет | Автор                     |
| `points`           | BIGINT    |           да | Количество баллов         |
| `comments_count`   | BIGINT    |           да | Количество комментариев   |
| `story_created_at` | TIMESTAMP |           да | Время создания публикации |
| `story_updated_at` | TIMESTAMP |          нет | Время обновления          |
| `url`              | STRING    |          нет | URL публикации            |
| `fetched_at`       | TIMESTAMP |           да | Время получения данных    |

### 5. stack_overflow_questions

Одна строка представляет один вопрос Stack Overflow, найденный по тегу технологии.

```text
s3://tech-trends-silver/stack_overflow_questions/year={YYYY}/month={MM}/day={DD}/
```

Логический уникальный ключ:
technology_id + question_id

| Поле                  | Тип            | Обязательное | Описание                              |
| --------------------- | -------------- | -----------: | ------------------------------------- |
| `question_id`         | BIGINT         |           да | Идентификатор вопроса                 |
| `technology_id`       | BIGINT         |           да | Идентификатор технологии              |
| `title`               | STRING         |           да | Заголовок вопроса                     |
| `tags`                | ARRAY\<STRING> |           да | Теги вопроса                          |
| `score`               | BIGINT         |           да | Рейтинг вопроса                       |
| `views`               | BIGINT         |           да | Количество просмотров                 |
| `answers`             | BIGINT         |           да | Количество ответов                    |
| `is_answered`         | BOOLEAN        |           да | Есть ли принятый или подходящий ответ |
| `question_created_at` | TIMESTAMP      |           да | Время создания вопроса                |
| `last_activity_at`    | TIMESTAMP      |          нет | Время последней активности            |
| `url`                 | STRING         |           да | URL вопроса                           |
| `fetched_at`          | TIMESTAMP      |           да | Время получения данных                |

### 6. rejected_records

Обработка некорректных записей

```text
s3://tech-trends-silver/rejected_records/source={source}/year={YYYY}/month={MM}/day={DD}/
```

| Поле                | Тип       | Описание              |
| ------------------- | --------- | --------------------- |
| `source`            | STRING    | Источник данных       |
| `bronze_object_key` | STRING    | Путь к исходному JSON |
| `error_reason`      | STRING    | Причина отклонения    |
| `raw_record`        | STRING    | Исходная запись       |
| `rejected_at`       | TIMESTAMP | Время обработки       |
