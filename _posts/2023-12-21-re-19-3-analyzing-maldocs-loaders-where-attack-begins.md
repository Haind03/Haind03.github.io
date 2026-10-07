---
title: "Lesson 19.3: Analyzing maldocs and loaders, where the attack begins"
date: 2023-12-21 23:48:00 +0700
categories: ["Technique Reverse", "Part 19 · Malware Analysis Basics"]
tags: [reverse-engineering, malware]
render_with_liquid: false
---
Most infections don't start with an `.exe` slapped in the victim's face. They start with something that looks harmless: a Word file attached to an email, a PDF invoice, a `.lnk` shortcut pretending to be a folder. These aren't the real malware, they're loaders, and their only job is to pull down the next-stage payload and run it. If you can reverse this step you stop the attack at the root, so this is a skill the blue team uses every day.

This whole lesson is from the defensive angle: we analyze to understand and detect, every example is benign and runs in an isolated lab (see [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/)).

## Four common types of loader

Before taking it apart, know what you're holding. Use `file`, read the magic, look at the real extension. The four types are Office macros in `.doc/.docm/.xls/.xlsm` (embedded VBA that runs automatically on open), malicious PDFs (embedded JavaScript or a launch action calling an external command), malicious LNKs (a shortcut hiding a long command line in the arguments field), and script loaders (PowerShell, JS, HTA, VBS, usually obfuscated in many layers).

All four share one mold: a lure (the file the user opens) that pulls in a chain of hidden commands, and that chain downloads the real payload. Your job is to peel layer by layer until you see the URL or the next-stage payload.

## Office macro, the classic

A modern Office file (`.docx`) is a ZIP containing XML. But the macro-enabled version (`.docm`, or the old OLE-style `.doc`) embeds VBA. The number one toolset is oletools (Python):

```
olevba sample.doc        # extract all the VBA macros as text
oleid sample.doc         # summary of suspicious indicators
mraptor sample.doc       # score how likely it is malicious (auto-exec + write + execute)
```

When reading a macro, look for three things. The first is auto-exec triggers: `AutoOpen`, `Document_Open`, `Workbook_Open`, `AutoClose`. These are functions that run right when the file opens without the user clicking anything, and olevba flags them for you. The second is obfuscated strings. Authors often concatenate strings (`"po" & "wer" & "shell"`), use `Chr()` for each character, or base64, and olevba has a flag to extract these strings. The third is external execution: `Shell`, `CreateObject("WScript.Shell").Run`, `WMI`, usually ending in a `powershell` call that downloads a payload.

Tip: olevba can also decode some common encodings right in its output. But custom obfuscation you have to undo yourself: copy the VBA out, replace `Shell`/`Run` with a print command (or translate it to Python) to get the final string without executing it.

## Malicious PDF

A PDF is a series of numbered objects linked by a cross-reference table. The dangerous parts are embedded JavaScript (`/JS`, `/JavaScript`), which runs on open and usually exploits a reader vulnerability or decodes a payload, launch actions (`/Launch`, `/OpenAction`, `/AA`), which call an external program, and embedded files (`/EmbeddedFile`), which hide a payload right inside the PDF.

The tools are pdf-parser (lists objects, filters by keyword) and peepdf:

```
pdf-parser.py --stats sample.pdf          # stats on object types
pdf-parser.py --search JavaScript sample.pdf
pdf-parser.py --object 12 --filter sample.pdf   # decode the stream of object 12
```

The process is to find which object `/OpenAction` points to, open that object, decode the stream (many streams are FlateDecode compressed so you need `--filter`), read the JavaScript, and decode further if it's encoded.

## Malicious LNK

A `.lnk` file is a Windows shortcut, but its target and arguments fields can hold a long command line that the user doesn't see (Explorer truncates the displayed part). Attackers stuff an entire PowerShell command in there, with an icon pretending to be a PDF or folder.

Analyze with lnkparse (Python) or LECmd (Eric Zimmerman):

```
lnkparse sample.lnk      # print target, arguments, working dir, icon
```

Look at `arguments`: if you see `powershell -enc ...` or `cmd /c ... & start ...` it's clearly a loader. The string inside is often base64, so continue unpacking following the next section.

## Script loaders and unpacking obfuscation layer by layer

Whether it came through a macro, PDF or LNK, the end point is almost always a script hidden in many layers. The most common pattern is PowerShell with `-EncodedCommand` (or `-enc`): the parameter after it is a base64'd UTF-16LE string.

The unpacking principle is to peel layer by layer, decode each layer and read it, and never execute. The common layers are base64 (PowerShell's encoded command uses UTF-16LE, different from plain base64), gzip/deflate compression inside base64, XOR with a small key, and tricks like `-join`, `Reverse`, character replace and format strings.

Seeing `IEX` (Invoke-Expression), `DownloadString`, `DownloadFile`, `New-Object Net.WebClient`, `Start-BitsTransfer` means you're getting close to the payload URL. Replace `IEX` with `Write-Output` (or copy it to Python) to print the next layer instead of running it.

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

Lab [19.3](https://github.com/Haind03/Technique-Reverse/tree/main/labs/19.3) has benign sample strings for you to practice exactly these two patterns.

## A compact workflow

```
1. Identify the file type (file, magic, real extension)
2. Extract the executable part:
     macro -> olevba        PDF -> pdf-parser/peepdf
     LNK   -> lnkparse      script -> open in an editor
3. Unpack obfuscation layer by layer (decode, do NOT execute)
4. Find next-stage IOCs: URL, IP, payload file name, mutex
5. Record the IOCs and write detection rules (YARA/Sigma, see Lesson 19.2)
```

What you're hunting at the end of the chain is the payload download URL and how it runs that payload. Having these two is enough to block and trace, you don't need to touch the next-stage payload yet.

## Key takeaways
A loader (maldoc, LNK or script) differs from a payload: it only pulls the payload down, and taking it apart stops things at the root. For macros, extract with olevba and look for AutoOpen/Document_Open, obfuscated strings and Shell/Run. For PDFs, use pdf-parser or peepdf, inspect /OpenAction, /JS and /Launch, and decode FlateDecode streams. For LNKs, read the arguments with lnkparse, since the real command is hidden there.

For scripts, unpack layer by layer (base64 UTF-16LE, gzip, XOR), replace IEX with a print, and don't run it. Always work in an isolated lab, because the goal is to get the next-stage URL and IOCs.

## Common pitfalls
One is forgetting that PowerShell `-enc` uses UTF-16LE and not UTF-8, so plain base64 decoding gives letters with gaps between them. Another is accidentally running the script when "trying it quickly", so always replace execute with print. The last is stopping at the first layer, since many loaders nest three or four layers before the URL shows up.

## Further reading
The oletools docs (decalage.info) and didierstevens.com (pdf-parser, base64dump) are good places to start. CyberChef is great for quickly unpacking many encoding layers with a drag-and-drop interface (see the [tool resources](/posts/re-resources-reverse-engineering-tool-repository-roundup/) post).
