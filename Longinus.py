import datetime
import threading
import selenium
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from colorama import init
from termcolor import colored
from urllib.parse import urljoin
from time import sleep, time

init()


# TODO handle uninstalled modules

def are_from_same_domain(url1, url2):
    return url1 in url2


def compDom(URL1, URL2):
    URL1Split = URL1.split(".")
    URL2Split = URL2.split(".")
    a = URL1Split[::-1]
    b = URL2Split[::-1]
    domain1 = a[1] + "." + a[0]
    domain2 = b[1] + "." + b[0]
    return domain1 == domain2


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


def write_to_file(url):
    with open("results.txt", "a+") as file:
        file.write(url + "\n")
        file.close()

# Strategies
ONLY_ORIGIN_DOMAIN = 0  # doesnt follow links that lead to a different domain
ONLY_SUBDOMAINS = 2  # follow only subdomains
FOLLOW_ALL_LINKS = 3  # follows everything tat comes up on the page
SHALLOW_LINKS = 4  # follows links that lead to other domains with depth 0


class Longinus:
    class QueuedURL:
        def __init__(self, url, depth):
            self.url = url
            self.depth = depth

    def __init__(self, name: str, threads: int = 4, wait_for_page_load_ms: int = 500, when_find: callable = write_to_file):
        self.name = name
        self.number_of_threads = threads
        self.threads = []
        self.crawled_links = []
        self.total_urls_crawled = 0
        self.total_urls = 0
        self.urls = ["https://hugosouza.com"]
        self.queue = []
        self.wait = wait_for_page_load_ms
        self.depth = 0
        self.strategy = SHALLOW_LINKS
        self.bonus = 1
        self.total_references_found = 0
        self.callback = when_find

        self.startup_message()

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
        print(colored("=" * 20, "green"))

    def match_current_strategy(self, origin, link):
        if self.strategy == FOLLOW_ALL_LINKS or self.strategy == SHALLOW_LINKS:
            return True
        elif self.strategy == ONLY_SUBDOMAINS:
            return are_from_same_domain(origin, link)
        elif self.strategy == ONLY_ORIGIN_DOMAIN:
            return compDom(origin, link)

    def get_new_depth(self, origin, link, current_depth):
        if self.strategy == SHALLOW_LINKS and not are_from_same_domain(link, origin):
            return 0
        return current_depth-1

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
            if (not link in self.crawled_links) and self.match_current_strategy(url, link):
                page_links += 1
                self.queue.append(self.QueuedURL(link, self.get_new_depth(url, link, depth)))
                self.total_urls += 1

        if page_links != 0:
            self.log(colored("{} new links found at {}".format(page_links, url), "blue"), thread=thread_id)

    def search(self, thread_id, keywords, page, url):
        total_cases = 0
        for word in keywords:
            cases = page.find_all(string=re.compile(word, re.IGNORECASE))
            if len(cases) > 0:
                self.log(colored("Found a match for {} in {}".format(word, url), "magenta", "on_grey", attrs=["bold"]), thread=thread_id)
                total_cases += 1
                self.callback(url)
        return total_cases > 0

    def crawl(self, thread_id, keywords: list, browser):
        while len(self.queue) > 0:
            current = self.queue.pop(0)
            url = current.url
            depth = current.depth

            self.total_urls_crawled += 1

            if url in self.crawled_links:
                self.log(colored("Skipping {}...".format(url), "red"), thread=thread_id)
                continue

            self.log(colored("({}/{})".format(self.total_urls_crawled, self.total_urls), "grey", "on_white") +
                     " Crawling over {} - Depth: {}".format(url, depth), thread=thread_id)

            self.crawled_links.append(url)

            page_source = self.hit_page(browser, url, thread_id)

            html = BeautifulSoup(page_source, features="lxml")

            self.log(colored("Searching for references in {}".format(url), "cyan", None, attrs=["bold"]), thread=thread_id)

            found = self.search(thread_id, keywords, html, url)

            if found:
                depth += self.bonus
            else:
                self.log(colored("No references found in {}".format(url), "cyan", None, attrs=["bold"]),
                         thread=thread_id)

            if depth > 0:
                self.queue_new_links(html, depth, url, thread_id)

            self.log("Exiting {}".format(url), color="red", thread=thread_id)

        self.log(colored("Thread {} finished".format(thread_id), "red", "on_white"))

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
            link = urljoin(url, link["href"])
            page_links.append(self.QueuedURL(link, depth))

        if len(page_links) < n:
            new_links = self.get_n_inside_links(page_links[0], browser, n - len(page_links))
            page_links += new_links

        return page_links

    def setup(self, depth: int = 3, strategy=SHALLOW_LINKS, bonus_when_match=1):
        for url in self.urls:
            self.queue.append(self.QueuedURL(url, depth))

        if len(self.urls) < self.number_of_threads:
            temp_browser = obtain_browser()
            self.queue += self.get_n_inside_links(self.urls[0], temp_browser, self.number_of_threads, depth)

        self.depth = depth
        self.strategy = strategy
        self.bonus = bonus_when_match

    def start(self, search_for=None):
        if search_for is None:
            search_for = []

        self.log(colored("Starting crawling at depth {}".format(self.depth), "blue"))
        self.log(colored("Searching for {}".format(search_for), "blue"))

        self.total_urls = len(self.queue)

        start = time()

        for thread_no in range(self.number_of_threads):
            self.log("Thread {} starting".format(thread_no))

            t = threading.Thread(target=self.crawl, args=(thread_no + 1, search_for,
                                                          obtain_browser()))
            t.start()
            self.threads.append(t)

        for thread in self.threads:
            thread.join()

        self.log(colored("Finished crawling in {:.2f} seconds".format(time() - start), "blue"))


longinus = Longinus("saint-longinus", 4)
longinus.setup(depth=3)
longinus.start(["eleCtron", "reaCt"])
