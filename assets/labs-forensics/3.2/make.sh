#!/usr/bin/env bash
# Lab 3.2 - carving: nhet JPG + PNG + ZIP + PDF (ghep bytes) vao mot image co junk xen giua.
set -eu
cd "$(dirname "$0")"
rm -f j.jpg p.png z.zip d.pdf doc.txt carve.img
rm -rf out

# JPG that
convert -size 200x140 xc:coral -pointsize 22 -gravity center -annotate 0 "CARVE JPG" j.jpg
# PNG that
convert -size 160x100 xc:seagreen p.png
# ZIP that (co chuoi email/URL de bai 3.2 nhiem vu bulk_extractor)
printf 'invoice contact: billing@example.com  http://evil.example.org/c2\n' > doc.txt
zip -q z.zip doc.txt
# PDF toi thieu hop le
python3 -I - <<'PY'
pdf=b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R>>endobj\n4 0 obj<</Length 34>>stream\nBT /F1 18 Tf 40 100 Td (CARVE PDF OK) Tj ET\nendstream endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
open('d.pdf','wb').write(pdf)
PY

# Ghep: junk + jpg + junk + png + junk + zip + junk + pdf + junk
python3 -I - <<'PY'
import os
out=bytearray(); out+=os.urandom(300)
for fn in ('j.jpg','p.png','z.zip','d.pdf'):
    out+=open(fn,'rb').read(); out+=os.urandom(200)
open('carve.img','wb').write(out)
print("carve.img size", len(out))
PY
ls -l carve.img j.jpg p.png z.zip d.pdf
