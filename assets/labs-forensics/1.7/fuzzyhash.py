#!/usr/bin/env python3
# Lab 1.7 - minh hoa fuzzy hashing khi khong co ssdeep.
# Day KHONG phai ssdeep that; no tinh do tuong dong bang Jaccard tren tap shingle (k-gram byte),
# du de thay hai file gan giong co diem cao, con hash mat ma (md5/sha) thi khac hoan toan.
# Chay: python3 -I fuzzyhash.py fileA fileB [fileC ...]
import sys, hashlib

K = 8  # do dai shingle (byte)

def shingles(path):
    data = open(path, "rb").read()
    if len(data) < K:
        return {hashlib.blake2b(data, digest_size=8).hexdigest()}
    return {hashlib.blake2b(data[i:i+K], digest_size=8).hexdigest()
            for i in range(len(data) - K + 1)}

def jaccard(a, b):
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)

paths = sys.argv[1:]
sig = {p: shingles(p) for p in paths}
print("Do tuong dong (Jaccard tren shingle %d-byte), 0..100:" % K)
for i in range(len(paths)):
    for j in range(i + 1, len(paths)):
        score = round(jaccard(sig[paths[i]], sig[paths[j]]) * 100)
        print("  %-10s vs %-10s : %3d" % (paths[i], paths[j], score))
