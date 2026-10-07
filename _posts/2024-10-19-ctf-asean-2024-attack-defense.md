---
title: "ASEAN Student Contest 2024: third prize, and my second real Attack-Defense"
image:
  path: /assets/img/covers/ctf-asean-2024-attack-defense.webp
  alt: "ASEAN Student Contest 2024: third prize, and my second real Attack-Defense"
date: 2024-10-19 21:00:00 +0700
categories: ["CTF Journey"]
tags: [ctf, attack-defense, asean, ptit]
render_with_liquid: false
---

On October 19, 2024 I played the Attack-Defense final of the ASEAN Student Contest on Information Security (the 17th one) at the Military Technical Academy in Hanoi, with team PTIT.Celebi. We got third prize. PTIT's other team also got third prize in the Jeopardy bracket, so we ended up with one in each.

![PTIT's two teams on stage with their third prizes and the ISP flag](/assets/img/posts/asean-2024/ptit-teams.webp)
_The two PTIT teams at the awards ceremony._

It was my second A&D final. At [the first one in 2023](/posts/ctf-asean-2023-first-attack-defense/) our services stayed up but we patched way too slowly and lost hundreds of flags. So this time I wanted to fix that. Looking at the final board, we only half fixed it.

![The Attack-Defense final scoreboard, with PTIT.Celebi highlighted in sixth place](/assets/img/posts/asean-2024/scoreboard.webp)
_Final board. PTIT.Celebi is 6th with 6,812.92 points._

We were 6th overall with 6,812.92 points, which was enough for third prize. There were two services, Linkextractor 2.0 and pepeviewer, and our results on them are kind of funny because they look like two different teams.

On Linkextractor we were careful. SLA was 91.30%, but we only stole 159 flags and lost 231. On pepeviewer we went all in on attacking and stole 651 flags, but we lost 433 and our SLA dropped to 71.36%. I think at some point we were so focused on hitting other teams' pepeviewer that nobody was really watching ours.

KMA.0range, who won, had big numbers on both services and still kept their SLA above 77% on pepeviewer. That's basically what we were missing, doing attack and defense at the same time instead of one or the other.

The day itself was chaotic, as A&D always is. Services going down, patches breaking things, exploits that worked on our box and not on others. When it ended I wasn't sure if we'd make the prize list, so hearing our name for third prize was a big relief.

![Team PTIT.Celebi with the ISP flag and the third prize board](/assets/img/posts/asean-2024/team-celebi.webp)
_PTIT.Celebi with the third prize._

After this I kept one simple rule for A&D: someone on the team always watches our own services, no matter how good the attack is going. A year later in Moscow [it worked out pretty well](/posts/ctf-mctf-2025-moscow/).
