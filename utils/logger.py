import json
import logging
import time
from datetime import datetime

from fastapi.logger import logger
from starlette.requests import Request

logger.setLevel(logging.INFO)


async def api_logger(request: Request, response=None, error=None):
    process_time = time.time() - request.state.start
    status_code = error.status_code if error else response.status_code
    error_log = None

    user = request.state.user

    if error:
        frame = request.state.inspect
        error_file = error_function = error_line = None
        if frame:
            error_file = frame.f_code.co_filename
            error_function = frame.f_code.co_name
            error_line = frame.f_lineno

        error_log = dict(
            errorFunc=error_function,
            location=f"{error_line} line in {error_file}",
            raised=str(error.__class__.__name__),
            msg=str(error.ex),
        )

    user_id = None
    hash_email = None

    if user:
        user_id = user.id
        if user.email:
            local, domain = user.email.split("@")
            hash_email = f"**{local[2:]}@{domain}"

    user_log = dict(
        client=request.state.ip,
        user=user_id,
        email=hash_email,
    )

    # url, method, status_code, error_detail, client, processed_time, datetime
    log_dict = dict(
        url=f"{request.url.hostname}{request.url.path}",
        method=request.method,
        status_code=status_code,
        error_detail=error_log,
        client=user_log,
        processed_time=f"{round(process_time * 1000, 5)} ms",
        datetime=f"{datetime.now():%Y-%m-%d %H:%M:%S}",
    )

    logger_to_json = json.dumps(log_dict, indent=4)
    if status_code >= 500:
        logger.error(logger_to_json)
    else:
        logger.info(logger_to_json)
