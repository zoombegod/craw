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
                         "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; "\
                         "x64; rv:57.0) Gecko/20100101 Firefox/57.0"}
        print self._headers
        self._base_url = 'https://api.xiaomiquan.com/v1.8/'#未被引用
        self._groups = {}#未被引用
        self.list_url = ['https://api.xiaomiquan.com/v1.8']
        self.end_time = urllib.quote(time.strftime("%Y-%m-%dT%H:%M:%S.679+0800", time.localtime())) #定义最后时间
        self.data = {}
        self.num = 20#每次请求的主题数
        self.topic_num = 1
        self.topic_id = []
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
        del self._groups[758548854] #del help topic
        return self._groups

    def _get_topics(self, group_id):
        topics_id = []
        if '%' not in self.end_time:
            self.end_time = urllib.quote(self.end_time)
        print self.end_time
        parm = 'topics?count=' + str(self.num) + '&end_time=' + self.end_time

        _list_url = ['groups', group_id, parm] #拼接url后缀
        cont_respone = requests.get(self._get_url(_list_url),
                                    headers=self._headers) #提交requests请求
        print cont_respone.request.url
        cont_respone = cont_respone.json()
        if cont_respone[u'succeeded']:
            i = 0
            self.num = len(cont_respone[u'resp_data'][u'topics'])
            print 'self.num is %d' % (self.num)
            return cont_respone
        else:
            return False

    def struct_end_time(self, create_time):
        time_ms = int(re.search(r'\.\d{3}', create_time).group().split('.')[1]) - 1
        return re.sub(r'\.\d{3}', '.%03d' % time_ms , create_time)
    def write_db(self, topics_dict, f):
        i = 0
        regex = r'<e\stype="hashtag".*/>|<e\stype.*?href="|"\stitle=.*?\scache=.*?/>|"\s/>'
            #遍历每次请求的20个主题
        while i < self.num:
        #判断是不是提问
            print 'i is %d, 主题数: %d' % (i, self.num)
            if 'talk' in topics_dict[i]:
                #判断是否有附件
                if self.has_file(topics_dict[i][u'talk']):
                    author = topics_dict[i][u'talk'][u'owner'][u'name']
                    #判断是否有文字内容
                    if 'text' in topics_dict[i][u'talk']:
                        text = topics_dict[i][u'talk'][u'text']
                        text = text + '<br>附件:%s' % (topics_dict[i][u'talk'][u'files'][0][u'name'])
                    else:
                        text = '<br>附件:%s' % (topics_dict[i][u'talk'][u'files'][0][u'name'])
                elif 'text' not in topics_dict[i][u'talk'] and 'images' in topics_dict[i][u'talk']:

                    author = topics_dict[i][u'talk'][u'owner'][u'name']
                    text = '<img src="%s" />' % (topics_dict[i][u'talk'][u'images'][0][u'large'][u'url'])
                elif ('text' in  topics_dict[i][u'talk'] and 'images'
                      in topics_dict[i][u'talk']):

                    author = topics_dict[i][u'talk'][u'owner'][u'name']
                    text = topics_dict[i][u'talk'][u'text'] + '<img src="%s" />' % (topics_dict[i][u'talk'][u'images'][0][u'large'][u'url'])
                else:
                    author = topics_dict[i][u'talk'][u'owner'][u'name']
                    text = topics_dict[i][u'talk'][u'text']

            else:
                author = topics_dict[i][u'question'][u'questionee'][u'name']
                text = '问:' + topics_dict[i][u'question'][u'text']
                if 'answer' in topics_dict[i]:
                    text += topics_dict[i][u'answer']['owner']['name'] + '答:'  + \
                    topics_dict[i][u'answer']['text']

            text = urllib.unquote(cgi.escape(re.sub(regex, '', text)))
            html = '''
            <tr><div class="author"><td>[%s]第 %d 条 作者:%s</td></div>
            <div class="cont"><td>内容:%s</td></div></tr>''' % \
            (topics_dict[0]['group']['name'], self.topic_num, author, text)
            f.write(html)
            self.topic_id.append(topics_dict[i]['topic_id'])
            self.topic_num += 1
            i = i + 1

    def get_cont(self, groups):
        group_key = groups.keys()#获取所有的groupid
        f = open('db.html', 'a')
        key_n = len(group_key)

        #循环组
        while key_n > 0:
            i = 0
            cont_respone = self._get_topics(str(group_key[key_n - 1]))

            if cont_respone:
                topics_dict = cont_respone[u'resp_data'][u'topics']
            else:
                continue

            #根据主题来循环
            while len(topics_dict) > 0:

                #遍历每次请求的20个主题
                self.write_db(topics_dict, f)
                self.end_time = self.struct_end_time(topics_dict[self.num - 1]['create_time'])
                print 'gou zao hou', self.end_time
                self.num = 20
                topics_dict = self._get_topics(str(group_key[key_n - 1]))
                topics_dict = topics_dict['resp_data'][u'topics']
                #判断是否有新的主题
                if not topics_dict:
                    break

            self.num = 20
            print '结束一个圈子后的self.num值', self.num
            self.end_time = urllib.quote(time.strftime("%Y-%m-%dT%H:%M:%S.679+0800",
                                       time.localtime()))#刷新最后时间
            self.topic_num = 0
            key_n = key_n - 1
        f.write("</table></body></html>")
        f.close()


if __name__ == '__main__':
    token = raw_input("Please input your token:")
    craw = CrawXiaoMQ(token)#传入token，1.构造headers 2.初始url 3.定义最后时间
    groups = craw._get_groups()
    craw.get_cont(groups)
