import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re
import PyPDF2
import io


class ChineseSpider(CrawlSpider):
    name = "chinese"
    allowed_domains = ["ezworktaiwan.wda.gov.tw", "law.moj.gov.tw"]
    start_urls = ["https://ezworktaiwan.wda.gov.tw"]
    rules = (
        Rule(LinkExtractor(allow_domains=allowed_domains, deny=["ezworktaiwan.wda.gov.tw/en"], deny_extensions=['pdf']), callback="parse", follow=True),
        Rule(LinkExtractor(allow=['pdf']), callback="parse_pdf", follow=True),
    )

    def parse(self, response):
        url = response.url
        title = response.xpath("//title/text()").get().strip()
        # Extract all text from the response
        text = ''.join(response.xpath("//text()").getall()).strip()
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        # Extract all links from the response
        # links = response.xpath("//a/@href").getall()
        # Filter links that are not http links
        # filtered_links = [link for link in links if link.startswith("http")]
        
        # You can also yield the extracted data to further process it in other functions
        yield {
            "url": url,
            "title": title,
            "text": text,
            # "filtered_links": filtered_links
        }
    
    def parse_pdf(self, response):
        # Read the PDF file from the response body
        pdf_file = io.BytesIO(response.body)

        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Extract the title from the response
        title = pdf_reader.metadata.title
        
        # Extract text from each page of the PDF
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()

        # Clean up the extracted text
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)

        # You can also yield the extracted data to further process it in other functions
        yield {
            "url": response.url,
            "title": title,
            "text": text,
        }