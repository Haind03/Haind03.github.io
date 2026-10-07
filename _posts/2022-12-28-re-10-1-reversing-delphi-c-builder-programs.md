---
title: "Lesson 10.1: Reversing Delphi and C++Builder programs"
image:
  path: /assets/img/covers/re-10-1-reversing-delphi-c-builder-programs.webp
  alt: "Lesson 10.1: Reversing Delphi and C++Builder programs"
date: 2022-12-28 10:34:00 +0700
categories: ["Technique Reverse", "Part 10 · Legacy: Delphi, VB6, AutoIt, AHK"]
tags: [reverse-engineering, legacy]
render_with_liquid: false
---
Say you open an old exe in IDA. The decompiler gives pseudocode but every function is `sub_xxx`, there isn't one familiar name, the strings have a length stuck in front of them, and thousands of functions from some framework fill the screen. You probably have a Delphi binary. Delphi is old but still in use in enterprise software, POS systems, Vietnamese accounting software and a fair amount of malware. It isn't harder than C, just different, and you need the right tools.

## What Delphi is and why it's different

Delphi (and its sibling C++Builder) uses the Borland compiler, now Embarcadero. The code is Object Pascal compiled straight to native x86/x64, so you're still reading normal assembly. But Delphi leaves some specific signatures that make reversing different from what you're used to in C.

The first is the VCL framework (Visual Component Library). Almost every Delphi app pulls in a lot of VCL functions for forms, buttons, strings and streams. Like a statically linked libc in C, most of the code you see isn't the author's but the framework's, and filtering it out is half the work.

The second is Pascal-style strings. Unlike C's null-terminated strings, Delphi strings (AnsiString, UnicodeString) have a length prefix, with the length and refcount right before the data pointer. In IDA you see strings that don't end in `00` but have a few length bytes in front, and you need to know that to read them correctly.

The UI is stored as DFM (Delphi Form Module) in the exe's resource section. The DFM describes each component and the names of the event handlers (for example `Button1Click`), which helps a lot for tracing the logic. Finally, Delphi defaults to the `register` calling convention (Borland's own fastcall), where the first three parameters go through EAX, EDX, ECX. That's different from the usual cdecl/stdcall, and if you misread the convention you misread the parameters.

## Spotting Delphi quickly

Drop the file into Detect It Easy (DIE). It usually names the compiler as Borland Delphi or Embarcadero, with the version. Other signs also give Delphi away. In strings you'll see `Borland` or `Embarcadero` and unit names like `System`, `SysUtils`, `Classes`, `Vcl.Forms`. The entry point calls a characteristic runtime init function that sets up the VCL and calls `InitExe`. The resource section also has DFM blobs, with component names, `TForm`, `TButton`.

Once you confirm it's Delphi, don't start reading assembly in IDA yet. Get the right tools first.

## IDR

The problem with plain IDA on Delphi is that it doesn't know those thousands of functions are VCL, so it leaves them as `sub_xxx` and you drown. IDR (Interactive Delphi Reconstructor) was made for exactly this. It recovers the names of known VCL/RTL functions, renaming them to things like `TStringList.Add` and `ShowMessage`, so you can skip them and focus on the author's code. It rebuilds the forms and event handlers from the DFM, so you see which address `Button1Click` is at and where the code runs when the user clicks a button. And it exports a map/idc that you import back into IDA, which turns the `sub_xxx` names into meaningful names.

My workflow: run IDR on the Delphi exe, let it analyze, export the helper file (for example .idc or .map), then load it into IDA. After this IDA becomes readable. DeDe is an older tool with the same idea, only good for very old Delphi, and these days I almost always use IDR.

C++Builder is a bit more complicated because it mixes C++ (name mangling, classes, vtables as in Part 4) with the Borland runtime, but the approach is similar. Identify with DIE, use IDR for the VCL part, then apply your C++ knowledge to the rest.

## Start from event handlers, not from main

This is the most useful tip in the lesson. With a C app you look for `main`. With a Delphi app that has a UI, `main` is just the VCL message loop and has nothing interesting. The real logic is in the event handlers. The user types a serial and clicks OK, so the `btnOKClick` function (or something named similarly) is where the check happens.

Since IDR rebuilds the forms, you know the names and addresses of the handlers. Jump straight to the handler of the relevant button and you're in the right place, skipping all the UI init code. If there are no names, search by message strings ("Wrong password", "Registration successful") and follow xrefs backwards, like in earlier parts. Just remember Delphi strings have a length prefix, so search for the text part and leave out the length byte.

