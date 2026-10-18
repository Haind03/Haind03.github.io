#!/usr/bin/env bash
# Lab 3.4 - du lieu an: tao cac artifact steg THAT (steghide jpg/wav, append zip, exif, LSB png).
set -eu
cd "$(dirname "$0")"
rm -f cover.jpg stego.jpg cover.wav stego.wav cover.png appended.png meta.jpg \
      lsb_cover.png lsb_stego.png secret.txt wsecret.txt s.zip s.txt

# --- steghide nhung vao JPG ---
convert -size 240x160 xc:skyblue -pointsize 18 -gravity center -annotate 0 "COVER" cover.jpg
printf 'FLAG{steghide_jpg_works}\n' > secret.txt
steghide embed -cf cover.jpg -ef secret.txt -sf stego.jpg -p haind -q

# --- steghide nhung vao WAV ---
python3 -I - <<'PY'
import wave, struct, math
w=wave.open('cover.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
w.writeframes(b''.join(struct.pack('<h', int(3000*math.sin(2*math.pi*440*i/44100))) for i in range(44100)))
w.close()
PY
printf 'FLAG{steghide_wav_works}\n' > wsecret.txt
steghide embed -cf cover.wav -ef wsecret.txt -sf stego.wav -p haind -q

# --- append ZIP vao sau PNG ---
convert -size 120x80 xc:white cover.png
printf 'co mat khau trong day: FLAG{append_zip}\n' > s.txt
zip -q s.zip s.txt
cat cover.png s.zip > appended.png

# --- exif metadata an ---
cp cover.jpg meta.jpg
exiftool -overwrite_original -Artist="HaiND" -Comment="hidden-note FLAG{exif_meta}" meta.jpg >/dev/null 2>&1

# --- LSB that tren PNG ---
convert -size 200x200 plasma: lsb_cover.png
python3 -I lsb.py embed lsb_cover.png lsb_stego.png "FLAG{lsb_png_works}"

echo "[make] da tao: stego.jpg stego.wav appended.png meta.jpg lsb_stego.png"
ls -l stego.jpg stego.wav appended.png meta.jpg lsb_stego.png
