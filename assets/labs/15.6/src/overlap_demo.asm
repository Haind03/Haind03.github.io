; Lab 15.6: anti-disassembly, junk bytes + overlapping instructions
; This is NOT a file you build and run, it's a sequence of bytes to practice
; reading by hand and in IDA/Ghidra. Goal: find the REAL CPU flow.
;
; ------------------------------------------------------------------
; PART 1: junk byte after an unconditional jmp
; ------------------------------------------------------------------
; Bytes on disk (read left to right):
;
;   EB 01 E8 B8 2A 00 00 00 C3
;
; How a LINEAR SWEEP disassembler reads it (wrong):
;   EB 01          jmp  short +1
;   E8 B8 2A 00 00 call <wrong address>     ; wrongly swallows bytes B8 2A 00 00 00
;   ...                                      ; everything is shifted from here
;
; The REAL CPU flow (the jmp skips exactly 1 byte, E8):
;   EB 01          jmp  short +1           ; jump to the byte B8
;   (byte E8 is skipped, never executed)
;   B8 2A 00 00 00 mov  eax, 0x2A          ; eax = 42
;   C3             ret
;
; => The real function is just: return 42. Byte E8 is junk.
;
; ------------------------------------------------------------------
; PART 2: overlapping instructions
; ------------------------------------------------------------------
; Bytes on disk:
;
;   31 C0 EB FF C0 48 FF C0 C3
;
; Reading from the start:
;   31 C0          xor eax, eax           ; eax = 0
;   EB FF          jmp short -1           ; LOOKS LIKE it jumps back into itself
;
; But EB FF actually targets the byte FF (inside itself), and the CPU reads
; again starting from there:
;   FF C0          inc eax                ; eax = 1
;   48 FF C0       inc rax                ; eax = 2  (REX.W + FF C0)
;   C3             ret
;
; => The disassembler locks onto "jmp short -1" and misses the two inc
;    instructions. The real flow is: eax = 0, then +1, then +1 => return 2.
