'''
爬取博客园某个作者所有文章
'''
from bs4 import BeautifulSoup
import requests
import sys
import re
import time

original_stdout = sys.stdout  # Save a reference to the original standard output


def get_bs(author, page=1):
    '''
    传入作者博客园的id，页数（不传页数则从第一页开始查找）
    如果存在下一页按钮，则递归调用自己获取下一页的数据
    '''
    r = requests.get(f'https://www.cnblogs.com/{author}/default.html/?page={page}')
    # print(r.content)
    soup = BeautifulSoup(r.content, 'html5lib')
    # print(f'第{page}页：')
    data_print(soup)
    # if soup.select(f'a[href="https://www.cnblogs.com/{author}/default.html?page={page+1}"]'):  # 如果有下一页的链接
    #     get_bs(author, page+1)

def data_print(soup):  # 这里可以优化显示文章链接啥的
    '''
    通过css选择器打印所有日期和文章标题
    '''
    with open('README.md', 'w') as f:
        sys.stdout = f  # Change the standard output to the file we created.
        print('## 最近的笔记')
        for day in soup.select('div.day'):
            for date in day.select('div.dayTitle a'):
                for aritle in day.select('a.postTitle2'): # 每天可能有多篇文章
                    date_text = re.search(r'(20\d{2})[/:-]([0-1]?\d)[/:-]([0-3]?\d)', date.get('href'))[0]
                    timeArray = time.strptime(date_text, "%Y/%m/%d")
                    strTime = time.strftime("%Y-%m-%d", timeArray)
                    print('- ',strTime, ' ', '[', aritle.get_text().strip(), '](', aritle.get('href'), ')', sep='')
        sys.stdout = original_stdout  # Reset the standard output to its original value


if __name__ == "__main__":
    get_bs('realzhaijiayu')
