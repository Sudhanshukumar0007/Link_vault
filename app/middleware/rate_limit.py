import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.redis import get_redis
from loguru import logger 

SKIP_PATHS = {"/docs","/health","/openapi.json","/redoc"}

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self,app,requests_per_minute:int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window = 60
    
    async def dispatch(self,request:Request,call_next):
        if request.url.path in SKIP_PATHS:
            return await call_next(request)
        
        ip = request.client.host
        key = f"rate_limit:{ip}"
        now = time.time()
        window_start = now - self.window
        try:
            redis = await get_redis()
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key,0,window_start)
            pipe.zadd(key,{str(now):now})
            pipe.zcard(key)
            pipe.expire(key,self.window)
            results = await pipe.execute()

            request_count = results[2]

            if request_count>self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail":"Too many requests"},
                    headers={"Retry-After":"60"}
                )
        except Exception:
            logger.warning(f"Rate limiter Redis unavailable -failing open")
        return await call_next(request)