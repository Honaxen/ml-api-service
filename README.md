# ML API Service

A production-ready REST API for LLM inference — with JWT authentication, rate limiting, and Redis caching.

🚧 **Work in progress.**

---

## What This Project Demonstrates

Every other project in this portfolio builds an ML system.
This one shows how to **ship** one.

Three production concerns most ML projects skip:

| Concern | Solution |
|---|---|
| Who can use it? | JWT authentication |
| How much can they use? | Rate limiting (10 req/60s per key) |
| How fast is it? | Redis caching (same prompt = instant response) |

---

## Build Checklist

- [ ] `app/__init__.py` + `app/routes/__init__.py` + `tests/__init__.py`
- [ ] `.gitignore` + `.env.example`
- [ ] `app/models.py` — Pydantic request/response schemas
- [ ] `app/auth.py` — JWT authentication
- [ ] `app/cache.py` — Redis caching with graceful fallback
- [ ] `app/limiter.py` — sliding window rate limiter
- [ ] `app/routes/generate.py` — POST /generate
- [ ] `app/routes/health.py` — GET /health
- [ ] `app/main.py` — FastAPI app entry point
- [ ] `tests/test_api.py` — unit tests
- [ ] `Dockerfile` + `docker-compose.yml`
- [ ] `requirements.txt`
- [ ] Test end-to-end
- [ ] Replace this README with full documentation

---

## Planned Structure

```
ml-api-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── auth.py
│   ├── cache.py
│   ├── limiter.py
│   ├── models.py
│   └── routes/
│       ├── __init__.py
│       ├── generate.py
│       └── health.py
├── tests/
│   └── test_api.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Stack

Python · FastAPI · Redis · JWT · Docker · Ollama · pytest

---

## Related Projects

- [document-agent](https://github.com/Honaxen/document-agent) — RAG system this API can serve
- [multi-tool-agent](https://github.com/Honaxen/multi-tool-agent) — agent that could be exposed via this API

---

## Author

[Honaxen](https://github.com/Honaxen)