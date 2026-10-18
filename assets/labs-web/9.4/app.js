#!/usr/bin/env node
/*
 * Lab 9.4 - Prototype pollution trong Node.js.
 *
 * App co lo hong CO Y de hoc (chi dung module built-in, khong can npm):
 *   - Ham merge() deep-merge KHONG loc key nguy hiem (__proto__,
 *     constructor, prototype). Request /api/profile cho phep gui JSON
 *     tuy y de merge -> doc duoc Object.prototype (prototype pollution).
 *   - Gadget 1 (doi hanh vi / leo quyen): /api/whoami tao object user moi
 *     chi set username. No kiem tra user.isAdmin. Binh thuong isAdmin
 *     khong he duoc set => false. Sau khi o nhiem __proto__.isAdmin=true,
 *     MOI object moi deu co isAdmin=true => bypass kiem tra quyen.
 *   - Gadget 2 (RCE): /api/export doc config.preprocess (lenh tien xu ly).
 *     Field nay app KHONG bao gio cho user set qua form. Nhung sau khi
 *     o nhiem __proto__.preprocess="<lenh>", config.preprocess tro thanh
 *     lenh do => execSync chay lenh cua ke tan cong.
 *
 * CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
 */
"use strict";
const http = require("http");
const { execSync } = require("child_process");

const PORT = 8075;

// Deep-merge CO LO HONG: khong chan __proto__ / constructor / prototype.
function merge(target, source) {
  for (const key in source) {
    const val = source[key];
    if (val && typeof val === "object") {
      if (!(key in target) || typeof target[key] !== "object") target[key] = {};
      merge(target[key], val);
    } else {
      target[key] = val;
    }
  }
  return target;
}

function readJson(req) {
  return new Promise((resolve) => {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", () => {
      try { resolve(JSON.parse(body || "{}")); }
      catch (e) { resolve({}); }
    });
  });
}

function send(res, code, obj) {
  const s = JSON.stringify(obj);
  res.writeHead(code, { "Content-Type": "application/json" });
  res.end(s);
}

const server = http.createServer(async (req, res) => {
  const url = req.url.split("?")[0];

  if (req.method === "POST" && url === "/api/profile") {
    // Nguoi dung cap nhat profile: merge JSON tuy y vao object settings.
    const input = await readJson(req);
    const settings = {}; // object moi moi request
    merge(settings, input); // LO HONG: __proto__ trong input -> o nhiem global
    return send(res, 200, { ok: true, settings });
  }

  if (url === "/api/whoami") {
    // Tao user moi, CHI set username. isAdmin KHONG duoc set o day.
    const user = { username: "guest" };
    // GADGET 1: kiem tra quyen dua vao thuoc tinh co the bi o nhiem.
    if (user.isAdmin === true) {
      return send(res, 200, {
        username: user.username,
        isAdmin: true,
        flag: "FLAG{9.4_prototype_pollution_priv_esc}",
        note: "object user moi tu nhien co isAdmin=true do Object.prototype bi o nhiem",
      });
    }
    return send(res, 200, { username: user.username, isAdmin: false });
  }

  if (req.method === "POST" && url === "/api/export") {
    // Xuat bao cao. Config duoc gop tu mac dinh (chi own props).
    const DEFAULTS = { format: "pdf" };
    const config = Object.assign({}, DEFAULTS);
    let preprocessOutput = null;
    // GADGET 2: app doc config.preprocess de chay lenh tien xu ly.
    // User khong he gui field nay; no den tu Object.prototype bi o nhiem.
    if (config.preprocess) {
      try {
        preprocessOutput = execSync(config.preprocess).toString().trim();
      } catch (e) {
        preprocessOutput = "error: " + e.message;
      }
    }
    return send(res, 200, {
      ok: true,
      format: config.format,
      preprocess_ran: config.preprocess || null,
      preprocess_output: preprocessOutput,
      flag: preprocessOutput ? "FLAG{9.4_prototype_pollution_to_rce}" : null,
    });
  }

  if (url === "/") {
    res.writeHead(200, { "Content-Type": "text/plain" });
    return res.end(
      "Lab 9.4 prototype pollution.\n" +
      "POST /api/profile {json}  -> merge (dinh __proto__)\n" +
      "GET  /api/whoami          -> kiem tra isAdmin\n" +
      "POST /api/export          -> doc config.preprocess (RCE gadget)\n"
    );
  }

  send(res, 404, { error: "not found" });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log("lab 9.4 listening on http://127.0.0.1:" + PORT);
});
