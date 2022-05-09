# SaintLonginus

**Version 1.1**

 A experiment with web scrapping

SaintLonginus is a web crawler that I developed while learning about web scrapping. It's functionality is to search for given words inside a set of pages.
While it looks for references to the searched words within the page, it also looks for links that lead to other pages, increasing its queue of pages to search in.

It's built on top of [Selenium](https://www.selenium.dev/) and [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

It's name comes from a popular tradition which says that the catholic saint [Longinus](https://en.wikipedia.org/wiki/Longinus) can help you to find anything you are looking for. 

This project is open-source, so feel free to contribute, report issues or make suggestions.

For any other cases, feel free to email me at [mail@hugosouza.com](mailto:mail@hugosouza.com)

## Doumentation

Here is how you can this crawler

### Longinus class

The program's main class.

#### Class Constructor:

##### Longinus(name: str, threads: int = 4, wait_for_page_load_ms: int = 500, when_find: callable = write_to_file, save_bot: bool = False)

This is the class constructor, it takes some arguments:

* *name (string)*: The name of that crawler instance

* *threads (int)*: How many threads it's going to use while searching

* *wait_for_page_load_ms (int)*:  How many milisseconds the crawler is going to wait for the page to load and run all of its scripts until return the source of that page *(this is important to make sure that pages built with React, Angular, Vue or even vanilla JavaScript can render everything it should before the crawler starts scrapping it)*

* *when_find (callable)*: A function that is going to be executed when there's a reference to a specific keyword on that page. The default function writes the url of that page in a text file called **results.txt**. It must take 3 arguments containing the **url of the page**, **keyword found at the page** and **the whole text of the page**:
  
  ```python
  def write_to_file(url, keyword, full_text):
      if "google.com" in url:
          return
      with open("results.txt", "a+") as file:
          file.write("{}: {} \n".format(url, keyword))
          file.write(full_text + "\n\n")
          file.close()
  ```

* *save_bot (bool)*: Sets if the bot is going to be periodically saved into a file for further loading. The frequency of the savings can be defined at setup.

#### Instance methods:

##### setup(depth: int = 3, strategy=SHALLOW_LINKS, bonus_when_match: int = 1, saving_frequency = NORMAL)

This method configures the process of searching that the bot is going to use. It takes the arguments:

* *Depth (int):* The amount of links beyond the root that are going to be scrapped
* *strategy (STRATEGY CONSTANT)*: The searching strategy that is going to be used (Read the strategy section) 
* *bonus_when_match (int)*: This bonus is a value that is added to the depth when the bot finds a reference to a keyword on a page. It's a way to "reward" the page for having a reference to a keyword because it's likely its links also lead to pages with references to a keyword.
* *saving_frequency (FREQUENCY CONSTANT)*: Defines the frequency the bot is going to the saved (Read the saving frequency section)

If you try to start the search without calling **setup** first, it will raise a **AssertionError**.

##### set_url(new_urls: list)

Changes the urls that the crawler is going to take as root when it starts searching. The root urls are the first ones to be scrapped, and starting from them, the scrapper is going to find the next urls to be visited.

When a Longinus object is instantiated, the urls' default value is *None*, in that case, the crawler is going to perform a Google search for each keyword and gather a list of urls from the results to be used as root.

##### set_callback(new_callback: callable):

Sets what function is going to be executed when there's a reference to a specific keyword on that page. The default function writes the url of that page in a text file called **results.txt**. It must take 4 arguments containing the **url of the page**, **keyword found at the page**, **the whole text of the page** and **the title of the HTML document**:

```python
def write_to_file(url, keyword, full_text, title):
    if "google.com" in url:
        return
    with open("results.txt", "a+") as file:
        file.write("{} ({}): {} \n".format(title, url, keyword))
        file.write(full_text + "\n\n")
        file.close()
```

##### set_filter(new_filter: callable)

Sets a new filtering function. A filtering function is used to determinate which pages are going to be crawled and which ones aren't based on their url.

The default function filters pages that contains *"webcache.googleusercontent.com"* on their url.

If you want to create a custom filtering function, follow the structure:

```python
def custom_filter(url: str):
    if condition_to_be_filtered(url):
        return True     # This page is going to be filtered (not crawled)
    return False        # This page is going to be crawled (not filtered)
```

##### start(keywords: list)

Starts the searching looking for the words described in the **keywords** list.

The search follow the processes configured in the **setup** method so it must be called after the **setup**.

**If the bot as loaded from a save-file, there's no need to speci**

#### Loading a bot

If you had previously saved a bot and you want to re-load it, you can do it with the:

##### load_bot_from_save(save_filename: str)

This function acts as a constructor, it reads the bot saved file and constructs another instance of the bot with the same specifications, history and searching queue.

The **save_filename** argument represents the name of the file generated when the previous bot was saved.

#### Strategies

There are several constants representing strategies that can be used to setup the crawler:

* *ONLY_ORIGIN_DOMAIN*: Doesn't follow links that lead to a different domain or subdomain

* *ONLY_SUBDOMAINS*: Follow only origin domain and subdomains

* *FOLLOW_ALL_LINKS:* Follows everything that comes up on the page

* *SHALLOW_LINKS:* Follows links that lead to other domains with depth 0

#### Saving frequency

There are several constants representing the frequency a bot will be saved:

* *ULTRA_FREQUENT*: Will save the bot after each single link searched. (NOT RECOMENDED, IT MIGHT CAUSE THE BOT TO BE EXTREMELLY SLOW)

* *VERY_FREQUENT*: Will save the bot after each 10 links searched.

* *FREQUENT*: Will save the bot after each 25 links searched.

* *NORMAL*: Will save the bot after each 50 links searched.

* *SOMETIMES*: Will save the bot after each 100 links searched.

* *RARELY*: Will save the bot after each 500 links searched.
