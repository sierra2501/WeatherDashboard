import csv
from datetime import datetime
import logging
from package import db, common

logger = logging.getLogger(__name__)

pre = '{http://xml.kishou.go.jp/jmaxml1/body/meteorology1/}'
pre2 = '{http://xml.kishou.go.jp/jmaxml1/elementBasis1/}'

# ==============================================
def switchMli(dic_root, num):
    dic_result = []
    dic_tsi = dic_root[pre + 'Body'][pre + 'MeteorologicalInfos'][num][pre + 'TimeSeriesInfo']

    if num == 0:
        if len(dic_tsi) == 1:
            dic_result.append(wrapTsi(dic_tsi))
        else:
            for j in range(len(dic_tsi)):
                dic_result.append(wrapTsi(dic_tsi[j]))
    elif num == 1 or 2 or 3:
        dic_result.append(wrapTsi(dic_tsi))
        
    return dic_result
    
def wrapTsi(dic_tsi):
    dic_result = {}
    for i in range(len(dic_tsi[pre + 'Item'])):
        
        # キーのチェック
        check_key = 0
        check_key_area = dic_tsi[pre + 'Item'][i].get(pre + 'Area')
        check_key_station = dic_tsi[pre + 'Item'][i].get(pre + 'Station')

        # Area or Station Name
        if check_key_area and dic_tsi[pre + 'Item'][i][pre + 'Area'][pre + 'Name'] == '東京地方':
            check_key = 1
        elif check_key_station and dic_tsi[pre + 'Item'][i][pre + 'Station'][pre + 'Name'] == '東京':
            check_key = 1
        else:
            #print('[info][yohou.py]skip: Area/Station')
            check_key = 0
            
        if check_key:
            
            # 時間の定義
            time = []
            for j in range(len(dic_tsi[pre + 'TimeDefines'][pre + 'TimeDefine'])):
                time.append(dic_tsi[pre + 'TimeDefines'][pre + 'TimeDefine'][j][pre + 'DateTime'])
            dic_result['time'] = time
            
            # Kind
            dic_kind = dic_tsi[pre + 'Item'][i][pre + 'Kind']
            if len(dic_kind) == 1:
                dic_result |= loopKind(dic_kind)
            else:
                for i in range(len(dic_kind)):
                    dic_result |= loopKind(dic_kind[i])

    return dic_result

    
def loopKind(dic_kind):
    result = {}
    if isinstance(dic_kind[pre + 'Property'], list):
        for j in range(len(dic_kind[pre + 'Property'])):
            result |= loopProp(dic_kind[pre + 'Property'][j])
    elif isinstance(dic_kind[pre + 'Property'], dict):
        result = loopProp(dic_kind[pre + 'Property'])
    else:
        logger.error("dic_prop はリストでも辞書でもありません")
    return result
            

def loopProp(dic_prop):
    dtype = dic_prop[pre + 'Type']
    key_name = ''
    result = []
    dic_result = {}
    if dtype == '天気':
        key_name = 'weather'
        for i in range(len(dic_prop[pre + 'DetailForecast'][pre + 'WeatherForecastPart'])):
            result.append(dic_prop[pre + 'DetailForecast'][pre + 'WeatherForecastPart'][i][pre + 'Sentence'])
    elif dtype == '風':
        key_name = 'wind'
        for i in range(len(dic_prop[pre + 'DetailForecast'][pre + 'WindForecastPart'])):
            result.append(dic_prop[pre + 'DetailForecast'][pre + 'WindForecastPart'][i][pre + 'Sentence'])
    elif dtype == '波':
        key_name = 'wave'
        for i in range(len(dic_prop[pre + 'DetailForecast'][pre + 'WaveHeightForecastPart'])):
            result.append(dic_prop[pre + 'DetailForecast'][pre + 'WaveHeightForecastPart'][i][pre + 'Sentence'])
    elif dtype == '降水確率':
        key_name = 'pop'
        for i in range(len(dic_prop[pre + 'ProbabilityOfPrecipitationPart'][pre2 + 'ProbabilityOfPrecipitation'])):
            result.append(dic_prop[pre + 'ProbabilityOfPrecipitationPart'][pre2 + 'ProbabilityOfPrecipitation'][i]['#text'])
    elif dtype == '朝の最低気温':
        key_name = 'temp_min'
        result.append(dic_prop[pre + 'TemperaturePart'][pre2 + 'Temperature']['#text'])
    elif dtype == '日中の最高気温':
        key_name = 'temp_max'
        result.append(dic_prop[pre + 'TemperaturePart'][pre2 + 'Temperature']['#text'])
    elif dtype == '最高気温':
        key_name = 'temp_max2'
        result.append(dic_prop[pre + 'TemperaturePart'][pre2 + 'Temperature']['#text'])
    elif dtype == '３時間内卓越天気':
        key_name = 'weather_3hour'
        for i in range(len(dic_prop[pre + 'WeatherPart'][pre2 + 'Weather'])):
            result.append(dic_prop[pre + 'WeatherPart'][pre2 + 'Weather'][i]['#text'])
    elif dtype == '３時間毎気温':
        key_name = 'temp_3hour'
        for i in range(len(dic_prop[pre + 'TemperaturePart'][pre2 + 'Temperature'])):
            result.append(dic_prop[pre + 'TemperaturePart'][pre2 + 'Temperature'][i]['#text'])         
    else:
        logger.info('処理にないタイプです: ' + dic_prop[pre + 'Type'])

    dic_result[key_name] = result
    
    return dic_result

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

    if dic_update['tenki_yohou']['readed']:
        logger.info('すでに読み込み済みです')
        logger.info('処理終了')
        return
    else:
        pass
        
    #tree = common.getXML(1, './xml/tenki-yohou.xml')
    tree = common.getXML(0, dic_update['tenki_yohou']['link'])
    root = tree.getroot()

    dic_root = common.element_to_dict(root)
    dic_res = []
    dic_res = dic_res + switchMli(dic_root, 0)
    dic_res = dic_res + switchMli(dic_root, 1)
    dic_res = dic_res + switchMli(dic_root, 2)
    dic_res = dic_res + switchMli(dic_root, 3)

    res = db.postDocumentTenki(dic_res)
    if res.status_code >= 400:
        logger.error(str(res.status_code) + ' ' + str(res.json()))
        logger.info('処理終了')
        return
    else:
        logger.info("tenki_yohouをpostしました")

    dic_update['tenki_yohou']['readed'] = 1
    res = db.putDocumentUpdate(dic_update)
    if res.status_code >= 400:
        logger.error(str(res.status_code) + ' ' + str(res.json()))
        logger.info('処理終了')
    else:
        logger.info("tenki_updateを更新しました")

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