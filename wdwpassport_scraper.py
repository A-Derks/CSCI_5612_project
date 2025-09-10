import argparse, calendar, os, re
from datetime import date, datetime
import requests, pandas as pd
from bs4 import BeautifulSoup

HDRS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}

def month_url(year: int, month: int) -> str:
    return f"https://wdwpassport.com/past-crowds/{calendar.month_name[month].lower()}-{year}"

def fetch(url: str) -> str:
    r = requests.get(url, headers=HDRS, timeout=30)  # bump timeout a bit
    r.raise_for_status()
    return r.text

# --- robust parser (avoids mixing up "x/10" with day-of-month) ---
CROWD_RE = re.compile(r'(\d{1,2})\s*/\s*10')              # e.g., "7/10" -> 7
ISO_DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')
LONG_DATE_RE = re.compile(
    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*\d{4}\b',
    re.I,
)

def parse_month(html: str, year: int, month: int) -> pd.DataFrame:
    soup = BeautifulSoup(html, "lxml")
    rows = []

    def class_has_day_or_calendar(c):
        if not c: return False
        if isinstance(c, (list, tuple)):
            return any(("day" in s) or ("calendar" in s) for s in c if isinstance(s, str))
        return ("day" in c) or ("calendar" in c)

    tiles = soup.find_all(True, class_=class_has_day_or_calendar)
    for tile in tiles:
        txt = tile.get_text(" ", strip=True)

        crowd = None
        m = CROWD_RE.search(txt)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 10:
                crowd = val
        if crowd is None:
            for tok in re.findall(r'\b\d{1,2}\b', txt):
                iv = int(tok)
                if 1 <= iv <= 10:
                    crowd = iv
                    break
        if crowd is None:
            continue

        day_date = None
        for attr in ("data-date", "datetime", "aria-label"):
            val = tile.get(attr)
            if not val:
                continue
            mi = ISO_DATE_RE.search(val)
            if mi:
                try:
                    d = datetime.strptime(mi.group(1), "%Y-%m-%d").date()
                    if d.year == year and d.month == month:
                        day_date = d; break
                except: pass
            ml = LONG_DATE_RE.search(val)
            if ml:
                try:
                    d = pd.to_datetime(ml.group(0)).date()
                    if d.year == year and d.month == month:
                        day_date = d; break
                except: pass
        if day_date is None:
            for a in tile.find_all("a", href=True):
                href = a["href"]
                mi = ISO_DATE_RE.search(href)
                if mi:
                    try:
                        d = datetime.strptime(mi.group(1), "%Y-%m-%d").date()
                        if d.year == year and d.month == month:
                            day_date = d; break
                    except: pass
                ml = LONG_DATE_RE.search(href)
                if ml:
                    try:
                        d = pd.to_datetime(ml.group(0)).date()
                        if d.year == year and d.month == month:
                            day_date = d; break
                    except: pass
        if day_date is None:
            tokens = [int(t) for t in re.findall(r'\b\d{1,2}\b', txt)]
            candidates = [t for t in tokens if 1 <= t <= 31 and t != crowd]
            for dn in sorted(candidates, reverse=True):
                try:
                    d = date(year, month, dn)
                    day_date = d; break
                except: continue

        if day_date is None:
            continue

        rows.append({"date": day_date.isoformat(), "crowd_index": crowd})

    if not rows:
        return pd.DataFrame(columns=["date", "crowd_index"])

    df = pd.DataFrame(rows).drop_duplicates(subset=["date"]).sort_values("date")
    return df

def month_iter(start: date, end: date):
    y, m = start.year, start.month
    while (y < end.year) or (y == end.year and m <= end.month):
        yield y, m
        if m == 12: y, m = y + 1, 1
        else: m += 1

def ensure_dir(path: str):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)

def main():
    ap = argparse.ArgumentParser(description="Scrape WDW Passport daily crowd index.")
    ap.add_argument("--start", help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--end", help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--year", type=int)
    ap.add_argument("--month", type=int)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    ensure_dir(args.out)

    if args.start and args.end:
        start = datetime.strptime(args.start, "%Y-%m-%d").date()
        end = datetime.strptime(args.end, "%Y-%m-%d").date()
        if end < start:
            raise SystemExit("--end must be >= --start")
        all_months = []
        for y, m in month_iter(start, end):
            url = month_url(y, m)
            html = fetch(url)
            df = parse_month(html, y, m)
            if not df.empty:
                all_months.append(df)
        if not all_months:
            pd.DataFrame(columns=["date", "crowd_index"]).to_csv(args.out, index=False)
            print(f"Wrote {args.out} with 0 rows (no data found).")
            return
        out_df = pd.concat(all_months, ignore_index=True)
        # Filter to exact start/end
        out_df["date"] = pd.to_datetime(out_df["date"])
        mask = (out_df["date"].dt.date >= start) & (out_df["date"].dt.date <= end)
        out_df = out_df.loc[mask].drop_duplicates(subset=["date"]).sort_values("date")
    else:
        # Single-month mode
        if args.year is None or args.month is None:
            raise SystemExit("Provide --start/--end OR --year/--month")
        url = month_url(args.year, args.month)
        html = fetch(url)
        out_df = parse_month(html, args.year, args.month)

    out_df.to_csv(args.out, index=False)
    print(f"Wrote {args.out} with {len(out_df)} rows")

if __name__ == "__main__":
    main()
