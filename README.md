# Лабораторна робота 7 - Rate Limiter

## Опис проекту

REST API для бібліотеки на FastAPI з реалізованим Rate Limiter.

### Основні можливості

* Авторизація користувачів
* Rate limiting для захисту API
* Підтримка MongoDB
* Асинхронна робота (`async/await`)
* Unit тести для rate limiter

---

## Реалізовані обмеження

### Авторизований користувач

* 10 запитів за хвилину

### Анонімний користувач

* 2 запити за хвилину

---

## Технології

* FastAPI
* MongoDB
* Redis
* Docker
* Docker Compose
* Pytest
* AsyncMock

---

## Структура проекту

```bash
fastapi-library-lab-7/
├── app/
│   ├── api/
│   ├── core/
│   │   └── rate_limiter.py
│   ├── models/
│   ├── repository/
│   ├── services/
│   └── main.py
│
├── tests/
│   └── test_rate_limiter.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Запуск проекту

### Запуск Docker контейнерів

```bash
docker compose up -d --build
```

---

## Swagger документація

http://localhost:8000/docs

---

## Запуск тестів

```bash
docker compose exec api pytest tests/ -v
```

---

## Результат тестів

4 passed

---

## Реалізовані тест кейси

### Авторизований користувач

* Не досяг ліміту → HTTP 200
* Досяг ліміту → HTTP 429

### Анонімний користувач

* Не досяг ліміту → HTTP 200
* Досяг ліміту → HTTP 429

