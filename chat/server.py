import asyncio
import logging
from datetime import datetime, timedelta

from aiofile import async_open
import aiohttp
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    print(f"Error status: {resp.status} for {url}")
        except aiohttp.ClientConnectorError as err:
            print(f'Connection error: {url}', str(err))


async def get_urls(days):
    await asyncio.sleep(0)
    date_today = datetime.now()
    list_of_urls = []
    for i in range(0, days+1):
        date_for_url = date_today - timedelta(days=i)
        if len(str(date_for_url.month)) == 1:
            date_for_url_month = f'0{str(date_for_url.month)}'
        else:
            date_for_url_month = str(date_for_url.month)
        if len(str(date_for_url.day)) == 1:
            date_for_url_day = f'0{str(date_for_url.day)}'
        else:
            date_for_url_day = str(date_for_url.day)
        url_for_date = f'https://api.privatbank.ua/p24api/exchange_rates?date={date_for_url_day}.{date_for_url_month}.{date_for_url.year}'
        list_of_urls.append(url_for_date)
    return list_of_urls


async def get_exchange(days):
    urls = await get_urls(days)
    ex_rates = []
    for url in urls:
        result = await request(url)
        if result:
            ex_rates_dicts = {}
            for el in result['exchangeRate']:
                if el['currency'] == 'USD':
                    ex_rates_currency = {result['date']: {'sale': el['saleRateNB'], 'purchase': el['purchaseRateNB']}}
                    ex_rates.append(ex_rates_currency)
    return f'Курс USD за {days} днів: {ex_rates}'


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            message_upp = message.upper()
            if message_upp.startswith('EXCHANGE'):
                async with async_open('exchange_logs.txt', 'a+') as afp:
                    await afp.write(f'{datetime.now()}\n')
                message_upp_split = message_upp.split(' ')
                try:
                    days = int(message_upp_split[1])
                except (IndexError, ValueError):
                    days = 0
                exc = await get_exchange(days)
                await self.send_to_clients(exc)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())