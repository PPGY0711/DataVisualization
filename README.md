# WeiboCrawler.py

功能：爬取新浪微博信息，并写入csv/txt文件，文件名为目标用户id加".csv"和".txt"的形式，同时还会下载该微博原始图片(可选)。

## 输入

用户id，例如新浪微博昵称为“人民日报”的id为“2803301701”

## 输出

- 昵称：用户昵称，如"人民日报"
- 微博数：用户的全部微博数（转发微博+原创微博）
- 关注数：用户关注的微博数量
- 粉丝数：用户的粉丝数
- 微博id：微博唯一标志
- 微博内容：微博正文
- 原始图片url：原创微博图片和转发微博转发理由中图片的url，若某条微博存在多张图片，每个url以英文逗号分隔，若没有图片则值为无
- 微博发布位置：位置微博中的发布位置
- 微博发布时间：微博发布时的时间，精确到分
- 点赞数：微博被赞的数量
- 转发数：微博被转发的数量
- 评论数：微博被评论的数量
- 微博发布工具：微博的发布工具，如iPhone客户端、HUAWEI Mate 20 Pro等
- 结果文件：保存在当前目录weibo文件夹下以用户昵称为名的文件夹里，名字为"user_id.csv"和"user_id.txt"的形式
- 微博图片：原创微博中的图片和转发微博转发理由中的图片，保存在以用户昵称为名的文件夹下的img文件夹里

运行环境

- 开发语言：python2/python3
- 系统： Windows/Linux/macOS

# 使用说明

### 1.下载脚本

```bash
$ git clone https://github.com/dataabc/weibospider.git
```

运行上述命令，将本项目下载到当前目录，如果下载成功当前目录会出现一个名为"weibospider"的文件夹；

### 2.设置cookie和user_id

打开weibospider文件夹下的"**weibospider.py**"文件，将“**your cookie**”替换成爬虫微博的cookie，后面会详细讲解如何获取cookie；将**user_id**替换成想要爬取的微博的user_id，后面会详细讲解如何获取user_id;

如何获取cookie

1.用Chrome打开<https://passport.weibo.cn/signin/login>；<br>
2.输入微博的用户名、密码，登录，如图所示：
![](https://picture.cognize.me/cognize/github/weibospider/cookie1.png)
登录成功后会跳转到<https://m.weibo.cn>;<br>
3.按F12键打开Chrome开发者工具，在地址栏输入并跳转到<https://weibo.cn>，跳转后会显示如下类似界面:
![](https://picture.cognize.me/cognize/github/weibospider/cookie2.png)
4.依此点击Chrome开发者工具中的Network->Name中的weibo.cn->Headers->Request Headers，"Cookie:"后的值即为我们要找的cookie值，复制即可，如图所示：
![](https://picture.cognize.me/cognize/github/weibospider/cookie3.png)

# 如何获取user_id

1.打开网址<https://weibo.cn>，搜索我们要找的人，如”迪丽热巴“，进入她的主页；<br>
![](https://picture.cognize.me/cognize/github/weibospider/user_home.png)
2.按照上图箭头所指，点击"资料"链接，跳转到用户资料页面；<br>
![](https://picture.cognize.me/cognize/github/weibospider/user_info.png)
如上图所示，迪丽热巴微博资料页的地址为"<https://weibo.cn/1669879400/info>"，其中的"1669879400"即为此微博的user_id。<br>
事实上，此微博的user_id也包含在用户主页(<https://weibo.cn/u/1669879400?f=search_0>)中，之所以我们还要点击主页中的"资料"来获取user_id，是因为很多用户的主页不是"<https://weibo.cn/user_id?f=search_0>"的形式，而是"<https://weibo.cn/个性域名?f=search_0>"或"<https://weibo.cn/微号?f=search_0>"的形式。其中"微号"和user_id都是一串数字，如果仅仅通过主页地址提取user_id，很容易将"微号"误认为user_id。

## 注意事项

1.user_id不能为爬虫微博的user_id。因为要爬微博信息，必须先登录到某个微博账号，此账号我们姑且称为爬虫微博。爬虫微博访问自己的页面和访问其他用户的页面，得到的网页格式不同，所以无法爬取自己的微博信息；<br>
2.cookie有期限限制，超过有效期需重新更新cookie。

# DataWash.py

功能：进行数据清洗和文本处理，以不同的时间粒度画出转赞评（平均）数量折线图，并将微博内容提取，取出特殊符号后，写入csv与txt文件。

使用到的图形图表库：plotly

# TextAnalysis.py

功能：进行文本分词与词频统计，实现微博关键词提取与可视化（标签云）

使用到的中文分词库：jieba

使用到的标签云生成库：wordcloud

使用到的图形图像库：matplotlib
