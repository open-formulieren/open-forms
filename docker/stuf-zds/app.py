import logging
from secrets import token_hex

from flask import Flask, Response, request
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())

app = Flask(__name__)

# Set up logging to stdout
logging.basicConfig(level=logging.INFO)


@app.route("/stuf-zds", methods=["POST", "GET"])
def handle_request():
    # Log the request body
    app.logger.info("Request body: %s", request.data.decode("utf-8"))

    if "genereerZaakIdentificatie" in request.data.decode("utf-8"):
        template = env.get_template("genereerZaakIdentificatie.xml")
        return Response(
            template.render(zaak_identificatie=token_hex(8)), content_type="text/xml"
        )
    elif "zakLk01" in request.data.decode("utf-8"):
        template = env.get_template("creeerZaak.xml")
        return Response(template.render(), content_type="text/xml")
    elif "genereerDocumentIdentificatie" in request.data.decode("utf-8"):
        template = env.get_template("genereerDocumentIdentificatie.xml")
        return Response(
            template.render(document_identificatie=token_hex(8)),
            content_type="text/xml",
        )
    elif "edcLk01" in request.data.decode("utf-8"):
        template = env.get_template("voegZaakdocumentToe.xml")
        return Response(template.render(), content_type="text/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
