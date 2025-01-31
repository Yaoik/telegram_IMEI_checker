import aiohttp
import json
import os
import logging
from dotenv import load_dotenv
import asyncio

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

url = 'https://api.imeicheck.net/v1/checks/'
IMEICHECK_TOKEN = os.getenv('IMEICHECK_TOKEN')
assert IMEICHECK_TOKEN is not None

headers = {
    'Authorization': 'Bearer ' + IMEICHECK_TOKEN,
    'Content-Type': 'application/json'
}

async def check_imei(device_id:str) -> None|dict:
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            body = json.dumps({
                "deviceId": device_id,
                "serviceId": 12,
            })
            async with session.post(url, data=body) as response:
                if response.status < 400:
                    data = await response.json()
                    return data.get('properties', {'ERROR': 'WTF'})
                elif response.status == 429:
                    return {'error': 'Too many requests.'}
                else:
                    logger.error(f"Request failed with status: {response.status}")
                
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            logger.info(f"{url=}")
            logger.info(f"{device_id=}")

if __name__ == "__main__":
    asyncio.run(check_imei('356735111052198'))
