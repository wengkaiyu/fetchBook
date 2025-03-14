import requests
from bs4 import BeautifulSoup
import zipfile
import os
import sys

# 定义请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

def get_chapter_links(base_url):
    """
    获取小说的所有章节链接和标题
    """
    chapter_links = []
    url = f"{base_url}"
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'  # 设置编码
    soup = BeautifulSoup(response.text, 'lxml')

    # 提取章节链接和标题（根据实际网页结构调整选择器）
    chapters = soup.find_all('dd')
    for chapter in chapters:
        link = chapter.find('a')['href']
        if link.startswith("/"):
            # 分割字符串，取前两部分
            parts = url.split('/')
            # 拼接前两部分，得到网站首页
            link = '/'.join(parts[0:3]) + link
        title = chapter.find('a').text.strip()
        chapter_links.append((link, title))

    return chapter_links

def get_chapter_content(chapter_url):
    """
    获取章节内容
    """
    response = requests.get(chapter_url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')

    # 提取章节内容（根据实际网页结构调整选择器）
    content = soup.find('div', id='content').get_text(separator='</p><p>')
    return '<p>' + content + '</p>'

def get_chapters(novel_name, chapter_links):
    chapters = []

    # 保存所有章节到一个TXT文件
    for link, title in chapter_links:
        print(title)
        content = get_chapter_content(link)
        full_text = f"\n\n# {title}\n\n{content}\n"
        chapters.append((title, full_text))
    return chapters

def create_epub(novel_name, chapters, author="Unknown"):
    """
    将小说内容保存为 epub 格式
    """
    # 创建临时目录结构
    temp_dir = "epub_temp"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(f"{temp_dir}/META-INF", exist_ok=True)
    os.makedirs(f"{temp_dir}/OEBPS", exist_ok=True)
    os.makedirs(f"{temp_dir}/OEBPS/Text", exist_ok=True)

    # 生成 mimetype 文件
    with open(f"{temp_dir}/mimetype", "w") as f:
        f.write("application/epub+zip")

    # 生成 container.xml
    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>"""
    with open(f"{temp_dir}/META-INF/container.xml", "w") as f:
        f.write(container_xml)

    # 生成 content.opf 文件
    content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>{novel_name}</dc:title>
        <dc:creator>{author}</dc:creator>
        <dc:language>zh-CN</dc:language>
    </metadata>
    <manifest>
        <item id="content.opf" href="content.opf" media-type="application/oebps-package+xml"/>
        <item id="toc.xhtml" href="toc.xhtml" media-type="application/xhtml+xml"/>
        <item id="style.css" href="style.css" media-type="text/css"/>
    </manifest>
    <spine>
        <itemref idref="toc.xhtml"/>
    </spine>
</package>"""
    with open(f"{temp_dir}/OEBPS/content.opf", "w") as f:
        f.write(content_opf)

    # 生成 toc.xhtml 文件（目录）
    toc_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Table of Contents</title>
    <link href="style.css" rel="stylesheet" type="text/css"/>
</head>
<body>
    <h1>{novel_name}</h1>
    <ul>
"""
    for index, (title, content) in enumerate(chapters, 1):
        chapter_id = f"chapter{index}"
        toc_xhtml += f"""        <li>
            <a href="Text/{chapter_id}.html">{title}</a>
        </li>
"""
    toc_xhtml += """    </ul>
</body>
</html>"""
    with open(f"{temp_dir}/OEBPS/toc.xhtml", "w") as f:
        f.write(toc_xhtml)

    # 生成 style.css 文件
    style_css = """body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0 10%;
}

h1 {
    text-align: center;
    margin-bottom: 20px;
}

h2 {
    margin-top: 30px;
    margin-bottom: 15px;
    border-bottom: 2px solid #333;
    padding-bottom: 5px;
}

p {
    margin: 10px 0;
}"""
    with open(f"{temp_dir}/OEBPS/style.css", "w") as f:
        f.write(style_css)

    # 生成章节内容 HTML 文件
    for index, (title, content) in enumerate(chapters, 1):
        chapter_id = f"chapter{index}"
        html_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{title}</title>
    <link href="../style.css" rel="stylesheet" type="text/css"/>
</head>
<body>
    <h2>{title}</h2>
    <p>{content}</p>
</body>
</html>"""
        with open(f"{temp_dir}/OEBPS/Text/{chapter_id}.html", "w") as f:
            f.write(html_content)

    # 打包成 epub 文件
    epub_path = f"{novel_name}.epub"
    # epub_path = os.path.join(os.environ['GITHUB_WORKSPACE'], epub_path)
    with zipfile.ZipFile(epub_path, "w") as epub:
        # 遍历临时目录中的所有文件
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                epub.write(file_path, arcname)

    # 删除临时目录
    import shutil
    shutil.rmtree(temp_dir)
    print(f"EPUB 文件已生成：{epub_path}")

if __name__ == "__main__":
    # novel_name = "八零年代"
    # base_url = "https://www.ipaoshubaxs.com/122248/"  # 替换为实际的小说目录页面
    novel_name = sys.argv[1]
    base_url = sys.argv[2]
    print(novel_name)
    print(base_url)

    author = "网络小说作家"

    # 获取章节链接和标题
    chapter_links = get_chapter_links(base_url)

    # 保存章节内容
    chapters = get_chapters(novel_name, chapter_links[-100:])
    create_epub(novel_name, chapters, author)
