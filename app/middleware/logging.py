import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from loguru import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request:Request,call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        request.state.request_id = request_id

        logger.info(
            f"-> {request.method} {request.url.path} | "
            f"request_id={request_id} | "
            f"ip={request.client.host}"
        )

        response = await call_next(request)

        duration_ms = round((time.time() - start_time) *1000,2)

        logger.info(
            f"← {request.method} {request.url.path} | "
            f"request_id={request_id} | "
            f"status={response.status_code} | "
            f"duration={duration_ms}ms"
        )

        response.headers["X-Request-ID"] = request_id
        return response