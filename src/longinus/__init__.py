#!/usr/bin/env python3
"""
Longinus web-crawler 1.1 © MIT licensed
https://pypi.org/project/longinus/
https://github.com/fatorius/Longinus
Hugo Souza 2022
"""

import datetime
import threading
import re
import pip
import sys
import json

from os import execl
from subprocess import check_call
from urllib.parse import urljoin
from urllib.parse import urlparse
from time import sleep, time


def install(package):
    """
    Automatically installs python pip package and restarts the program
    This script was taken from https://github.com/revoxhere/duino-coin/blob/master/PC_Miner.py
    """
    try:
        pip.main(["install", package])
    except AttributeError:
        check_call([sys.executable, '-m', 'pip', 'install', package])

    execl(sys.executable, sys.executable, *sys.argv)


try:
    import html2text
except ModuleNotFoundError:
    print("html2text is not installed. "
          + "Longinus will try to automatically install it "
          + "If it fails, please manually execute "
          + "python3 -m pip install html2text")
    install("html2text")

try:
    import selenium

    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
except ModuleNotFoundError:
    print("selenium is not installed. "
          + "Longinus will try to automatically install it "
          + "If it fails, please manually execute "
          + "python3 -m pip install selenium")
    install("selenium")

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    print("BeautifulSoup is not installed. "
          + "Longinus will try to automatically install it "
          + "If it fails, please manually execute "
          + "python3 -m pip install beautifulsoup4")
    install("beautifulsoup4")

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ModuleNotFoundError:
    print("webdriver_manager is not installed. "
          + "Longinus will try to automatically install it "
          + "If it fails, please manually execute "
          + "python3 -m pip install webdriver_manager")
    install("webdriver_manager")

try:
    from colorama import init

    init(autoreset=True)
except ModuleNotFoundError:
    print("Colorama is not installed. "
          + "Longinus will try to automatically install it "
          + "If it fails, please manually execute "
          + "python3 -m pip install colorama")
    install("colorama")

try:
    from termcolor import colored
except ModuleNotFoundError:
    print("termcolor is not installed. "
          + "Longinus will try to automatically install it "
          + "If it fails, please manually execute "
          + "python3 -m pip install termcolor")
    install("termcolor")

VERSION = "1.1"


def are_from_same_domain(url1, url2):
    return url1 in url2


def comp_dom(url1, url2):
    domain1 = urlparse(url1).hostname
    domain2 = urlparse(url2).hostname

    if domain1 != domain2:
        return False

    domain1 = domain1.split(".")
    domain2 = domain2.split(".")

    url1 = url1.replace("://", ".").split(".")
    url2 = url2.replace("://", ".").split(".")

    if url1[url1.index(domain1[0]) - 1] != url2[url2.index(domain2[0]) - 1]:
        return False

    return True


def obtain_browser():
    options = webdriver.ChromeOptions()

    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-in-process-stack-traces")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_argument("--output=/dev/null")

    driver = Service(ChromeDriverManager().install())
    driver.EnableVerboseLogging = False
    driver.SuppressInitialDiagnosticInformation = True
    driver.HideCommandPromptWindow = True

    browser = webdriver.Chrome(service=driver, options=options)

    return browser


def write_to_file(url, keyword, full_text, title):
    if "google.com" in url:
        return
    with open("results.txt", "a+") as file:
        file.write("{} ({}): {} \n".format(title, url, keyword))
        file.write(full_text + "\n\n")
        file.close()


# Strategies
ONLY_ORIGIN_DOMAIN = 0  # doesnt follow links that lead to a different domain
ONLY_SUBDOMAINS = 2  # follow only subdomains
FOLLOW_ALL_LINKS = 3  # follows everything that comes up on the page
SHALLOW_LINKS = 4  # follows links that lead to other domains with depth 0

# Saving frequency
ULTRA_FREQUENT = 1
VERY_FREQUENT = 10
FREQUENT = 25
NORMAL = 50
SOMETIMES = 100
RARELY = 200


def get_text(page):
    for tag in page(["script", "style"]):
        tag.decompose()
    return html2text.html2text(page.prettify())


def default_filter(url):
    # ignore google search results page
    if "webcache.googleusercontent.com" in url:
        return True
    return False


