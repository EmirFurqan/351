import json
from flask import Flask, jsonify, request, abort, redirect, make_response
import time
from flask_cors import CORS
 
app = Flask(__name__)
 
# JSON file name
JSON_FILE = 'items.json'
 
# token for authentication
TOKEN = "token"
 
CORS(app)
# Model for items
class Item:
    def __init__(self, item_id, name, description, price):
        self.id = item_id
        self.name = name
        self.description = description
        self.price = price
 
    # method to convert the object attributs to dictionary as key value pairs
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
        }
       
# Load items from the json file
def load_items():
    try:
        with open(JSON_FILE, 'r') as file:
            items_data = json.load(file)
            items = {}
            for item in items_data:
                items[item['id']] = Item(item["id"], item["name"], item["description"], item["price"])
            return items
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
 
# Save the items in the json file
def save_items(items):
    with open(JSON_FILE, 'w') as file:
        json.dump([item.to_dict() for item in items.values()], file, indent=4)
 
# load items from the json file
items_db = load_items()
 
# check function for string size is larger than 100
def check_string_size(field):
    if len(field) > 100:
        abort(413, description="Too long field")
 
# check function number of object in the json file
def check_storage():
    counter = 0
    for item in items_db:
        counter += 1
       
    if counter >= 2:
        return True
 
 
 
# Helper function to get item by ID
def get_item_or_404(item_id):
    item = items_db.get(item_id)
    if item is None:
        abort(404, description="Item not found")
    return item
 
# Authentication checker for POST, PUT, DELETE requests
def check_authentication():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        abort(401, description="Unauthorized")
    
    token = auth_header.split(" ")[1]
    if token != TOKEN:
        abort(401, description="Unauthorized")
    return True
 
# get all items
@app.route("/items", methods=["GET"])
def get_items():
    etag = request.headers.get('If-None-Match')
    current_etag = str(len(items_db)) 

    #compare with previous result
    if etag == current_etag:
        return '', 304
    
    #if no match return new
    response = make_response(jsonify([item.to_dict() for item in items_db.values()]))
    response.headers['ETag'] = current_etag
    return response
 
# Get one item
@app.route("/items/<int:item_id>", methods=["GET"])
def get__spesific_item(item_id):
    item = get_item_or_404(item_id)
    return jsonify(item.to_dict())
 
# post an item if authenticated
@app.route("/items", methods=["POST"])
def create_item():
    check_authentication()  # check authentication
    data = request.json
    item_id = data.get("id")
   
    if data.get("name") == "":
        abort(400, description="Bad request")
    # check for existing item
    if item_id in items_db:
        abort(409, description="Item already exists")
   
    if check_storage():
        return jsonify({'error': 'Insufficient Storage'}), 507
   
    check_string_size(data["name"])
    check_string_size(data["description"])
    # initiliaze and add the new item and svae the updated items on the json file
    new_item = Item(item_id, data["name"], data["description"], data["price"])
    items_db[item_id] = new_item
    save_items(items_db)
   
    # return the new added item with status code of 201
    return jsonify(new_item.to_dict()), 201
 
# PUT
@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    check_authentication()  # Requires authentication
    item = get_item_or_404(item_id)
   
    data = request.json #get the request as a python dictionary
    item.name = data["name"]
    item.description = data.get("description", "")
    item.price = data["price"]
   
    check_string_size(data["name"])
    check_string_size(data["description"])
   
    items_db[item_id] = item
    save_items(items_db)
    return jsonify(item.to_dict())
 
# PATCH
@app.route("/items/<int:item_id>", methods=["PATCH"])
def patch_item(item_id):
    check_authentication()  # Requires authentication
    item = get_item_or_404(item_id)
    data = request.json #get the request as a python dictionary
   
    # Check each field, if exists in data patch the chosen item
    if "name" in data:
        check_string_size(data["name"])
        item.name = data["name"]
    if "description" in data:
        check_string_size(data["description"])
        item.description = data["description"]
    if "price" in data:
        item.price = data["price"]
       
    items_db[item_id] = item
    save_items(items_db)
    return jsonify(item.to_dict())
 
# delete
@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    check_authentication()  # Requires authentication
    item = get_item_or_404(item_id)
   
    del items_db[item_id]
    save_items(items_db)
    return '', 204
 
@app.route("/admin")
def admin_section(item_id):
    check_authentication()  # Requires authentication
    abort()


#redirect to /items
@app.route("/redirect", methods=["GET"])
def redirect_items():
    return redirect("/items", code=307)
 
if __name__ == "__main__":
    app.run(debug=True, port=5000,host='0.0.0.0')