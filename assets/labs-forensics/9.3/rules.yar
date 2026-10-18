rule LAB_marker_weak
{
    meta:
        author = "TechForensics lab 9.3"
        description = "Rule YEU: mot chuoi pho bien duy nhat - de false positive va de ne"
    strings:
        $w = "malware" ascii nocase
    condition:
        $w
}

rule LAB_BADGER_strong
{
    meta:
        author = "TechForensics lab 9.3"
        description = "Rule MANH cho ho BADGER: magic + marker hiem + nhom API, it false positive"
        reference = "ho gia lap BADGER de day hoc"
    strings:
        $mutex = "Global\\LAB_BADGER_" ascii          // chuoi manh, rat hiem
        $c2    = "evil-tunnel.test" ascii              // ha tang C2
        $cfg   = "C2=http://" ascii                    // dinh dang cau hinh
        $api1  = "CreateRemoteThread" ascii            // nhom API yeu (pho bien)
        $api2  = "VirtualAllocEx" ascii
        $api3  = "WriteProcessMemory" ascii
    condition:
        uint16(0) == 0x5A4D          // magic MZ, giam false positive + quet nhanh
        and filesize < 1MB
        and $mutex                   // mot chuoi manh la du
        and ($c2 or $cfg)            // kem bang chung cau hinh C2
        and 2 of ($api*)             // nhom chuoi yeu: can it nhat 2
}
