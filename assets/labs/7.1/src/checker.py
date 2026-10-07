def check(name):
    total = 0
    for c in name:
        total += ord(c)
    return total == 0x29A


def main():
    name = input("Name: ")
    if check(name):
        print("Correct!")
    else:
        print("Wrong.")


if __name__ == "__main__":
    main()
