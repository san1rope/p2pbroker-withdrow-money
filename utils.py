import json
import logging

import base58
from typing import Union

from aiohttp import ClientSession

from config import Config

logger = logging.getLogger(__name__)


async def base58_to_hex(value: str) -> str:
    decoded_bytes = base58.b58decode(value)
    address_bytes = decoded_bytes[:-4]
    return address_bytes.hex()


async def auth(session: ClientSession) -> Union[str, None]:
    try:
        url = "https://new.p2pbroker.xyz/api/user/login"
        headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "fingerprint": "fingerprint",
            "origin": "https://new.p2pbroker.xyz",
            "priority": "u=1, i",
            "referer": "https://new.p2pbroker.xyz/sign/in",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": Config.USER_AGENT
        }

        otp_code = input("Введите код подтверждения для авторизации: ").strip()
        data = {
            "login": Config.USERNAME,
            "password": Config.PASSWORD,
            "otpCode": otp_code
        }

        async with session.post(url=url, headers=headers, json=data, timeout=Config.LOAD_TIMEOUT,
                                ssl=False) as response:
            answer_cookies = response.headers.getall('Set-Cookie', [])

        cookies_out = []
        for cookie_data in answer_cookies:
            cookies_out.append(cookie_data.split(';')[0])

        return "; ".join(cookies_out)

    except TimeoutError:
        logger.error("Ошибка авторизации! Сервер не вернул ответ!")
        return None


async def get_balance(session: ClientSession, cookie: str, retries: int = 3) -> Union[float, None]:
    try:
        url = "https://new.p2pbroker.xyz/api/balance/get_balance?currency=usdt"
        headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "cookie": cookie,
            "fingerprint": "fingerprint",
            "priority": "u=1, i",
            "referer": "https://new.p2pbroker.xyz/usdt-payout",
            "sec-ch-ua": '"Chromium";v="130", "Opera GX";v="115", "Not?A_Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": Config.USER_AGENT
        }

        async with session.get(url=url, headers=headers, timeout=Config.LOAD_TIMEOUT, ssl=False) as response:
            answer_bytes = await response.read()
            print(f"balance answer = {answer_bytes}")
            start_index = answer_bytes.find(b'{')
            if start_index == -1:
                return None

            clean_response = answer_bytes[start_index:].decode('utf-8')
            answer_json = json.loads(clean_response)

        balance = answer_json.get("balance")
        if balance is None:
            raise TimeoutError

        else:
            return float(str(balance).replace(',', '.').strip())

    except TimeoutError:
        if retries:
            logger.warning(f"TimeourError при получении баланса. Осталось попыток: {retries}")
            return await get_balance(session=session, cookie=cookie, retries=retries - 1)

        logger.error("Ошибка получения баланса! Сервер не вернул ответ!")
        return None


async def payment(session: ClientSession, cookie: str, amount: float) -> Union[bool, None]:
    try:
        url = "https://new.p2pbroker.xyz/api/withdrawal/create_withdrawal_order"
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "cookie": cookie,
            "fingerprint": "fingerprint",
            "origin": "https://new.p2pbroker.xyz",
            "priority": "u=1, i",
            "referer": "https://new.p2pbroker.xyz/usdt-payout",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="89"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": Config.USER_AGENT
        }

        data = {
            "amount": amount,
            "wallet": Config.RECEIVER_ADDRESS
        }
        async with session.post(url=url, headers=headers, json=data, timeout=Config.LOAD_TIMEOUT,
                                ssl=False) as response:
            answer = await response.text()

        print(f"payment asnwer = {answer}")
        return answer.strip() == "OK"

    except TimeoutError:
        logger.error("Ошибка выплаты! Сервер не вернул ответ!")
        return None
