# Lab 9.4 - Prototype pollution (Node.js)

App Node.js tu chua (chi dung module built-in `http`, `child_process`, khong can `npm install`), co lo hong CO Y, bind loopback `127.0.0.1:8075`. Chay local, KHONG deploy ra Internet.

## Lo hong
- Ham `merge()` deep-merge KHONG loc key nguy hiem (`__proto__`, `constructor`, `prototype`). `POST /api/profile` nhan JSON tuy y -> o nhiem `Object.prototype` (prototype pollution).
- **Gadget 1 (leo quyen / doi hanh vi)**: `/api/whoami` tao object user moi, chi set `username`, roi kiem tra `user.isAdmin`. Sau khi o nhiem `__proto__.isAdmin=true`, MOI object moi deu co `isAdmin=true`.
- **Gadget 2 (RCE)**: `/api/export` doc `config.preprocess` (lenh tien xu ly) ma user khong he gui. Sau khi o nhiem `__proto__.preprocess="<lenh>"`, app `execSync` lenh cua ke tan cong.

## Chay
```bash
node app.js             # server len cong 8075 (Node 18+/20)
node exploit.js         # terminal khac
```

## Kich ban khai thac
1. Baseline: `GET /api/whoami` -> `isAdmin=false`.
2. O nhiem: `POST /api/profile` voi body raw `{"__proto__":{"isAdmin":true,"preprocess":"id"}}`.
3. Doi hanh vi: `GET /api/whoami` -> gio `isAdmin=true` + flag.
4. RCE: `POST /api/export` -> app doc `config.preprocess` bi o nhiem va chay lenh `id` -> output that + flag.

## Ket qua
- `FLAG{9.4_prototype_pollution_priv_esc}` (leo quyen)
- `FLAG{9.4_prototype_pollution_to_rce}` (RCE qua gadget config)

Xem `transcript.txt` (co output lenh `id` that tren may).

## Vá
- Chan key `__proto__` / `constructor` / `prototype` trong merge; dung `Object.create(null)`, `Map`, hoac thu vien an toan (`structuredClone`, `lodash.merge` ban da va).
- Dung `Object.freeze(Object.prototype)` neu phu hop.
- Khong doc option/config dieu khien hanh vi nhay cam (lenh, duong dan) tu object co the bi o nhiem prototype.
