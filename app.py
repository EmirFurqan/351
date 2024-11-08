import json
from flask import Flask, jsonify, request, abort, redirect, make_response
import time

app = Flask(__name__)

# JSON dosya adı
JSON_FILE = 'items.json'

# Dummy token for authentication (this would usually be a JWT or similar)
VALID_TOKEN = "token"

# Model for items
class Item:
    def __init__(self, item_id, name, description, price):
        self.id = item_id
        self.name = name
        self.description = description
        self.price = price

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
        }
        

# Helper functions for JSON file operations
def load_items():
    try:
        with open(JSON_FILE, 'r') as file:
            items_data = json.load(file)
            return {item['id']: Item(**item) for item in items_data}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_items(items):
    with open(JSON_FILE, 'w') as file:
        json.dump([item.to_dict() for item in items.values()], file, indent=4)

# In-memory cache of items (loaded from JSON file initially)
items_db = load_items()

# Helper function to get item by ID
def get_item_or_404(item_id):
    item = items_db.get(item_id)
    if item is None:
        abort(404, description="Item not found")
    return item

# Authentication decorator
def authenticate():
    token = request.headers.get("Authorization")
    if token != VALID_TOKEN:
        abort(401, description="Network Authentication Required")  # or 401 for Unauthorized
    return True

@app.route("/items", methods=["GET"])
def get_items():
    """GET all items, return 304 Not Modified if ETag matches"""
    etag = request.headers.get('If-None-Match')
    current_etag = str(hash(tuple(items_db.keys())))  # Generate a simple ETag from item IDs

    # If ETag matches, return 304 Not Modified
    if etag == current_etag:
        return '', 304

    # Otherwise, return items with a new ETag
    response = make_response(jsonify([item.to_dict() for item in items_db.values()]))
    response.headers['ETag'] = current_etag
    return response

@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    """GET a single item by ID"""
    item = get_item_or_404(item_id)
    return jsonify(item.to_dict())

@app.route("/items", methods=["POST"])
def create_item():
    """POST to create a new item"""
    authenticate()  # Requires authentication
    data = request.json
    item_id = data.get("id")
    if item_id in items_db:
        abort(409, description="Item already exists")
    new_item = Item(item_id, data["name"], data.get("description", ""), data["price"])
    items_db[item_id] = new_item
    save_items(items_db)
    return jsonify(new_item.to_dict()), 201

@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    """PUT to update an existing item"""
    authenticate()  # Requires authentication
    item = get_item_or_404(item_id)
    data = request.json
    item.name = data["name"]
    item.description = data.get("description", "")
    item.price = data["price"]
    items_db[item_id] = item
    save_items(items_db)
    return jsonify(item.to_dict())

@app.route("/items/<int:item_id>", methods=["PATCH"])
def patch_item(item_id):
    """PATCH to partially update an existing item"""
    authenticate()  # Requires authentication
    item = get_item_or_404(item_id)
    data = request.json
    if "name" in data:
        item.name = data["name"]
    if "description" in data:
        item.description = data["description"]
    if "price" in data:
        item.price = data["price"]
    items_db[item_id] = item
    save_items(items_db)
    return jsonify(item.to_dict())

@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """DELETE an item by ID"""
    authenticate()  # Requires authentication
    item = get_item_or_404(item_id)
    del items_db[item_id]
    save_items(items_db)
    return '', 204

# New endpoint to temporarily redirect to /items
@app.route("/items/redirect", methods=["GET"])
def redirect_items():
    """GET to temporarily redirect to /items"""
    return redirect("/items", code=307)

@app.route("/items/long_process", methods=["GET"])
def long_process():
    """Bu endpoint, bir işlem süresi boyunca 408 hata kodu döndürmeye çalışacak"""
    timeout = int(request.args.get('timeout', 10))  # Varsayılan timeout 10 saniye
    print(f"Process will run for {timeout} seconds...")

    # Burada belirli bir süreyi bekletiyoruz, bu süreyi aşarsa 408 dönecek
    time.sleep(timeout)

    if timeout > 5:
        # Eğer 5 saniyeden fazla beklediyse, 408 Request Timeout hatası döner
        abort(408, description="Request took too long, timeout reached")

    return jsonify({"message": "Process completed successfully!"})



if __name__ == "__main__":
    app.run(debug=True)
