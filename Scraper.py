import requests
from bs4 import BeautifulSoup

URL = "https://ware-consulting.vercel.app/"

def scrape_products():
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    products = []
    seen = set()
    # find cards or items
    for card in soup.find_all(["article", "div"], class_=lambda c: c and "product" in c.lower()):
        title = desc = img = ""
        t = card.find(["h2","h3","h4"])
        if t: title = t.get_text(strip=True)
        p = card.find("p")
        if p: desc = p.get_text(strip=True)
        imgtag = card.find("img")
        if imgtag and imgtag.has_attr("src"):
            img = imgtag["src"]
        if title and (title, desc) not in seen:
            seen.add((title, desc))
            products.append({"title": title, "desc": desc, "img": img})
    # fallback if no products found
    if not products:
        for h in soup.find_all(["h3","h4"]):
            title = h.get_text(strip=True)
            if len(title) > 3:
                products.append({"title": title, "desc": "", "img": ""})
    return products
