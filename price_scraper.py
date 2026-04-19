import asyncio
import re

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Smart Price Finder API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRAPER_API_KEY = "1ad339d0ee8948b4170a315f1ea7df28"

def scraper_url(target: str, render: bool = False) -> str:
    base = f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={target}&country_code=us"
    if render:
        base += "&render=true"
    return base

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ─────────────────────────────────────────────────────────
#  AMAZON  (amazon.com – more reliable than .in with proxy)
# ─────────────────────────────────────────────────────────
async def scrape_amazon(client: httpx.AsyncClient, q: str) -> list[dict]:
    target = f"https://www.amazon.com/s?k={q.replace(' ', '+')}"
    url = scraper_url(target)
    products = []
    try:
        r = await client.get(url, headers=HEADERS, timeout=60)
        soup = BeautifulSoup(r.content, "lxml")

        # Amazon uses data-component-type="s-search-result" on grid items
        items = soup.select('[data-component-type="s-search-result"]')
        print(f"[Amazon] Found {len(items)} raw items")

        for item in items[:15]:
            try:
                # Title — multiple fallback selectors
                name_el = (
                    item.select_one("h2 > a > span") or
                    item.select_one("h2 span.a-text-normal") or
                    item.select_one(".a-size-medium.a-color-base.a-text-normal")
                )

                # Price — whole number part
                price_el = item.select_one(".a-price > .a-offscreen")
                if not price_el:
                    price_el = item.select_one(".a-price-whole")

                # Link
                link_el = item.select_one("h2 > a") or item.select_one("a.a-link-normal")

                # Image
                img_el = item.select_one("img.s-image")

                if not (name_el and price_el and link_el):
                    continue

                raw_price = price_el.get_text(strip=True).replace("$", "").replace(",", "").strip()
                price = float(re.search(r"[\d.]+", raw_price).group())

                href = link_el.get("href", "")
                if not href.startswith("http"):
                    href = "https://www.amazon.com" + href

                products.append({
                    "name": name_el.get_text(strip=True),
                    "price": price,
                    "price_formatted": f"${price:,.2f}",
                    "link": href,
                    "image": img_el.get("src") if img_el else None,
                    "platform": "Amazon",
                    "currency": "USD",
                })
            except Exception:
                continue

        print(f"[Amazon] Parsed {len(products)} products")
    except Exception as e:
        print(f"[Amazon] Error: {e}")
    return products


# ─────────────────────────────────────────────────────────
#  EBAY  — selectors verified against live ScraperAPI HTML
# ─────────────────────────────────────────────────────────
async def scrape_ebay(client: httpx.AsyncClient, q: str) -> list[dict]:
    target = f"https://www.ebay.com/sch/i.html?_nkw={q.replace(' ', '+')}&_sacat=0&LH_BIN=1"
    url = scraper_url(target)
    products = []
    try:
        r = await client.get(url, headers=HEADERS, timeout=60)
        soup = BeautifulSoup(r.content, "lxml")

        # eBay renders items in <li class="s-item s-item__pl-on-bottom"> inside ul.srp-results
        items = (
            soup.select("ul.srp-results li.s-item") or
            soup.select("li.s-item") or
            soup.select(".s-item__wrapper")
        )
        print(f"[eBay] Found {len(items)} raw items")

        for item in items[:15]:
            try:
                # Skip "More results" placeholder items
                if "s-item--large" not in item.get("class", []) and not item.select_one(".s-item__title"):
                    continue

                name_el  = item.select_one(".s-item__title span[role='heading']") or item.select_one(".s-item__title")
                price_el = item.select_one(".s-item__price")
                link_el  = item.select_one("a.s-item__link")
                img_el   = item.select_one("img.s-item__image-img") or item.select_one(".s-item__image img")

                if not (name_el and price_el and link_el):
                    continue

                title = name_el.get_text(strip=True)
                if not title or title.lower() == "shop on ebay":
                    continue

                raw = price_el.get_text(strip=True).replace(",", "").replace(" ", "")
                m = re.search(r"[\d.]+", raw)
                if not m:
                    continue
                price = float(m.group())

                img_src = None
                if img_el:
                    img_src = img_el.get("src") or img_el.get("data-src")
                    # eBay uses lazy-loading; swap tiny placeholder for real image
                    if img_src and "gif" in img_src:
                        img_src = img_el.get("data-src") or img_src

                products.append({
                    "name": title,
                    "price": price,
                    "price_formatted": f"${price:,.2f}",
                    "link": link_el["href"],
                    "image": img_src,
                    "platform": "eBay",
                    "currency": "USD",
                })
            except Exception:
                continue

        print(f"[eBay] Parsed {len(products)} products")
    except Exception as e:
        print(f"[eBay] Error: {e}")
    return products


