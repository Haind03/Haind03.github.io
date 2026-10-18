---
title: "ASEAN Student Contest 2024: third prize in Attack-Defense"
image:
  path: /assets/img/covers/ctf-asean-2024-attack-defense.webp
  alt: "ASEAN Student Contest 2024: third prize in Attack-Defense"
date: 2024-10-19 21:00:00 +0700
categories: ["CTF Journey"]
tags: [ctf, attack-defense, asean, ptit]
render_with_liquid: false
---

On October 19, 2024 I played the Attack-Defense final of the 17th ASEAN Student Contest on Information Security, held at the Military Technical Academy in Hanoi, with team PTIT.Celebi. We finished sixth on the board and took third prize. PTIT's other team took third in the Jeopardy bracket the same day.

![PTIT's two teams on stage with their third prizes and the ISP flag](/assets/img/posts/asean-2024/ptit-teams.webp)
_The two PTIT teams at the awards ceremony._

This was my second A&D final. In [the first one, in 2023](/posts/ctf-asean-2023-first-attack-defense/) our services stayed up but we patched too slowly and leaked a lot of flags, so for 2024 the whole team prepared differently. We practiced together most weekends through the year, playing events off CTFtime, and we put real work into defense this time, reading up on EDR tooling so we could actually watch our own services during the game and react when something looked wrong instead of noticing a leak after the fact.

The plan survived about the first five minutes. The organizer infrastructure kept dropping, and the first thing we found when we got in was that we did not have root on our boxes, which quietly killed half of the defensive setup we had rehearsed. There were only two web services this year, Linkextractor 2.0 and pepeviewer, and only one of us focused on web, so we leaned on each other and improvised.

![The Attack-Defense final scoreboard, with PTIT.Celebi highlighted in sixth place](/assets/img/posts/asean-2024/scoreboard.webp)
_Final board. PTIT.Celebi is 6th with 6,812.92 points._

At least the rhythm was familiar this time. You cannot only attack or only defend. Pour everything into stealing flags and your own services keep leaking, sit on defense and your score never moves, so it is a constant loop of reading logs, firing payloads, and patching source without taking the service down.

My favorite memory of the day is small and stupid. We had an exploit chain working against Linkextractor, but the service hands the flag back rendered inside an image, so we were pulling it out with OCR. The OCR kept confusing `0` and `O`. In a flag that has to match exactly, one wrong character is a rejected submission, so after all the practice and tooling we ended up fixing the output and typing some flags in by hand. In the middle of a tense final, the hard part was not the bug, it was a font.

![Team PTIT.Celebi with the ISP flag and the third prize board](/assets/img/posts/asean-2024/team-celebi.webp)
_PTIT.Celebi with the third prize._

The scoreboard tells the honest version. We finished 6th with 6,812.92 points. On Linkextractor our SLA was 91.30%, with 159 flags captured and 231 lost. On pepeviewer we captured 651 flags, our best attack of the day, but lost 433 and the SLA was only 71.36%. The attack was far stronger than in 2023, but defense on pepeviewer was still weak and the service spent too much of the game down or exploitable. For a long stretch it was a tight race with DTU and UIT for sixth, and a mid-game system reset made it tighter, so the board stayed nerve-wracking until the end.

Third prize in my second A&D final felt like real progress over the year, even with everything that went sideways. The next A&D final I played was [M\*CTF 2025 in Moscow](/posts/ctf-mctf-2025-moscow/).

## The exploits

Both services fell to the same shape of bug, a server-side fetch that will happily read a local file.

- **pepeviewer (PHP).** Upload a PHP file through `home.php`, read the PHP session file through the LFI in `viewer.php?url=file:///tmp/sess_...` to recover the upload directory, then request the uploaded file to run `/readflag`. The script loops that over every team and submits the flags.
- **Linkextractor 2.0 (Java).** Log in, then post a page whose HTML links to `file:///flag1_linkextractor`. The service fetches it, renders the result as an image, and OCR reads the flag off the picture. This is the `0` versus `O` one.

I cleaned up the two scripts from the day. The game server address is dead and the team token is removed.

**Challenge files:** [pepeviewer.rar](/assets/ctf-files/asean-2024/pepeviewer.rar) (the PHP source) and [linkextractor.jar](/assets/ctf-files/asean-2024/linkextractor.jar) (the Java service).
**Exploit scripts:** [asean-2024-web-payloads.zip](/assets/ctf-files/asean-2024/asean-2024-web-payloads.zip)
