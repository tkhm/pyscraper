#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Navitime  I/C, JCT情報取得

* https://www.navitime.co.jp/category/0803/

事前に　RoboBrowser, BeautifulSoup を pip install しておく
BeautifulSoupについては
Beautiful Soup Documentation — Beautiful Soup 4.4.0 documentation
@see https://www.crummy.com/software/BeautifulSoup/bs4/doc/

UTF-8とUTF-8-sigについては
u ufeff in Python string - Stack Overflow
@see https://stackoverflow.com/questions/17912307/u-ufeff-in-python-string#17912811
"""
import argparse
import codecs
import csv
import json
import pickle
import sys
import time
from random import randint
from tqdm import tqdm
from robobrowser import RoboBrowser
from bs4 import BeautifulSoup

class MyBrowser(object):
    """
    ロボブラウザーをラップしたクラス
    """

    def __init__(self, encoding=None, **kwargs):
        self.r_browser = RoboBrowser(**kwargs)
        self.encoding = encoding
        self.host = ''

    def get_url_soup(self, host, url):
        """
        指定のhost + urlでページを取得しSoupオブジェクトにして返す

        :returns: BeautifulSoup
        """
        self.host = host
        self.r_browser.open(host + url)

        res = self.r_browser.state.response

        if self.encoding:
            res.encoding = self.encoding
        return BeautifulSoup(res.text, "html.parser")

class NavitimeSpotAddressScraper(object):
    """
    NavitimeのI/C、JCTの住所をスクレイピングする
    """
    def __init__(self, starting_url="/category/0803", sleeping_time=3):
        self.browser = MyBrowser(encoding='UTF8', history=True)
        self.hostname = "https://www.navitime.co.jp"
        self.starting_url = starting_url
        self.sleeping_time = sleeping_time

    def get_spot_links(self, max_pref_no, max_page_no):
        """ to be updated """
        pref_no = 1
        result = []
        # 01 to 47 北海道から沖縄まで
        while pref_no <= max_pref_no:
            page_no = 1
            while page_no <= max_page_no:
                page = '/%02d/?page=%d' % (pref_no, page_no)
                result.append(self.starting_url + page)

                page_no += 1
            pref_no += 1
        return result

    def get_spot_address(self, links):
        """
        受け取ったリンクに従ってbeautifulSoupオブジェクトを取得、
        取得結果から、事前に定めた特定の属性を抜き出した辞書オブジェクトを取得し、yieldの形で返す
        yieldにすることで、たくさんのページを抜いてきても一気にメモリに展開しないので安全度が高まる
        """
        for link in tqdm(links):
            print link

            # /category/0803/01/?page=1
            # /category/0803/01/?page=2
            # /category/0803/01/?page=3
            # /category/0803/02/?page=1
            # 次の形で値を取得 scraper.browser.get_url_soup(link)
            # 取得のサンプル soup = scraper.browser.get_url_soup("/category/0803/02/?page=1")

            time.sleep(randint(self.sleeping_time, self.sleeping_time+3))
            soup = self.browser.get_url_soup(self.hostname, link)
            unpacked_soup = self.unpack_spot_soup(soup)

            yield unpacked_soup

    @classmethod
    def append_json(cls, filename, dict_value, encoding='utf-8'):
        """
        utf-8 = UTF-8 w/o BOM
        to be updated
        """
        with codecs.open(filename, "a", encoding) as fil:
            json.dump(dict_value, fil, ensure_ascii=False)

    @classmethod
    def load_json(cls, filename, encoding='utf-8'):
        """
        utf-8 = UTF-8 w/o BOM
        """

        with codecs.open(filename, "r", encoding) as fil:
            return json.load(fil, encoding)

    @classmethod
    def write_pickle(cls, filename, dict_value):
        """
        pickleとして書き出し
        """
        with open(filename, "wb") as fil:
            pickle.dump(dict_value, fil)

    @classmethod
    def load_pickle(cls, filename):
        """
        pickleとして読み込み、読み込んだオブジェクトを返す
        """
        with open(filename, "rb") as fil:
            return pickle.load(fil)

    @classmethod
    def append_csv(cls, filename, dict_value, encoding='utf-8', delimiter='\t'):
        """
        utf-8 = UTF-8 w/o BOM
        13.1. csv — CSV File Reading and Writing — Python 2.7.14 documentation
        @see https://docs.python.org/2/library/csv.html
        """
        with codecs.open(filename, "a", encoding) as fil:
            fieldnames = ["spot_name", "spot_address", "spot_link"]
            writer = csv.DictWriter(fil, fieldnames=fieldnames, delimiter=delimiter)
            writer.writerows(dict_value)

    @classmethod
    def unpack_spot_soup(cls, soup):
        """
        この関数実行では、下記のようなオブジェクトを返す
        [{"spot_address": "xxx", "spot_name": "", "spot_link": ""}, {}]"
        """

        spot_list_soup = soup.find_all(class_="list_item_frame")
        spot_list = [] # 書き出し用リスト

        #answer_bad_list = soup.find_all(id=re.compile('.*(?=evaluate-bad-¥d+).*$'))

        for spot_soup in spot_list_soup:
            spot = {
                "spot_name" : spot_soup.find(class_="spot_name").text.replace("\n", ""),
                "spot_link" : "https://" + spot_soup.find(class_="address_name").a.extract().get("href"),
                "spot_address" : spot_soup.find(class_="address_name").text.replace("\n", "")
            }
            spot_list.append(spot)

        return spot_list

def main():
    """
    main entry point
    """
    reload(sys)
    # デフォルトの文字コードを変更する．
    sys.setdefaultencoding("utf-8")

    scraper = NavitimeSpotAddressScraper()

    # 引数をとるためのparser
    arg_psr = argparse.ArgumentParser()
    # -d / --debug というオプションを追加，デフォルトはFalse
    arg_psr.add_argument("--debug", action="store_true")
    arg_psr.add_argument("--skip", action="store_true")
    arg_psr.add_argument("--input", default="var/spot_address.pickle")
    arg_psr.add_argument("--output", default="var/spot_address.pickle")
    arg_psr.add_argument("--type", default="")
    arg_psr.add_argument("--pref", default=1, type=int)
    arg_psr.add_argument("--page", default=1, type=int)

    # コマンドラインの引数をパースしてargsに入れる．エラーがあったらexitする
    args = arg_psr.parse_args()
    debug_mode = args.debug
    skip_mode = args.skip
    output_file_name = args.output
    input_file_name = args.input
    output_type = args.type
    max_pref = args.pref
    max_page = args.page

    print args

    ### デバッグ用コードここから、デバッグ用コードはすべて削除しても動作上一切問題は発生しない
    # この値を切り替えて一時的なテストに用いる、デバッグ=True時はBaiduへ通信しない
    if debug_mode:
        """
        # soupオブジェクトからの書き出しデバッグ
        output = []

        # 実際に取得する代わりに事前に出力しておいたsoupオブジェクトを使う
        testFilename = "test.soup"
        soup = scraper.load_pickle(testFilename)

        result = scraper.unpack_spot_soup(soup)
        output.append(result)
        output.append(result)
        scraper.write_pickle(output_file_name, output)
        """

        import pprint
        # 書き出し済pickleオブジェクトの中身を確かめるデバッグ
        results = scraper.load_pickle(output_file_name)

        class MyPrettyPrinter(pprint.PrettyPrinter):
            def format(self, object, context, maxlevels, level):
                if isinstance(object, unicode):
                    return (object.encode('utf-8'), True, False)
                return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)

        mpp = MyPrettyPrinter()
        for result in results:
            mpp.pprint(result)

        # 強制的にプログラムを終了させる
        sys.exit()

        ### デバッグ用コードここまで

    # スポット一覧を取得
    if skip_mode:
        print "skip to get data"
        if output_type == "tsv":
            if input_file_name == output_file_name:
                print "input and output is the same file"
                sys.exit()
            # tsv(csv with tab) / csvについては現状はpickleでまとめて読み込んでからでないと書き出せない
            results = scraper.load_pickle(input_file_name)
            for result in results:
                scraper.append_csv(output_file_name, list(result), delimiter='\t')
        elif output_type == "csv":
            if input_file_name == output_file_name:
                print "input and output is the same file"
                sys.exit()

            # tsv(csv with tab) / csvについては現状はpickleでまとめて読み込んでからでないと書き出せない
            results = scraper.load_pickle(input_file_name)
            for result in results:
                scraper.append_csv(output_file_name, list(result), delimiter=',')
        else:
            print "nothing to do"
    else:
        spot_links = scraper.get_spot_links(max_pref_no=max_pref, max_page_no=max_page)
        output_iterator = scraper.get_spot_address(spot_links)

        # イテレータオブジェクトをリストに変換して出力、pickle以外はappendするので注意
        if output_type == "tsv":
            print "tsv"
            # tsv(csv with tab) / csvについては現状はpickleでまとめて読み込んでからでないと書き出せない
            scraper.write_pickle("tmp", list(output_iterator))
            results = scraper.load_pickle("tmp")
            for result in results:
                scraper.append_csv(output_file_name, list(result), delimiter='\t')
        elif output_type == "csv":
            scraper.write_pickle("tmp", list(output_iterator))
            results = scraper.load_pickle("tmp")
            for result in results:
                scraper.append_csv(output_file_name, list(result), delimiter=',')
        elif output_type == "json":
            scraper.append_json(output_file_name, list(output_iterator))
        else:
            scraper.write_pickle(output_file_name, list(output_iterator))

if __name__ == '__main__':
    main()
