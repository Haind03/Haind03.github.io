#!/usr/bin/env bash
# Lab 3.4 - solve: trich secret tu steghide (jpg/wav), binwalk+unzip append, exiftool, LSB.
set -u
cd "$(dirname "$0")"

echo "=== B1: steghide trich tu JPG ==="
steghide extract -sf stego.jpg -p haind -xf out_jpg.txt -f -q 2>/dev/null; cat out_jpg.txt

echo
echo "=== B2: steghide trich tu WAV ==="
steghide extract -sf stego.wav -p haind -xf out_wav.txt -f -q 2>/dev/null; cat out_wav.txt

echo
echo "=== B3: append ZIP sau PNG - binwalk phat hien + unzip lay ra ==="
/usr/bin/python3 binwalk_shim.py appended.png 2>&1 | head -8
echo "-- unzip phan dinh kem --"
unzip -o appended.png -d out_append 2>&1 | tail -2
echo "-- noi dung file giau --"; cat out_append/s.txt 2>/dev/null

echo
echo "=== B4: exiftool doc metadata an ==="
exiftool -Artist -Comment meta.jpg 2>&1 | head

echo
echo "=== B5: LSB tren PNG - trich bang lsb.py ==="
python3 -I lsb.py extract lsb_stego.png
echo "-- so khac o muc PIXEL (mat thuong khong thay) --"
python3 -I -W ignore -c "
from PIL import Image
a=list(Image.open('lsb_cover.png').convert('RGB').getdata())
b=list(Image.open('lsb_stego.png').convert('RGB').getdata())
diff=[max(abs(x-y) for x,y in zip(p,q)) for p,q in zip(a,b)]
chg=sum(1 for d in diff if d)
print('so pixel bi doi:', chg, '/', len(a), '; muc doi lon nhat moi kenh:', max(diff), '(chi LSB, tuc +/-1)')"
