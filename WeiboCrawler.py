#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import re
import os
import sys
import random
import csv
import traceback
import requests
from lxml import etree
from tqdm import tqdm
from collections import OrderedDict
from datetime import datetime, timedelta
from time import sleep


class Weibo:
    #记录Cookie
    cookies = {
        "Cookie": "_T_WM=f04d1a679d509e0abd73d80784187559; "
                  "SUB=_2A25wAytMDeRhGeBL41sW8yrFwzqIHXVTD7UErDV6PUJbkdAKLVaskW1NRtGCeVuYhX4X0UeBlacY-tYE-wljJzj4; "
                  "SUHB=0XD1LmMLpm7Sbj; "
                  "SCF=AoCylhvmimo9xhRQI3w_Cu484Q8Wk3x3Z5RhRa-ledDRkezbhNZ8yKtnPgpe_NpjxdwfauUWz4g5LLYA8eWbMfw.;"
                  " SSOLoginState=1560763164"}

    def __init__(self, userid, getAll=0, getPic=0):
        """Weibo类初始化"""
        if not isinstance(userid, int):
            sys.exit(u"userid值应该为数字形式,请重新输入")
        if getAll != 0 and getAll != 1:
            sys.exit(u"请选择是否获取所有微博,0表示仅获取原创微博,1表示获取原创+转发微博")
        if getPic != 0 and getPic!= 1:
            sys.exit(u"请选择是否下载图片,0表示不下载图片,1表示下载图片")
        self.userid = userid
        self.getAll = getAll
        self.getPic = getPic
        self.nickname = ""
        self.WBNum = 0
        self.PageNum = 0
        self.getNum = 0
        self.following = 0
        self.followers = 0
        self.WBInfo = []

    def getWBInfo(self):
        """获取微博信息"""
        try:
            url = "https://weibo.cn/u/%d" % (self.userid)
            selector = self.dealHTML(url)
            self.getUserAttr(selector)  # 获取用户昵称、微博数、关注数、粉丝数
            self.getPageNum(selector)  # 获取微博总页数
            wrote_num = 0
            page1 = 0
            random_pages = random.randint(1, 5)
            for page in tqdm(range(1, self.pageNum + 1), desc=u"进度"):
                self.get_one_page(page)  # 获取第page页的全部微博

                if page % 20 == 0:  # 每爬20页写入一次文件
                    self.write_file(wrote_num)
                    wrote_num = self.getNum

                # 通过加入随机等待避免被限制。
                # 默认是每爬取1到5页随机等待6到10秒，如果仍然被限，可适当增加sleep时间。
                if page - page1 == random_pages:
                    sleep(random.randint(6, 10))
                    page1 = page
                    random_pages = random.randint(1, 5)

            self.write_file(wrote_num)  # 将剩余不足20页的微博写入文件
            if not self.getAll:
                print(u"共爬取" + str(self.getNum) + u"条微博")
            else:
                print(u"共爬取" + str(self.getNum) + u"条原创微博")
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_one_weibo(self, info):
        """获取一条微博的全部信息"""
        try:
            WBInfo = OrderedDict()
            isOriginal = self.isOriginal(info)
            if (not self.getAll) or isOriginal:
                WBInfo["id"] = info.xpath("@id")[0][2:]
                WBInfo["content"] = self.getWBContent(info, isOriginal)  # 微博内容
                picture_urls = self.get_picture_urls(info, isOriginal)
                WBInfo["original_pictures"] = picture_urls[
                    "original_pictures"]  # 原创图片url
                if not self.getAll:
                    WBInfo["repost_pictures"] = picture_urls["repost_pictures"]  # 转发图片url
                    WBInfo["original"] = isOriginal  # 是否原创微博
                WBInfo["publish_place"] = self.getWBLocation(info)  # 微博发布位置
                WBInfo["publish_time"] = self.getWBTime(info)  # 微博发布时间
                WBInfo["publish_tool"] = self.getPublishTool(info)  # 微博发布工具
                data = self.getWBData(info)
                WBInfo["upNum"] = data["upNum"]  # 微博点赞数
                WBInfo["reNum"] = data["reNum"]  # 转发数
                WBInfo["commentNum"] = data["commentNum"]  # 评论数
            else:
                WBInfo = None
            return WBInfo
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_one_page(self, page):
        """获取第page页的全部微博"""
        try:
            url = "https://weibo.cn/u/%d?page=%d" % (self.userid, page)
            selector = self.dealHTML(url)
            info = selector.xpath("//div[@class='c']")
            is_exist = info[0].xpath("div/span[@class='ctt']")
            if is_exist:
                for i in range(0, len(info) - 2):
                    weibo = self.get_one_weibo(info[i])
                    if weibo:
                        self.WBInfo.append(weibo)
                        self.getNum += 1
                        print("-" * 100)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def dealHTML(self, url):
        """爬取HTML网页"""
        try:
            html = requests.get(url, cookies=self.cookies).content
            selector = etree.HTML(html)
            return selector
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getNickname(self):
        """获取用户昵称"""
        try:
            url = "https://weibo.cn/%d/info" % (self.userid)
            selector = self.dealHTML(url)
            nickname = selector.xpath("//title/text()")[0]
            self.nickname = nickname[:-3]
            if self.nickname == u"登录 - 新" or self.nickname == u"新浪":
                sys.exit(u"cookie错误或已过期,请按照README中方法重新获取")
            print(u"用户昵称: " + self.nickname)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getUserAttr(self, selector):
        """获取用户昵称、微博数、关注数、粉丝数"""
        try:
            self.getNickname()
            userInfo = selector.xpath("//div[@class='tip2']/*/text()")
            self.WBNum = int(userInfo[0][3:-1])
            self.following = int(userInfo[1][3:-1])
            self.followers = int(userInfo[2][3:-1])
            print(u"用户昵称：" + self.nickname)
            print(u"微博数：" + str(self.WBNum))
            print(u"关注数：" + str(self.following))
            print(u"粉丝数：" + str(self.followers))
            print("*"*101)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getPageNum(self, selector):
        """获取微博总页数"""
        try:
            if selector.xpath("//input[@name='mp']")==[]:
                self.pageNum = 1
            else:
                self.pageNum = (int)(selector
                .xpath("//input[@name='mp']")[0].attrib["value"])
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def dealGrabled(self, info):
        """处理乱码"""
        try:
            #去掉零长度空格
            info = (info.xpath("string(.)").replace(u"\u200b", "").encode(
                    sys.stdout.encoding, errors="ignore").decode(sys.stdout.encoding))
            return info
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def isOriginal(self,info):
        """判断微博是否为原创微博"""
        try:
            isOriginal = info.xpath("div/span[@class='cmt']")
            if len(isOriginal) > 3:
                return False
            else:
                return True
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getWBContent(self, info, isOriginal):
        """获取微博内容"""
        try:
            WBurl = info.xpath("@id")[0][2:]
            if isOriginal:
                WBContent = self.getOriginalWB(info, WBurl)
            else:
                WBContent = self.getRepostWB(info, WBurl)
            print(WBContent)
            return WBContent
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getOriginalWB(self, info, WBurl):
        """获取原创微博"""
        try:
            WBContent = self.dealGrabled(info)
            WBContent = WBContent[:WBContent.rfind(u"赞")]
            aTxT = info.xpath("div//a/text()")
            if u"全文" in aTxT:
                OriUrl = "https://weibo.cn/comment/"+WBurl
                tmpWBContent = self.getLongOriWB(OriUrl)
                if tmpWBContent:
                    WBContent = tmpWBContent
            return WBContent
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getLongOriWB(self, url):
        """获取原创长微博"""
        try:
            selector = self.dealHTML(url)
            info = selector.xpath("//div[@class='c']")[1]
            WBTime = selector.xpath("//span[@class='ct']/text()")[0]
            WBContent = self.dealGrabled(info)
            WBContent = WBContent[WBContent.find(":")+1:WBContent.rfind(WBTime)]
            return WBContent
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getRepostWB(self, info, WBurl):
        """获取转发微博"""
        try:
            originUsr = info.xpath("div/span[@class='cmt']/a/text()")
            if not originUsr:
                WBContent = u"转发微博已被作者删除"
                return WBContent
            else:
                originUsr = originUsr[0]
            WBContent = self.dealGrabled(info)
            WBContent = WBContent[WBContent.find(":")+1:WBContent.rfind(u"赞")]
            aTxT = info.xpath("div//a/text()")
            if u"全文" in aTxT:
                OriUrl = "https://weibo.cn/comment"+WBurl
                tmpWBContent = self.getLongOriWB(OriUrl)
                if tmpWBContent:
                    WBContent = tmpWBContent
            repostReason = self.dealGrabled(info.xpath("div")[-1])
            repostReason = repostReason[:repostReason.rfind(u"赞")]
            WBContent = (repostReason + "\n" + u"原始用户：" + originUsr
                         + "\n" + u"转发内容" + WBContent)
            return WBContent
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getWBTime(self, info):
        """获取微博发布时间"""
        try:
            tmpinfo = info.xpath("div/span[@class='ct']")
            tmpinfo = self.dealGrabled(tmpinfo[0])
            publishTime = tmpinfo.split(u"来自")[0]
            if u"刚刚" in publishTime:
                publishTime = datetime.now().strftime("%Y-%m-%d %H:%M")
            elif u"分钟" in publishTime:
                minute = publishTime[:publishTime.find(u"分钟")]
                minute = timedelta(minutes=int(minute))
                publishTime = (datetime.now()-minute).strftime("%Y-%m-%d %H:%M")
            elif u"今天" in publishTime:
                today = datetime.now().strftime("%Y-%m-%d")
                time = publishTime[3:]
                publishTime = today + " " + time
            elif u"月" in publishTime:
                year = datetime.now().strftime("%Y")
                month = publishTime[0:2]
                day = publishTime[3:5]
                time = publishTime[7:12]
                publishTime = year + "-" + month + "-" + day + "-" + time
            else:
                publishTime = publishTime[:16]
            print(u"微博发布时间：" + publishTime)
            return publishTime
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getPublishTool(self, info):
        """获取微博发布工具"""
        try:
            tmpinfo = info.xpath("div/span[@class='ct']")
            tmpinfo = self.dealGrabled(tmpinfo[0])
            if len(tmpinfo.split(u"来自")) > 1:
                publishTool = tmpinfo.split(u"来自")[1]
            else:
                publishTool = u"无"

            print(u"微博发布工具：" + publishTool)
            return publishTool
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getWBData(self, info):
        """获取微博数据：点赞数、转发数、评论数"""
        try:
            data = {}
            pattern = r"\d+"
            tmpinfo = info.xpath("div")[-1]
            tmpinfo = self.dealGrabled(tmpinfo)
            tmpinfo = tmpinfo[tmpinfo.rfind(u"赞"):]
            WBData = re.findall(pattern, tmpinfo, re.M)
            upNum = int(WBData[0])
            data["upNum"] = upNum
            print(u"点赞数：" + str(upNum))

            reNum = int(WBData[1])
            data["reNum"] = reNum
            print(u"转发数：" + str(reNum))

            commentNum = int(WBData[2])
            data["commentNum"] = commentNum
            print(u"评论数：" + str(commentNum))
            return data
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getWBLocation(self, info):
        """获取微博发布位置"""
        try:
            div_first = info.xpath("div")[0]
            a_list = div_first.xpath("a")
            publish_place = u"无"
            for a in a_list:
                if ("place.weibo.com" in a.xpath("@href")[0]
                        and a.xpath("text()")[0] == u"显示地图"):
                    weibo_a = div_first.xpath("span[@class='ctt']/a")
                    if len(weibo_a) >= 1:
                        publish_place = weibo_a[-1]
                        if (u"视频" == div_first.xpath(
                                "span[@class='ctt']/a/text()")[-1][-2:]):
                            if len(weibo_a) >= 2:
                                publish_place = weibo_a[-2]
                            else:
                                publish_place = u"无"
                        publish_place = self.dealGrabled(publish_place)
                        break
            print(u"微博发布位置: " + publish_place)
            return publish_place
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def extract_picture_urls(self, info, WBurl):
        """提取微博原始图片url"""
        try:
            a_list = info.xpath("div/a/@href")
            first_pic = "https://weibo.cn/mblog/pic/" + WBurl + "?rl=0"
            all_pic = "https://weibo.cn/mblog/picAll/" + WBurl + "?rl=1"
            if first_pic in a_list:
                if all_pic in a_list:
                    selector = self.dealHTML(all_pic)
                    preview_picture_list = selector.xpath("//img/@src")
                    picture_list = [p.replace("/thumb180/", "/large/") for p in preview_picture_list]
                    picture_urls = ",".join(picture_list)
                else:
                    preview_picture = info.xpath(".//img/@src")[-1]
                    picture_urls = preview_picture.replace(
                        "/wap180/", "/large/")
            else:
                picture_urls = "无"
            return picture_urls
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_picture_urls(self, info, isOriginal):
        """获取微博原始图片url"""
        try:
            WBurl = info.xpath("@id")[0][2:]
            picture_urls = {}
            if isOriginal:
                original_pictures = self.extract_picture_urls(info, WBurl)
                picture_urls["original_pictures"] = original_pictures
                if not self.getPic:
                    picture_urls["repost_pictures"] = "无"
            else:
                repost_url = info.xpath("div/a[@class='cc']/@href")[0]
                repost_id = repost_url.split("/")[-1].split("?")[0]
                repost_pictures = self.extract_picture_urls(info, repost_id)
                picture_urls["repost_pictures"] = repost_pictures
                a_list = info.xpath("div[last()]/a/@href")
                original_picture = "无"
                for a in a_list:
                    if a.endswith((".gif", ".jpeg", ".jpg", ".png")):
                        original_picture = a
                        break
                picture_urls["original_pictures"] = original_picture
            return picture_urls
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def download_pic(self, url, pic_path):
        """下载单张图片"""
        try:
            p = requests.get(url)
            with open(pic_path, "wb") as f:
                f.write(p.content)
        except Exception as e:
            error_file = self.get_filepath(
                "img") + os.sep + "not_downloaded_pictures.txt"
            with open(error_file, "ab") as f:
                url = url + "\n"
                f.write(url.encode(sys.stdout.encoding))
            print("Error: ", e)
            traceback.print_exc()

    def download_pictures(self):
        """下载微博图片"""
        try:
            print(u"即将进行图片下载")
            img_dir = self.get_filepath("img")
            for w in tqdm(self.WBInfo, desc=u"图片下载进度"):
                if w["original_pictures"] != "无":
                    pic_prefix = w["publish_time"][:11].replace(
                        "-", "") + "_" + w["id"]
                    if "," in w["original_pictures"]:
                        w["original_pictures"] = w["original_pictures"].split(
                            ",")
                        for j, url in enumerate(w["original_pictures"]):
                            pic_suffix = url[url.rfind("."):]
                            pic_name = pic_prefix + "_" + str(j +
                                                              1) + pic_suffix
                            pic_path = img_dir + os.sep + pic_name
                            self.download_pic(url, pic_path)
                    else:
                        pic_suffix = w["original_pictures"][
                                     w["original_pictures"].rfind("."):]
                        pic_name = pic_prefix + pic_suffix
                        pic_path = img_dir + os.sep + pic_name
                        self.download_pic(w["original_pictures"], pic_path)
            print(u"图片下载完毕,保存路径:")
            print(img_dir)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def write_csv(self, wrote_num):
        """将爬取的信息写入csv文件"""
        try:
            result_headers = [
                "微博id",
                "微博正文",
                "原始图片url",
                "发布位置",
                "发布时间",
                "发布工具",
                "点赞数",
                "转发数",
                "评论数",
            ]
            if not self.getAll:
                result_headers.insert(3, "被转发微博原始图片url")
                result_headers.insert(4, "是否为原创微博")
            result_data = [w.values() for w in self.WBInfo][wrote_num:]
            with open(self.get_filepath("csv"),
                      "a", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                if wrote_num == 0:
                    writer.writerows([result_headers])
                writer.writerows(result_data)
            print(u"%d条微博写入csv文件完毕,保存路径:" % self.getNum)
            print(self.get_filepath("csv"))
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def write_txt(self, wrote_num):
        """将爬取的信息写入txt文件"""
        try:
            temp_result = []
            if wrote_num == 0:
                if self.getAll:
                    result_header = u"\n\n原创微博内容: \n"
                else:
                    result_header = u"\n\n微博内容: \n"
                result_header = (u"用户信息\n用户昵称：" + self.nickname + u"\n用户id: " +
                                 str(self.userid) + u"\n微博数: " +
                                 str(self.WBNum) + u"\n关注数: " +
                                 str(self.following) + u"\n粉丝数: " +
                                 str(self.followers) + result_header)
                temp_result.append(result_header)
            for i, w in enumerate(self.WBInfo[wrote_num:]):
                temp_result.append(
                    str(wrote_num + i + 1) + ":" + w["content"] + "\n" +
                    u"微博位置: " + w["publish_place"] + "\n" + u"发布时间: " +
                    w["publish_time"] + "\n" + u"点赞数: " + str(w["upNum"]) +
                    u"   转发数: " + str(w["reNum"]) + u"   评论数: " +
                    str(w["commentNum"]) + "\n" + u"发布工具: " +
                    w["publish_tool"] + "\n\n")
            result = "".join(temp_result)
            with open(self.get_filepath("txt"), "ab") as f:
                f.write(result.encode(sys.stdout.encoding))
            print(u"%d条微博写入txt文件完毕,保存路径:" % self.getNum)
            print(self.get_filepath("txt"))
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def write_file(self, wrote_num):
        """写文件"""
        if self.getNum > wrote_num:
            self.write_csv(wrote_num)
            self.write_txt(wrote_num)

    def get_filepath(self, type):
        """获取结果文件路径"""
        try:
            file_dir = os.path.split(os.path.realpath(
                __file__))[0] + os.sep + "Weibo" + os.sep + self.nickname
            if type == "img":
                file_dir = file_dir + os.sep + "img"
            if not os.path.isdir(file_dir):
                os.makedirs(file_dir)
            if type == "img":
                return file_dir
            file_path = file_dir + os.sep + "%d" % self.userid + "." + type
            return file_path
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def start(self):
        """运行爬虫"""
        try:
            self.getWBInfo()
            print(u"信息抓取完毕")
            print("*" * 100)
            if self.getPic == 1:
                self.download_pictures()
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()


def main():
    try:
        # 使用实例,输入一个用户id，所有信息都会存储在wb实例中
        userid = 6592596872  # 可以改成任意合法的用户id（爬虫的微博id除外）
        getAll = 0  # 值为0表示爬取全部微博（原创微博+转发微博），值为1表示只爬取原创微博
        getPic = 0  # 值为0代表不下载微博原始图片,1代表下载微博原始图片
        wb = Weibo(userid, getAll, getPic)  # 调用Weibo类，创建微博实例wb
        wb.start()  # 爬取微博信息
        print(u"用户昵称: " + wb.nickname)
        print(u"全部微博数: " + str(wb.WBNum))
        print(u"关注数: " + str(wb.following))
        print(u"粉丝数: " + str(wb.followers))
        if wb.WBInfo:
            print(u"最新/置顶 微博为: " + wb.WBInfo[0]["content"])
            print(u"最新/置顶 微博位置: " + wb.WBInfo[0]["publish_place"])
            print(u"最新/置顶 微博发布时间: " + wb.WBInfo[0]["publish_time"])
            print(u"最新/置顶 微博获得赞数: " + str(wb.WBInfo[0]["upNum"]))
            print(u"最新/置顶 微博获得转发数: " + str(wb.WBInfo[0]["reNum"]))
            print(u"最新/置顶 微博获得评论数: " + str(wb.WBInfo[0]["commentNum"]))
            print(u"最新/置顶 微博发布工具: " + wb.WBInfo[0]["publish_tool"])
    except Exception as e:
        print("Error: ", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
