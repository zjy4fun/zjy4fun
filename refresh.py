from bs4 import BeautifulSoup
import requests
import sys
from datetime import datetime


original_stdout = sys.stdout  # Save a reference to the original standard output
def get_bs(username, access_token):
    # ------------  START blogs  ------------------
    page = 1
    r = requests.get(f'https://www.cnblogs.com/{username}/default.html?page={page}')
    blogs = BeautifulSoup(r.content, 'html5lib')
    # ------------  END   blogs  ------------------

    # ------------  START issues  ------------------

    # 得到一个人有多少仓库名字
    # repos_url = f'https://api.github.com/users/{username}/repos'
    # repos_response = requests.get(repos_url)
    # repos_name = []
    # if repos_response.status_code == 200:
    #     repos = repos_response.json()
    #     for repo in repos:
    #         # add repo to repos_name
    #         repos_name.append(repo['name'])

    # TODO 暂时只有一个仓库
    repos_name = ['notes']
    issues = []
    for repo in repos_name:
        issues_url = f'https://api.github.com/repos/{username}/{repo}/issues'
        params = {
            'labels': 'todo',
            'state': 'open',
            'fields': 'title,html_url,repository_url',
        }
        issues_response = requests.get(issues_url, headers={'Authorization': f'token {access_token}'}, params=params)
        if issues_response.status_code == 200:
            issues.extend(issues_response.json())
    # ------------  END   issues  ------------------

    new_content = data_print(blogs, issues)

    # Check if the content has changed before writing to README.md
    if has_content_changed(new_content):
        new_content += get_old_waka_data()
        write_to_readme(new_content)

# TODO 优化版本比较算法
def has_content_changed(new_content):
    try:
        with open('README.md', 'r') as f:
            existing_content = f.read()
            if "\n🌱 **上周**" in existing_content:
                existing_content = existing_content.split("\n## 🌱 **上周**")[0]
            return existing_content != new_content
    except FileNotFoundError:
        # README.md doesn't exist yet, so content has definitely changed
        return True

def get_old_waka_data():
    try:
        with open('README.md', 'r') as f:
            existing_content = f.read()
            if "\n🌱 **上周**" in existing_content:
                existing_content = existing_content.split("\n## 🌱 **上周**")[1]
                return "\n## 🌱 **上周**" + existing_content
            else:
                return "\n## 🌱 **上周**\n\n<!--START_SECTION:waka-->\n\n<!--END_SECTION:waka-->\n"
    except FileNotFoundError:
        # README.md doesn't exist yet, so content has definitely changed
        return "\n## 🌱 **上周**\n\n<!--START_SECTION:waka-->\n\n<!--END_SECTION:waka-->\n"

def data_print(blogs, issues):
    content = ''
    content += "## 🕛 **待办**\n"
    # only show 6 issues
    issues = issues[:10]
    # 如果 issuse 不足 6 个，用空位补齐
    # for i in range(6 - len(issues)):
    #     issues.append({'title': 'TODO', 'html_url': 'https://github.com/zjy4fun/notes/issues', 'repository_url': '', 'created_at': '1990-01-01'})
    for issue in issues:
        # repo_name = issue['repository_url'].split("/")[-1]
        # username = issue['repository_url'].split("/")[-2]
        date = issue['created_at'].split("T")[0]
        content += f"- `{date}`&nbsp;&nbsp;[{issue['title']}]({issue['html_url']})\n"

    # content += '<table style="width: 100%;">\n<td style="width: 60%">\n\n'
    content += "\n## 📒 **笔记**\n"
    blog_count = 0

    for day in blogs.select('div.day'):
        for date in day.select('div.dayTitle a'):
            for aritle in day.select('a.postTitle2'):
                temp = date.text.replace('\n', '')
                date_obj = datetime.strptime(temp, '%Y年%m月%d日')
                new_date_str = date_obj.strftime('%Y-%m-%d')
                if blog_count < 10:
                    content += f'- `{new_date_str}`&nbsp;&nbsp;[{aritle.get_text().strip()}]({aritle.get("href")})\n'
                    blog_count += 1
    # content += '\n</td>\n<td style="width: 60%">\n\n'

    # content += '\n</td>\n</table>\n'

    return content

def write_to_readme(new_content):
    with open('README.md', 'w') as f:
        sys.stdout = f  # Change the standard output to the file we created.
        print(new_content, end='')
        sys.stdout = original_stdout  # Reset the standard output to its original value

if __name__ == "__main__":
    access_token = sys.argv[1]
    get_bs('zjy4fun', access_token)
