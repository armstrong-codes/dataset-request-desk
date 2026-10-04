import logging, time, jwt
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import auth, requests, episodes, analytics, users

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("desk")
app = FastAPI(title="Dataset Request Desk", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def request_log(request: Request, call_next):
    start = time.perf_counter()
    request.state.user_id = None
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        try: request.state.user_id = int(jwt.decode(auth.split(" ",1)[1], settings.jwt_secret, algorithms=["HS256"]).get("sub"))
        except Exception: pass
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info('{"method":"%s","path":"%s","status":%s,"duration_ms":%s,"user_id":%s}', request.method, request.url.path, response.status_code, duration_ms, getattr(request.state, "user_id", None))
    return response

@app.get("/health")
def health(): return {"status": "ok"}

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(requests.router, prefix="/requests", tags=["requests"])
app.include_router(episodes.router, prefix="/episodes", tags=["episodes"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(users.router, prefix="/users", tags=["users"])
