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
    repos_url = f'https://api.github.com/users/{username}/repos'
    repos_response = requests.get(repos_url)
    repos_name = []
    if repos_response.status_code == 200:
        repos = repos_response.json()
        for repo in repos:
            # add repo to repos_name
            repos_name.append(repo['name'])

    issues = []
    for repo in repos_name:
        issues_url = f'https://api.github.com/repos/{username}/{repo}/issues'
        params = {
            'labels': 'todo',
            'state': 'open',
            'fields': 'title,html_url,repository_url'
        }
        issues_response = requests.get(issues_url, headers={'Authorization': f'token {access_token}'}, params=params)
        if issues_response.status_code == 200:
            issues.extend(issues_response.json())
    # ------------  END   issues  ------------------

    data_print(blogs, issues)

def data_print(blogs, issues):
    with open('README.md', 'w') as f:
        sys.stdout = f  # Change the standard output to the file we created.

        print("🌱 **last week**\n\n<!--START_SECTION:waka-->\n\n<!--END_SECTION:waka-->", end='\n\n')

        print('<table style="width: 100%;">\n<td style="width: 60%">\n\n')

        print("📒 **recent notes**\n")
        blog_count = 0
        for day in blogs.select('div.day'):
            for date in day.select('div.dayTitle a'):
                for aritle in day.select('a.postTitle2'):
                        temp = date.text.replace('\n', '')
                        date_obj = datetime.strptime(temp, '%Y年%m月%d日')
                        new_date_str = date_obj.strftime('%Y-%m-%d')
                        if blog_count < 6:
                            print('- `', new_date_str, '`&nbsp;&nbsp;[', aritle.get_text().strip(), '](', aritle.get('href'), ')', sep='')
                            blog_count += 1

        print('\n</td>\n<td style="width: 60%">\n\n')

        print("\n🕛 **recent todos**\n")

        # only show 6 issues
        issues = issues[:6]
        for issue in issues:
            repo_name = issue['repository_url'].split("/")[-1]
            username = issue['repository_url'].split("/")[-2]
            print(f"- [{issue['title']}]({issue['html_url']}) `{repo_name}` ")

        print('\n</td>\n</table>\n')

        sys.stdout = original_stdout  # Reset the standard output to its original value


if __name__ == "__main__":
    access_token = sys.argv[1]
    get_bs('zjy4fun', access_token)
