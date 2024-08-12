# Speed of crawling.py
Since I use tqdm bar, some of the time is spent on updating the bar. The performance can be further improved by disabling the bar. \
$t_{n}$ : time(in seconds) used for crawling $n$ pages.
| Settings   | $t_{100}$ | $t_{500}$ |
| ---------- | --------- | --------- |
| original   | 64.5      | 2394.28   |
| 4 threads  | 20        | 379.96    |
| 8 threads  | 14.6      | 342.01    |
| 16 threads | 8.15      | 55.4      |
2196