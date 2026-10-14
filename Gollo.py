import json
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# Telegram config
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Product list with expected/wanted prices
products = [
    {
        "name": "GOLLO-WHIRLPOOL-WRFF3536SZ",
        "url": "https://www.gollo.com/refrigerador-whirlpool-850l-3-french-door-wrff3536sz-6001420061/p",
        "expected": "1279265",
        "expected_msrp": "1499900",
        "wanted": "1150000",
    },
    {
        "name": "MONGE-SAMSUNG-RF32CG5410S9A",
        "url": "https://www.tiendamonge.com/refrigeradora-french-door-samsung-31cp-rf32cg5410s9a-wi-fi-inoxidable-187719",
        "expected": "1399900",
        "expected_msrp": "1474999",
        "wanted": "1250000",
    },
    {
        "name": "GOLLO-SAMSUNG-RF32CG5910B1AP",
        "url": "https://www.gollo.com/refrigeradora-samsung-french-door-semi-automatico-31-pies-rf32cg5910b1ap-6001420042/p",
        "expected": "1799875",
        "expected_msrp": "1925000",
        "wanted": "1600000",
    },
    {
        "name": "MONGE-SAMSUNG-RF80H30CETED",
        "url": "https://www.tiendamonge.com/refrigeradora-french-door-samsung-30cp-rf80h30ceted-inoxidable-203628",
        "expected": "1879900",
        "expected_msrp": "1879900",
        "wanted": "1650000",
    },
]

# Products tracked only for stock status (in stock / sold out), not price.
stock_products = [
    {
        "name": "TOYS-POKEMON-BLISTER-30TH-SURT2",
        "url": "https://www.tiendatoys.com/products/23619/cartas-para-intercambio-pokemon-blister-3-sobres-x10-1-gratis-30thaniversario-con-stickers-surt2-6a-en",
        "expected_status": "OutOfStock",
    },
    {
        "name": "TOYS-POKEMON-30ANOS-COLLECTION-POSTER",
        "url": "https://www.tiendatoys.com/products/23618/cartas-para-intercambio-pokemon-30th-anos-de-pokemon-collection-con-poster-6a-en",
        "expected_status": "OutOfStock",
    },
    {
        "name": "TOYS-POKEMON-SYLVEON-MEGA-TARJETA",
        "url": "https://www.tiendatoys.com/products/23617/cartas-de-pokemon-coleccion-30th-aniversario-sylveon-con-mega-trajeta-6a",
        "expected_status": "OutOfStock",
    },
    {
        "name": "TOYS-POKEMON-ENTRENAMIENTO-ELITE-BOX",
        "url": "https://www.tiendatoys.com/products/23616/cartas-de-pokemon-entrenamiento-30th-aniversario-6a",
        "expected_status": "OutOfStock",
    },
]

# Gollo's WAF blocks requests carrying a browser-like User-Agent on product
# pages (406 Not Acceptable); a plain/curl-style UA passes through fine.
# Monge and TiendaToys have no such restriction, so the same header works for all.
headers = {"User-Agent": "curl/8.0"}

messages = []
changed = []

for product in products:
    try:
        response = requests.get(product["url"], headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        price_box = soup.select_one(".product-info-price")
        price_span = price_box.find("span", class_="price-wrapper", attrs={"data-price-type": "finalPrice"}) if price_box else None
        msrp_span = price_box.find("span", class_="price-wrapper", attrs={"data-price-type": "oldPrice"}) if price_box else None
        price_raw = price_span["data-price-amount"] if price_span else None
        # No old-price block means there's no active discount, so MSRP == current price.
        msrp_raw = msrp_span["data-price-amount"] if msrp_span else price_raw
    except requests.RequestException as e:
        messages.append(f"{product['name']}: Error al consultar ({e})")
        continue

    if not price_raw:
        if "infinite_product_404_redirect" in response.text:
            messages.append(f"{product['name']}: La página ya no existe (404)")
        else:
            messages.append(f"{product['name']}: Precio no encontrado")
        continue

    current = int(float(price_raw))
    msrp = int(float(msrp_raw))
    expected = int(product["expected"])
    expected_msrp = int(product["expected_msrp"])
    wanted = int(product["wanted"])
    gap = current - wanted

    if current <= wanted:
        changed.append(f"🚨 BUY IT NOW 🚨\n{product['name']}: ₡{current:,} (alcanzó tu precio deseado ₡{wanted:,})")
    elif current != expected:
        changed.append(f"{product['name']}: ₡{current:,} (CAMBIÓ, antes ₡{expected:,})")

    if msrp != expected_msrp:
        changed.append(f"⚠️ {product['name']}: MSRP CAMBIÓ ₡{expected_msrp:,} → ₡{msrp:,}")

    messages.append(
        f"{product['name']}: ₡{current:,} (MSRP ₡{msrp:,})\nFaltan ₡{gap:,} para tu precio deseado (₡{wanted:,})"
    )

for product in stock_products:
    try:
        response = requests.get(product["url"], headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        status = None
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
            except (TypeError, ValueError):
                continue
            offers = data.get("offers") if isinstance(data, dict) else None
            if isinstance(offers, list):
                offers = offers[0] if offers else None
            if isinstance(offers, dict) and offers.get("availability"):
                status = offers["availability"].rsplit("/", 1)[-1]
                break
    except requests.RequestException as e:
        messages.append(f"{product['name']}: Error al consultar ({e})")
        continue

    if not status:
        messages.append(f"{product['name']}: Estado de stock no encontrado")
        continue

    expected_status = product["expected_status"]
    estado = "Agotado" if status == "OutOfStock" else "Disponible"

    if status != expected_status:
        changed.append(f"📦 {product['name']}: CAMBIÓ DE STOCK → {estado}")

    messages.append(f"{product['name']}: {estado}")

# Send Telegram message
if changed:
    message = "🔔 Hubo cambios:\n\n" + "\n\n".join(changed) + "\n\n---\n\n" + "\n\n".join(messages)
else:
    message = "Precios: sin cambios.\n\n" + "\n\n".join(messages)

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
data = {"chat_id": CHAT_ID, "text": message}
requests.post(telegram_url, data=data)
