from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import logging

logger = logging.getLogger("admin-api")

global dm, next_page

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

@router.get("/ok")
async def health_check():
    return "OK"

@router.get("/admin/lcd_on")
async def lcd_on():
    await dm.screen_on()

@router.get("/admin/lcd_off")
async def lcd_off():
    await dm.screen_off()

@router.get("/admin/down")
async def down():
    dm.close()

@router.get("/admin/prev")
async def prev():
    await next_page(-1)

@router.get("/admin/next")
async def next():
    await next_page(1)