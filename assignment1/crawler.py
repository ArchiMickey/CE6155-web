from bs4 import BeautifulSoup
import time
import requests
import json
from collections import deque
import re
from tqdm.auto import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


def deque_popleft(deque, num_workers):
    """爲方便threading，將deque.popleft()包裝成函數"""
    results = []
    for _ in range(num_workers):
        if deque:
            results.append(deque.popleft())
    return results

def clean_url(url):
    """把url末尾的/去掉，以免同一個網頁被爬兩次"""
    if url.endswith("/"):
        url = url[:-1]
    return url

class Crawler:
    def __init__(
        self,
        root_url,
        max_depth=1,
        benchmark=False,
        benchmark_max_crawled=500,
        num_workers=1,
    ):
        self.root_url = clean_url(root_url)
        self.max_depth = max_depth
        self.benchmark = benchmark
        self.benchmark_max_crawled = benchmark_max_crawled
        self.num_workers = num_workers
        self.visited = set()
        self.num_crawled = 0

        self.time_start = None

    def scrape(self, url, depth):
        try:
            resp = requests.get(url=url, timeout=5)
            if resp.status_code != 200:
                raise RuntimeError

            soup = BeautifulSoup(resp.text, "html.parser")

            # 獲取標題（title）
            title = soup.title
            title = title.string if title else ""

            # 獲取所有文字內容
            content = soup.get_text(separator="\n").strip()

            content = soup.get_text().strip()
            content = re.sub(r"\n+", "\n", content)
            
            # 獲取所有圖片
            imgs = []
            img_content = soup.find_all("img")
            for img in img_content:
                alt, src = img.get("alt"), img.get("src")
                if not alt:
                    continue
                if src:
                    if "http" not in src:
                        if src[0] != "/":
                            src = f"{root_url}/{src}"
                        else:
                            src = root_url + src
                    imgs.append((alt, src))
            

            # 獲取所有links
            links = []
            all_links = soup.find_all(href=True)
            for link in all_links:
                href = link.get("href")
                if href:
                    if "http" not in href:
                        if href[0] != "/":
                            href = f"{self.root_url}/{href}"
                        else:
                            href = self.root_url + href
                    text = link.get_text().strip()
                    if text == "":
                        text = link.get("title", "").strip()
                    if text == "":
                        continue

                    links.append((text, clean_url(href)))
            time.sleep(0.5)
            return url, depth, title, content, links, imgs
        except:
            print("Invalid url:", url)
            return url, depth, "", {}, [], []

    def crawl(self):
        self.time_start = time.time()
        results = []
        t_100 = "N/A"
        t_500 = "N/A"

        queue = deque([(self.root_url, 0)])
        with tqdm() as pbar:
            pbar.set_postfix({"num_crawled": 0, "t_100": t_100, "t_500": t_500})
            with ThreadPoolExecutor(max_workers=self.num_workers) as ex:
                end_flag = False
                while queue:
                    processing_url = deque_popleft(queue, self.num_workers)
                    future = [
                        ex.submit(self.scrape, url, depth)
                        for url, depth in processing_url
                    ]
                    for f in as_completed(future):
                        url, depth, title, content, links, imgs = f.result()

                        if depth > self.max_depth:
                            end_flag = True
                            print(f"Reached max depth {self.max_depth}")
                            continue

                        if url in self.visited:
                            continue
                        
                        if title and (content or links):
                            print(f"Scraped {url} at depth {depth}")
                            for text, link in links:
                                if link not in self.visited:
                                    queue.append((link, depth + 1))
                            self.visited.add(url)
                            results.append(
                                {
                                    "url": url,
                                    "title": title,
                                    "depth": depth,
                                    "content": content,
                                    "links": links,
                                    "imgs": imgs
                                }
                            )
                            self.num_crawled += 1
                            pbar.set_postfix(
                                {
                                    "num_crawled": self.num_crawled,
                                    "t_100": t_100,
                                    "t_500": t_500,
                                }
                            )
                        pbar.update(1)
                        if self.num_crawled == 100:
                            t_100 = time.time() - self.time_start
                            print(f"100 URLs crawled in {t_100:.2f} seconds")

                        elif self.num_crawled == 500:
                            t_500 = time.time() - self.time_start
                            print(f"500 URLs crawled in {t_500:.2f} seconds")

                    if end_flag or (
                        self.benchmark
                        and self.num_crawled >= self.benchmark_max_crawled
                    ):
                        break
        print(
            f"Total {self.num_crawled} URLs crawled in {time.time() - self.time_start:.2f} seconds"
        )
        return results

def run_benchmark():
    root_url = "https://www.csie.ncu.edu.tw"
    for num_worker in [4, 16]:
        crawler = Crawler(root_url, max_depth=2, num_workers=num_worker, benchmark=True)
        crawl_results = crawler.crawl()

if __name__ == "__main__":
    filename = "result.json"
    root_url = "https://www.csie.ncu.edu.tw"
    benchmark = False
    if benchmark:
         run_benchmark()
    else:
        crawler = Crawler(root_url, max_depth=2, num_workers=16)
        crawl_results = crawler.crawl()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(crawl_results, f, ensure_ascii=False, indent=4)
            print(f"{len(crawl_results)} of data were successfully saved")
