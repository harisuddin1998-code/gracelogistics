"""Live PSO fuel prices.

PSO has no public price API, so the rates are read from the official fuel price page
(https://psopk.com/en/fuels/fuel-prices).  Results are cached in memory for an hour and
the last good result is kept, so a slow/unreachable PSO site never breaks the fuel form.
"""
import re
import time
import urllib.request
from datetime import datetime

PSO_PRICES_URL = 'https://psopk.com/en/fuels/fuel-prices'
CACHE_SECONDS = 60 * 60

# Product image on the PSO page -> (key, label, unit)
_PRODUCTS = {
    'premier': ('petrol', 'Petrol (Premier Euro 5)', 'Ltr'),
    'cetanewhite': ('diesel', 'Diesel (Hi-Cetane Euro 5)', 'Ltr'),
    'octanewhite': ('hobc', 'HOBC (High Octane)', 'Ltr'),  # first city on the page (Karachi)
}

_PRICE_RE = r'Rs\.\s*([\d,]+(?:\.\d+)?)\s*/\s*(Ltr|KG)'

_cache = {'data': None, 'fetched_at': 0}


def _parse(html):
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)  # PSO keeps retired products commented out
    prices = {}

    for image, (key, label, unit) in _PRODUCTS.items():
        match = re.search(rf'fuels/fp/{image}\.png.*?{_PRICE_RE}', html, flags=re.S)
        if match:
            prices[key] = {'label': label, 'price': float(match.group(1).replace(',', '')), 'unit': unit}

    match = re.search(rf'LPG[^<]*</label>\s*<p[^>]*>\s*{_PRICE_RE}', html, flags=re.S)
    if match:
        prices['lpg'] = {'label': 'LPG', 'price': float(match.group(1).replace(',', '')), 'unit': 'KG'}

    return prices


def get_pso_prices(force=False):
    """Return {'prices': {...}, 'fetched_at': str, 'source': url, 'stale': bool, 'error': str|None}."""
    now = time.time()
    if not force and _cache['data'] and now - _cache['fetched_at'] < CACHE_SECONDS:
        return _cache['data']

    try:
        request = urllib.request.Request(PSO_PRICES_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=15) as response:
            prices = _parse(response.read().decode('utf-8', errors='ignore'))
        if not prices:
            raise ValueError('price layout on PSO website has changed')
        _cache['data'] = {
            'prices': prices,
            'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'source': PSO_PRICES_URL,
            'stale': False,
            'error': None,
        }
        _cache['fetched_at'] = now
        return _cache['data']
    except Exception as exc:
        if _cache['data']:
            return dict(_cache['data'], stale=True, error=str(exc))
        return {'prices': {}, 'fetched_at': None, 'source': PSO_PRICES_URL, 'stale': True, 'error': str(exc)}
