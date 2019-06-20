#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from collections import Counter
from os import path
import jieba
import codecs
import traceback
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import random
import re

def stop_word_list(filepath):
    """创建停用词list"""
    f = codecs.open(filepath, 'r', encoding='utf-8')
    stopwords = [line.strip() for line in f.readlines()]
    f.close()
    return stopwords


def seg_sentence(sentence):
    """中文分词"""
    sentence_seged = jieba.cut(sentence.strip())
    stopwords = stop_word_list('stopword.txt')
    outstr = ''
    for word in sentence_seged:
        if word not in stopwords:
            if word != '\t':
                outstr += word
                outstr += " "
    return outstr


def write_word_count(filename):
    """词频统计"""
    with open('seged_'+filename+'.txt', 'r', encoding="utf-8-sig") as fr:
        data = jieba.cut(fr.read())
    data = dict(Counter(data))
    sorted_data = []
    for k, v in data.items():
        sorted_data.append([k, v])
    sorted_data = sorted(sorted_data, key=lambda x: x[1], reverse=True)
    with open(filename+'_word_count.txt', 'w', encoding="utf-8-sig") as fw:
        for k, v in sorted_data:
            if k != ' ' and k != '\n' and len(k) != len(u"一") and k.isdigit() != True:
                fw.write("{0:25}{1:>25}\n".format(k, v))
    print("词频统计成功，写入路径：")
    print(filename+"_word_count.txt")


def read_counter(filename):
    file = codecs.open(filename+"_word_count.txt", "r", "utf-8")
    tmp_count = file.readlines()
    word_count = {}
    for row in tmp_count:
        row = re.sub(r',{2,}', ',',
                        re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])",
                               ',', row), re.S)
        row = row.split(',')
        if row[0] == '':
            row = row[1:-1]
        else:
            row = row[:-1]
        word_count[row[0]] = int(row[1])

    return word_count


def gen_tag_cloud(frequencies, filename):
    """生成标签云"""
    d = path.dirname(__file__)
    mask = np.array(Image.open(path.join(d, "view.jpg")))
    stopwords = STOPWORDS.copy()

    wc = WordCloud(background_color="white", max_words=2000, mask=mask, stopwords=stopwords, margin=10,
                   random_state=42, font_path="msyh.ttf", width=1280, height=1024).fit_words(frequencies)
    image_colors = ImageColorGenerator(mask)

    plt.imshow(wc)
    plt.axis("off")
    plt.figure()
    wc.to_file(filename + "_tag_cloud_default.png")

    plt.imshow(wc.recolor(color_func=image_colors))
    plt.axis("off")
    plt.figure()
    wc.to_file(filename+"_tag_cloud_colored.png")


def main():
    print("Usage:[filename] e.g. rmrb_hot_weibo_content")
    print("filename: ", end='')
    filename = input()
    try:
        inputs = codecs.open(filename+'.txt', 'r', 'utf-8')
        outputs = codecs.open('seged_'+filename+'.txt', 'w', 'utf-8')
        for line in inputs:
            line_seg = seg_sentence(line.replace(u'\u200b', ''))
            outputs.write(line_seg+'\n')
        print("分词成功，写入路径：")
        print("seged_"+filename+'.txt')
        outputs.close()
        inputs.close()
        write_word_count(filename)
        word_freq = read_counter(filename)
        gen_tag_cloud(word_freq, filename)
    except Exception as e:
        print("Error: ", e)
        traceback.print_exc()


if __name__ == '__main__':
    main()