<?php
// Lab 7.2 - xu ly upload (co y de lo hong)
// LOI: chi tin Content-Type do client gui ($_FILES['type']), khong kiem duoi file,
// khong kiem noi dung, luu nguyen ten vao thu muc web chay duoc PHP.

if ($_SERVER['REQUEST_METHOD'] !== 'POST' || !isset($_FILES['file'])) {
    http_response_code(400);
    echo "Thieu file.";
    exit;
}

$f = $_FILES['file'];
$clientType = $f['type']; // <-- do TRINH DUYET/CLIENT gui, ke tan cong tu dat duoc

// "Kiem tra" duy nhat: MIME phia client phai la anh
if (strpos($clientType, 'image/') !== 0) {
    http_response_code(400);
    echo "Chi cho phep anh. Content-Type nhan duoc: " . htmlspecialchars($clientType);
    exit;
}

$name = basename($f['name']);                 // giu nguyen ten goc (ke ca .php)
$dest = __DIR__ . '/uploads/' . $name;        // thu muc nay web truy cap + chay PHP duoc
if (!move_uploaded_file($f['tmp_name'], $dest)) {
    http_response_code(500);
    echo "Loi luu file.";
    exit;
}

echo "Tai len thanh cong: /uploads/" . htmlspecialchars($name) . "\n";
echo "Content-Type (client khai bao): " . htmlspecialchars($clientType) . "\n";