# ─────────────────────────────────────────────────────────
#  WALMART — selectors verified against live ScraperAPI HTML
# ─────────────────────────────────────────────────────────
async def scrape_walmart(client: httpx.AsyncClient, q: str) -> list[dict]:
    target = f"https://www.walmart.com/search?q={q.replace(' ', '+')}"
    url = scraper_url(target)
    products = []
    try:
        r = await client.get(url, headers=HEADERS, timeout=60)
        soup = BeautifulSoup(r.content, "lxml")

        # Walmart uses data-item-id on article or div elements
        items = (
            soup.select("div[data-item-id]") or
            soup.select("article[data-item-id]") or
            soup.select('[data-testid="item-stack"]') or
            soup.select(".sans-serif.mid-gray")
        )
        print(f"[Walmart] Found {len(items)} raw items")

        for item in items[:15]:
            try:
                # Multiple title selector fallbacks
                name_el = (
                    item.select_one('[data-automation-id="product-title"]') or
                    item.select_one("span.w_iUH7") or
                    item.select_one("[itemprop='name']") or
                    item.select_one("a[link-identifier] span") or
                    item.select_one("span.lh-title")
                )

                # Price fallbacks
                price_el = (
                    item.select_one('[itemprop="price"]') or
                    item.select_one("div[data-automation-id='product-price'] span.w_0K2k") or
                    item.select_one(".price-main span") or
                    item.select_one(".f2.fw4.w_iUH7")
                )

                link_el = item.select_one("a[link-identifier]") or item.select_one("a")
                img_el  = item.select_one("img[data-testid='productTileImage']") or item.select_one("img")

                if not (name_el and link_el):
                    continue

                # Price can be in content attr or text
                price = None
                if price_el:
                    content_val = price_el.get("content", "")
                    raw_text = price_el.get_text(strip=True).replace("$", "").replace(",", "")
                    for attempt in [content_val, raw_text]:
                        m = re.search(r"[\d.]+", attempt)
                        if m:
                            price = float(m.group())
                            break
                if price is None:
                    continue

                href = link_el.get("href", "")
                if not href.startswith("http"):
                    href = "https://www.walmart.com" + href

                products.append({
                    "name": name_el.get_text(strip=True),
                    "price": price,
                    "price_formatted": f"${price:,.2f}",
                    "link": href,
                    "image": img_el.get("src") if img_el else None,
                    "platform": "Walmart",
                    "currency": "USD",
                })
            except Exception:
                continue

        print(f"[Walmart] Parsed {len(products)} products")
    except Exception as e:
        print(f"[Walmart] Error: {e}")
    return products


