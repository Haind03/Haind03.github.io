# Lab 9.2 - GraphQL security

App Flask + `graphql-core` tu chua, co lo hong CO Y, bind loopback `127.0.0.1:8072`. Chay local, KHONG deploy ra Internet.

## Lo hong
- **Introspection bat san**: ai cung tai duoc toan bo schema qua `__schema` / `__type`.
- **Thieu field-level authorization**: field nhay cam `apiKey`, `ssn` tra ve cho bat ky ai hoi.
- **Mutation khong kiem quyen**: `promoteUser` ai goi cung chay.
- **Khong gioi han do sau / so luong**: query long nhau va alias batching khuech dai chi phi (DoS).

## Chay
```bash
pip install flask graphql-core requests     # neu chua co
python3 app.py                                # server len cong 8072
python3 exploit.py                            # terminal khac
```

Thu tay:
```bash
curl -s localhost:8072/graphql -H 'Content-Type: application/json' \
  -d '{"query":"query{ user(id:\"1\"){ username apiKey ssn } }"}'
```

## Kich ban khai thac
1. Gui introspection query -> liet ke type/field/mutation -> phat hien `apiKey`, `ssn`, mutation `promoteUser`.
2. Truy van thang `user(id:"1"){ apiKey }` -> lo flag (khong co field-level authz).
3. Goi `mutation { promoteUser(id:"2") }` bang client thuong -> flag (mutation khong kiem quyen).
4. Query long 5 tang (`author <-> posts`) va alias batching 12 lan -> minh hoa khuech dai chi phi.

## Ket qua
- `FLAG{9.2_graphql_introspection_hidden_field}` (field `apiKey` cua admin)
- `FLAG{9.2_graphql_mutation_no_authz}` (mutation `promoteUser`)

Xem `transcript.txt`.

## Vá
- Tat introspection o production; dung persisted queries / allowlist.
- Kiem quyen o TUNG resolver (ca field nhay cam lan mutation), khong chi o lop vao.
- Gioi han do sau (depth limit), do phuc tap (query complexity/cost), va rate limit.
