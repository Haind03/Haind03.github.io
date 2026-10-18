#!/usr/bin/env bash
# Lab 8.1 - script giai: truy van History (Chrome) va places/formhistory (Firefox)
# bang sqlite3, doi dung timestamp WebKit va PRTime ra UTC.
#
# Dung: bash solve.sh [thu_muc_profile]   (mac dinh ./profile)
set -u
P="${1:-profile}"
H="$P/History"; PL="$P/places.sqlite"; FH="$P/formhistory.sqlite"
line(){ printf '\n==== %s ====\n' "$1"; }

for f in "$H" "$PL" "$FH"; do
  [ -f "$f" ] || { echo "Thieu $f (chay make_artifacts.py truoc)"; exit 1; }
done

line "0. Hash truoc khi dong (lam viec tren ban sao)"
sha256sum "$H" "$PL" "$FH"

line "1. Chrome: trang ghe nhieu nhat (WebKit -> UTC: /1e6 - 11644473600)"
sqlite3 -header -column "$H" "
SELECT url, title, visit_count,
  datetime(last_visit_time/1000000 - 11644473600,'unixepoch') AS last_utc
FROM urls ORDER BY visit_count DESC, last_visit_time;"

line "2. Chrome: chuoi ghe theo thoi gian + kieu transition"
sqlite3 -header -column "$H" "
SELECT datetime(v.visit_time/1000000 - 11644473600,'unixepoch') AS visit_utc,
  CASE v.transition & 0xff
    WHEN 0 THEN 'LINK' WHEN 1 THEN 'TYPED' WHEN 7 THEN 'FORM_SUBMIT'
    ELSE v.transition END AS transition,
  u.url
FROM visits v JOIN urls u ON u.id=v.url ORDER BY v.visit_time;"

line "3. Chrome: tu khoa tim kiem trich tu URL (giai URL-encoding)"
sqlite3 "$H" "SELECT url FROM urls WHERE url LIKE '%search?q=%' OR url LIKE '%?q=%';" \
| while IFS= read -r u; do
    q="${u#*q=}"; q="${q%%&*}"
    dec=$(python3 -I -c "import urllib.parse,sys; print(urllib.parse.unquote_plus(sys.argv[1]))" "$q")
    echo "  $u"
    echo "    -> tu khoa: $dec"
  done

line "4. Chrome: download (file tai ve va trang khoi phat)"
sqlite3 -header -column "$H" "
SELECT datetime(start_time/1000000 - 11644473600,'unixepoch') AS started,
  target_path, tab_url, total_bytes FROM downloads ORDER BY start_time;"

line "5. Firefox places.sqlite (PRTime -> UTC: chi /1e6, KHONG tru)"
sqlite3 -header -column "$PL" "
SELECT datetime(last_visit_date/1000000,'unixepoch') AS t, url, title
FROM moz_places ORDER BY last_visit_date;"

line "6. Firefox formhistory.sqlite (lo tu khoa da go, ke ca khong Enter)"
sqlite3 -header -column "$FH" "
SELECT fieldname, value, timesUsed,
  datetime(firstUsed/1000000,'unixepoch') AS first_utc
FROM moz_formhistory ORDER BY firstUsed;"

line "KET LUAN (timeline duyet web, moi moc co nguon artifact)"
cat <<'K'
  14:02:00 UTC  Chrome urls/visits  go tay vao Google (TYPED)
  14:02:10 UTC  Chrome urls         tim "usb wiping tool" (FORM_SUBMIT, giai tu q=)
  14:03:05 UTC  Chrome visits       click sang eraser-tools.example/download (LINK)
  14:05:12 UTC  Chrome downloads    tai eraser-setup.exe ve C:\Users\...\Downloads (7.3 MB)
  14:08:00 UTC  Firefox formhistory go "how to wipe usb without trace" vao search box
  14:20:00 UTC  Chrome urls         ghe webmail inbox (TYPED)
  Chrome  = WebKit epoch (1601), phai tru 11644473600; Firefox = PRTime (1970), chi chia 1e6.
K
