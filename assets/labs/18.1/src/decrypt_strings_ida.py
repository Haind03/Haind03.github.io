# IDAPython: bulk-decrypt XOR strings and set comments
# Run in IDA: File > Script file... or Alt+F7
# Adjust KEY and the way the pointer/length is obtained to match your binary.

import idautils
import idc
import ida_bytes
import ida_name

KEY = 0x5A          # single-byte XOR key (example)
DECRYPT_FUNC = "decrypt_string"  # name of the renamed decryption function


def xor_decrypt(data, key):
    return bytes(b ^ key for b in data)


def read_cstring_enc(ptr, max_len=256):
    out = bytearray()
    for i in range(max_len):
        b = ida_bytes.get_byte(ptr + i)
        # the original string ends with 0, and after encryption the 0 byte becomes the key
        if b == KEY:
            break
        out.append(b)
    return bytes(out)


def main():
    func_ea = idc.get_name_ea_simple(DECRYPT_FUNC)
    if func_ea == idc.BADADDR:
        print("Function %s not found. Rename the decryption function first." % DECRYPT_FUNC)
        return

    count = 0
    for xref in idautils.XrefsTo(func_ea):
        call_ea = xref.frm
        # get the pointer passed in (operand of the instruction just before the call)
        ptr = idc.get_operand_value(idc.prev_head(call_ea), 1)
        if ptr == idc.BADADDR or ptr == 0:
            continue
        enc = read_cstring_enc(ptr)
        if not enc:
            continue
        try:
            dec = xor_decrypt(enc, KEY).decode("latin1")
        except Exception:
            continue
        idc.set_cmt(call_ea, "str: " + dec, 1)
        print(hex(call_ea), "->", dec)
        count += 1

    print("Decrypted %d strings." % count)


if __name__ == "__main__":
    main()
