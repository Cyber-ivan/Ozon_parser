import scrapy
from selenium import webdriver
from selenium_stealth import stealth
import time
import pandas as pd

class OzonSpiderSpider(scrapy.Spider):
    name = "ozon_spider"
    allowed_domains = ["ozon.ru"]
    start_urls = ["https://ozon.ru"]

    def parse(self, response):
        pass


def get_html(url: str, deep: int = 500):
    driver = init_webdriver()
    driver.get(url)
    scrolldown(driver, deep)
    html = driver.page_source
    driver.close()
    return html


def scrolldown(driver, deep):
    for _ in range(deep):
        driver.execute_script('window.scrollBy(0, 500)')
        time.sleep(0.1)


def init_webdriver():
    driver = webdriver.Chrome()
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    driver.maximize_window()
    return driver


def parse_searh_page(html):
    selector = scrapy.Selector(text=html)
    items = selector.css('div#paginatorContent div[data-index]')
    smarphones = []
    for item in items:
        title = item.css('span.tsBody500Medium::text').get()
        if not "Смартфон" in title:
            continue
        link = item.css('a.tile-clickable-element::attr(href)').get()
        smarphones.append((title, link))

    return smarphones


def parse_smartphone_page(html, title):
    selector = scrapy.Selector(text=html)

    if title.split()[0] == "Apple":
        dt_element = selector.xpath('//dt[span[text()="Версия iOS"]]')
    else:
        dt_element = selector.xpath('//dt[span[text()="Версия Android"]]')

    dl_element = dt_element.xpath('./ancestor::dl[1]')
    dd_element = dl_element.xpath('./dd[1]')
    os_version = dd_element.xpath('.//text()').get()
    if os_version is None:
        os_version = dd_element.xpath('string(.)').get()
    if os_version is None:
        try:
            dt_element = selector.xpath('//dt[span[text()="Операционная система"]]')
            dl_element = dt_element.xpath('./ancestor::dl[1]')
            dd_element = dl_element.xpath('./dd[1]')
            os_version = dd_element.xpath('.//text()').get()
        except Exception as e:
            print(e)


    return os_version

def save_to_file(os_versions, filename):
    df = pd.DataFrame(list(os_versions.items()), columns=['OS', 'Count'])
    total = df['Count'].sum()
    df['Percentage'] = (df['Count'] / total * 100).round(2)
    df.to_csv(filename, sep='\t', index=False)



def main():
    searh_page = get_html("https://www.ozon.ru/category/telefony-i-smart-chasy-15501/?sorting=rating", 700)
    smartphones = parse_searh_page(searh_page)
    # smartphones = smartphones[:100]
    os_versions = {}
    for smartphone in smartphones:
        smartphone_page = get_html("https://www.ozon.ru" + smartphone[1], 10)
        os = parse_smartphone_page(smartphone_page, smartphone[0])
        if os not in os_versions:
            os_versions[os] = 1
        else:
            os_versions[os] += 1
    save_to_file(os_versions, "top_100_os.txt")



if __name__ == "__main__":
    main()
