import logging
import urllib.request
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# ===================================================
def getXML(mode, path):
    root = ""
    tree = ""
    if mode:
        logger.debug('mode: test')
        return ET.parse(path)
    else:
        logger.debug('mode: request')
        try:
            with urllib.request.urlopen(path) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
            tree = ET.ElementTree(root)
            logger.info('読み込み成功')
        except HTTPError as e:
            logger.error('HTTPエラー: ', e.code, e.reason)
        except URLError as e:
            logger.error('URLエラー: ', e.reason)
        except ET.ParseError as e:
            logger.error('XMLパースエラー: ', e)
        return tree
        
# ==============================================
def element_to_dict(element):
    """Elementオブジェクトを辞書に変換する（属性も保存）"""
    result = {}

    # 属性があれば辞書に追加（例: @id, @class など）
    if element.attrib:
        for attr, value in element.attrib.items():
            result[f"@{attr}"] = value

    # 子要素がなければテキストを返す
    if len(element) == 0:
        if element.text and element.text.strip():
            # 属性もあればテキストは '#text' キーで保存
            if element.attrib:
                result["#text"] = element.text
                return result
            else:
                return element.text
        else:
            # テキストがなければ属性だけを返す
            return result if result else None

    # 子要素があれば再帰的に辞書化
    for child in element:
        child_data = element_to_dict(child)
        if child_data is None:
            continue

        # 同じタグ名が複数ある場合はリストにする
        if child.tag in result:
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_data)
        else:
            result[child.tag] = child_data

    # テキストがあれば '#text' で保存
    if element.text and element.text.strip():
        result["#text"] = element.text

    return result