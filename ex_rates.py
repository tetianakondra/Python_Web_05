import aiohttp
import asyncio
import platform
from datetime import datetime, timedelta


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


async def client_request():
    while True:
        await asyncio.sleep(0)
        currency = input("Enter the currency (USD and EUR as default). If you don't want to add additional currency, skip: ")
        days_for_rates = input("Enter quantity of days for getting rates (0 as default): ")
        if currency.upper() not in ['USD', 'EUR', '']:
            list_of_currency = ['USD', 'EUR', currency.upper()]
        else:
            list_of_currency = ['USD', 'EUR']
        try:
            days = int(days_for_rates)
        except (ValueError):
            print('will be search the exchange rate for today')
            return [list_of_currency, 0]
        else:
            if int(days_for_rates)>10:
                days_for_rates = 10
                print('The exchange rate will be shown for 10 days')
            if int(days_for_rates)<0:
                print('will be search the exchange rate for today')
            return [list_of_currency, int(days_for_rates)]
            
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


async def main():
    currency_and_days = await client_request()
    urls = await get_urls(currency_and_days[1])
    ex_rates = []
    for url in urls:
        result = await request(url)
        if result:
            ex_rates_dicts = {}
            for el in result['exchangeRate']:
                if el['currency'] in currency_and_days[0]:
                    ex_rates_currency = {el['currency']: {'sale': el['saleRateNB'], 'purchase': el['purchaseRateNB']}}
                    ex_rates_dicts.update(ex_rates_currency)
            ex_rates.append({result['date']: ex_rates_dicts})
    if len(ex_rates_dicts) == 2 and len(currency_and_days[0])==3:
        print("Your additional currency wasn't found")
    return ex_rates
    

if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    r = asyncio.run(main())
    print(r)