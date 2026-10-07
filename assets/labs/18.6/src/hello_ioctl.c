// Lab 18.6: a minimal Linux kernel module with a character device + ioctl.
// Only for learning to read a .ko, load it in a practice VM.
//
// Build: make  (needs linux-headers matching uname -r)
// Try loading it in a VM: sudo insmod hello_ioctl.ko ; dmesg | tail
// Remove: sudo rmmod hello_ioctl

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>
#include <linux/ioctl.h>

#define DEVICE_NAME "hello_ioctl"
#define CLASS_NAME  "hello"

// Three IOCTL commands (this is the module's "API", try to find it again in the .ko).
#define HELLO_MAGIC 'H'
#define IOCTL_PING  _IO(HELLO_MAGIC, 1)
#define IOCTL_SET   _IOW(HELLO_MAGIC, 2, int)
#define IOCTL_GET   _IOR(HELLO_MAGIC, 3, int)

static int major;
static int stored_value;

static long hello_ioctl(struct file *f, unsigned int cmd, unsigned long arg)
{
    int tmp;
    switch (cmd) {
    case IOCTL_PING:
        pr_info("hello_ioctl: PING\n");
        return 0;
    case IOCTL_SET:
        if (copy_from_user(&tmp, (int __user *)arg, sizeof(tmp)))
            return -EFAULT;
        stored_value = tmp;
        pr_info("hello_ioctl: SET %d\n", stored_value);
        return 0;
    case IOCTL_GET:
        if (copy_to_user((int __user *)arg, &stored_value, sizeof(stored_value)))
            return -EFAULT;
        return 0;
    default:
        return -EINVAL;
    }
}

static int hello_open(struct inode *i, struct file *f)  { return 0; }
static int hello_release(struct inode *i, struct file *f) { return 0; }

static const struct file_operations hello_fops = {
    .owner          = THIS_MODULE,
    .open           = hello_open,
    .release        = hello_release,
    .unlocked_ioctl = hello_ioctl,
};

static int __init hello_init(void)
{
    major = register_chrdev(0, DEVICE_NAME, &hello_fops);
    if (major < 0) {
        pr_err("hello_ioctl: register_chrdev failed\n");
        return major;
    }
    pr_info("hello_ioctl: loaded, major=%d\n", major);
    return 0;
}

static void __exit hello_exit(void)
{
    unregister_chrdev(major, DEVICE_NAME);
    pr_info("hello_ioctl: unloaded\n");
}

module_init(hello_init);
module_exit(hello_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Blog Reverse Engineering");
MODULE_DESCRIPTION("Lab 18.6 character device with ioctl for RE practice");
