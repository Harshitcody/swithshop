from flask import Flask, jsonify, request, render_template_string
from rec_engine import RecEngine
import scraper

app = Flask(__name__)
engine = RecEngine()

# Scrape data from the website
products = scraper.scrape_products()
if not products:
    products = [
        {"title": "Wireless Headphones", "desc": "Bluetooth noise cancelling", "img": ""},
        {"title": "Running Shoes", "desc": "Lightweight breathable mesh", "img": ""},
        {"title": "Smart Watch", "desc": "Heart rate and fitness tracking", "img": ""},
        {"title": "Laptop Bag", "desc": "Stylish waterproof laptop bag", "img": ""}
    ]

# Add scraped products to the recommender
for i, p in enumerate(products):
    engine.add_product(i + 1, p["title"], p["desc"], p.get("img", ""))
engine.build()

# -----------------------------
# HTML Frontend (served at "/")
# -----------------------------
TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Ware Consulting Recommender</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f6f8fa; margin: 0; padding: 20px; }
        h1 { text-align: center; color: #333; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; }
        .card { background: white; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); padding: 15px; text-align: center; }
        img { width: 100%; height: 180px; object-fit: cover; border-radius: 8px; }
        button { background: #007BFF; color: white; border: none; border-radius: 6px; padding: 8px 12px; cursor: pointer; margin-top: 10px; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <h1>Ware Consulting Product Recommender</h1>
    <div id="product-grid" class="grid"></div>

    <h2 style="margin-top:40px; text-align:center;">Recommended for You</h2>
    <div id="recommend-grid" class="grid"></div>

    <script>
        async function loadProducts() {
            const res = await fetch('/products');
            const data = await res.json();
            const grid = document.getElementById('product-grid');
            grid.innerHTML = '';
            data.forEach(p => {
                const div = document.createElement('div');
                div.className = 'card';
                div.innerHTML = `
                    <img src="${p.img || 'https://via.placeholder.com/250'}" />
                    <h3>${p.title}</h3>
                    <p>${p.desc}</p>
                    <button onclick="likeProduct(${p.id})">Like</button>
                `;
                grid.appendChild(div);
            });
        }

        async function likeProduct(id) {
            await fetch('/like', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id})
            });
            loadRecommendations();
        }

        async function loadRecommendations() {
            const res = await fetch('/recommend');
            const data = await res.json();
            const grid = document.getElementById('recommend-grid');
            grid.innerHTML = '';
            data.forEach(p => {
                const div = document.createElement('div');
                div.className = 'card';
                div.innerHTML = `
                    <img src="${p.img || 'https://via.placeholder.com/250'}" />
                    <h3>${p.title}</h3>
                    <p>${p.desc}</p>
                    <p><strong>Score:</strong> ${p.score.toFixed(2)}</p>
                `;
                grid.appendChild(div);
            });
        }

        loadProducts();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/products")
def get_products():
    return jsonify(engine.products)

@app.route("/like", methods=["POST"])
def like_product():
    data = request.json
    pid = data.get("id")
    try:
        engine.like_product(int(pid))
        return jsonify({"status": "liked", "id": pid})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/recommend")
def recommend():
    top = int(request.args.get("top", 5))
    recs = engine.get_recommendations(top_n=top)
    return jsonify(recs)

if __name__ == "__main__":
    print("🚀 Running Flask + Cython recommender on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
