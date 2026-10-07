rule FakeBot_Demo
{
    meta:
        description = "Demo rule recognizing a simulated FakeBot sample (for learning only)"
        author = "blog Reverse Engineering"
        date = "2026-10-06"
        reference = "lab 19.2"

    strings:
        $mutex   = "Global\\FakeBot_Mutex_v1" ascii
        $c2      = "http://c2.example-fakebot.test/gate.php" ascii
        $ua      = "Mozilla/5.0 (FakeBot; Win64)" ascii
        $key     = { 52 43 34 4B 65 79 31 32 33 }   // "RC4Key123"
        $pdb     = "fakebot\\release\\bot.pdb" ascii nocase

    condition:
        uint16(0) == 0x5A4D and          // MZ, only scan PE files
        3 of ($mutex, $c2, $ua, $key, $pdb)
}
