#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import re
import codecs
import csv
import traceback
import time
import plotly.offline as pltoff
import plotly.graph_objs as go
from collections import OrderedDict


def main():
    try:
        with open(u"人民日报/2803301701.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = [row for row in reader]
            #建立数据字典
            wb_content = [rows[i][1] for i in range(1, len(rows))]
            is_original = [rows[i][4] for i in range(1, len(rows))]
            pb_time = [rows[i][6] for i in range(1, len(rows))]
            pb_tool = [rows[i][7] for i in range(1, len(rows))]
            upNum = [int(rows[i][8]) for i in range(1, len(rows))]
            reNum = [int(rows[i][9]) for i in range(1, len(rows))]
            coNum = [int(rows[i][10]) for i in range(1, len(rows))]
            wb_dict = OrderedDict()
            for i in range(0, len(rows)-1):
                wb_dict[str(i+1)] = [wb_content[i], is_original[i],
                                     pb_time[i], pb_tool[i], upNum[i], reNum[i], coNum[i]]
            #所有微博内容写入txt
            total_wb_content_txt(wb_dict)
            #是否清除数据异常点
            handle_exception = 1

            # 1.按年代将微博进行分组：转赞评数量分析画图及整体画图
            wb_dict = handle_exception_records(wb_dict, handle_exception)
            yearly_records = group_by_year(wb_dict)
            # 数据按年份分开并写入csv
            write_yearly_to_csv(yearly_records)
            yearly_daily_records = group_by_year_daily(yearly_records)
            yearly_monthly_records = group_by_year_monthly(yearly_records)

            handle_average_data(yearly_daily_records)
            handle_average_data(yearly_monthly_records)

            plot_data_yearly(yearly_records)
            plot_data_yearly_daily(yearly_daily_records)
            plot_data_yearly_monthly(yearly_monthly_records)
            plot_data_total_year(yearly_records, yearly_daily_records, yearly_monthly_records)

    except Exception as e:
        print("Error: ", e)
        traceback.print_exc()


def group_by_year(wb_dict):
    """按照年代划分记录"""
    years = ["2019-01-01 00:00", "2018-01-01 00:00", "2017-01-01 00:00",
             "2016-01-01 00:00", "2015-01-01 00:00", "2014-01-01 00:00", "2013-01-01 00:00", "2012-01-01 00:00"]
    piece_cnt = {"2020": 0, "2019": 0, "2018": 0, "2017": 0, "2016": 0, "2015": 0, "2014": 0, "2013": 0, "2012": 0}
    yearly_records = []
    pb_time = [value[2] for value in wb_dict.values()]
    try:
        for year in years:
            pivot_time = time.mktime(time.strptime(year, "%Y-%m-%d %H:%M"))
            for wb_time in pb_time:
                cmp_time = time.mktime(time.strptime(wb_time.strip(), "%Y-%m-%d %H:%M"))
                if int(cmp_time)-int(pivot_time) >= 0:
                    piece_cnt[year[:4]] += 1
                else:
                    break
        #数据按年存放
        for i in range(len(years)):
            tmpDict = OrderedDict()
            for j in range(piece_cnt[str(2020-i)], piece_cnt[str(2019-i)]):
                tmpDict[str(j+1)] = wb_dict[str(j+1)]
            yearly_records.append(tmpDict)
        return yearly_records
    except Exception as e:
        print("Error :", e)
        traceback.print_exc()


def group_by_year_daily(yearly_records):
    year_daily = []
    for i in range(len(yearly_records)):
        tmpDict = OrderedDict()
        days = set([row[2].strip()[:10] for row in yearly_records[i].values()])
        days = list(days)
        days.sort()
        for day in days:
            tmpDict[day] = [[row[0] for row in yearly_records[i].values() if row[2].strip()[:10] == day],
                            [int(row[4]) for row in yearly_records[i].values() if row[2].strip()[:10] == day],
                            [int(row[5]) for row in yearly_records[i].values() if row[2].strip()[:10] == day],
                            [int(row[6]) for row in yearly_records[i].values() if row[2].strip()[:10] == day],
                            [1 for row in yearly_records[i].values() if row[2].strip()[:10] == day]]
        year_daily.append(tmpDict)
    return year_daily


def group_by_year_monthly(yearly_records):
    year_monthly = []
    for i in range(len(yearly_records)):
        tmpDict = OrderedDict()
        days = set([row[2].strip()[:7] for row in yearly_records[i].values()])
        days = list(days)
        days.sort()
        for day in days:
            tmpDict[day] = [[row[0] for row in yearly_records[i].values() if row[2].strip()[:7] == day],
                            [int(row[4]) for row in yearly_records[i].values() if row[2].strip()[:7] == day],
                            [int(row[5]) for row in yearly_records[i].values() if row[2].strip()[:7] == day],
                            [int(row[6]) for row in yearly_records[i].values() if row[2].strip()[:7] == day],
                            [1 for row in yearly_records[i].values() if row[2].strip()[:7] == day]]
        year_monthly.append(tmpDict)
    return year_monthly


def handle_average_data(records):
    for i in range(len(records)):
        for key, value in records[i].items():
            value[1] = sum(value[1])/sum(value[4])
            value[2] = sum(value[2])/sum(value[4])
            value[3] = sum(value[3])/sum(value[4])


def write_yearly_to_csv(yearly_records):
    """将各年的精简信息写入csv与txt文件"""
    try:
        for i in range(len(yearly_records)):
            result_data = yearly_records[i].values()
            write_weibo_content("rmrb_"+str(2019-i)+"_weibo_content", result_data)

    except Exception as e:
        print("Error: ", e)
        traceback.print_exc()


def plot_data_yearly(yearly_records):
    """对每年(每日若干条)的微博数据转赞评进行分析"""
    for i in range(len(yearly_records)):
        up_line = go.Scatter(name=u"点赞数", x=[row[2] for row in yearly_records[i].values()],
                             y=[row[4] for row in yearly_records[i].values()], mode="lines")
        re_line = go.Scatter(name=u"转发数", x=[row[2] for row in yearly_records[i].values()],
                             y=[row[5] for row in yearly_records[i].values()], mode="lines")
        co_line = go.Scatter(name=u"评论数", x=[row[2] for row in yearly_records[i].values()],
                             y=[row[6] for row in yearly_records[i].values()], mode="lines")
        layout = go.Layout(showlegend=True,
                           legend=dict(x=0.9,
                                       y=1.1), xaxis={'title': 'year'}, yaxis={'title': 'weibo_data'})
        data = [up_line, re_line, co_line]
        fig = go.Figure(data=data, layout=layout)
        pltoff.plot(fig, filename=str(2019-i)+"yearly_chaos.html")


def plot_data_yearly_daily(yearly_daily_records):
    """对每年(按每天微博汇总）的微博数据转赞评进行分析"""
    for i in range(len(yearly_daily_records)-1, 0, -1):
        up_line = go.Scatter(name=u"点赞数", x=list(yearly_daily_records[i].keys()),
                             y=[row[1] for row in yearly_daily_records[i].values()], mode="lines")
        re_line = go.Scatter(name=u"转发数", x=list(yearly_daily_records[i].keys()),
                             y=[row[2] for row in yearly_daily_records[i].values()], mode="lines")
        co_line = go.Scatter(name=u"评论数", x=list(yearly_daily_records[i].keys()),
                             y=[row[3] for row in yearly_daily_records[i].values()], mode="lines")
        layout = go.Layout(showlegend=True,
                           legend=dict(x=0.9, y=1.1),
                           xaxis={'title': 'year(daily average)'}, yaxis={'title': 'weibo_data'})
        data = [up_line, re_line, co_line]
        fig = go.Figure(data=data, layout=layout)
        pltoff.plot(fig, filename=str(2019-i)+"yearly_daily.html")


def plot_data_yearly_monthly(yearly_monthly_records):
    """对每年(按每月微博汇总）的微博数据转赞评进行分析"""
    for i in range(len(yearly_monthly_records)-1, 0, -1):
        up_line = go.Scatter(name=u"点赞数", x=list(yearly_monthly_records[i].keys()),
                             y=[row[1] for row in yearly_monthly_records[i].values()], mode="lines")
        re_line = go.Scatter(name=u"转发数", x=list(yearly_monthly_records[i].keys()),
                             y=[row[2] for row in yearly_monthly_records[i].values()], mode="lines")
        co_line = go.Scatter(name=u"评论数", x=list(yearly_monthly_records[i].keys()),
                             y=[row[3] for row in yearly_monthly_records[i].values()], mode="lines")
        layout = go.Layout(showlegend=True,
                           legend=dict(x=0.9, y=1.1),
                           xaxis={'title': 'year(monthly average)'}, yaxis={'title': 'weibo_data'})
        data = [up_line, re_line, co_line]
        fig = go.Figure(data=data, layout=layout)
        pltoff.plot(fig, filename=str(2019-i)+"yearly_monthly.html")


def plot_data_total_year(yearly_records,yearly_daily_records,yearly_monthly_records):
    """把所有数据合在一起画图，体现趋势，这一个函数画三张图"""
    #year-day
    totalx = [[], [], []]
    totalup = [[], [], []]
    totalre = [[], [], []]
    totalco = [[], [], []]
    chart_titles = ['total_year_day(without cluster)', 'total_year_daily_average', 'total_year_monthly_average']
    for i in range(len(yearly_records)):
        totalx[0].extend([row[2] for row in yearly_records[i].values()])
        totalup[0].extend([row[4] for row in yearly_records[i].values()])
        totalre[0].extend([row[5] for row in yearly_records[i].values()])
        totalco[0].extend([row[6] for row in yearly_records[i].values()])
    #year-day-average
    for i in range(len(yearly_daily_records)-1, 0, -1):
        totalx[1].extend(list(yearly_daily_records[i].keys()))
        totalup[1].extend([row[1] for row in yearly_daily_records[i].values()])
        totalre[1].extend([row[2] for row in yearly_daily_records[i].values()])
        totalco[1].extend([row[3] for row in yearly_daily_records[i].values()])
    #year-month-average
    for i in range(len(yearly_monthly_records)-1, 0, -1):
        totalx[2].extend(list(yearly_monthly_records[i].keys()))
        totalup[2].extend([row[1] for row in yearly_monthly_records[i].values()])
        totalre[2].extend([row[2] for row in yearly_monthly_records[i].values()])
        totalco[2].extend([row[3] for row in yearly_monthly_records[i].values()])
    for i in range(len(totalx)):
        up_line = go.Scatter(name=u"点赞数", x=totalx[i], y=totalup[i], mode="lines")
        re_line = go.Scatter(name=u"转发数", x=totalx[i], y=totalre[i], mode="lines")
        co_line = go.Scatter(name=u"评论数", x=totalx[i], y=totalco[i], mode="lines")
        layout = go.Layout(showlegend=True,
                           legend=dict(x=0.9,
                                       y=1.1), xaxis={'title': chart_titles[i]}, yaxis={'title': 'weibo_data'})
        data = [up_line, re_line, co_line]
        fig = go.Figure(data=data, layout=layout)
        pltoff.plot(fig, filename=chart_titles[i]+".html")


def handle_exception_records(wb_dict, handle_exception):
    """处理异常数据点，主要是转发量有时会异常(从数据集中去掉再分析平均水平）,
        另外需要有函数接口在这里保存异常数据集"""
    if handle_exception:
        tmp_wb_dict_records = []
        large_records = []
        for value in wb_dict.values():
            tmp_wb_dict_records.append(value)
        tmp_wb_dict_records = sorted(tmp_wb_dict_records, key=lambda x: sum([x[4], x[5], x[6]]), reverse=True)
        #记录其前2%的数据
        large_records = tmp_wb_dict_records[:len(tmp_wb_dict_records)//50]
        write_weibo_content("rmrb_hot_weibo_content", large_records)
        #将前2%的数据从数据集中去掉
        try:
            del tmp_wb_dict_records[:len(tmp_wb_dict_records)//50]
            tmp_wb_dict_records = sorted(tmp_wb_dict_records, key=lambda x: x[2], reverse=True)
            new_wb_dict = OrderedDict()
            for i in range(len(tmp_wb_dict_records)):
                new_wb_dict[str(i+1)] = tmp_wb_dict_records[i]
            return new_wb_dict
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()
    else:
        return wb_dict


def write_weibo_content(filename, large_records):
    #将微博精简内容写入csv
    try:
        result_headers = [
            "微博正文",
            "是否原创",
            "发布时间",
            "发布工具",
            "点赞数",
            "转发数",
            "评论数",
        ]
        with open(filename+".csv", "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows([result_headers])
            writer.writerows(large_records)
        print(u"微博内容写入csv文件完毕,保存路径:")
        print(filename+".csv")
        #微博内容文本初步处理并存入txt
        hot_wb = codecs.open(filename+".txt", "w", "utf-8")
        #处理网址与特殊标点符号
        for row in large_records:
            row[0] = str(row[0][:row[0].rfind('http')]
                                         if row[0].rfind('http') != -1 else row[0])
            row[0] = re.sub(r',{2,}', ',',
                    re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])",
                           ',', row[0]), re.S)
        hot_wb.writelines(row[0]+'\n' for row in large_records)
        hot_wb.close()
        print(u"微博内容写入txt文件完毕,保存路径:")
        print(filename+".txt")
    except Exception as e:
        print("Error: ", e)
        traceback.print_exc()


def total_wb_content_txt(wb_dict):
    """写入所有微博内容"""
    tmp_dict = wb_dict
    wb_content = []
    for value in tmp_dict.values():
        wb_content.append(value)
    write_weibo_content("rmrb_total_weibo_content", wb_content)


if __name__ == "__main__":
    main()