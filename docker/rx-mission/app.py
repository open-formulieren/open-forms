import json

from flask import Flask, jsonify

app = Flask(__name__)
products = {}


@app.route("/product/<string:product_uuid>", methods=["GET"])
def handle_request(product_uuid):
    if product_uuid not in products:
        return jsonify({"message": "Product not found"}), 404

    product = products[product_uuid]
    return jsonify(product)


if __name__ == "__main__":
    with open("./fixtures/rx-mission-products.json", encoding="utf-8") as json_file:
        parsed_json = json.load(json_file)
        products = {product["id"]: product for product in parsed_json["products"]}

    app.run(host="0.0.0.0", port=81, debug=True)