## Key takeaways
Delphi/C++Builder is native x86/x64, but it pulls in a lot of VCL functions and has its own signatures. Delphi strings have a length prefix and are not null-terminated, and the default calling convention is register (EAX, EDX, ECX for the first 3 parameters), so keep both in mind when reading and searching.

Identify with DIE, then use IDR to recover VCL names and rebuild forms and event handlers. Start from event handlers such as Button1Click rather than from main, because main is just the message loop.

## Lab

In this lab you recognize a Delphi binary yourself, use IDR to rebuild its forms and event handlers, and then trace to the check function behind the OK button. You need Detect It Easy (DIE), IDR (Interactive Delphi Reconstructor, from the author's official site), and IDA Free or Ghidra to look at the code once IDR has supplied the symbols. You also need a Delphi exe to practice on. A good option is to compile a small VCL app yourself with the free Delphi Community Edition, with one form, one input box and an OK button that checks a password, or to use a Delphi crackme from crackmes.one (filtered by the Delphi language).

Drag the exe into DIE and note whether the compiler is Borland or Embarcadero Delphi, which version, and whether it's 32 or 64-bit. Open Strings and look for VCL traces (unit names such as `SysUtils`, `Classes`, `Vcl.Forms`) and the app's own message strings. Then run IDR on the exe, let it finish analyzing, and look at the list of forms and event handlers it rebuilt, noting the handler names (for example `Button1Click` or `btnOKClick`).

Export the support file from IDR (map or idc) and load it into IDA, and see how the number of named functions grows compared with before. Jump to the event handler of the OK or Login button and read the check logic. Keep in mind that the compared strings are Delphi strings with a length prefix, and that parameters are passed in EAX, EDX and ECX. Finally find the password or the condition for success.

Some questions to think about. Why is starting from an event handler so much faster than reading from the entry point? How does a Delphi string differ from a C string, and how does that affect your searching in IDA? And if you didn't have IDR, how long would it take you to work out by yourself which functions are VCL and which are the author's code? Try it yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This writeup describes the standard workflow on a typical Delphi app. The steps and the shape of the results below follow the way IDR and IDA work with Delphi binaries, so the exact output on your sample will differ.

For triage with DIE, a typical Delphi exe is reported like this.

```
Compiler: Embarcadero Delphi (or Borland Delphi 7)
Linker: Turbo Linker
```

That's the first confirmation. When you see "Delphi", you know you need IDR, and you shouldn't waste time reading raw assembly in IDA.

In Strings, some strings show the VCL and the Borland runtime.

```
System
SysUtils
Classes
Vcl.Forms
TButton
TForm
Borland
```

Mixed in among them are the app's own strings (for example messages such as "Wrong password" or "Registration successful"). Each Delphi string has a few bytes of length and refcount in front of the text.

IDR analyzes the exe, recognizes a lot of VCL and RTL functions and gives them their standard names (`TStringList.Add`, `ShowMessage`, `UpperCase` and so on). It also reads the DFM from the resources and lists the forms with their event handlers, for example this.

```
TfrmMain
  btnOK: TButton      OnClick -> btnOKClick  @ 0x00451A20
  edtSerial: TEdit
  lblStatus: TLabel
```

Now you know the exact address of the function that runs when the user presses OK.

When importing into IDA, load the map or idc file exported by IDR. Before that, IDA may have had a few thousand `sub_` functions. After the import most of them carry VCL names, and what remains is a handful of unnamed functions, which are the author's code. That's where the real reversing starts, on a small number of functions instead of thousands.

Next, read `btnOKClick`. Inside you typically see the text being fetched from `edtSerial` through a VCL getter (`TControl.GetText` or similar), then a comparison with the expected value using `System.@LStrCmp` or a loop, and then a call to `ShowMessage` with the success string if it matches and the failure string if not. Remember the register calling convention: the first parameter is in EAX, the second in EDX and the third in ECX. When you see `@LStrCmp` comparing, the two strings are in EAX and EDX.

To find the valid condition, read up to the compare instruction and you see the expected value (or the transformation algorithm, if the crackme was built more carefully). With a simple Delphi crackme the correct serial is usually visible directly in the operand of `@LStrCmp`.

On the questions: starting from an event handler is faster because the `main` of a VCL app is only a message loop (`Application.Run`) and contains no logic, while the handler is where the real action happens. Delphi strings carry a length prefix and a refcount and are not null-terminated, so when searching in IDA you look for the text part, and when reading the length you look at the few bytes before the pointer. Without IDR you'd have to guess which functions are VCL through FLIRT or experience, which takes hours and is easy to get wrong, especially when you don't know the event handler names that would locate the logic.

</details>

