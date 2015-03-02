# -*- coding: utf-8 -*-
import threading
import re

from bs4 import BeautifulSoup
import requests

from global_variable import HAS_QT, HEADERS

if HAS_QT:
    from global_variable import SENDER

class Novel():
    """
    get novel information for creating epub file

    Attributes:
        volume_name: A string represent the volume name
        volume_number: A string represent the volume number
        volume_author: A string represent the author
        volume_illustrator: A string represent the illustrator
        volume_introduction: A string represent the introduction
        volume_cover_url: A string represent the cover_url
        chapter_links: A string represent the chapter links
        output_dir: A stirng represent the epub save path
        cover_path: A string represent the cover path
        book_name: A string represent the book name
        chapter: A list represent the chapter
        base_path: A string represent the epub temp path

    """

    def __init__(self, url, single_thread):
        self.url = url
        self.single_thread = single_thread

        self.chapters = []
        self.volume_name = ''
        self.volume_number = ''
        self.author = ''
        self.illustrator = ''
        self.introduction = ''
        self.cover_url = ''
        self.chapters_links = []
        self.base_path = ''

    @staticmethod
    def parse_page(url):
        """
        parse page with BeautifulSoup

        Args:
            url: A string represent the url to be parsed

        Return:
            A BeatifulSoup element
        """
        r = requests.get(url, headers=HEADERS)
        r.encoding = 'utf-8'
        return BeautifulSoup(r.text)

    @staticmethod
    def find_chapter_links(soup):
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

    def find_volume_name_number(self, soup):
        name_and_number = soup.select("h1.ft-24 strong")[0].text.replace("\t", "").strip().split("\n")
        self.volume_name = name_and_number[0]
        self.volume_number = name_and_number[1]
        self.print_info('Volume_name:' + self.volume_name + ',Volume_number:' + self.volume_number)

    @property
    def book_name(self):
        return self.volume_name + ' ' + self.volume_number

    def find_author_illustrator(self, soup):
        temp_author_name = soup.select('table.lk-book-detail td')

        self.author = temp_author_name[3].text
        self.illustrator = temp_author_name[5].text
        self.print_info('Author:' + self.author + '\nillustrator:' + self.illustrator)

    def find_introduction(self, soup):
        temp_introduction = soup.select(
            'html body div.content div.container div.row-fluid div.span9 div.well div.row-fluid div.span10 p')
        self.introduction = temp_introduction[1]

    def find_cover_url(self, soup):
        temp_cover_url = soup.select(
            'div.container div.row-fluid div.span9 div.well div.row-fluid div.span2 div.lk-book-cover a')
        self.cover_url = 'http://lknovel.lightnovel.cn' + temp_cover_url[0].find("img")["src"]

    def extract_epub_info(self):
        """
        extract volume's basic info

        Args:
            soup: A parsed page

        Return:
            A dict contains the volume's info
        """
        soup = self.parse_page(self.url)

        self.find_volume_name_number(soup)
        self.find_author_illustrator(soup)
        self.find_introduction(soup)
        self.find_cover_url(soup)
        self.chapters_links = self.find_chapter_links(soup)

    @staticmethod
    def get_new_chapter_name(soup):
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

    @staticmethod
    def print_info(info):
        try:
            print(info)
            if HAS_QT:
                SENDER.sigChangeStatus.emit(info)
        except UnicodeDecodeError as e:
            print('Ignored:', e)

    @staticmethod
    def get_content(soup):
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

    def add_chapter(self, chapter):
        """
        add chapter
        chapter structure：a tuple (chapter number,chapter name,content)
        """
        self.chapters.append(chapter)

    def extract_chapter(self, url, number):
        """
        add each chapter's content to the Epub instance

        Args:
            url: A string represent the chapter url to be added
            epub: A Epub instance
            number: A int represent the chapter's number
        """
        try:
            soup = self.parse_page(url)

            new_chapter_name = self.get_new_chapter_name(soup)
            self.print_info(new_chapter_name)
            content = self.get_content(soup)
            self.add_chapter((number, new_chapter_name, content))

        except Exception as e:
            if HAS_QT:
                SENDER.sigWarningMessage.emit('错误', str(e) + '\nat:' + url)
                SENDER.sigButton.emit()
            print(self.url)
            raise e

    def get_chapter_content(self):
        """
        start extract every chapter in epub

        Args:
            epub: The Epub instance to be created
        """
        th = []

        if not self.single_thread:
            for i, link in enumerate(self.chapters_links):
                t = threading.Thread(target=self.extract_chapter, args=(link, i))
                t.start()
                th.append(t)
            for t in th:
                t.join()
        else:
            for i, link in enumerate(self.chapters_links):
                self.extract_chapter(link, i)


    def get_novel_information(self):
        """get novel information"""
        self.extract_epub_info()
        self.get_chapter_content()
        self.print_info('novel信息获取完成')

    def novel_information(self):
        return {'chapter': self.chapters, 'volume_name': self.volume_name, 'volume_number': self.volume_number,
                'book_name': self.book_name, 'author': self.author,
                'illustrator': self.illustrator, 'introduction': self.introduction, 'cover_url': self.cover_url}
