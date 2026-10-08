---
title: "Lesson 19.3: Analyzing maldocs and loaders"
image:
  path: /assets/img/covers/re-19-3-analyzing-maldocs-loaders-where-attack-begins.webp
  alt: "Lesson 19.3: Analyzing maldocs and loaders"
date: 2023-10-27 16:21:00 +0700
categories: ["Reverse Engineering", "Part 19 · Malware Analysis Basics"]
tags: [reverse-engineering, malware]
render_with_liquid: false
---
Most infections don't start with an `.exe` thrown at the victim. They start with something that looks harmless, such as a Word file attached to an email, a PDF invoice, a `.lnk` shortcut pretending to be a folder. These aren't the real malware, they're loaders, and their only job is to pull down the next-stage payload and run it. If you can reverse this step you stop the attack at the start, so the blue team does this every day.

The whole lesson is from the defensive side. We analyze to understand and detect, every example is benign and runs in an isolated lab (see [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/)).

## Four common types of loader

Before taking it apart, know what you're holding. Use `file`, read the magic, look at the real extension. The four types are Office macros in `.doc/.docm/.xls/.xlsm` (embedded VBA that runs automatically on open), malicious PDFs (embedded JavaScript or a launch action calling an external command), malicious LNKs (a shortcut hiding a long command line in the arguments field), and script loaders (PowerShell, JS, HTA, VBS, usually obfuscated in many layers).

All four follow the same pattern, which is a lure (the file the user opens) that triggers a chain of hidden commands, and that chain downloads the real payload. Your job is to unpack it layer by layer until you see the URL or the next-stage payload.

## Office macros

A modern Office file (`.docx`) is a ZIP containing XML. The macro-enabled version (`.docm`, or the old OLE-style `.doc`) embeds VBA. The main toolset is oletools (Python):

```
olevba sample.doc        # extract all the VBA macros as text
oleid sample.doc         # summary of suspicious indicators
mraptor sample.doc       # score how likely it is malicious (auto-exec + write + execute)
```

When reading a macro, look for three things. The first is auto-exec triggers, such as `AutoOpen`, `Document_Open`, `Workbook_Open`, `AutoClose`. These functions run when the file opens, without the user clicking anything, and olevba flags them. The second is obfuscated strings. Authors often concatenate strings (`"po" & "wer" & "shell"`), use `Chr()` for each character, or base64, and olevba has a flag to extract these strings. The third is external execution, such as `Shell`, `CreateObject("WScript.Shell").Run`, `WMI`, usually ending in a `powershell` call that downloads a payload.

olevba can also decode some common encodings in its output. Custom obfuscation you have to undo yourself. Copy the VBA out, replace `Shell`/`Run` with a print command (or translate it to Python) to get the final string without executing it.

## Malicious PDF

A PDF is a series of numbered objects linked by a cross-reference table. The dangerous parts are embedded JavaScript (`/JS`, `/JavaScript`), which runs on open and usually exploits a reader vulnerability or decodes a payload, launch actions (`/Launch`, `/OpenAction`, `/AA`), which call an external program, and embedded files (`/EmbeddedFile`), which hide a payload inside the PDF.

The tools are pdf-parser (lists objects, filters by keyword) and peepdf:

```
pdf-parser.py --stats sample.pdf          # stats on object types
pdf-parser.py --search JavaScript sample.pdf
pdf-parser.py --object 12 --filter sample.pdf   # decode the stream of object 12
```

Find which object `/OpenAction` points to, open that object, decode the stream (many streams are FlateDecode compressed so you need `--filter`), read the JavaScript, and decode further if it's encoded.

## Malicious LNK

A `.lnk` file is a Windows shortcut, but its target and arguments fields can hold a long command line that the user doesn't see (Explorer truncates the displayed part). Attackers put a whole PowerShell command in there, with an icon that pretends to be a PDF or folder.

Analyze with lnkparse (Python) or LECmd (Eric Zimmerman):

```
lnkparse sample.lnk      # print target, arguments, working dir, icon
```

Look at `arguments`. If you see `powershell -enc ...` or `cmd /c ... & start ...` it's a loader. The string inside is often base64, so continue with the next section.

## Script loaders and unpacking obfuscation layers

