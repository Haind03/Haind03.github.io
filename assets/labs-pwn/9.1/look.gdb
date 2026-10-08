set pagination off
tbreak src.c:39
run
printf "=== dia chi 3 chunk ===\n"
print a
print b
print c
printf "=== header + fd + key cua chunk a (a-0x10) ===\n"
x/4gx (char*)a-16
printf "=== vung heap ===\n"
info proc mappings
quit
