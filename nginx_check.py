#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
功能     : nginx zabbix监控脚本

说明     : 适用zabbix 4.0
        
Author  : [weijiaqin@huawei.com]
Version : 2018/12/21 初始版本
"""
__version__ = '1.0.1'
__all__ = ['NginxCheck']
__author__ = 'JiaQin Wei <weijiaqin@huawei.com>'

import os
import re
import sys
import json
import tempfile
import optparse
import ConfigParser
import subprocess

reload(sys)
sys.setdefaultencoding('utf-8')

cur_path = os.path.split(os.path.realpath(__file__))[0]
os.chdir(cur_path)
nginx_check_config = os.path.exists("nginx_check.conf") and "nginx_check.conf" or "nginx_check.conf"


class NginxCheck:

    def __init__(self, ip_address, url_path):
        self.ip = ip_address
        self.url_path = url_path

    def get_nginx_status_json(self):
        """
        获取nginx所有状态信息
        :return: json
        """
        status_info = {}
        process = subprocess.Popen(['curl', '-s', 'http://%s/%s' % (self.ip, self.url_path)], shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, error = process.communicate()

        # 创建临时文件,存储curl命令返回的信息
        tmp_file = tempfile.TemporaryFile(mode="w+t")
        try:
            tmp_file.write(out)
            tmp_file.seek(0)
            for line in tmp_file:
                lower_line = line.strip().lower()
                if "active" in lower_line:
                    status_info['active'] = lower_line.split(':')[1].strip()
                elif re.match('^\d+ \d+ \d+$', lower_line):
                    infos = lower_line.split()
                    status_info['accept'] = infos[0]
                    status_info['handled'] = infos[1]
                    status_info['request'] = infos[2]
                elif "reading" in lower_line:
                    match = re.match("^reading: (\d+) writing: (\d+) waiting: (\d+)$", lower_line)
                    status_info['reading'] = match.group(1)
                    status_info['writing'] = match.group(2)
                    status_info['waiting'] = match.group(3)
        finally:
            tmp_file.close()

        return json.dumps(status_info)

    def get_nginx_status(self, key):
        """
        获取nginx某个状态的信息
        :return:
        """
        status = json.loads(self.get_nginx_status_json())
        return status[key]


if __name__ == '__main__':
    parser = optparse.OptionParser(usage='\033[43;37m%(prog)s function param [options]\033[0m', version=__version__)
    parser.add_option('-q', '--query', dest='query', help='[active|accept|handled|request|reading|writing|waiting]')
    parser.add_option('--json', dest='json', action='store_true', help=u'打印nginx所有状态的json字符串信息')
    (option, args) = parser.parse_args()
    #######################################################################################################
    if len(sys.argv) == 1:
        from pydoc import render_doc

        print(render_doc(NginxCheck, title="[NginxCheck Documentation] %s"))
        print(parser.print_help())
        exit(1)

    if not os.path.exists(nginx_check_config):
        print("the config file [%s] is not exist" % nginx_check_config)
        exit(1)

    cfg_parser = ConfigParser.ConfigParser()
    cfg_parser.read(nginx_check_config)
    ip = cfg_parser.get("COMMON", "ip")
    status_url = cfg_parser.get("COMMON", "url_path")
    nginx_check = NginxCheck(ip, status_url)

    if option.json:
        status_str = nginx_check.get_nginx_status_json()
        print(status_str)
    elif option.query:
        status_str = nginx_check.get_nginx_status(option.query)
        print(status_str)

