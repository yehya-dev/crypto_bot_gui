from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.templating import Jinja2Templates
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
import cryptobot

templates = Jinja2Templates(directory='./cryptoserve/templates')

added_coins = dict()

async def homepage(request):
    return templates.TemplateResponse('index.html', {'request': request})

async def addcoin(request):
    base = request.query_params['base']
    quote = request.query_params['quote']
    buy_percentage = request.query_params['percent']
    coin = cryptobot.CryptoAsset(base, quote)
    if buy_percentage:
        coin.market_buy(float(buy_percentage))
    added_coins[base + quote] = coin
    return JSONResponse({
        'status': True
    })

async def buycoin(request):
    form = await request.form()
    symbol = form['base'] + form['quote']
    buy_percentage = form['buy_percentage']
    follow_percentage = form['follow_percentage']
    safety_percentage = form['safety_percentage']
    coin : cryptobot.CryptoAsset
    coin = added_coins[symbol]
    if buy_percentage:
        coin.market_buy(float(buy_percentage))
    if follow_percentage and safety_percentage:
        coin.start_TSL(
            float(follow_percentage),
            limit_sell_safety_percent=float(safety_percentage),
            sell_order_type='limit'
        )
    elif follow_percentage and not safety_percentage:
        coin.start_TSL(
            float(follow_percentage),
            sell_order_type='market'
        )

    return JSONResponse({
        'status': True
    })

async def get_added_coins(request):
    coin : cryptobot.CryptoAsset
    data = {}
    for coin in added_coins.values():
        data[f"{coin.base_currency} {coin.quote_currency}"] = coin.get_balance()
    return JSONResponse(data)

async def stop_tsl(request):
    base = request.query_params['base']
    quote = request.query_params['quote']
    added_coins[base+quote].stop_TSL()
    return JSONResponse({
        'status': True
    })

async def sell_all(request):
    base = request.query_params['base']
    quote = request.query_params['quote']
    added_coins[base+quote].stop_TSL()
    added_coins[base+quote].market_sell()
    return JSONResponse({
        'status': True
    })

async def remove_coin(request):
    base = request.query_params['base']
    quote = request.query_params['quote']
    added_coins.pop(base+quote)
    return JSONResponse({
        'status': True
    })

async def multi_limit(request):
    coin : cryptobot.CryptoAsset
    form = await request.form()
    base, quote = form['base'], form['quote']
    sell_perc = [float(num) for num in form['sell-perc'].split()]
    sell_quant = [float(num) for num in form['sell-quant'].split()]
    sell_data = {}
    for index, item in enumerate(sell_perc):
        sell_data[item] = sell_quant[index] if index < len(sell_quant) else None
    coin = added_coins[base+quote]
    coin.multi_limit_sell(sell_data)
    return JSONResponse({
        'status': True
    })

app = Starlette(debug=True, routes=[
    Route('/', homepage),
    Route('/addcoin', addcoin),
    Route('/getcoins', get_added_coins),
    Route('/buycoin', buycoin, methods=['POST']),
    Route('/stoptsl', stop_tsl),
    Route('/sellall', sell_all),
    Route('/removecoin', remove_coin),
    Route('/multilimit', multi_limit, methods=['POST']),
    Mount('/static', StaticFiles(directory='./cryptoserve/static'), name='static')
])
