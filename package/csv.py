import csv

def readCsvToDict(file_path):
#    with open(file_path, mode='r', encoding='utf-8-sig') as f:   # BOMなし
    with open(file_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        data = list(reader)  # 各行が辞書のリストになる
    return data

def writeDictToCsv(data, file_path):
    if not data:
        return

    # 1行目の辞書からヘッダ（列名）を取得
    fieldnames = list(data[0].keys())

    with open(file_path, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()      # ヘッダ行を書き込み
        writer.writerows(data)    # 全行を書き込み