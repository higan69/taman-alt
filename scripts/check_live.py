#!/usr/bin/env python3
"""FMたまんの YouTube ライブ配信状態を live.json に書き出す。

GitHub Actions から5分ごとに実行される。判定方法:
  1. チャンネルの新着RSSから最新動画を取得
  2. その動画ページに配信中の目印 ("isLive":true) があるか確認
"""
import json
import os
import re
import sys
import urllib.request

CHANNEL_ID = 'UCxsijZ-IubrgLiaY4le_KaA'
RSS_URL = f'https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
OUT = os.path.join(os.path.dirname(__file__), '..', 'live.json')


def fetch(url, tries=3):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja'})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def main():
    result = {'live': False}
    try:
        rss = fetch(RSS_URL)
        m = re.search(r'<entry>(.*?)</entry>', rss, re.S)
        if m:
            entry = m.group(1)
            vid = re.search(r'<yt:videoId>([\w-]{11})</yt:videoId>', entry).group(1)
            title_m = re.search(r'<title>([^<]*)</title>', entry)
            title = title_m.group(1) if title_m else ''
            watch = fetch(f'https://www.youtube.com/watch?v={vid}')
            if '"isLive":true' in watch:
                result = {'live': True, 'videoId': vid, 'title': title}
    except Exception as e:  # noqa: BLE001
        print(f'check failed: {e}', file=sys.stderr)
        # 取得に失敗したときは既存の live.json を壊さない（前回の状態を維持）
        return
    old = None
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT))
        except Exception:  # noqa: BLE001
            old = None
    if old != result:
        with open(OUT, 'w') as f:
            json.dump(result, f, ensure_ascii=False)
        print(f'live.json updated: {result}')
    else:
        print(f'no change: {result}')


if __name__ == '__main__':
    main()
