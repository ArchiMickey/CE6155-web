from bs4 import BeautifulSoup
import time
import requests
import json
from collections import deque
import re
from tqdm.auto import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from icecream import ic
from mpire import WorkerPool


def ncu_crawl(url):
    try:
        resp = requests.get(url=url, timeout=5)
        if resp.status_code != 200:
            print("Invalid url:", resp.url)
            return "", "", []

        soup = BeautifulSoup(resp.text, "html.parser")

        # 獲取標題（title）
        title = soup.title
        title = title.string if title else ""

        # 獲取所有文字內容
        content = soup.get_text().strip()
        content = re.sub(r"\n+", "\n", content)

        # 獲取所有links
        links = []
        all_links = soup.find_all(href=True)
        for link in all_links:
            href = link.get("href")
            if href:
                if "http" not in href:
                    if href[0] != "/":
                        href = f"{root_url}/{href}"
                    else:
                        href = root_url + href
                text = link.get_text().strip()
                if text == "":
                    text = link.get("title", "").strip()

                links.append((text, href))
        time.sleep(0.5)
        return title, content, links
    except:
        return "", "", []


def bfs_crawl(root_url, max_depth, benchmark=False, benchmark_max_crawled=500):
    visited = set()
    queue = deque([(root_url, 0)])
    results = []
    time_start = time.time()
    num_crawled = 0
    t_100 = "N/A"
    t_500 = "N/A"

    with tqdm() as pbar:
        pbar.set_postfix({"num_crawled": 0, "t_100": t_100, "t_500": t_500})
        while queue:
            pbar.set_postfix(
                {"num_crawled": num_crawled, "t_100": t_100, "t_500": t_500}
            )
            current_url, depth = queue.popleft()

            # 停止條件：達到指定的最大深度
            if (depth > max_depth) or (
                benchmark and num_crawled >= benchmark_max_crawled
            ):
                break

            # 如果該 URL 已經訪問過，跳過
            if current_url in visited:
                continue

            # 獲取該 URL 的所有超連結
            title, content, links = ncu_crawl(current_url)

            if title and content and links:
                print("Depth:", depth, "URL:", current_url)

                # 將所有未訪問過的超連結加入隊列，並更新深度
                for text, link in links:
                    if link not in visited:
                        queue.append((link, depth + 1))

                # 標記當前 URL 為已訪問
                visited.add(current_url)
                results.append(
                    {
                        "url": current_url,
                        "title": title,
                        "depth": depth,
                        "content": content,
                        "links": links,
                    }
                )
                num_crawled += 1

            if num_crawled == 100:
                t_100 = time.time() - time_start
                print(f"100 URLs crawled in {t_100:.2f} seconds")

            elif num_crawled == 500:
                time_500 = time.time() - time_start
                print(f"500 URLs crawled in {time_500:.2f} seconds")

            pbar.update(1)
    print(f"Total {num_crawled} URLs crawled in {time.time() - time_start:.2f} seconds")
    return results


def deque_popleft(deque, num_workers):
    results = []
    for _ in range(num_workers):
        if deque:
            results.append(deque.popleft())
    return results


def fast_bfs_crawl(
    root_url, max_depth, benchmark=False, benchmark_max_crawled=500, num_workers=4
):
    visited = set([root_url])
    queue = deque([(root_url, 0)])
    results = []
    time_start = time.time()
    num_crawled = 0
    t_100 = "N/A"
    t_500 = "N/A"

    def depthaware_crawl(url, depth):
        return {"url": url, "depth": depth, "out": ncu_crawl(url)}

    with tqdm() as pbar:
        pbar.set_postfix({"num_crawled": 0, "t_100": t_100, "t_500": t_500})
        with ThreadPoolExecutor(max_workers=num_workers) as ex:
            while queue:
                processing_url = deque_popleft(queue, num_workers)
                future = [
                    ex.submit(depthaware_crawl, url, depth)
                    for url, depth in processing_url
                ]
                thread_results = [f.result() for f in as_completed(future)]
                for r in thread_results:
                    current_url, depth = r["url"], r["depth"]
                    title, content, links = r["out"]
                    if title and content and links:
                        num_crawled += 1

                        print("Depth:", depth, "URL:", current_url)

                        for text, link in links:
                            if link not in visited:
                                if (depth + 1) <= max_depth:
                                    queue.append((link, depth + 1))

                        visited.add(current_url)
                        results.append(
                            {
                                "url": current_url,
                                "title": title,
                                "depth": depth,
                                "content": content,
                                "links": links,
                            }
                        )

                        if num_crawled == 100:
                            t_100 = time.time() - time_start
                            print(f"100 URLs crawled in {t_100:.2f} seconds")

                        if num_crawled == 500:
                            t_500 = time.time() - time_start
                            print(f"500 URLs crawled in {t_500:.2f} seconds")
                        
                        pbar.set_postfix(
                            {"num_crawled": num_crawled, "t_100": t_100, "t_500": t_500}
                        )
                        
                        if benchmark and num_crawled >= benchmark_max_crawled:
                            return results
                    pbar.update(1)
    return results


if __name__ == "__main__":
    filename = "result.json"
    root_url = "https://www.csie.ncu.edu.tw"
    max_depth = 2
    benchmark = False
    benchmark_max_crawled = 500
    # crawl_results = fast_bfs_crawl(root_url, max_depth, benchmark=benchmark, benchmark_max_crawled=benchmark_max_crawled, num_workers=8)
    crawl_results = bfs_crawl(root_url, max_depth, benchmark=benchmark, benchmark_max_crawled=benchmark_max_crawled)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(crawl_results, f, ensure_ascii=False, indent=4)
        print(f"{len(crawl_results)} of data were successfully saved")
