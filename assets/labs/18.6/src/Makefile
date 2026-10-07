# Lab 18.6: build the kernel module hello_ioctl.ko
# Needs the linux-headers package matching the running kernel version (uname -r).

obj-m += hello_ioctl.o

KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