# ─────────────────────────────────────────────────────────
#  BEST BUY  (with JS rendering)
# ─────────────────────────────────────────────────────────
async def scrape_bestbuy(client: httpx.AsyncClient, q: str) -> list[dict]:
    target = f"https://www.bestbuy.com/site/searchpage.jsp?st={q.replace(' ', '+')}"
    url = scraper_url(target, render=True)
    products = []
    try:
        r = await client.get(url, headers=HEADERS, timeout=90)
        soup = BeautifulSoup(r.content, "lxml")

        items = soup.select("li.sku-item")
        print(f"[Best Buy] Found {len(items)} raw items")

        for item in items[:15]:
            try:
                name_el  = item.select_one(".sku-title a") or item.select_one("h4.sku-header a")
                price_el = (
                    item.select_one(".priceView-hero-price span[aria-hidden='true']") or
                    item.select_one(".priceView-customer-price span") or
                    item.select_one('[data-testid="customer-price"] span')
                )
                link_el  = item.select_one(".sku-title a") or item.select_one("a.image-link")
                img_el   = item.select_one("img.product-image")

                if not (name_el and price_el and link_el):
                    continue

                raw = price_el.get_text(strip=True).replace("$", "").replace(",", "")
                m = re.search(r"[\d.]+", raw)
                if not m:
                    continue
                price = float(m.group())

                href = link_el.get("href", "")
                if not href.startswith("http"):
                    href = "https://www.bestbuy.com" + href

                products.append({
                    "name": name_el.get_text(strip=True),
                    "price": price,
                    "price_formatted": f"${price:,.2f}",
                    "link": href,
                    "image": img_el.get("src") if img_el else None,
                    "platform": "Best Buy",
                    "currency": "USD",
                })
            except Exception:
                continue

        print(f"[Best Buy] Parsed {len(products)} products")
    except Exception as e:
        print(f"[Best Buy] Error: {e}")
    return products


# ─────────────────────────────────────────────────────────
#  API Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/compare-prices")
async def compare_prices(product: str = Query(...)):
    if len(product.strip()) < 2:
        raise HTTPException(status_code=400, detail="Product name must be at least 2 characters.")

    async with httpx.AsyncClient() as client:
        # Best Buy uses JS render so we run it separately to not block the others
        amazon_task  = scrape_amazon(client, product)
        ebay_task    = scrape_ebay(client, product)
        walmart_task = scrape_walmart(client, product)
        bestbuy_task = scrape_bestbuy(client, product)

        results_nested = await asyncio.gather(
            amazon_task, ebay_task, walmart_task, bestbuy_task
        )

    all_results = [item for sublist in results_nested for item in sublist]
    all_results.sort(key=lambda x: x["price"])

    seen: set = set()
    for item in all_results:
        item["best_in_platform"] = item["platform"] not in seen
        seen.add(item["platform"])

    if all_results:
        all_results[0]["overall_best"] = True

    return all_results


@app.get("/debug-scrape")
async def debug_scrape(product: str = Query(default="iPhone 15"), site: str = Query(default="ebay")):
    """
    Debug endpoint – returns the raw HTML snippet so you can inspect what
    ScraperAPI actually returns for a given site.
    Visit: http://localhost:8000/debug-scrape?product=iphone+15&site=ebay
    """
    sites = {
        "amazon":  f"https://www.amazon.com/s?k={product.replace(' ', '+')}",
        "ebay":    f"https://www.ebay.com/sch/i.html?_nkw={product.replace(' ', '+')}",
        "walmart": f"https://www.walmart.com/search?q={product.replace(' ', '+')}",
        "bestbuy": f"https://www.bestbuy.com/site/searchpage.jsp?st={product.replace(' ', '+')}",
    }

    target = sites.get(site.lower(), sites["ebay"])
    render = site.lower() == "bestbuy"
    url = scraper_url(target, render=render)

    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS, timeout=90)
        html = r.text

    soup = BeautifulSoup(html, "lxml")
    return {
        "site": site,
        "product": product,
        "status_code": r.status_code,
        "html_length": len(html),
        "title": soup.title.string if soup.title else "N/A",
        "snippet": html[:3000],
    }


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0", "scraper": "ScraperAPI",
            "api_key": f"{SCRAPER_API_KEY[:6]}…{SCRAPER_API_KEY[-4:]}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "price_scraper:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["."],
        reload_includes=["price_scraper.py"],
    )
