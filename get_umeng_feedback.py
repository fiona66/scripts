# coding=utf-8

import json
import time
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import requests

from unicode_csv import UnicodeWriter
#预定义变量

APP_CONFIGS = [
    { 'name': 'gandalf', 'app_key': '4fda9f6d5270157ea00000b8'},
    { 'name': 'nayutas', 'app_key': '505a97405270152c4500003e'},
]
DATE_FROM='2016-06-13' # modify date
DATE_TO='2016-07-13'

URL = u'http://mobile.umeng.com/api/feedback_request_proxy/?path=fb.umeng.com%%2Fapi%%2Fv2%%2Ffeedback%%2Fshow2&appkey=%s&count=10&from=%s&to=%s&page=%d'
URL_REPLY = u'http://mobile.umeng.com/api/feedback_request_proxy?path=fb.umeng.com%%2Fapi%%2Fv2%%2Ffeedback%%2Freply%%2Fshow&feedback_id=%s&appkey=%s'
COOKIE = 'cna=79xUDHIWtjYCAXTiJOl1PW3Z; umplusappid=umcenter; __ufrom=http://www.umeng.com/; um_lang=zh; umlid_556c1e0967e58e5cde002ef4=20160615; CNZZDATA1258498910=1110389553-1465973947-%7C1465973947; umengplus_name=jingchao.di%40duitang.com; umplusuuid=0622dc1d0185d7a91ec334d620528ef7; cn_a61627694930aa9c80cf_dplus=%7B%22distinct_id%22%3A%20%22155530687b0384-084f649d75a7fa-133c6857-1fa400-155530687b127c%22%2C%22%24_sessionid%22%3A%200%2C%22%24_sessionTime%22%3A%201465976877%2C%22%24initial_time%22%3A%20%221465973947%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22%24recent_outside_referrer%22%3A%20%22%24direct%22%2C%22%24dp%22%3A%200%2C%22%24_sessionPVTime%22%3A%201465976877%7D; l=AufnyTyWhZJlbBttkegkR4X19xGxCLtO; ummo_ss=BAh7CUkiGXdhcmRlbi51c2VyLnVzZXIua2V5BjoGRVRbCEkiCVVzZXIGOwBGWwZvOhNCU09OOjpPYmplY3RJZAY6CkBkYXRhWxFpWmlxaSNpDmlsaQHlaQGOaWFpAd5pAGkzaQH0SSIZVk9tdDhwYmNZQ0E2MzVBQUFLUnIGOwBUSSIPdW1wbHVzdXVpZAY7AEYiJTA2MjJkYzFkMDE4NWQ3YTkxZWMzMzRkNjIwNTI4ZWY3SSIQX2NzcmZfdG9rZW4GOwBGSSIxR3FhZG9WeFg2SzJoOThsRkZtRFA1Wk9sV1U0ZldDTFVwZUx1aFFuQ0xOaz0GOwBGSSIPc2Vzc2lvbl9pZAY7AFRJIiVjMGNiMWQyOWQ4NjBhY2ViODA4OWMxZjNmYzFlMWIwNAY7AEY%3D--6f53204f859142fe1c2c568a5bcc7317778584c7'

KEYS = 'access,app_version,appkey,carrier,contact,content,pic,country,datetime,device_model,feedback_id,is_replied,os,os_version,reply_num,status,tags,uid'.split(',')
EXTRA_KEYS = ['reply']


#预定义变量

#处理多级回复
def get_replys(feedback_id, app_key):
    url = URL_REPLY % (feedback_id, app_key)
    try:
        response = requests.get(url, headers={'Cookie': COOKIE}, timeout=30)
    except Exception, e:
        print 'waiting 30s'
        time.sleep(30)
        response = requests.get(url, headers={'Cookie': COOKIE}, timeout=30)

    print 'request reply url: %s' % url
    try:
        data = response.json()['data']
    except Exception, e:
        print 'get replys error, response: %s' % response
        # raise e
        return []
    replys = [x['content'] for x in data['result']]
    return replys

#构造请求,发送请求,筛选数据,写入文件.
def process_one(writer, app_key, page, keywords):
    #构造请求
    url = URL % (app_key, DATE_FROM, DATE_TO, page + 1)
    print 'request url: %s' % url
    #发送请求
    try:
        response = requests.get(url, headers={'Cookie': COOKIE}, timeout=30)
    except Exception, e:
        print 'waiting 30s'
        time.sleep(30)
        response = requests.get(url, headers={'Cookie': COOKIE}, timeout=30)
    try:
        #找到关键数据
        data = response.json()['data']
    except Exception, e:
        print 'error, response: %s' % response.text
        raise e

    if len(data) == 0:
        return 0
    if page == 0:
        writer.writerow(KEYS + EXTRA_KEYS)
    #筛选数据
    print '----------------------------------------------------------------------------------'
    print data
    print '----------------------------------------------------------------------------------'
    for row in data:
        #目标数据集
        csv_row = []
        is_match_keywords = 0  #是否匹配关键词

        for key in KEYS:
            if (key == 'contact'):
                value = (row.get(key) or {}).get('plain', '')
            elif (key == 'remark'):
                value = (row.get(key) or {}).get('username', '')
            else:
                value = unicode(row.get(key, ''))

            if (key == 'content'):  #判断content中是否含有关键字
                print '*******************************************************************************************'
                print keywords
                for keyword in keywords:
                    print '********************************'
                    print keyword
                    print value
                    print '********************************'
                    if keyword in value:

                        is_match_keywords = 1

            csv_row.append(value)

        if row.get('reply_num', 0) > 0:
            replys = get_replys(row.get('feedback_id'), app_key)
            replys_str = '\n'.join(replys)
            csv_row.append(replys_str)

            for keyword in keywords:  #判断reply中是否含有关键字
                if keyword in replys_str:
                    is_match_keywords = 1

        #和关键词匹配的数据才写入报表
        if is_match_keywords == 1:
            writer.writerow(csv_row)
    return len(data)


#入口
def main():
    # for arg in sys.argv[1:]
    keywords = sys.argv[1:]
    print keywords

    for app_config in APP_CONFIGS:
        #准备要写的文件
        csv_file = open('./umeng_%s.csv' % app_config['name'], 'wb')
        writer = UnicodeWriter(csv_file)
        for i in range(0, 10000):
            count = process_one(writer, app_config['app_key'], i, keywords)
            time.sleep(0.2)
            if count == 0:
                break


if __name__ == '__main__':
    main()
