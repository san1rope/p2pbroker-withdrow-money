import asyncio
import json
import logging

from aiohttp import ClientSession

from config import Config
from utils import auth, get_balance, payment, base58_to_hex

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.INFO,
                        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

    try:
        with open("cookies.txt", "r", encoding="utf-8") as file:
            cookies = file.read()
            if cookies:
                cookies = cookies.strip()

    except FileNotFoundError:
        cookies = ""

    async with ClientSession() as session:
        url = "https://api.trongrid.io/jsonrpc"
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [
                {
                    "to": await base58_to_hex(value=Config.CONTRACT_ADDRESS),
                    "data": f"0x70a08231{(await base58_to_hex(value=Config.RELATED_ADDRESS))[2:].zfill(64)}"
                },
                "latest"
            ],
            "id": 1
        }

        headers = {
            "Content-Type": "application/json"
        }

        balance = 0
        old_balance_rel_address = None
        counter = 0
        while True:
            if counter % 1000 == 0:
                balance = await get_balance(session=session, cookie=cookies)
                if balance is None:
                    logger.error("Не смог получить баланс! Авторизация...")
                    cookies = await auth(session=session)
                    if not cookies:
                        logger.warning("Не удалось авторизироваться! Попробуйте ещё раз...")
                        continue

                    with open("cookies.txt", "w", encoding="utf-8") as file:
                        file.write(cookies)

                    continue

                logger.info(f"Баланс: {balance}")
                counter = 1

            else:
                counter += 1

            try:
                async with session.post(url=url, headers=headers, json=payload, timeout=Config.LOAD_TIMEOUT,
                                        ssl=False) as response:
                    answer = json.loads(await response.text())
                    usdt_balance = int(answer["result"], 16) / 1_000_000
                    if (not (old_balance_rel_address is None)) and (usdt_balance > old_balance_rel_address):
                        logger.info(f"Зафиксировал пополнение USDT по RELATED_ADDRESS")
                        for _ in range(3):
                            if balance < 5:
                                logger.error(f"Баланс аккаунта: {balance} < 5. Не смог произвести выплату...")
                                balance = await get_balance(session=session, cookie=cookies)
                                if balance is None:
                                    logger.warning("Не смог получить баланс! Авторизация...")
                                    cookies = await auth(session=session)
                                    if not cookies:
                                        logger.warning("Не удалось авторизироваться! Попробуйте ещё раз...")

                                    else:
                                        with open("cookies.txt", "w", encoding="utf-8") as file:
                                            file.write(cookies)

                                continue

                            result = await payment(session=session, cookie=cookies, amount=balance)
                            if result:
                                logger.info(f"Выплата успешно произведена!")
                                break

                            else:
                                logger.error("Не смог произвести оплату!")

                    old_balance_rel_address = usdt_balance

                await asyncio.sleep(0.25)

            except TimeoutError:
                logger.error("Сервер не вернул ответ!")


if __name__ == "__main__":
    asyncio.run(main())
