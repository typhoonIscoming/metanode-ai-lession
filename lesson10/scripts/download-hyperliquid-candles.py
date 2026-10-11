import csv
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)

END_MS = int(time.time() * 1000)
START_MS = END_MS - 240 * 24 * 60 * 60 * 1000
URL = 'https://api.hyperliquid.xyz/info'
SYMBOLS = ['BTC', 'ETH', 'SOL']

for symbol in SYMBOLS:
    payload = {
        'type': 'candleSnapshot',
        'req': {
            'coin': symbol,
            'interval': '1d',
            'startTime': START_MS,
            'endTime': END_MS,
        },
    }
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        candles = json.loads(response.read().decode('utf-8'))

    rows = []
    for c in candles:
        rows.append({
            'timestamp': time.strftime('%Y-%m-%d', time.gmtime(int(c['t']) / 1000)),
            'open': c['o'],
            'high': c['h'],
            'low': c['l'],
            'close': c['c'],
            'volume': c['v'],
        })

    if len(rows) < 60:
        raise RuntimeError(f'Hyperliquid returned too few rows for {symbol}: {len(rows)}')

    out = DATA / f'{symbol}.csv'
    with out.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        writer.writeheader()
        writer.writerows(rows)
    print(f'{symbol}: wrote {len(rows)} rows to {out}')
