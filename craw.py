# -*- coding:utf-8 -*-
import requests
import json
import urllib
import time
import re
import cgi
import sys
import os
import HTMLParser
reload(sys)
sys.setdefaultencoding('utf8')


class CrawXiaoMQ(object):

    def __init__(self, token):#构造请求头、定义最后时间、定义初始的url
    #定义初始参数，token，URL，请求头
        self._headers = {"Authorization" : token,
                         "User-Agent": agent}
        print self._headers
        self.list_url = ['https://api.xiaomiquan.com/v1.8']
        self.end_time = urllib.quote(time.strftime("%Y-%m-%dT%H:%M:%S.679+0800", time.localtime())) #定义最后时间
        self.data = {}
        self.num = 20#每次请求的主题数
        self.topic_num = 1
        self.topic_id = []
        self._groups = {}
        self._files_id = {}
        with open('db.html', 'w') as self.html:#创建一个存放数据的html文件
            self.html.write('<html><head><meta http-equiv="content-type"' \
                            'content="text/html; charset=utf-8">' \
                           '<style type="text/css">p {margin-left: 18px;} ' \
                            'td {color: #eee8d5; background-color:#073642; ' \
                                'border: 1px solid black;} .cont {width: 400px;' \
                             'line-height: 30px;text-indent: 2em;} ' \
                            ' .author {width: 60px;}</style><body><table ' \
                            'cellspacing="5" align="center">')
    def _get_url(self, end_point):
        _list_url = self.list_url + end_point
        return '/'.join(_list_url)
    def _get_fileid(self, groupid):
        files_dict = {}
        print '获取所有附件ID'
        for group_id in groupid:
            while True:
                down_parm = "files?count=20&end_time=" + self.end_time
                _down_url = ['groups', str(group_id), down_parm]
                down_fileids = requests.get(self._get_url(_down_url),
                                            headers=self._headers).json()#请求获取一组文件ID号
                files_iddata =  down_fileids['resp_data']['files']
                self.num = len(files_iddata)    #获取当前请求有多少ID
                n = 0
                if self.num > 0:
                       while n < self.num:
                           files_dict[files_iddata[n]['file']['file_id']] = \
                           files_iddata[n]['file']['name']
                           n += 1
                else:
                    break
                #最后一个附件的创建时间
                create_time = files_iddata[self.num - 1]['file']['create_time']
                self.end_time = urllib.quote(self.struct_end_time(create_time))
                n = 0
                self.num = 20
            self.end_time = urllib.quote(time.strftime("%Y-%m-%dT%H:%M:%S.679+0800",
                                       time.localtime()))#刷新最后时间
        return files_dict
    def downloadfile(self, groupid):
        if not os.path.exists('./download'):
            os.mkdir('./download')
        html_parser = HTMLParser.HTMLParser()
        files_dict = self._get_fileid(groupid)
        for id in files_dict.keys():
            down_url = "https://api.xiaomiquan.com/v1.8/files/" + str(id) + \
            "/download_url" #获取文件真实下载地址
            file_url =  requests.get(down_url,
                                     headers=self._headers).json()['resp_data']['download_url']
            r = requests.get(file_url, headers=self._headers, stream=True)
            filename = html_parser.unescape(files_dict[id].replace(" ","_"))
            filename = filename.replace("\'", "")
            with open('./download/' + filename, 'wb') as fd:
                print u'正在下载->', filename
                for chunk in r.iter_content(1024 * 100):
                    fd.write(chunk)

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
        parm = 'topics?count=' + str(self.num) + '&end_time=' + self.end_time

        _list_url = ['groups', group_id, parm] #拼接url后缀
        cont_respone = requests.get(self._get_url(_list_url),
                                    headers=self._headers) #提交requests请求
        cont_respone = cont_respone.json()
        if cont_respone[u'succeeded']:
            i = 0
            self.num = len(cont_respone[u'resp_data'][u'topics'])
            return cont_respone
        else:
            return False

    def struct_end_time(self, create_time):
        time_ms = int(re.search(r'\.\d{3}', create_time).group().split('.')[1]) - 1
        return re.sub(r'\.\d{3}', '.%03d' % time_ms , create_time)
    def write_db(self, topics_dict, f):
        i = 0
        regex = r'<e\stype="hashtag".*?/>|<e\stype.*?href="|"\stitle=.*?\scache=.*?/>|"\s/>'
            #遍历每次请求的20个主题
        while i < self.num:
        #判断是不是提问
            if 'talk' in topics_dict[i]:
                #判断是否有附件
                if self.has_file(topics_dict[i][u'talk']):
                    author = topics_dict[i][u'talk'][u'owner'][u'name']
                    #判断是否有文字内容
                    if 'text' in topics_dict[i][u'talk']:
                        text = topics_dict[i][u'talk'][u'text']
                        text = text + '  附件:%s' % (topics_dict[i][u'talk'][u'files'][0][u'name'])
                    else:
                        text = '  附件:%s' % (topics_dict[i][u'talk'][u'files'][0][u'name'])
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
            <tr><td class="author"><p>[%s]</p><p>第 %d 条 作者:%s</p></td>
            <td class="cont">内容:%s</td></tr>''' % \
            (topics_dict[0]['group']['name'], self.topic_num, author, text)
            f.write(html)
            self.topic_id.append(topics_dict[i]['topic_id'])
            print "正在写入[%s]第%d条" % (topics_dict[0]['group']['name'],
                                                self.topic_num)
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
                self.num = 20
                topics_dict = self._get_topics(str(group_key[key_n - 1]))
                topics_dict = topics_dict['resp_data'][u'topics']
                #判断是否有新的主题
                if not topics_dict:
                    break

            self.num = 20
            self.end_time = urllib.quote(time.strftime("%Y-%m-%dT%H:%M:%S.679+0800",
                                       time.localtime()))#刷新最后时间
            self.topic_num = 1
            key_n = key_n - 1
        f.write("</table></body></html>")
        f.close()
        if is_down == 'y':
            print '所有主题爬取完毕，开始下载附件...'
            self.downloadfile(group_key)


if __name__ == '__main__':
    agent = raw_input("Please input your User-Agent:")
    token = raw_input("Please input your token:")
    is_down = raw_input("download file?('y/n')")
    craw = CrawXiaoMQ(token)#传入token，1.构造headers 2.初始url 3.定义最后时间
    groups = craw._get_groups()
    craw.get_cont(groups)
