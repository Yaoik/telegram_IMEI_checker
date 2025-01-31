from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import verify_token
from .imeicheck import check_imei
import logging
import re

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

from db import initialize_db
initialize_db()

app = FastAPI()

class RequestBody(BaseModel):
    token: str
    imei: str

def is_valid_imei(imei: str) -> bool:
    if not re.fullmatch(r"\d{15}", imei):
        return False
    
    def luhn_checksum(imei: str) -> bool:
        total = 0
        for i, digit in enumerate(reversed(imei)):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0
    
    return luhn_checksum(imei)

@app.post("/api/check-imei")
async def check_imei_endpoint(request: RequestBody):
    if not verify_token(request.token):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not is_valid_imei(request.imei):
        return {'error':'Некорректный IMEI.'}
    res = await check_imei(request.imei)
    if res:
        return res
    return {'error':'Вообще непонятно что тут пошло не так -_-'}
