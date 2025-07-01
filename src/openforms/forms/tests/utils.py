import os

EXPORTS_DIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "exports",
)
EXPORT_BLOB_FILENAMES = ["forms", "formSteps", "formDefinitions", "formLogic"]
EXPORT_BLOB = {
    "forms": "",
    "formSteps": "",
    "formDefinitions": "",
    "formLogic": "",
}

# convert the readable JSON files into an actual export blob of strings
for filename in EXPORT_BLOB_FILENAMES:
    path = os.path.join(EXPORTS_DIR, f"{filename}.json")
    with open(path) as infile:
        EXPORT_BLOB[filename] = infile.read()
