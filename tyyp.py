import time
import re
import os
import rsa
import base64
import hashlib
import requests
import random

# 变量 ty_username（手机号）,ty_password（密码）
ty_username = os.getenv("TYYP_USERNAME").split('&')
ty_password = os.getenv("TYYP_PSW").split('&')

BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")
B64MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
s = requests.Session()

# 创建日志字符串
log_md = "# 签到日志\n"

for i in range(len(ty_username)):
    print(f'开始执行帐号{i + 1}')

    def int2char(a):
        return BI_RM[a]

    def b64tohex(a):
        d, e, c = "", 0, 0
        for i in range(len(a)):
            if list(a)[i] != "=":
                v = B64MAP.index(list(a)[i])
                if e == 0:
                    e, d, c = 1, d + int2char(v >> 2), 3 & v
                elif e == 1:
                    e, d, c = 2, d + int2char(c << 2 | v >> 4), 15 & v
                elif e == 2:
                    e, d, c = 3, d + int2char(c) + int2char(v >> 2), 3 & v
                else:
                    e, d = 0, d + int2char(c << 2 | v >> 4) + int2char(15 & v)
        if e == 1:
            d += int2char(c << 2)
        return d

    def rsa_encode(j_rsakey, string):
        rsa_key = f"-----BEGIN PUBLIC KEY-----\n{j_rsakey}\n-----END PUBLIC KEY-----"
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode())
        result = b64tohex((base64.b64encode(rsa.encrypt(f'{string}'.encode(), pubkey))).decode())
        return result

    def login(ty_username, ty_password):
        urlToken = "https://m.cloud.189.cn/udb/udb_login.jsp?pageId=1&redirectURL=https://m.cloud.189.cn/zhuanti/2021/shakeLottery/index.html"
        s = requests.Session()
        r = s.get(urlToken)
        match = re.search(r"https?://[^\s'\"]+", r.text)
        url = match.group() if match else print("没有找到url")

        r = s.get(url)
        match = re.search(r"<a id=\"j-tab-login-link\"[^>]*href=\"([^\"]+)\"", r.text)
        href = match.group(1) if match else print("没有找到href链接")

        r = s.get(href)
        captchaToken, lt, returnUrl, paramId, j_rsakey = re.findall(r"captchaToken' value='(.+?)'", r.text)[0], \
                                                          re.findall(r'lt = "(.+?)"', r.text)[0], \
                                                          re.findall(r"returnUrl= '(.+?)'", r.text)[0], \
                                                          re.findall(r'paramId = "(.+?)"', r.text)[0], \
                                                          re.findall(r'j_rsaKey" value="(\S+)"', r.text, re.M)[0]
        s.headers.update({"lt": lt})

        username, password = rsa_encode(j_rsakey, ty_username[i]), rsa_encode(j_rsakey, ty_password[i])
        url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/76.0',
            'Referer': 'https://open.e.189.cn/',
        }
        data = {
            "appKey": "cloud",
            "accountType": '01',
            "userName": f"{{RSA}}{username}",
            "password": f"{{RSA}}{password}",
            "validateCode": "",
            "captchaToken": captchaToken,
            "returnUrl": returnUrl,
            "mailSuffix": "@189.cn",
            "paramId": paramId
        }
        r = s.post(url, data=data, headers=headers, timeout=5)
        print(r.json()['msg'])
        redirect_url = r.json()['toUrl']
        s.get(redirect_url)
        return s

    def main():
        s = login(ty_username, ty_password)
        rand = str(round(time.time() * 1000))
        url = f"https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN&activityId=ACT_SIGNIN&rand={rand}&clientType=TELEANDROID&version=8.7.0&model=SM-G930K"
        response = s.get(url)
        netdiskBonus = response.json()['netdiskBonus']
        res1 = f"未签到，签到获得{netdiskBonus}M空间" if response.json()['isSign'] == "false" else f"已经签到过了，签到获得{netdiskBonus}M空间"

        description = response.json()['description']
        res2 = f"抽奖获得{description}" if "errorCode" not in response.text else ""

        url = "https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_PHOTOS&activityId=ACT_SIGNIN&rand=6541015307801&clientType=TELEANDROID&version=8.6.3&model=SM-G930K"
        response = s.get(url)
        description = response.json()['description']
        res3 = f"抽奖获得{description}" if "errorCode" not in response.text else ""

        url = "https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_COIN&activityId=ACT_SIGNIN&rand=6541015307801&clientType=TELEANDROID&version=8.6.3&model=SM-G930K"
        response = s.get(url)
        description = response.json()['description']
        res4 = f"链接3抽奖获得{description}" if "errorCode" not in response.text else ""

        return res1, res2, res3, res4

    # 将每个账号的结果添加到日志字符串
    result1, result2, result3, result4 = main()
    log_md += f"\n帐号{i + 1}:\n- {result1}\n- {result2}\n- {result3}\n- {result4}\n"

# 将日志字符串写入文件
with open("log.md", "w") as file:
    file.write(log_md)

print("所有帐号执行完毕")
