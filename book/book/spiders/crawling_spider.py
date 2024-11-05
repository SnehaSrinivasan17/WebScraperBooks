from scrapy.spiders import CrawlSpider, Rule #useful when scraping multiple pages
from scrapy.linkextractors import LinkExtractor
import re
import json

class CrawlingSpider(CrawlSpider):
    name = "book" #id of the spider
    allowed_domains = ["toscrape.com"]
    start_urls = ['https://books.toscrape.com/']

    #Rules are independent of each other
    rules = (
        Rule(LinkExtractor(allow = "catalogue/category/"), callback = "parse_links"), #will extract all the URLs which are in this format
        Rule(LinkExtractor(restrict_xpaths='//li[@class="next"]/a'), follow=True),
        Rule(LinkExtractor(allow = "catalogue/", deny="category"), callback = "parse_item", follow=False),
        # Rule(LinkExtractor(allow=r'catalogue/page-\d+\.html'), callback="parse_item", follow=True),
    )

    def save_to_json(self, item, filename):
        # Try to load existing data
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = []

        # Check if item already exists in data
        if item not in data:
            data.append(item)  # Add item if it's unique

            # Save updated data to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    def parse_links(self, response):
        item_data = {
            'title': response.xpath('//title/text()').get().strip().split(" | ")[0],
            'url': response.url,
        }
        self.save_to_json(item_data, 'parse_links.json')
        # yield item_data 

    def parse_item(self, response):
        #yield -> to generate the item

        #Product Description
        data_list = response.xpath('//p[1]/text()').getall()
        # self.log(type(data_list))
        # self.log(data_list[1])
        # self.log(len(data_list))
    
        #Table Data
        table_data = {}
        table = response.xpath('//*[@class="table table-striped"]')
        rows = table.xpath('//tr')

        for row in rows:
            heading = row.xpath('th//text()')[0].extract()
            data = row.xpath('td//text()')[0].extract()
            # self.log(heading)
            # self.log(data)
            if heading != 'Availability':
                table_data[heading.strip()] = data.strip()

        #Hyperlink
        ul = response.xpath('//*[@class="breadcrumb"]')
        li = ul.xpath('//li/a/text()').getall()
        # self.log(ul)
        # self.log(li[2])

        #Price
        price = response.css(".price_color::text").get().strip()
        # self.log(price)
        # price = price.encode('utf-8')
        # price = price.decode('unicode_escape')
        # price = price[1:]

        #Stars
        stars = response.css('.star-rating').xpath("@class").re(r"(?<=star-rating\s)\w+")[0]
        # classes = response.css('.star-rating').xpath("@class").get()
        # stars = None
        # if classes:
        #     match = re.search(r"(?<=star-rating\s)\w+", classes)
        #     stars = match.group(0) if match else "No rating"
        
        #classes = response.css('.star-rating').xpath("@class").extract()
        # for cls in classes:
        #     stars = re.search(r"(?<=rating\s).*", cls)
            # if stars:
            #     self.log("Class = {}".format(stars.group(0)))
            #     self.log(stars.group(0))

        #Image
        image_urls = [response.urljoin(src) for src in response.css('img').xpath('@src').getall()]
        # title = response.css('img::attr(alt)').get().strip()


        item = {
           "title": response.css(".product_main h1::text").get().strip(),
           "category": li[2].strip(),
           "price": price,
           "stars":stars,
           "availability": re.search(r'\d+', response.css(".availability::text")[1].get().strip()).group(),
           "description": data_list[1].strip(),
           "table": table_data,
           "image_urls": image_urls
        } 

        self.save_to_json(item, 'parse_item.json')
        yield item

