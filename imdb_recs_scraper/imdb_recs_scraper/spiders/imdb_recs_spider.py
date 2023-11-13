import scrapy


class ImdbRecsSpider(scrapy.Spider):
    name = "imdb_recs_spider"

    def start_requests(self):
        urls = [
            "https://www.imdb.com/chart/top/?ref_=nv_mv_250"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_top_movies)

    def parse_top_movies(self, response):
        for top_movie_page in response.xpath("//a[@class='ipc-title-link-wrapper']/@href").getall():
            # Only follow if it is a movie page (starts with /title)
            if top_movie_page.startswith("/title"):
                yield response.follow(top_movie_page, self.parse_movie_recs)

    def parse_movie_recs(self, response):
        title = response.xpath("//span[@class='sc-7f1a92f5-1 benbRT']/text()").get()
        recs = response.xpath("//span[@data-testid='title']/text()").getall()
        yield {
            "title": title,
            "recs": recs
        }
        self.log(f"Saved recommendations for {title}")