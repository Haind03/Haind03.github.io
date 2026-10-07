---
title: "Lesson 10.1: Reversing Delphi and C++Builder programs"
date: 2023-10-30 10:21:00 +0700
categories: ["Technique Reverse", "Part 10 · Legacy: Delphi, VB6, AutoIt, AHK"]
tags: [reverse-engineering, legacy]
render_with_liquid: false
---
One day you open an old exe in IDA, the decompiler spits out pseudocode but every function is `sub_xxx`, there isn't one familiar name, the strings have a length stuck in front of them, and thousands of functions from some framework flood the screen. Chances are you just met a Delphi binary. This is a kind of legacy program that's still alive and well in enterprise software, POS, Vietnamese accounting software, and quite a bit of malware. It isn't harder than C, just different, and it needs the right tools.

## What Delphi is, and why it's different

Delphi (along with its sibling C++Builder) uses the Borland compiler, now Embarcadero. The code is written in Object Pascal and compiled straight to native x86/x64, so at heart you're still reading plain assembly. But Delphi leaves a few very specific fingerprints that push reversing away from your C habits.

The first is the VCL framework (Visual Component Library). Almost every Delphi app drags in a whole forest of VCL functions for form management, buttons, strings, and streams. Like a statically linked libc in C, most of the code you see isn't the author's but the framework's, and filtering it out wins you half the battle.

The second is Pascal-style strings. Unlike C's null-terminated strings, Delphi strings (AnsiString, UnicodeString) have a length prefix, with the length and refcount sitting right before the data pointer. In IDA you see strings that don't end in `00` but have a few length bytes in front, and you need to know this to read them right.

The UI is stored as DFM (Delphi Form Module) inside the exe's resource section. The DFM describes each component and, importantly, the names of the event handlers (for example `Button1Click`), which makes it a gold mine for tracing the logic. Finally, Delphi defaults to the `register` calling convention (Borland's own fastcall), where the first three parameters go through EAX, EDX, ECX, different from the familiar cdecl/stdcall. Misread the convention and you misunderstand the parameters.

## Spotting Delphi in a minute

Drop the file into **Detect It Easy (DIE)**. It usually points straight at the compiler as Borland Delphi or Embarcadero, with the version. A few other signs give Delphi away too. You'll see the strings `Borland` or `Embarcadero` and unit names like `System`, `SysUtils`, `Classes`, `Vcl.Forms` in strings. The entry point calls a very characteristic runtime init function that sets up the VCL and calls `InitExe`. The resource section also has DFM blobs, where you'll see component names, `TForm`, `TButton`.

Once you confirm it's Delphi, don't rush into reading assembly in IDA. Get the right gear first.

## IDR: the helper you can't do without

The problem with plain IDA on Delphi is that it doesn't know those thousands of functions are VCL, so it leaves them as `sub_xxx` and you drown. **IDR (Interactive Delphi Reconstructor)** was built to solve exactly this. It recovers the names of known VCL/RTL functions, renaming them to things like `TStringList.Add` and `ShowMessage`, so you can skip them and focus on the author's code. It rebuilds the forms and event handlers from the DFM, so you see which address `Button1Click` lives at and know right away where the code runs when the user clicks a button. And it exports a map/idc to import back into IDA, turning the pile of `sub_xxx` into meaningful names.

The practical workflow: run IDR on the Delphi exe, let it analyze, export the helper file (for example .idc or .map), then load it into IDA. After this step your IDA is suddenly readable. **DeDe** is an older tool with the same idea, only good for very old Delphi, and these days I almost always pick IDR.

C++Builder is a bit more complicated because it mixes C++ (with name mangling, classes, vtables as in Part 4) with the Borland runtime, but the approach is similar: identify with DIE, use IDR for the VCL part, then apply your C++ knowledge to the rest.

## Start from event handlers, not from main

This is the most important tip of the lesson. With a C app you look for `main`. With a Delphi app that has a UI, `main` is just the VCL message loop, nothing interesting. The real logic lives in the **event handlers**: the user types a serial and clicks OK, so the `btnOKClick` function (or something with a similar name) is where the check happens.

Thanks to IDR rebuilding the forms, you know the names and addresses of the handlers. Jump straight to the handler of the relevant button and you're at the right place, skipping all the UI init code. If there are no names, search by message strings ("Wrong password", "Registration successful") and xref backwards, just like the habit from earlier parts, only remember that Delphi strings have a length prefix, so when searching, search for the text part and don't include the length byte.

## Key takeaways
Delphi/C++Builder is native x86/x64, but it drags in a forest of VCL functions and has its own fingerprints. Delphi strings have a length prefix and are not null-terminated, and the default calling convention is register (EAX, EDX, ECX for the first 3 parameters), so keep both in mind when reading and searching.

Identify with DIE, then use IDR to recover VCL names and rebuild forms and event handlers. Start from event handlers such as Button1Click rather than from main, because main is just the message loop.

## Lab
See [labs/10.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/10.1): identify a Delphi exe with DIE, use IDR to rebuild the forms and event handlers, then trace to the function that handles the OK button.
