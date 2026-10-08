---
title: "Lesson 6.1: JVM bytecode and Java decompilers"
image:
  path: /assets/img/covers/re-6-1-jvm-bytecode-java-decompiler-lineup.webp
  alt: "Lesson 6.1: JVM bytecode and Java decompilers"
date: 2022-04-11 04:52:00 +0700
categories: ["Reverse Engineering", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
If the C/C++ part left you annoyed that all the variable names are gone, Java is easier. A Java `.class` file keeps almost everything, including class names, method names, field names and data types. Drop a `.jar` into JADX and you get Java code that reads almost like the original. Java, like .NET, doesn't compile straight to machine code. It stops at an intermediate layer called bytecode. This lesson explains that layer and the tools that turn it back into Java.

## Why .class is easy to read

When you run `javac Hello.java`, the compiler doesn't produce CPU instructions. It produces JVM bytecode, the instruction set of the Java Virtual Machine. At runtime the JVM translates the bytecode to machine code (through the JIT) or interprets it instruction by instruction.

For the JVM to run a `.class` file, the file has to carry a lot of metadata. Method names must stay so they can be called, parameter types must stay so they can be checked, field names must stay so they can be accessed. A C compiler throws these away, a Java compiler can't. That's why Java decompilers give much nicer results than native ones.

## Inside a .class file

A `.class` has several parts. The two you care about most are the constant pool and the methods. The constant pool is a lookup table with every constant, name and reference the class uses. Strings, method names and class names are all collected there, and the bytecode points to them by index (`#7`, `#13`...). When reversing, reading the constant pool already gives you all the strings and the names of the external functions called. Each method then has a Code block with the bytecode.

The JVM is a stack-based virtual machine, unlike x86 which is register-based. Instead of loading data into registers and computing, bytecode pushes operands onto a stack and instructions pop them to process. For example, an addition doesn't say "add this register to that register". It takes the top two values of the stack, adds them and pushes the result back.

## Reading some real bytecode

![Stack-based JVM bytecode vs register-based DEX bytecode](/assets/img/re/part-06/dex-vs-jvm.svg)

Take a method that adds two numbers:

```java
static int add(int a, int b) {
    return a + b;
}
```

Use `javap -c` (it ships with the JDK) to see the bytecode:

```
static int add(int, int);
  Code:
     0: iload_0      // push parameter 0 (a) onto the stack
     1: iload_1      // push parameter 1 (b) onto the stack
     2: iadd         // take the two numbers on the stack, add, push the result
     3: ireturn      // return the integer on top of the stack
```

Four instructions and you can read the meaning directly. The `i` at the start is integer, `load` loads onto the stack, `add` adds, `return` returns. You don't need to memorize anything, you can guess from the prefix.

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

Look at `ldc "JavaRev!"`. The comparison string is right there in the bytecode, so a naive Java crackme gives up its password like this. `invokevirtual String.equals` says it compares strings, and the `if_icmpne`/`ifeq` pair is the two conditions of the `&&`. It's like looking for the `cmp`/`jne` pair in assembly in Lesson 1.3, just easier to read.

Names like `String.length` and `String.equals` and the string `JavaRev!` all come from the constant pool. The bytecode only has the numbers `#7`, `#13`, and `javap` looks them up and annotates them for you.

## Java decompilers

You only need to read raw bytecode when a decompiler gets it wrong. Most of the time you read the rebuilt Java directly. Each tool has its own strengths:

| Tool | Strengths | When to use |
|---|---|---|
| JADX | Opens APK/DEX as well as JAR, clean UI, basic deobfuscation and generates Frida snippets | The default for Android, also good for JAR. |
| CFR | Handles newer Java syntax very well (lambdas, modern switch), command line | When JADX output is hard to read, for cross-checking |
| Procyon | Stable, long-standing | A third option for cross-checking |
| Vineflower | Successor to Fernflower/Quiltflower, high quality, often used in modding | Complex code, when you need a clean translation |
| Recaf | Not just viewing but also editing bytecode and repackaging | When you need to patch a class/jar |
| Bytecode Viewer | Combines several decompilers in one GUI, side-by-side comparison | When you want several views at once |

No decompiler is 100% right. When one tool gives you weird code (a meaningless `var3` variable, tangled control structures), I open the same file with another tool, and very often one of them gets it clean. People who do Java RE usually keep two or three decompilers around.

## Android is a bit different

Android doesn't run `.class` directly. It compiles them into DEX (Dalvik Executable), a different format, and the Android virtual machine (ART/Dalvik) is register-based rather than stack-based like the standard JVM. You almost never have to read Dalvik bytecode by hand though, because JADX merges every `.dex` in the APK and rebuilds Java directly. The APK and DEX structure is in Lesson 6.2.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 6.1</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/6.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/6.1/src/Hello.java" download><i class="fa-solid fa-download"></i>src/Hello.java</a>
</div>
</div>

The goal is to see how Java source, JVM bytecode and decompiler output relate. You need a JDK (with `javac`, `java` and `javap`; check with `javac -version`) and a decompiler such as JADX, CFR (`cfr.jar`) or Bytecode Viewer. The source file is `Hello.java`.

First compile and run it to learn the original behavior, and write down the output:

```
javac Hello.java
java Hello
```

Then view the bytecode of the whole class, private methods included. Find the `add` and `checkPass` methods and match each instruction against the source:

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

Answer four questions along the way. In the `checkPass` bytecode, which instructions correspond to `s.length() == 8` and which to `s.equals(...)`? What password does `checkPass` accept, and where in the bytecode can you find it without running the program? How faithfully did JADX rebuild the source, and were local variable names lost? And if you like, open the same file with two different decompilers (JADX and CFR) and check whether they give different results. Try it yourself before opening the solution.

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

`s.length() == 8` is the instructions at offsets 1 to 6 (`invokevirtual length`, `bipush 8`, `if_icmpne`), and `s.equals("JavaRev!")` is offsets 10 to 15 (`ldc`, `invokevirtual equals`, `ifeq`). The `&&` operator shows up as short-circuiting, where both failing branches jump to `22` (return false).

The password is `JavaRev!`, exactly 8 characters, which also satisfies the `length() == 8` condition. You can find it without running anything, since the `ldc "JavaRev!"` instruction at offset 10 loads the constant string directly, and in `javap -v` it sits in the constant pool:

```
#13 = String             #14            // JavaRev!
#14 = Utf8               JavaRev!
```

So a naive Java crackme leaks its password in the constant pool. You only need to read the string, not understand the logic.

On decompile quality, JADX and CFR recover `add`, `checkPass` and `main` almost verbatim, with the right method names, types and logic. What gets lost is local variable names (parameters and body variables can become `s`, `a`, `b` if a LocalVariableTable is present, or `var1`, `var2` if the class was compiled without `-g`). Compared with native C/C++, where every name is gone, that's a big difference. The line `System.out.println("x = " + x)` uses `invokedynamic makeConcatWithConstants` (the modern way Java concatenates strings). Some older decompilers translate it oddly, while newer ones (CFR, Vineflower) restore it as a normal `+`.

For this simple class, JADX and CFR are nearly identical. Differences show up when the code has lambdas, streams, newer-style switches, or has been obfuscated, and then opening it in several tools and comparing is a good habit.

The decompiler comparison describes standard JADX and CFR behavior, and the exact output can differ a little between versions.

</details>

## Key takeaways
Java compiles to JVM bytecode (not machine code), so `.class` keeps method, field and type names intact. The JVM is stack-based, so operands get pushed onto the stack and instructions pop them to process. The constant pool holds every string and referenced name, so reading it shows you all the clues, and `javap -c` shows the bytecode, where the instruction prefix (`i` for int, `a` for reference) tells you the type.

The main decompilers are JADX (the default), CFR, Vineflower and Procyon, with Recaf for editing. If a translation looks odd, switch tools. Android uses DEX (register-based), but JADX handles it all, see Lesson 6.2.
