"""
Lint the document definitions.
"""

from ausweiskopie.resources.document import Rectangle
from ausweiskopie.resources import DOCUMENTS, list_resources, get_resource, load_document

def test_all_unique_id():
    docs = {}
    for filename in list_resources(DOCUMENTS):
        with get_resource(filename, "rb") as document:
            doc = load_document(document, str(filename).endswith(".toml"))
            if doc.id in docs.keys():
                raise Exception(f"ID {doc.id} of '{filename}' is already used by {docs[doc.id]}")
            else:
                docs[doc.id] = filename

def test_issue_date_in_filename():
    for filename in list_resources(DOCUMENTS):
        with get_resource(filename, "rb") as document:
            doc = load_document(document, str(filename).endswith(".toml"))
            assert filename.stem.endswith(str(doc.meta.issuedSince))
