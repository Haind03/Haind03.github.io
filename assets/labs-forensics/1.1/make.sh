#!/usr/bin/env bash
# Lab 1.1 - magic byte: tao bo file bi doi sai duoi de luyen nhan dien bang magic.
# Chay tren Linux thuong, khong can root. Can: ImageMagick (convert), zip, printf.
set -eu
cd "$(dirname "$0")"
rm -f *.pdf *.jpg *.png *.dat *.bin benh-nhan.png goc.png 2>/dev/null || true

# 1) PNG that nhung dat ten .pdf  -> extension noi doi
# convert suy ra dinh dang tu duoi file, nen tao PNG truoc roi doi ten thanh .pdf
convert -size 160x100 xc:steelblue _tmp.png && mv -f _tmp.png report.pdf

# 2) JPEG that nhung dat ten hoa-don.pdf  (giong vi du trong bai)
convert -size 200x140 xc:coral -pointsize 20 -gravity center -annotate 0 "JPG" _tmp.jpg
mv -f _tmp.jpg hoa-don.pdf

# 3) PDF that nhung dat ten logo.jpg
python3 - <<'PY'
pdf=b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
open('logo.jpg','wb').write(pdf)
PY

# 4) ZIP that nhung dat ten backup.dat
printf 'noi dung bi mat\n' > _inzip.txt && zip -q _z.zip _inzip.txt && mv -f _z.zip backup.dat && rm -f _inzip.txt

# 5) text thuan dat ten anh.png
printf 'day chi la text thuong, khong phai anh\n' > anh.png

# 6) mot PNG hop le de lam bai tap pha/va magic byte
convert -size 120x80 xc:white goc.png

echo "[make] da tao: report.pdf hoa-don.pdf logo.jpg backup.dat anh.png goc.png"
ls -l report.pdf hoa-don.pdf logo.jpg backup.dat anh.png goc.png
