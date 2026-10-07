# Lab 7.3: sample check function for practicing bytecode reading.
# Compile it to .pyc, then try decompiling it or reading the bytecode.

def check(pw):
    key = "r3v3rs3"
    if len(pw) != 10:
        return False
    total = 0
    for c in pw:
        total += ord(c)
    return total == 1000 and pw.startswith(key[:3])


if __name__ == "__main__":
    import sys
    print("Correct!" if check(sys.argv[1]) else "Nope.")
