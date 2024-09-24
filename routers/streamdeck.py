from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import logging

logger = logging.getLogger("admin-api")

dm = None
next_page = None

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

@router.get("/ok")
async def health_check():
    return "OK"

@router.get("/lcd_on")
async def lcd_on():
    await dm.screen_on()

@router.get("/lcd_off")
async def lcd_off():
    await dm.screen_off()

@router.get("/down")
async def down():
    dm.close()

@router.get("/prev")
async def prev():
    await next_page(-1)

@router.get("/next")
async def next():
    await next_page(1)