import sys


def check(pw):
    return pw == "PyInst@ller_2024"


def main():
    pw = input("License key: ")
    if check(pw):
        print("Licensed!")
    else:
        print("Wrong key.")


if __name__ == "__main__":
    main()
