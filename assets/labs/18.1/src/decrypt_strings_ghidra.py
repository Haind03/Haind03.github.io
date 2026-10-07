# Ghidra Python (Jython): decrypt XOR strings and set comments
# Run in Ghidra: Window > Script Manager, or drag the file into Script Manager.
# Illustration: scan a data section, XOR-decrypt, set an EOL comment.

# @category RE.Lab

KEY = 0x5A


def xor_decrypt(data, key):
    return bytes(bytearray((b ^ key) & 0xFF for b in data))


def read_enc_cstring(addr, max_len=256):
    out = bytearray()
    mem = currentProgram.getMemory()
    for i in range(max_len):
        b = mem.getByte(addr.add(i)) & 0xFF
        if b == KEY:   # original 0 byte -> KEY after encryption
            break
        out.append(b)
    return bytes(out)


def main():
    # example: get the symbol of the renamed decryption function
    func = getFunction("decrypt_string")
    if func is None:
        print("decrypt_string not found. Rename the decryption function first.")
        return

    refs = getReferencesTo(func.getEntryPoint())
    listing = currentProgram.getListing()
    count = 0
    for ref in refs:
        call_addr = ref.getFromAddress()
        # (binary-specific) get the pointer argument; a simple illustration here
        instr = listing.getInstructionAt(call_addr)
        if instr is None:
            continue
        # the real ptr extraction depends on the architecture, fill it in for your binary
        # example: ptr = instr.getPrevious().getOpObjects(1)[0]
        print("call at %s (fill in the ptr extraction logic for your binary)" % call_addr)
        count += 1

    print("Found %d call sites of decrypt_string." % count)


main()