Whether it came through a macro, PDF or LNK, the end is almost always a script hidden in many layers. The most common pattern is PowerShell with `-EncodedCommand` (or `-enc`), where the parameter after it is a base64 UTF-16LE string.

Unpack it layer by layer. Decode each layer and read it, and never execute. Common layers are base64 (PowerShell's encoded command uses UTF-16LE, different from plain base64), gzip/deflate compression inside base64, XOR with a small key, and tricks like `-join`, `Reverse`, character replace and format strings.

`IEX` (Invoke-Expression), `DownloadString`, `DownloadFile`, `New-Object Net.WebClient` and `Start-BitsTransfer` mean you're close to the payload URL. Replace `IEX` with `Write-Output` (or copy it to Python) to print the next layer instead of running it.

Example of unpacking one layer of UTF-16LE base64 with Python (safe, only prints):

```python
import base64
enc = "VwByAGkAdABlAC0ASABvAHMAdAAg..."   # the string after -enc
print(base64.b64decode(enc).decode("utf-16-le"))
```

If the inner layer is base64 + gzip:

```python
import base64, gzip
print(gzip.decompress(base64.b64decode(enc)).decode())
```

Lab `19.3` has benign sample strings to practice these two patterns.

## A short workflow

```
1. Identify the file type (file, magic, real extension)
2. Extract the executable part:
     macro -> olevba        PDF -> pdf-parser/peepdf
     LNK   -> lnkparse      script -> open in an editor
3. Unpack obfuscation layer by layer (decode, do NOT execute)
4. Find next-stage IOCs: URL, IP, payload file name, mutex
5. Record the IOCs and write detection rules (YARA/Sigma, see Lesson 19.2)
```

At the end of the chain you want the payload download URL and how it runs the payload. With those two you can block and trace, and you don't need to touch the next-stage payload yet.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 19.3</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/19.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/19.3/src/benign_macro.vba" download><i class="fa-solid fa-download"></i>src/benign_macro.vba</a>
<a class="lab-file" href="/assets/labs/19.3/src/decode_layers.py" download><i class="fa-solid fa-download"></i>src/decode_layers.py</a>
<a class="lab-file" href="/assets/labs/19.3/src/stage1_encoded.txt" download><i class="fa-solid fa-download"></i>src/stage1_encoded.txt</a>
<a class="lab-file" href="/assets/labs/19.3/src/stage2_gzip_b64.txt" download><i class="fa-solid fa-download"></i>src/stage2_gzip_b64.txt</a>
</div>
</div>

The goal of this lab is to practice stripping away a loader's obfuscation without ever executing it. Every sample here is harmless (it only prints text), but the point is to build the habit, which is to decode and read and never run. You need Python 3, and optionally `pip install oletools` if you want to try `olevba` on a macro. If you later move on to a real sample, do it in an isolated lab as covered in Lesson 0.3.

There are four files. `stage1_encoded.txt` holds a string shaped like a `powershell -EncodedCommand` argument (base64 over UTF-16LE). `stage2_gzip_b64.txt` holds a base64-wrapped gzip pattern, the kind a multi-stage loader uses. `benign_macro.vba` is a harmless macro that mimics the structure of a real maldoc (an AutoOpen trigger, a string split into pieces). `decode_layers.py` is a reference script that decodes both encoded strings (it only prints, it never executes anything).

Start with `stage1_encoded.txt`. It's the argument that would follow `-enc`. Decode it by hand. Base64 decode it, then decode the result as UTF-16LE. What's the real command? Then work out why you decode as UTF-16LE and not UTF-8, and try decoding as UTF-8 to see what goes wrong.

Next open `stage2_gzip_b64.txt` and recognize the gzip magic (`1f 8b`) once you base64 decode it, then finish decoding with gzip to get the command. Read `benign_macro.vba` and point out which part is the auto-exec trigger, which part is the string split apart to hide it, and where in a real maldoc the payload-downloading command would sit. If you have oletools installed, put this macro into an Office file (or use a known-safe sample) and run `olevba` to see how it flags AutoOpen. Finally check your work against the reference script by running `decode_layers.py`.

Two questions to think about. If you came across `IEX (New-Object Net.WebClient).DownloadString('http://...')`, what would you replace `IEX` with to get the content of the next stage without running it? And why do loaders like to nest several layers of encoding instead of just one? Try it yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

To decode the first stage:

```python
import base64
enc = "VwByAGkAdABlAC0ASABvAHMAdAAg...ACcA"   # see stage1_encoded.txt
print(base64.b64decode(enc).decode("utf-16-le"))
```

The result is this.

```
Write-Host 'Hello from a benign decoded payload'
```

The real command just prints a line of text. In a real maldoc, this spot would hold a call to `DownloadString` or `DownloadFile`.

On why UTF-16LE, PowerShell's `-EncodedCommand` specifies that the string is UTF-16LE before it gets base64 encoded. If you decode it as UTF-8 instead, every ASCII character is interleaved with a `00` byte, so you get a string with scattered spaces like `W r i t e - H o s t`. Letters separated by null bytes like that mean you need to switch to UTF-16LE.

For the second stage, base64 decoding `stage2_gzip_b64.txt` gives a result whose first two bytes are `1f 8b`, the gzip magic. Finishing the decode:

```python
import base64, gzip
print(gzip.decompress(base64.b64decode(b64)).decode())
```

The result is this.

```
Write-Host 'Stage 2 reached, still benign'
```

In the macro `benign_macro.vba`, the auto-exec trigger is `Sub AutoOpen()` (and `Document_Open`), which runs as soon as the file is opened, with no user click needed, and olevba always flags these functions as AutoExec. The hidden string is `a = "Hel" & "lo" & Chr(32) & "Ana" & "lyst"`, pieces joined together with `Chr(32)` standing in for a space to dodge a plain grep, which reassembles into `Hello Analyst`. The spot that would hold the payload in a real maldoc is marked by a comment, where you'd expect something like `CreateObject("WScript.Shell").Run "powershell -enc ..."`. The lab leaves it blank on purpose, for safety.

With oletools installed, running `olevba benign.doc` lists the macros and marks the Type column as `AutoExec` for `AutoOpen` and `Document_Open`, with the Keyword column flagging `Chr` and `MsgBox`. On a real maldoc it would also flag `Shell`, `Run`, `powershell`, and extract any base64 string it recognizes.

Checking everything with the reference script gives this.

```
$ python3 decode_layers.py
[Stage 1: base64 UTF-16LE]
  -> Write-Host 'Hello from a benign decoded payload'

[Stage 2: base64 + gzip]
  -> Write-Host 'Stage 2 reached, still benign'

Both are harmless commands that only print text.
```

On the questions, you would replace `IEX` (or `Invoke-Expression`, or `.Invoke()`) with `Write-Output` (or copy the string over to Python and `print` it). That way the next stage gets printed instead of executed, and you can read the URL or payload without getting infected. Loaders nest several layers because each layer gets past one layer of detection (an antivirus scanning strings, an EDR scanning commands), and it costs an analyst more effort to unpack. For us it's the same decode step repeated until the layers run out.

</details>

## Key takeaways
A loader (maldoc, LNK or script) is different from a payload. It only pulls the payload down, and taking it apart stops things early. For macros, extract with olevba and look for AutoOpen/Document_Open, obfuscated strings and Shell/Run. For PDFs, use pdf-parser or peepdf, inspect /OpenAction, /JS and /Launch, and decode FlateDecode streams. For LNKs, read the arguments with lnkparse, since the real command is hidden there.

For scripts, unpack layer by layer (base64 UTF-16LE, gzip, XOR), replace IEX with a print, and don't run it. Always work in an isolated lab, because the goal is to get the next-stage URL and IOCs.

## Common pitfalls
One is forgetting that PowerShell `-enc` uses UTF-16LE and not UTF-8, so plain base64 decoding gives letters with gaps between them. Another is accidentally running the script when trying it quickly, so always replace execute with print. The last is stopping at the first layer, since many loaders nest three or four layers before the URL shows up.

## Further reading
The oletools docs (decalage.info) and didierstevens.com (pdf-parser, base64dump) are good places to start. CyberChef is useful for quickly unpacking many encoding layers with a drag-and-drop interface (see the [tool resources](/posts/re-resources-reverse-engineering-tool-repository-roundup/) post).
