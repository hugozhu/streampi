from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import logging

logger = logging.getLogger("admin-api")

router = APIRouter(
    prefix="/api/v1",
    tags=["ch"],
    responses={404: {"description": "Not found"}},
)

@router.post("/admin")
async def admin():
    pass