# Lab 3.4: Du lieu an (steganography, append, metadata, LSB)

Lab chay that tren Linux (khong can root): nhung va trich secret THAT bang steghide (JPG va WAV),
phat hien ZIP noi duoi anh bang binwalk, doc metadata an bang exiftool, va LSB that tren PNG bang python.

## Cong cu
`steghide`, `binwalk`, `exiftool`, `unzip`, `zip`, `python3` + Pillow, ImageMagick (`convert`).

## Chay lab
```bash
bash make.sh     # tao stego.jpg, stego.wav, appended.png, meta.jpg, lsb_stego.png (password steghide: haind)
bash solve.sh    # trich het cac secret
```
`transcript.txt` la output THAT. Cac file stego nhe nen GIU trong repo de tu probe. (binwalk chay qua `binwalk_shim.py`,
giai thich o lab 3.2.)

## Nhiem vu (co lab chay that)
1. Steghide: trich secret tu `stego.jpg` va `stego.wav` voi password `haind` (`steghide extract -sf <file> -p haind`).
2. Append: `appended.png` la PNG noi them 1 ZIP. Dung `binwalk` phat hien, `unzip` lay file giau. Giai thich vi sao anh van mo
   binh thuong (trinh xem anh doc den IEND la dung, bo qua phan sau).
3. Metadata: `exiftool meta.jpg` doc truong Artist/Comment chua ghi chu an.
4. LSB: `lsb_stego.png` giau thong diep trong LSB kenh do. Trich bang `lsb.py extract`. So pixel voi `lsb_cover.png`:
   chi mot so pixel doi +/-1, mat thuong khong phan biet duoc.

## Nhiem vu la bai tap (can Windows / NTFS)
5. ADS: tao ADS giau text (`echo secret > file:hidden`), phat hien bang `dir /r` va `Get-Item -Stream *`; doc `Zone.Identifier`
   cua file tai tu web de lay URL nguon (MOTW). ADS chi song tren NTFS (bai 1.5), copy sang FAT la mat.
6. Slack: trich slack bang `blkls -s` tren image da ghi de (bai 3.3 / 1.2), tim manh file cu bang `strings`.

## Thu tu thu khi gap "steg" trong CTF
file -> exiftool -> strings -> binwalk -> roi moi toi LSB tool (zsteg/stegsolve). Rat nhieu "steg" chi la noi duoi ZIP.

## Dap an
Xem `solution.md`. Output that: `transcript.txt`.
