---
title: "Lesson 6.1: JVM bytecode and the Java decompiler lineup"
image:
  path: /assets/img/covers/re-6-1-jvm-bytecode-java-decompiler-lineup.webp
  alt: "Lesson 6.1: JVM bytecode and the Java decompiler lineup"
date: 2022-09-01 09:11:00 +0700
categories: ["Technique Reverse", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
If you just came through the C/C++ part and feel discouraged because all the variable names are gone, Java will be a consolation. A Java `.class` file keeps almost all the information: class names, method names, field names, data types. Drop a `.jar` into JADX and you get back Java code that reads almost like the original. The reason is that Java, like .NET, doesn't compile straight to machine code but stops at an intermediate layer called bytecode. This lesson explains that layer and goes over the lineup of tools to flip it back into Java.

## Why .class is so easy to read

When you run `javac Hello.java`, the compiler doesn't produce instructions for the CPU. It produces JVM bytecode, an instruction set for the Java Virtual Machine. At runtime, the JVM translates that bytecode into machine code (through the JIT) or interprets it instruction by instruction.

The key point for a reverser: for the JVM to run it, a `.class` file has to carry a lot of metadata. Method names have to stay so they can be called, parameter types have to stay so they can be checked, field names have to stay so they can be accessed. Things a C compiler throws away, a Java compiler has to keep. That's why Java decompilers give much nicer results than native decompilers.

## Inside a .class file

A `.class` has several parts, and the two you care about most are the constant pool and the methods. The constant pool is a lookup table holding every constant, name, and reference the class uses. Strings, method names, class names, all gathered here and then the bytecode only points to them by index (`#7`, `#13`...). This is a gold mine when reversing: just read the constant pool and you see all the strings and the names of external functions called. Each method then has a Code block containing the bytecode.

The JVM is a stack-based virtual machine, unlike x86 which is register-based. That means instead of loading data into registers and computing, bytecode pushes operands onto a stack and then instructions pop from the stack to process them. For example, an addition doesn't say "add this register to that register", it says "take the top two values of the stack, add them, push the result back".

## Reading some real bytecode

![Stack-based JVM bytecode vs register-based DEX bytecode](/assets/img/re/part-06/dex-vs-jvm.svg)

Take a method that adds two numbers:

```java
static int add(int a, int b) {
    return a + b;
}
```

Use `javap -c` (a tool that ships with the JDK) to see the bytecode:

```
static int add(int, int);
  Code:
     0: iload_0      // push parameter 0 (a) onto the stack
     1: iload_1      // push parameter 1 (b) onto the stack
     2: iadd         // take the two numbers on the stack, add, push the result
     3: ireturn      // return the integer on top of the stack
```

Four instructions, and you can read the meaning directly. The `i` at the start is integer, `load` is load onto the stack, `add` is add, `return` is return. No need to memorize, you can guess from the prefix.

Now a method with a branch, like what you'd meet in a crackme:

```java
static boolean checkPass(String s) {
    return s.length() == 8 && s.equals("JavaRev!");
}
```

The bytecode:

```
0: aload_0                       // push parameter s (a reference type) onto the stack
1: invokevirtual String.length  // call s.length(), result goes onto the stack
4: bipush 8                      // push the constant 8
6: if_icmpne 22                  // if the two numbers differ, jump to 22 (return false)
9: aload_0                       // push s
10: ldc "JavaRev!"              // push the string constant (looked up in constant pool #13)
12: invokevirtual String.equals // call s.equals("JavaRev!")
15: ifeq 22                      // if the result is 0 (false), jump to 22
18: iconst_1                     // push 1 (true)
19: goto 23
22: iconst_0                     // push 0 (false)
23: ireturn
```

Notice `ldc "JavaRev!"`: the comparison string shows up right in the bytecode. A naive Java crackme hands over the password like this. `invokevirtual String.equals` tells you it compares strings, and the `if_icmpne`/`ifeq` pair is the two conditions of the `&&`. It's exactly like looking for the `cmp`/`jne` pair in assembly in Lesson 1.3, just much easier to read.

Names like `String.length`, `String.equals`, the string `JavaRev!`, all come from the constant pool. The bytecode just writes the numbers `#7`, `#13`, and `javap` looks them up for you and annotates beside them.

## The Java decompiler lineup, which to pick

You only need to read raw bytecode when a decompiler translates wrong. Most of the time you read the rebuilt Java directly. Each tool is strong in its own way:

| Tool | Strengths | When to use |
|---|---|---|
| JADX | Swallows APK/DEX as well as JAR, clean UI, basic deobfuscation and generates Frida snippets | The default for Android, also good for JAR. |
| CFR | Handles newer Java syntax very well (lambdas, modern switch), command line | When JADX output is hard to read, for cross-checking |
| Procyon | Stable, long-standing | A third option for cross-checking |
| Vineflower | Successor to Fernflower/Quiltflower, high quality, often used in modding | Complex code, when you need a clean translation |
| Recaf | Not just viewing but also editing bytecode and repackaging | When you need to patch a class/jar |
| Bytecode Viewer | Combines several decompilers in one GUI, side-by-side comparison | When you want several views at once |

A practical tip: no decompiler is 100% right. When one tool gives you weird code (a meaningless `var3` variable, tangled control structures), open the same file with another tool. Very often one of them translates it cleanly. Java RE people often keep two or three decompilers ready.

## Android is a bit different

Android doesn't run `.class` directly. It compiles them into DEX (Dalvik Executable), a different format, and the Android virtual machine (ART/Dalvik) is register-based rather than stack-based like the standard JVM. But the good news: you almost never have to read Dalvik bytecode by hand, because JADX merges every `.dex` in the APK and rebuilds Java directly. The APK and DEX structure is saved for Lesson 6.2.

## Lab

The goal is to see for yourself how Java source, JVM bytecode and decompiler output relate. You need a JDK (with `javac`, `java` and `javap`; check with `javac -version`) and a decompiler such as JADX, CFR (`cfr.jar`) or Bytecode Viewer. The source file is `Hello.java`.

First compile and run it to learn the original behavior, and write down the output:

```
javac Hello.java
java Hello
```

Then view the bytecode of the whole class, private methods included, and find the `add` and `checkPass` methods and match each instruction against the source:

```
javap -c -p Hello.class
```

Next, look at the constant pool to see where strings and reference names live. Find the `String JavaRev!` line, and notice that the bytecode only says `ldc #13` while the real string sits in the pool:

```
javap -v Hello.class
```

Finally, pack `Hello.class` into a JAR and decompile it with JADX or CFR:

```
jar cf Hello.jar Hello.class
```

Open `Hello.jar` in JADX-GUI (or run `java -jar cfr.jar Hello.class`) and compare the decompiled code with the original `Hello.java`.

Along the way, answer four questions. In the `checkPass` bytecode, which instructions correspond to `s.length() == 8` and which to `s.equals(...)`? What password does `checkPass` accept, and where in the bytecode can you find it without running the program? How faithfully did JADX rebuild the source, and were local variable names lost? And, if you like, open the same file with two different decompilers (JADX and CFR): do they give different results? Try it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 6.1</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/6.1/src/Hello.java" download><i class="fa-solid fa-file-code"></i>src/Hello.java</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

All the bytecode below is real output from `javac 21` followed by `javap -c -p`, unedited. Running the program prints:

```
x = 7
Correct!
```

The source of `checkPass` is:

```java
static boolean checkPass(String s) {
    return s.length() == 8 && s.equals("JavaRev!");
}
```

and its bytecode is:

```
0: aload_0                        // push s onto the stack
1: invokevirtual String.length    // }
4: bipush 8                       // } the s.length() == 8 part
6: if_icmpne 22                   // } not 8, jump down and return false
9: aload_0                        // }
10: ldc "JavaRev!"               // }
12: invokevirtual String.equals   // } the s.equals("JavaRev!") part
15: ifeq 22                       // } not equal, jump down and return false
18: iconst_1                      // true
19: goto 23
22: iconst_0                      // false
23: ireturn
```

`s.length() == 8` is the instructions at offsets 1 to 6 (`invokevirtual length`, `bipush 8`, `if_icmpne`), and `s.equals("JavaRev!")` is offsets 10 to 15 (`ldc`, `invokevirtual equals`, `ifeq`). The `&&` operator shows up as short-circuiting: both failing branches jump to `22` (return false).

The password is `JavaRev!`, exactly 8 characters, which also satisfies the `length() == 8` condition. You can find it without running anything: the `ldc "JavaRev!"` instruction at offset 10 loads the constant string directly, and in `javap -v` it sits in the constant pool:

```
#13 = String             #14            // JavaRev!
#14 = Utf8               JavaRev!
```

That is the core lesson: a naive Java crackme leaks its password right in the constant pool. You only need to read the string, not understand the logic.

On decompile quality, JADX and CFR recover `add`, `checkPass` and `main` almost verbatim, with the right method names, types and logic. What gets lost is local variable names (parameters and body variables can become `s`, `a`, `b` if a LocalVariableTable is present, or `var1`, `var2` if the class was compiled without `-g`). Compared with native C/C++, where every name is gone, that is a world of difference. Note that the line `System.out.println("x = " + x)` uses `invokedynamic makeConcatWithConstants` (the modern way Java concatenates strings). Some older decompilers translate it oddly, while newer ones (CFR, Vineflower) restore it as a normal `+`.

For this simple class, JADX and CFR are nearly identical. Differences show up when the code has lambdas, streams, newer-style switches, or has been obfuscated, and then opening it in several tools and comparing is a good habit.

The decompiler comparison describes standard JADX and CFR behavior, and the exact output can differ a little between versions.

</details>

## Key takeaways
Java compiles to JVM bytecode (not machine code), so `.class` keeps method/field/type names intact. The JVM is a stack-based virtual machine: operands get pushed onto the stack and then instructions pop them to process. The constant pool holds every string and referenced name, so reading it shows you all the clues, and `javap -c` shows the bytecode, where the instruction prefix (`i` for int, `a` for reference) tells you the type.

The main decompilers are JADX (the default), CFR, Vineflower, and Procyon, with Recaf for editing, and if a translation looks odd you switch tools. Android uses DEX (register-based), but JADX handles it all, see Lesson 6.2.
