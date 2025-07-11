from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/json_plugin", methods=["POST"])
def json_plugin_post():
    data = request.get_json()

    app.logger.info("Data received: %r", data)

    message = "No data" if data is None else "Data received"
    return jsonify({"message": message, "data": data}), 201


@app.route("/test_connection", methods=["GET"])
def test_connection():
    return jsonify({"message": "OK"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
