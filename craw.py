# -*- coding:utf-8 -*-
import requests
import json
import urllib
import time
import re
import cgi
import sys
reload(sys)
sys.setdefaultencoding('utf8')


class CrawXiaoMQ(object):

    def __init__(self, token):#构造请求头、定义最后时间、定义初始的url
    #定义初始参数，token，URL，请求头
        self._headers = {"Authorization" : token,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0"}
        self._base_url = 'https://api.xiaomiquan.com/v1.8/'#未被引用
        self._groups = {}#未被引用
        self.list_url = ['https://api.xiaomiquan.com/v1.8']
        self.end_time = urllib.quote(time.strftime("%Y-%m-%dT%H:%M:%S.679+0800", time.localtime())) #定义最后时间
        self.data = {}
        self.num = 20#每次请求的主题数
        with open('db.html', 'w') as self.html:#创建一个存放数据的html文件
            self.html.write('<html><head><meta http-equiv="content-type" content="text/html; charset=utf-8"><body><table>')
    def _get_url(self, end_point):
        _list_url = self.list_url + end_point
        return '/'.join(_list_url)

    def has_file(self, topic_talk):#判断是否有附件
        return 'files' in topic_talk

    def _get_groups(self):#返回一个字典，该字典包括圈子名和ID
        r = requests.get(self._get_url(['groups']), headers=self._headers)#该请求获取所有的groupsID
        r.encoding = 'utf-8'
        print r.json()[u'succeeded']
        if r.json()[u'succeeded']:
            data = r.json()
            for group in data[u'resp_data'][u'groups']:
                group_id = group[u'group_id']
                group_name = group[u'name']
                self._groups[group_id] = group_name
        return self._groups

    def _get_topics(self, group_id):
        topics_id = []
        parm = 'topics?count=' + str(self.num) + '&end_time=' + self.end_time
        _list_url = ['groups', group_id, parm] #拼接url后缀
        cont_respone = requests.get(self._get_url(_list_url), headers=self._headers).json() #提交requests请求

        if cont_respone[u'succeeded']:
            i = 0
            while i < self.num:
                topics_id.append(str(cont_respone[u'resp_data'][u'topics'][i][u'topic_id']))
                i = i + 1
        return cont_respone, topics_id

        n = 0
        if has_topic and self.num:
            return True
        else:
            while n > 0:

    def struct_end_time(self, create_time):
        time_ms = int(re.search(r'\.\d{3}', create_time).group().split('.')[1]) + 1
        return re.sub(r'\.\d{3}', '.%03d' + time_ms , create_time)
        

    def get_cont(self, groups):
        group_key = groups.keys()#获取所有的groupid
        regex = r'<e\stype="hashtag".*/>|<e\stype.*?href="|"\stitle=.*?\scache=.*?/>|"\s/>'
        f = open('db.html', 'a')
        key_n = len(group_key)
        print key_n
        while key_n > 0:
            i = 0
            cont_respone, topics_id = self._get_topics(str(group_key[key_n - 1]))
            topics_dict = cont_respone[u'resp_data'][u'topics']

            while len(topics_dict) > 0:
                while i < self.num:
                    if 'talk' in topics_dict[i]:
                        if self.has_file(topics_dict[i][u'talk']):
                            author = topics_dict[i][u'talk'][u'owner'][u'name']
                            if 'text' in topics_dict[i][u'talk']:
                                text = topics_dict[i][u'talk'][u'text']
                                text = text + '<br>附件:%s' % (topics_dict[i][u'talk'][u'files'][0][u'name'])
                            else:
                                text = '<br>附件:%s' % (topics_dict[i][u'talk'][u'files'][0][u'name'])
                        elif 'text' not in topics_dict[i][u'talk'] and 'images' in topics_dict[i][u'talk']:
                            text = '<img src="%s" />' % (topics_dict[i][u'talk'][u'images'][0][u'large'][u'url'])
                        else:
                            author = topics_dict[i][u'talk'][u'owner'][u'name']
                            text = topics_dict[i][u'talk'][u'text']
                    else:
                       #print topics_dict[i]
                        author = topics_dict[i][u'question'][u'questionee'][u'name']
                        text = topics_dict[i][u'question'][u'text']

                    text = urllib.unquote(cgi.escape(re.sub(regex, '', text)))
                    html = '''
                    <tr><td>di %d tiao 作者:%s</td>
                    <td>内容:%s</td></tr><tr></tr>''' % (i,author, text)
                    f.write(html)
                    i = i + 1
                self.end_time = struct_end_time(topics_dict[self.num - 1]['create_time'])
                topics_dict = self._get_topics(str(group_key[key_n - 1]))
            key_n = key_n - 1
        f.write("</table></body></html>")
        f.close()


if __name__ == '__main__':
    token = raw_input("Please input your token:")
    craw = CrawXiaoMQ(token)#传入token，1.构造headers 2.初始url 3.定义最后时间
    groups = craw._get_groups()
    craw.get_cont(groups)
