import datetime
import threading
import selenium

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

def split_list(arr, parts):
    k, m = divmod(len(arr), parts)
    return (arr[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(parts))


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


class Longinus:
    def __init__(self, name: str, threads: int = 4, wait_for_page_load_ms:int = 500):
        self.name = name
        self.number_of_threads = threads
        self.threads = []
        self.crawled_links = []
        self.total_urls_crawled = 0
        self.total_urls = 0
        self.urls = ["https://hugosouza.com"]
        self.wait = wait_for_page_load_ms

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
              colored(self.number_of_threads, "green"))
        print(colored("=" * 20, "green"))

    def crawl(self, thread_id, depth: int, keywords: list, urls: list, browser, is_parent:bool=True):
        self.total_urls += len(urls)
        for url in urls:
            self.log(colored("({}/{})".format(self.total_urls_crawled, self.total_urls), "grey", "on_white") +
                     " Crawling over {} - Depth: {}".format(url, depth), thread=thread_id)

            self.crawled_links.append(url)
            self.total_urls_crawled += 1

            start = time()
            try:
                browser.get(url)
                sleep(self.wait/1000)
            except selenium.common.exceptions.WebDriverException:
                self.log(colored("ERROR: Couldn't access url {}".format(url), "red"), thread=thread_id)
            else:
                self.log(colored("{} responded 200 in {:.2f} seconds".format(url, time() - start)), "green", thread=thread_id)

            html = BeautifulSoup(browser.page_source, features="lxml")

            links = html.find_all('a')

            # SCRAPE DATA HERE

            if depth > 0:
                page_links = []
                for link in links:
                    link = urljoin(url, link["href"])
                    if not (link in urls) and not (link in self.crawled_links):
                        page_links.append(link)
                
                if len(page_links) != 0:
                    self.log(colored("{} new links found at {}".format(len(page_links), url), "blue"), thread=thread_id)

                self.crawl(thread_id, depth - 1, keywords, page_links, browser, False)

        if is_parent:
            self.log(colored("Thread {} finished".format(thread_id), "red", "on_white"))

    def get_n_inside_links(self, url, browser, n):
        browser.get(url)
        sleep(self.wait/1000)

        try:
            browser.get(url)
            sleep(self.wait / 1000)
        except selenium.common.exceptions.WebDriverException:
            pass

        html = BeautifulSoup(browser.page_source, features="lxml")

        links = html.find_all('a')

        # SCRAPE DATA HERE

        page_links = []
        for link in links:
            link = urljoin(url, link["href"])
            page_links.append(link)

        if len(page_links) < n:
            new_links = self.get_n_inside_links(page_links[0], browser, n - len(page_links))
            page_links += new_links

        return page_links

    def start(self, depth: int = 0, search_for=None):
        self.log(colored("Starting crawling at depth {}".format(depth), "blue", "on_white"))
        if search_for is None:
            search_for = []

        if len(self.urls) < self.number_of_threads:
            temp_browser = obtain_browser()
            self.urls += self.get_n_inside_links(self.urls[0], temp_browser, self.number_of_threads)

        divided_urls = list(split_list(self.urls, self.number_of_threads))

        for thread_no in range(self.number_of_threads):
            self.log("Thread {} starting".format(thread_no))

            t = threading.Thread(target=self.crawl, args=(thread_no + 1, depth, search_for, divided_urls[thread_no],
                                                          obtain_browser()))
            t.start()
            self.threads.append(t)

        for thread in self.threads:
            thread.join()

        self.log(colored("Finished crawling", "blue", "on_white"))


longinus = Longinus("saint-longinus", 4)
longinus.start(3)
