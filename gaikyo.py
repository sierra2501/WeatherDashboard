from package import db, common
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def main():
    str_body = '{http://xml.kishou.go.jp/jmaxml1/body/meteorology1/}Body'
    str_comment = '{http://xml.kishou.go.jp/jmaxml1/body/meteorology1/}Comment'
    str_text = '{http://xml.kishou.go.jp/jmaxml1/body/meteorology1/}Text'

    logger.info('処理開始')
    
    res = db.getDocumentUpdate()
    if res == {}:
        logger.error("tenki_updateのドキュメント取得に失敗しました")
        logger.info('処理終了')
        return
    elif res.status_code >= 400:
        logger.error(str(res.status_code) + ' ' + str(res.json()))
        logger.info('処理終了')
        return
    else:
        dic_update = res.json()

    if dic_update['tenki_gaikyo']['readed']:
        logger.info('すでに読み込み済みです')
        logger.info('処理終了')
        return
    else:
        pass
    
    tree = common.getXML(0, dic_update['tenki_gaikyo']['link'])
    root = tree.getroot()

    dic_root = common.element_to_dict(root)

    txt = dic_root[str_body][str_comment][str_text]['#text']
    txt = txt.strip()
    txt = txt.replace(" ", "")
    res = db.postDocumentGaikyo(txt)

    if res.status_code >= 400:
        logger.error(str(res.status_code) + ' ' + str(res.json()))
        logger.info('処理終了')
        return
    else:
        logger.info("tenki_gaikyoをpostしました")

    dic_update['tenki_gaikyo']['readed'] = 1
    res = db.putDocumentUpdate(dic_update)
    if res.status_code >= 400:
        logger.error(str(res.status_code) + ' ' + str(res.json()))
        logger.info('処理終了')
    else:
        logger.info("updateを更新しました")
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