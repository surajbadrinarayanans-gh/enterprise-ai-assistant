# 04 · HTTP, servers and FastAPI

## Your code vs the server
```
Browser/curl ──HTTP request──> Uvicorn (listens on 127.0.0.1:8000) ──calls──> FastAPI app ──> health_check()
             <──JSON response──                                   <──returns── {"status": "healthy"}
```
- Your `main.py` defines **what to answer**. It doesn't listen on the network.
- **Uvicorn** is the server: opens the port, receives requests, hands them to `app`.
- **`uv run fastapi dev src/eka/main.py`** starts Uvicorn in dev mode: auto-reload on save, reachable only from your own machine. Stop with `Ctrl+C`.

## The first endpoint
```python
from fastapi import FastAPI          # load the class from site-packages
app = FastAPI()                      # the application object the server looks for
@app.get("/healthz")                 # decorator: GET /healthz → call the function below (a "route")
def health_check():
    return {"status": "healthy"}     # dict → JSON automatically
```

## Network basics
- **127.0.0.1 / localhost** = "this computer".
- **Port** = which program on the computer (IP = building, port = apartment number). Dev server uses 8000.
- **HTTP method** = the verb: GET (read), POST (create), PUT/PATCH (update), DELETE.
- **Route** = method + path that maps to a function. No route → **404**.

## Status codes
| Range | Meaning | Examples |
|---|---|---|
| 2xx | success | 200 OK, 201 Created, 202 Accepted (work continues later), 204 No Content |
| 4xx | **client** made a mistake | 400 bad input, 401 not authenticated, 403 not allowed, 404 not found, 429 too many requests |
| 5xx | **server** broke | 500 internal error, 502 bad gateway, 503 unavailable, 504 timeout |

SRE error-rate SLOs usually count **5xx only**. 4xx is not the service's fault.

## FastAPI extras
- **`/docs`** is interactive API documentation generated from your code (OpenAPI). Contract tests use the OpenAPI file.
- **`curl -i http://127.0.0.1:8000/healthz`** shows the status line and headers (`content-type: application/json`).
- Unknown path returns `404 {"detail": "Not Found"}`. The server doesn't crash.

## Health checks
- **Liveness (`/healthz`):** is the process alive? If not, restart it.
- **Readiness (`/readyz`):** can it serve traffic now (DB reachable)? If not, stop sending traffic but don't restart.
Kubernetes uses both. We'll wire them up later.

## Interview questions
1. What is the difference between a web framework (FastAPI) and a web server (Uvicorn)?
2. What is a port? What does 127.0.0.1 mean?
3. 4xx vs 5xx: which counts against your availability SLO and why?
4. Why does upload return 202 instead of 200 in our design?
5. Liveness vs readiness probe?
