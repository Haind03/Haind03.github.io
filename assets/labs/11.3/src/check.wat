;; check.wat - sample WebAssembly keygenme for Lab 11.3
;; Build to .wasm:      wat2wasm check.wat -o check.wasm
;; Read it back:      wasm2wat check.wasm -o out.wat
;;
;; The "check" function takes a pointer to the key string in linear memory and its length,
;; and returns 1 if correct, 0 if wrong. Algorithm: every key byte key[i] satisfies
;;   (key[i] + i) ^ 0x1F == TARGET[i]
;; where TARGET is preloaded in the data section at offset 256.
;; The learner works out the correct key themselves.

(module
  (memory (export "memory") 1)

  ;; TARGET = the target bytes of the correct key, placed at offset 256
  (data (i32.const 256) "\48\7d\6a\6f\7c\48\74\62")

  (func $check (export "check") (param $ptr i32) (param $len i32) (result i32)
    (local $i i32)
    (local $c i32)
    (local $want i32)

    ;; the length must be exactly 8
    local.get $len
    i32.const 8
    i32.ne
    if
      i32.const 0
      return
    end

    (local.set $i (i32.const 0))
    (block $done
      (loop $next
        local.get $i
        i32.const 8
        i32.ge_u
        br_if $done

        ;; c = memory[ptr + i]
        local.get $ptr
        local.get $i
        i32.add
        i32.load8_u
        local.set $c

        ;; want = memory[256 + i]
        local.get $i
        i32.const 256
        i32.add
        i32.load8_u
        local.set $want

        ;; if ((c + i) ^ 0x1F) != want  -> return 0
        local.get $c
        local.get $i
        i32.add
        i32.const 0x1f
        i32.xor
        local.get $want
        i32.ne
        if
          i32.const 0
          return
        end

        local.get $i
        i32.const 1
        i32.add
        local.set $i
        br $next
      )
    )
    i32.const 1
  )
)
