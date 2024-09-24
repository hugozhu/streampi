#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os, logging
from fastapi import FastAPI, Body, Query
from contextlib import asynccontextmanager
import asyncio
import traceback
import uvicorn
from contextlib import asynccontextmanager
from routers.utils import load_routes
from routers import streamdeck

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
    dm.close()

app = FastAPI(lifespan=lifespan)

from cli import start as stream_deck_start, dm, next_page
streamdeck.dm = dm
streamdeck.next_page = next_page
app.include_router(streamdeck.router)

from plugins.uptime_plugin import router as router1
from plugins.clickhouse_plugin import router as router2
from plugins.apisix_plugin import router as router3
app.include_router(router1)
app.include_router(router2)
app.include_router(router3)

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