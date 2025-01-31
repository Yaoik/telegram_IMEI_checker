from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import verify_token
from .imeicheck import check_imei
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

from db import initialize_db
initialize_db()

app = FastAPI()

class RequestBody(BaseModel):
    token: str
    imei: str

@app.post("/api/check-imei")
async def check_imei_endpoint(request: RequestBody):
    if not verify_token(request.token):
        raise HTTPException(status_code=403, detail="Forbidden")
    res = await check_imei(request.imei)
    if res:
        return res
    return {'error':'Вообще непонятно что тут пошло не так -_-'}
