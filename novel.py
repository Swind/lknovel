# -*- coding: utf-8 -*-
import re
import StringIO

from bs4 import BeautifulSoup
import requests

from global_variable import HAS_QT, HEADERS

from opencc import OpenCC
opencc = OpenCC()

class Novel():
    """
    parse novel information from lknovel

    Attributes:
        volume_name: A string represent the volume name
        volume_number: A string represent the volume number
        volume_author: A string represent the author
        volume_illustrator: A string represent the illustrator
        volume_introduction: A string represent the introduction
        volume_cover_url: A string represent the cover_url
        chapter_links: A string represent the chapter links
        cover_path: A string represent the cover path
        book_name: A string represent the book name
        chapter: A list represent the chapter
        base_path: A string represent the temp path

    """

    def __init__(self, url, convert_to_tw=True):
        self.url = url
        self.convert_to_tw = convert_to_tw

        self.chapters = []
        self.volume_name = ''
        self.volume_number = ''
        self.author = ''
        self.illustrator = ''
        self.introduction = ''
        self.cover_url = ''
        self.chapters_links = []
        self.base_path = ''

    @property
    def book_name(self):
        return self.volume_name + u' ' + self.volume_number

    def parse(self):
        """get novel information"""
        self.__extract_novel_info()
        self.__get_chapter_content()

    def save(self, folder_path):
        """Save novel information and chapters content as markdown"""
        file_name = self.book_name() + u".md"         

        if self.convert_to_tw:
            file_name = opencc.convert(file_name)

        file_path = os.path.join(folder_path, file_name)
       
        md_buf = StringIO.StringIO()

        # Book Name
        md_buf.write("% {}\n".format(self.book_name))
        # Author Name
        md_buf.write("% {}\n".format(self.author))
        # Introduction
        md_buf.write("{}\n".format(self.introduction))

        for chapter in sorted(self.chapters, key=lambda x: x[0]):
            # Chapter Name
            md_buf.write("# {}\n".format(chapter[1]))

            for line in chapter[2]:
                if line.startswith('/illustration/'):
                    content.append("![illustration](images/{})\n".format(line))
                else:
                    content.append("{}\n".format(line))

        with open(file_path, "w") as md_file:
            if self.convert_to_tw:
                md_file.write(opencc.convert(md_buf.getvalue()))
            else:
                md_file.write(md_buf.getvalue())

    def __parse_page(self, url):
        """
        parse page with BeautifulSoup

        Args:
            url: A string represent the url to be parsed

        Return:
            A BeatifulSoup element
        """
        r = requests.get(url, headers=HEADERS)
        r.encoding = 'utf-8'
        import ipdb;ipdb.set_trace()
        return BeautifulSoup(r.text)

    # ===================================================================================================
    #
    #   Parse novel information
    #
    # ===================================================================================================
    def __extract_novel_info(self):
        """
        extract volume's basic info

        Args:
            soup: A parsed page

        Return:
            A dict contains the volume's info
        """
        soup = self.__parse_page(self.url)

        self.__find_volume_name_number(soup)
        self.__find_author_illustrator(soup)
        self.__find_introduction(soup)
        self.__find_cover_url(soup)
        self.chapters_links = self.__find_chapter_links(soup)

    def __find_volume_name_number(self, soup):
        name_and_number = soup.select("h1.ft-24 strong")[0].text.replace("\t", u"").strip().split("\n")
        self.volume_name = name_and_number[0].strip()
        self.volume_number = name_and_number[1].strip()

    def __find_author_illustrator(self, soup):
        temp_author_name = soup.select('table.lk-book-detail td')

        self.author = temp_author_name[3].text
        self.illustrator = temp_author_name[5].text

    def __find_introduction(self, soup):
        temp_introduction = soup.select(
            'html body div.content div.container div.row-fluid div.span9 div.well div.row-fluid div.span10 p')
        self.introduction = temp_introduction[1]

    def __find_cover_url(self, soup):
        temp_cover_url = soup.select(
            'div.container div.row-fluid div.span9 div.well div.row-fluid div.span2 div.lk-book-cover a')
        self.cover_url = 'http://lknovel.lightnovel.cn' + temp_cover_url[0].find("img")["src"]

    def __find_chapter_links(self, soup):
        """
        extract chapter links from page

        Args:
            soup: A parsed page

        Returns:
            a list contains the book's chapter links
        """
        temp_chapter_links = soup.select(
            'body div.content div.container div.row-fluid div.span9 div.well div.row-fluid ul.lk-chapter-list li')
        chapter_links = []
        for i in temp_chapter_links:
            chapter_links.append(i.find("a")["href"])
        return chapter_links

    # ===================================================================================================
    #
    #   Parse all chapters content 
    #
    # ===================================================================================================
    def __get_chapter_content(self):
        """
        start extract every chapter
        """
        for i, link in enumerate(self.chapters_links):
            self.__extract_chapter(link, i)

    def __extract_chapter(self, url, number):
        """
        get each chapter's content

        Args:
            url: A string represent the chapter url to be added
            number: A int represent the chapter's number
        """
        soup = self.__parse_page(url)

        new_chapter_name = self.__get_new_chapter_name(soup)
        content = self.__get_content(soup)
        self.__add_chapter((number, new_chapter_name, content))

    def __get_new_chapter_name(self, soup):
        """
        get the formal chapter name

        Args:
            soup: A parsed page

        Returns:
            A string contain the chapter name
        """
        chapter_name = soup.select('h3.ft-20')[0].get_text()
        new_chapter_name = chapter_name[:chapter_name.index(u'章') + 1] + ' ' + chapter_name[chapter_name.index(u'章') + 1:]
        return new_chapter_name

    def __get_content(self, soup):
        """
        extract contents from each page

        Args:
            soup: parsed page

        Return:
            A list contain paragraphs of one chapter
        """
        content = []
        temp_chapter_content = soup.select('div.lk-view-line')
        for line in temp_chapter_content:
            if 'lk-view-img' not in str(line):
                content.append(line.get_text().strip())
            else:
                picture_url = line.find("img")["data-cover"]
                content.append(picture_url)
        return content

    def __add_chapter(self, chapter):
        """
        add chapter
        chapter structure：a tuple (chapter number,chapter name,content)
        """
        self.chapters.append(chapter)
