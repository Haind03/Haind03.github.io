#!/usr/bin/env python3
"""
Lab 9.2 - GraphQL security.

Dung graphql-core (ban Python cua GraphQL) + Flask.

App co lo hong CO Y de hoc:
  - Introspection BAT san: ai cung tai duoc toan bo schema (type, field,
    mutation) qua query __schema / __type.
  - Field nhay cam KHONG co field-level authorization: apiKey, ssn tra ve
    cho bat ky ai hoi, mien la biet ten field (lo nho introspection).
  - Mutation promoteUser KHONG kiem tra quyen: user thuong goi duoc.
  - KHONG gioi han do sau / so luong truy van -> query long nhau va alias
    batching khuech dai chi phi (DoS).

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
from flask import Flask, request, jsonify
from graphql import build_schema, graphql_sync

app = Flask(__name__)
PORT = 8072

SDL = """
type User {
  id: ID!
  username: String!
  email: String
  isAdmin: Boolean
  apiKey: String
  ssn: String
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
  body: String
  author: User!
}

type PromoteResult {
  ok: Boolean!
  message: String
  flag: String
}

type Query {
  me: User
  user(id: ID!): User
  posts: [Post!]!
}

type Mutation {
  promoteUser(id: ID!): PromoteResult!
}

schema { query: Query, mutation: Mutation }
"""

schema = build_schema(SDL)

# "CSDL" trong bo nho. Xay user truoc, post tham chieu user, roi gan nguoc.
USERS = {
    1: {
        "id": "1", "username": "admin", "email": "admin@shop.local",
        "isAdmin": True,
        # Field nhay cam: UI binh thuong khong bao gio hoi toi, chi lo qua
        # introspection roi truy van truc tiep.
        "apiKey": "FLAG{9.2_graphql_introspection_hidden_field}",
        "ssn": "999-99-9999",
    },
    2: {
        "id": "2", "username": "alice", "email": "alice@shop.local",
        "isAdmin": False, "apiKey": "ak_alice_normal", "ssn": "002-22-2222",
    },
}

POSTS = [
    {"id": "p1", "title": "Chao mung", "body": "bai viet cong khai",
     "author": USERS[2]},
    {"id": "p2", "title": "Lo trinh noi bo", "body": "ke hoach bi mat",
     "author": USERS[1]},
]

# Gan nguoc posts cho moi user (tao vong tham chieu de minh hoa query long nhau).
for u in USERS.values():
    u["posts"] = [p for p in POSTS if p["author"]["id"] == u["id"]]


def resolve_me(info):
    # Nguoi dung hien tai gia lap la alice (user thuong, isAdmin=False).
    return USERS[2]


def resolve_user(info, id):
    return USERS.get(int(id))


def resolve_posts(info):
    return POSTS


def resolve_promote(info, id):
    # LO HONG: khong kiem tra quyen admin truoc khi nang quyen.
    uid = int(id)
    if uid in USERS:
        USERS[uid]["isAdmin"] = True
    return {
        "ok": True,
        "message": "user %s da duoc nang quyen (KHONG kiem tra authorization)" % id,
        "flag": "FLAG{9.2_graphql_mutation_no_authz}",
    }


ROOT = {
    "me": resolve_me,
    "user": resolve_user,
    "posts": resolve_posts,
    "promoteUser": resolve_promote,
}


@app.route("/")
def index():
    return (
        "Lab 9.2 GraphQL. POST /graphql JSON {query, variables}.\n"
        "Introspection dang BAT. Thu query __schema de xem toan bo schema.\n"
    )


@app.route("/graphql", methods=["POST"])
def graphql_endpoint():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "")
    variables = data.get("variables")
    op = data.get("operationName")
    # LO HONG: introspection khong bi tat, khong co depth/complexity limit.
    result = graphql_sync(schema, query, root_value=ROOT,
                          variable_values=variables, operation_name=op)
    out = {}
    if result.errors:
        out["errors"] = [str(e) for e in result.errors]
    out["data"] = result.data
    return jsonify(out)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
