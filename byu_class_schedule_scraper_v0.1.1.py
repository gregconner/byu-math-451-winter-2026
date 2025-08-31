#!/usr/bin/env python3
import sys
import json
import re
from typing import Optional, Dict, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from html.parser import HTMLParser

BYU_CLASS_SEARCH_URL = "https://commtech.byu.edu/noauth/classSchedule/index.php"

class SimpleTableParser(HTMLParser):
    """
    Minimal HTML table parser tailored to the BYU class schedule listing table.
    Extracts rows from the first table that looks like the results grid.
    Falls back gracefully if the page contains no results.
    """
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_tr = False
        self.in_td = False
        self.current_row = []
        self.rows = []
        self.header_seen = False
        self.table_depth = 0
        self.current_cell = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.table_depth += 1
            if not self.in_table:
                self.in_table = True
        elif tag == 'tr' and self.in_table:
            self.in_tr = True
            self.current_row = []
        elif tag in ('td', 'th') and self.in_tr:
            self.in_td = True
            self.current_cell = ''

    def handle_endtag(self, tag):
        if tag == 'table' and self.in_table:
            self.table_depth -= 1
            if self.table_depth <= 0:
                self.in_table = False
        elif tag == 'tr' and self.in_tr:
            self.in_tr = False
            if self.current_row:
                if not self.header_seen:
                    self.header_seen = True
                else:
                    self.rows.append([cell.strip() for cell in self.current_row])
            self.current_row = []
        elif tag in ('td', 'th') and self.in_td:
            self.in_td = False
            self.current_row.append(self.current_cell.strip())

    def handle_data(self, data):
        if self.in_td:
            self.current_cell += data


def fetch_page(url: str, data: Optional[Dict[str, str]] = None, headers: Optional[Dict[str, str]] = None) -> str:
    req_headers: Dict[str, str] = {"User-Agent": "Mozilla/5.0 (compatible; schedule-bot/0.1)"}
    if headers:
        req_headers.update(headers)
    if data is None:
        req = Request(url, headers=req_headers)
    else:
        payload = urlencode(data).encode()
        req = Request(url, data=payload, headers=req_headers)
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8', errors='ignore')


def search_math_451_winter_2026(department_hint: str, instructor_hint: str) -> List[Dict[str, str]]:
    """
    Best-effort attempt to retrieve schedule results. The site appears to be form-driven;
    we first GET the page to see if Winter 2026 is available and if a default results table exists.
    If the page shows '0 courses found', we return empty.
    """
    html = fetch_page(BYU_CLASS_SEARCH_URL)
    if re.search(r"0\s*courses\s*found", html, re.I):
        return []

    parser = SimpleTableParser()
    parser.feed(html)

    extracted: List[Dict[str, str]] = []
    for row in parser.rows:
        # Expected columns per site snippet: Section | Type | Mode | Instructor | Credits | Term | Days | Start | End | Location | Available | Waitlist
        if len(row) >= 12:
            section, type_, mode, instructor, credits, term, days, start, end, location, available, waitlist = row[:12]
            if ('Winter 2026' in term) and ('451' in section or 'MATH 451' in section) and re.search(r"conner", instructor, re.I):
                extracted.append({
                    "section": section,
                    "type": type_,
                    "mode": mode,
                    "instructor": instructor,
                    "credits": credits,
                    "term": term,
                    "days": days,
                    "start": start,
                    "end": end,
                    "location": location,
                    "available": available,
                    "waitlist": waitlist,
                })
    return extracted


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape BYU class schedule for MATH 451 Winter 2026")
    parser.add_argument('--department', default='Mathematics')
    parser.add_argument('--course', default='MATH 451')
    parser.add_argument('--instructor', default='Conner')
    parser.add_argument('--out', default='byu_math451_winter2026_schedule.json')
    args = parser.parse_args()

    try:
        results = search_math_451_winter_2026(args.department, args.instructor)
        payload = {"ok": True, "count": len(results), "results": results}
    except Exception as exc:
        payload = {"ok": False, "error": str(exc)}

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(json.dumps(payload))

if __name__ == '__main__':
    main()
