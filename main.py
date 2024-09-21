#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os, logging
from fastapi import FastAPI, Body, Query
from contextlib import asynccontextmanager
from routers import streamdeck
import asyncio
import traceback
import uvicorn
from cli import start as stream_deck_start, stop as stream_deck_stop, next_page, set_bright_level
from contextlib import asynccontextmanager

logger = logging.getLogger("streamdeck")

def handle_exception(loop, context):
    # Extract the exception from the context
    exception = context.get("exception")
    if exception:
        logger.error(f"Caught exception: {exception}")
        traceback.print_exc()
    else:
        logger.error("Caught unknown exception")

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)    
    asyncio.create_task(stream_deck_start())
    yield    
    stream_deck_stop()

app = FastAPI(lifespan=lifespan)

# app.include_router(apisix_web.router)
# app.include_router(clickhouse.router)
app.include_router(streamdeck.router)

@app.get("/health/check")
async def health_check():
    return "OK"

@app.get("/admin/lcd_on")
async def lcd_on():
    await set_bright_level(60)

@app.get("/admin/lcd_off")
async def lcd_off():
    await set_bright_level(0)

@app.get("/admin/up")
async def up():
    await stream_deck_start()

@app.get("/admin/down")
async def down():
    stream_deck_stop()

@app.get("/admin/next")
async def next():
    await next_page()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run the server.')
    parser.add_argument('--log', type=str, default='info', help='logging level')
    parser.add_argument('--port', type=int, default=8000, help='port')
    args = parser.parse_args()    
    log_level = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_level)
    logger.setLevel(getattr(logging, args.log.upper()))

    dirname = os.path.abspath(os.path.dirname(__file__))
    config = uvicorn.Config("server:app", 
                            port=args.port, 
                            host="0.0.0.0", 
                            log_level="info", 
                            reload=True,
                            reload_dirs=[dirname]
                            )
        
    server = uvicorn.Server(config)    
    server.run()

#for development:  uvicorn --reload server:app 
if __name__ == "__main__":
    main()