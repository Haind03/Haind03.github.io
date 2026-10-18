<?php
// Lab 7.3 - LFI leo thang RCE (co y de lo hong)
// Mini CMS: chon "trang" de hien thi. LOI: include thang tham so nguoi dung.
// Ngoai ra ghi User-Agent moi request vao logs/access.log => phuc vu log poisoning.

$log = __DIR__ . '/../logs/access.log';
@file_put_contents(
    $log,
    date('c') . ' UA=' . ($_SERVER['HTTP_USER_AGENT'] ?? '-') . "\n",
    FILE_APPEND
);

$page = isset($_GET['page']) ? $_GET['page'] : 'pages/home.php';

echo "<!doctype html><meta charset=utf-8><title>Mini CMS</title>";
echo "<h1>Mini CMS</h1>";
echo "<p>Dang xem: " . htmlspecialchars($page) . "</p><hr>";

// LOI CHET NGUOI: include truc tiep chuoi nguoi dung dieu khien
include($page);
