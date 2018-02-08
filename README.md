# Quick Start
Navitimeのスポット情報をスクレイピングする。Python 2.7前提。

## 環境準備
virtualenvの利用を前提としているが、必須ではない。気にならないならinstallから初めても良い。

```
pip install virtualenv
virtualenv venv
source venv/bin/activate

pip install -r requirements.txt
```

また、依存先を増やした場合は次のコマンドで永続化する。

```
pip freeze > requirements.txt
```

## プログラム実行

```
# 47都道府県各最大50ページのデータを取得
python NavitimeSpotAddressScraperMain.py --output var/spot_address.tsv --type tsv --pref 47 --page 50

# pickle(Pythonオブジェクト)に保存したデータから変換処理を行う
python NavitimeSpotAddressScraperMain.py --input var/spot_address.pickle --output var/spot_address.tsv --type tsv --skip
```