class Longinus:
    class QueuedURL:
        def __init__(self, url, depth):
            self.url = url
            self.depth = depth

    def __init__(self, name: str, threads: int = 4, wait_for_page_load_ms: int = 500,
                 when_find: callable = write_to_file, save_bot: bool = False):
        self.name = name
        self.number_of_threads = threads
        self.threads = []
        self.crawled_links = []
        self.total_urls_crawled = 0
        self.total_urls = 0
        self.urls = None
        self.queue = []
        self.wait = wait_for_page_load_ms
        self.depth = 0
        self.strategy = SHALLOW_LINKS
        self.bonus = 1
        self.total_references_found = 0
        self.callback = when_find
        self.filtering_function = default_filter
        self.issetup = False
        self.save_bot = save_bot
        self.saving_frequency = NORMAL
        self.currently_saving = False
        self.total_saves = 0

        self.startup_message()

    def set_callback(self, new_callback: callable):
        self.callback = new_callback

    def set_url(self, new_urls):
        self.urls = new_urls

    def set_filter(self, new_filter):
        self.log("Filtering function set to {}".format(new_filter.__name__), "green")
        self.filtering_function = new_filter

    def log(self, msg, color=None, on_color=None, thread: int = 0):
        t = datetime.datetime.now()

        thread_info = " "

        if thread != 0:
            thread_info = colored(" Thread {} |".format(thread), "cyan")

        print(colored("[{}] {} |{}".format(t.isoformat(), self.name, thread_info), "green") +
              colored(msg, color, on_color))

    def startup_message(self):
        print(colored("=" * 20, "green"))
        print(colored("Created Longinus bot", "green"))
        print(colored("=====BOT INFO=====", "green"))
        print(colored("BOT_NAME:", None, "on_green") + " " +
              colored(self.name, "green"))
        print(colored("NUMBER_OF_THREADS:", None, "on_green") + " " +
              colored(str(self.number_of_threads), "green"))
        print(colored("SAVING BOT:", None, "on_green") + " " +
              colored(str(self.save_bot), "green"))
        print(colored("=" * 20, "green"))

    def match_current_strategy(self, origin, link):
        if self.strategy == FOLLOW_ALL_LINKS or self.strategy == SHALLOW_LINKS:
            return True
        elif self.strategy == ONLY_SUBDOMAINS:
            return are_from_same_domain(origin, link)
        elif self.strategy == ONLY_ORIGIN_DOMAIN:
            return comp_dom(origin, link)

    def get_new_depth(self, origin, link, current_depth):
        if self.strategy == SHALLOW_LINKS and not are_from_same_domain(link, origin):
            return 0
        return current_depth - 1

    def hit_page(self, browser, url, thread_id=0):
        start = time()
        try:
            browser.get(url)
            sleep(self.wait / 1000)
        except selenium.common.exceptions.WebDriverException:
            self.log(colored("ERROR: Couldn't access url {}".format(url), "red"), thread=thread_id)
        else:
            self.log(colored("{} responded 200 in {:.2f} seconds".format(url, time() - start)), "green",
                     thread=thread_id)

        return browser.page_source

    def queue_new_links(self, html, depth, url, thread_id=0):
        links = html.find_all('a')
        page_links = 0
        for link in links:
            try:
                link = urljoin(url, link["href"])
            except KeyError:
                continue
            if (link not in self.crawled_links) and self.match_current_strategy(url, link):
                page_links += 1
                self.queue.append(self.QueuedURL(link, self.get_new_depth(url, link, depth)))
                self.total_urls += 1

        if page_links != 0:
            self.log(colored("{} new links found at {}".format(page_links, url), "blue"), thread=thread_id)

    def search(self, thread_id, keywords, page, url):
        total_cases = 0
        title = page.title.string
        page = page.body
        for word in keywords:
            cases = page.find_all(string=re.compile(word, re.IGNORECASE))
            if len(cases) > 0:
                self.log(colored("Found a match for {} in {}".format(word, url), "magenta", "on_grey", attrs=["bold"]),
                         thread=thread_id)
                total_cases += 1
                full_text = get_text(page)
                self.callback(url, word, full_text, title)
        return total_cases > 0

    def crawl(self, thread_id, keywords: list, browser):
        while len(self.queue) > 0:
            while self.currently_saving:
                sleep(5)

            current = self.queue.pop(0)
            url = current.url
            depth = current.depth

            self.total_urls_crawled += 1

            if url in self.crawled_links:
                self.log(colored("Skipping {}...".format(url), "red"), thread=thread_id)
                continue
            elif self.filtering_function(url):
                self.log(colored("{} filtered...".format(url), "red"), thread=thread_id)
                continue

            self.log(colored("({}/{})".format(self.total_urls_crawled, self.total_urls), "grey", "on_white") +
                     " Crawling over {} - Depth: {}".format(url, depth), thread=thread_id)

            self.crawled_links.append(url)

            page_source = self.hit_page(browser, url, thread_id)

            html = BeautifulSoup(page_source, features="lxml")

            self.log(colored("Searching for references in {}".format(url), "cyan", None, attrs=["bold"]),
                     thread=thread_id)

            found = self.search(thread_id, keywords, html, url)

            if found:
                depth += self.bonus
            else:
                self.log(colored("No references found in {}".format(url), "cyan", None, attrs=["bold"]),
                         thread=thread_id)

            if depth > 0:
                self.queue_new_links(html, depth, url, thread_id)

            self.log("Exiting {}".format(url), color="red", thread=thread_id)

            if self.save_bot:
                if self.total_urls_crawled % self.saving_frequency == 0:
                    self.currently_saving = True
                    self.log("Currently saving bot, pausing threads", "red", "on_yellow")
                    self.save_state()
                    self.currently_saving = False

        self.log(colored("Thread {} finished".format(thread_id), "red", "on_white"))
        browser.quit()

    def save_state(self):
        save_filename = "{}-{}".format(self.name, self.total_saves)
        with open(save_filename, "a+") as file:
            file.write('{' + '"name": "{}", "threads": {}, "wait_for_load": {}, "strategy": "{}", "bonus": {}, '
                       '"saving_frequency": {}, "depth": {}, "seen_urls": [\n"google.com"'.format(
                self.name, self.number_of_threads, self.wait, self.strategy, self.bonus, self.saving_frequency, self.depth
            ))
            for seen_url in self.crawled_links:
                file.write(',\n"{}"'.format(seen_url))
            file.write('], "queue":[{}')
            for item in self.queue:
                file.write(',\n{' + '"link": "{}", "depth": {}'.format(item.url, item.depth) + '}')
            file.write(']}')
            file.close()
        self.total_saves += 1
        self.log("Bot successfully saved to {}, resuming threads".format(save_filename), "red", "on_yellow")

    def get_n_inside_links(self, url, browser, n, depth):
        browser.get(url)
        sleep(self.wait / 1000)

        try:
            browser.get(url)
            sleep(self.wait / 1000)
        except selenium.common.exceptions.WebDriverException:
            pass

        html = BeautifulSoup(browser.page_source, features="lxml")

        links = html.find_all('a')

        page_links = []
        for link in links:
            try:
                link = urljoin(url, link["href"])
            except KeyError:
                continue

            page_links.append(self.QueuedURL(link, depth))

        if len(page_links) < n:
            new_links = self.get_n_inside_links(page_links[0], browser, n - len(page_links), depth - 1)
            page_links += new_links

        return page_links

    def setup(self, depth: int = 3, strategy=SHALLOW_LINKS, bonus_when_match: int = 1, saving_frequency=NORMAL):
        self.issetup = True
        if type(self.urls) == list:
            for url in self.urls:
                self.queue.append(self.QueuedURL(url, depth))

            if len(self.urls) < self.number_of_threads:
                temp_browser = obtain_browser()
                self.queue += self.get_n_inside_links(self.urls[0], temp_browser, self.number_of_threads, depth)

        self.depth = depth
        self.strategy = strategy
        self.bonus = bonus_when_match

        if self.save_bot:
            self.saving_frequency = saving_frequency

        self.log("Longinus has been successfully setup", "green")

    def not_setup_error_message(self):
        return "The Longinus bot {} has not been setup, please call Longinus.setup() before you start crawling \nIf " \
               "you have any doubts about this method please check the documentation: " \
               "https://github.com/fatorius/Longinus/blob/main/README.md \n".format(self.name)

    def start(self, search_for: list):
        if not self.issetup:
            raise AssertionError(self.not_setup_error_message())

        if self.urls is None:
            self.urls = []
            for words in search_for:
                self.urls.append("https://www.google.com/search?q=" + words)
            self.setup(self.depth, self.strategy, self.bonus, self.saving_frequency)

        self.log(colored("Starting crawling at depth {}".format(self.depth), "blue"))
        self.log(colored("Searching for {}".format(search_for), "blue"))

        self.total_urls = len(self.queue)

        start = time()

        for thread_no in range(self.number_of_threads):
            self.log("Thread {} starting".format(thread_no + 1))

            t = threading.Thread(target=self.crawl, args=(thread_no + 1, search_for,
                                                          obtain_browser()))
            t.start()
            self.threads.append(t)

        for thread in self.threads:
            thread.join()

        self.log(colored("Finished crawling in {:.2f} seconds".format(time() - start), "blue"))


def load_bot_from_save(save_filename: str):
    loaded_bot = None

    with open(save_filename, "r") as file:
        obj = json.loads(file.read())

        bot = Longinus(obj["name"], obj["threads"], obj["wait_for_load"], save_bot=True)

        bot.crawled_links = obj["seen_urls"]

        queue_obj = obj["queue"]
        saved_queue = []

        queue_obj.pop(0)

        for item in queue_obj:
            saved_queue.append(Longinus.QueuedURL(item["link"], item["depth"]))

        bot.queue = saved_queue

        bot.setup(obj["depth"], obj["strategy"], obj["bonus"], obj["saving_frequency"])

        loaded_bot = bot

        file.close()

    return loaded_bot
