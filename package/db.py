from datetime import datetime
import logging
import requests

logger = logging.getLogger(__name__)

COUCHDB_URL = ""
USER = ""
PASSWORD = ""
ID = "" # update

# ====================================================
def convert_datetimes(obj):
    if isinstance(obj, dict):
        return {k: convert_datetimes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetimes(v) for v in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

# ====================================================
def create_index():
    pass
    #index = {
    #    "index": {
    #        "fields": ["type", "fetched_at"]
    #    },
    #    "name": "type-fetched_at-index"
    #}
    #session = requests.Session()
    #res = session.post(f"{COUCHDB_URL}/tenki-yohou/_index",auth=(USER, PASSWORD), json=index)

# ====================================================
def getDocumentUpdate():
    try:
        return requests.get(f"{COUCHDB_URL}/tenki_update/{ID}",auth=(USER, PASSWORD))
    except Exception as e:
        logger.error('getDocumentUpdate エラー: %s', e)
        return {}

def putDocumentUpdate(doc):
    try:
        clean_doc = convert_datetimes(doc)
        return requests.put(f"{COUCHDB_URL}/tenki_update/{ID}",auth=(USER, PASSWORD),json=clean_doc)
    except Exception as e:
        logger.error('putDocumentUpdate エラー: %s', e)
        return {}

def postDocumentTenki(doc):
    try:
        session = requests.Session()
        new_doc = {"type": "tenki_yohou","fetched_at": datetime.now().isoformat(),"data": doc}
        return session.post(f"{COUCHDB_URL}/tenki_yohou",auth=(USER, PASSWORD),json=new_doc)
    except Exception as e:
        logger.error('postDocumentTenki エラー: %s', e)
        return {}

def postDocumentGaikyo(doc):
    try:
        session = requests.Session()
        new_doc = {"type": "tenki_gaikyo","fetched_at": datetime.now().isoformat(),"text": doc}
        return session.post(f"{COUCHDB_URL}/tenki_gaikyo",auth=(USER, PASSWORD),json=new_doc)
    except Exception as e:
        logger.error('postDocumentTenki エラー: %s', e)
        return {}

# =================================================
def getLatestTenki():
    query = {
        "selector": {
            "type": "tenki_yohou"
        },
        "sort": [{"fetched_at": "desc"}],  # fetched_atの降順(新しい順)
        "limit": 1                          # 先頭の1件だけ
    }
    session = requests.Session()
    res = session.post(f"{COUCHDB_URL}/tenki_yohou/_find",auth=(USER, PASSWORD),json=query)
    result = res.json()

    return result["docs"][0]["data"]

def getLatestGaikyo():
    query = {
        "selector": {
            "type": "tenki_gaikyo"
        },
        "sort": [{"fetched_at": "desc"}],  # fetched_atの降順(新しい順)
        "limit": 1                          # 先頭の1件だけ
    }
    session = requests.Session()
    res = session.post(f"{COUCHDB_URL}/tenki_gaikyo/_find",auth=(USER, PASSWORD),json=query)
    result = res.json()

    return result["docs"][0]["text"]
        