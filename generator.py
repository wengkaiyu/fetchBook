import zipfile
import os

class EpubGenerator:
    def __init__(self, book_title, book_author):
        self.book_title = book_title
        self.book_author = book_author
        self.files = []

    def create_epub(self, output_filename):
        epub = zipfile.ZipFile(output_filename, 'w')
        # 添加mimetype文件
        epub.writestr('mimetype', 'application/epub+zip')
        # 添加容器文件 META-INF/container.xml
        self.create_container(epub)
        # 添加内容文件 OEBPS/content.opf
        self.create_content_opf(epub)
        # 添加HTML内容文件
        for file in self.files:
            epub.write(file, os.path.join('OEBPS', os.path.basename(file)))
        epub.close()

    def create_container(self, epub):
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
            <rootfiles>
                <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
            </rootfiles>
        </container>'''
        epub.writestr('META-INF/container.xml', container_xml)

    def create_content_opf(self, epub):
        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
        <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
            <metadata>
                <title>{self.book_title}</title>
                <creator>{self.book_author}</creator>
            </metadata>
            <manifest>
                <item id="toc" href="toc.xhtml" media-type="application/xhtml+xml"/>
                <!-- 添加其他文件 -->
            </manifest>
            <spine>
                <itemref idref="toc"/>
                <!-- 添加其他章节 -->
            </spine>
        </package>'''
        epub.writestr('OEBPS/content.opf', content_opf)
