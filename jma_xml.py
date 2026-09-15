from package import db, common
from datetime import datetime
import logging

FLAG_UPDATE = -1
logger = logging.getLogger(__name__)

key_update = 'teiji_choki'  # 定時情報（長期）
key_yohou = 'tenki_yohou'   # 府県天気予報（Ｒ１）
key_gaikyo = 'tenki_gaikyo' # 府県天気概況

# ==============================================

# タグの種類
# {http://www.w3.org/2005/Atom}title
# {http://www.w3.org/2005/Atom}id
# {http://www.w3.org/2005/Atom}updated
# {http://www.w3.org/2005/Atom}author
# {http://www.w3.org/2005/Atom}link
# {http://www.w3.org/2005/Atom}content
# {http://www.w3.org/2005/Atom}entry

def storeEntryToDict(entry):
    dic_entry={
        'title':'',
        'id':'',
        'updated':'',
        'content':'',
        'link':'',
        'author':''
    }
    try:
        for item in entry:
            match item.tag:
                case '{http://www.w3.org/2005/Atom}title':
                    dic_entry['title'] = item.text
                case '{http://www.w3.org/2005/Atom}id':
                    dic_entry['id'] = item.text
                case '{http://www.w3.org/2005/Atom}updated':
                    dic_entry['updated'] = item.text
                case '{http://www.w3.org/2005/Atom}content':
                    dic_entry['content'] = item.text
                case '{http://www.w3.org/2005/Atom}link':
                    dic_entry['link'] = item.get("href")
                case '{http://www.w3.org/2005/Atom}author':
                    entry_author = item.find('{http://www.w3.org/2005/Atom}name')
                    if entry_author is not None:
                        dic_entry['author'] =entry_author.text
    except Exception as e:
        logger.error('辞書作成中にエラー: ', e)
    return dic_entry
    
# ==============================================
def main():
    logger.info('処理開始')
    res = db.getDocumentUpdate()
    if res == {}:
        logger.error("updateのドキュメント取得に失敗しました")
        logger.info('処理終了')
        return
    elif res.status_code >= 400:
        logger.error(str(res.status_code) + ' ' + str(res.json()))
        logger.info('処理終了')
        return
    else:
        dic_update = res.json()

    FLAG_UPDATE = 1
    dic_update = dic_update
    tree = common.getXML(0, dic_update[key_update]['link'])
    root = tree.getroot()
    for entry in root:
        # =======================================
        # 更新日のチェックを行う
        # 更新されていなければ処理をせずに終了する
        # =======================================
        if entry.tag == '{http://www.w3.org/2005/Atom}updated':
            dt1 = datetime.fromisoformat(entry.text)
            dt2 = datetime.fromisoformat(dic_update[key_update]['update'])
    
            if(dt1 <= dt2):
                FLAG_UPDATE = 0
                logger.info('更新なしのため、処理終了')
                break
            else:
                dic_update[key_update]['update'] = dt1
        # =======================================
        # Entryのみ処理をする
        # =======================================
        if entry.tag == '{http://www.w3.org/2005/Atom}entry':
            
            dic_entry = storeEntryToDict(entry)
            
            # =======================================
            # 特定の予報のみ処理をする
            # =======================================
            if dic_entry['author'] == dic_update[key_yohou]['author'] and dic_entry['title'] == dic_update[key_yohou]['title']:
                
                dt3 = datetime.fromisoformat(dic_entry['updated'])
                dt4 = datetime.fromisoformat(dic_update[key_yohou]['update'])
                
                if dt3 >= dt4:

                    # 辞書の更新
                    logger.info('更新: 府県天気予報（Ｒ１）/' + dic_entry['author'])
                    dic_update[key_yohou]['update'] = dic_entry['updated']
                    dic_update[key_yohou]['link'] = dic_entry['link']
                    dic_update[key_yohou]['readed'] = 0
            # =======================================
            # 特定の予報のみ処理をする
            # =======================================
            if dic_entry['author'] == dic_update[key_gaikyo]['author'] and dic_entry['title'] == dic_update[key_gaikyo]['title']:
                
                dt3 = datetime.fromisoformat(dic_entry['updated'])
                dt4 = datetime.fromisoformat(dic_update[key_gaikyo]['update'])
                
                if dt3 >= dt4:

                    # 辞書の更新
                    logger.info('更新: 府県天気概況 /' + dic_entry['author'])
                    dic_update[key_gaikyo]['update'] = dic_entry['updated']
                    dic_update[key_gaikyo]['link'] = dic_entry['link']
                    dic_update[key_gaikyo]['readed'] = 0

    if FLAG_UPDATE:
        res = db.putDocumentUpdate(dic_update)
        if res.status_code >= 400:
            logger.error(str(res.status_code) + ' ' + str(res.json()))
            logger.info('処理終了')
        else:
            logger.info("updateを更新しました")
    else:
        pass
    
    logger.info('処理終了')
# ==============================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("ユーザーによって中断されました")
        sys.exit(130)
    except Exception:
        logger.exception("予期しないエラーが発生しました")
        sys.exit(1)