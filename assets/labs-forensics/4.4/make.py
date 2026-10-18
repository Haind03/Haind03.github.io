#!/usr/bin/env python3
# Lab 4.4: tu sinh mot shell link (.lnk) LANH TINH bang pylnk3, tro toi mot file
# tren o E: (removable). Day la artifact DU LIEU (shortcut metadata), khong phai file thuc thi.
import os, pylnk3

HERE = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(HERE, "bang_luong.xlsx.lnk")
pylnk3.for_file(r"E:\Du_an_mat\bang_luong.xlsx", lnk_name=out)
print("created", os.path.basename(out), os.path.getsize(out), "bytes")
