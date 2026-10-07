---
title: "ASEAN Student Contest 2023: my first Attack-Defense final"
image:
  path: /assets/img/covers/ctf-asean-2023-first-attack-defense.webp
  alt: "ASEAN Student Contest 2023: my first Attack-Defense final"
date: 2023-11-30 21:00:00 +0700
categories: ["CTF Journey"]
tags: [ctf, attack-defense, asean, ptit]
render_with_liquid: false
---

This was my first time playing Attack-Defense at a real final. The ASEAN Student Contest on Information Security 2023 had its A&D final on November 11, and I played it with team PTIT.Sn0rlax. We got a consolation prize, and the awards were handed out on November 30.

PTIT sent three teams and all three got a consolation prize, two in Attack-Defense (PTIT.inj3cted and us) and one in Jeopardy (PTIT.R4c1ngBoizzz).

![ISP Club's congratulations post listing the three PTIT teams and their prizes](/assets/img/posts/asean-2023/ptit-results.webp)
_Results of the three PTIT teams._

Before this I had basically only played Jeopardy, where you solve a challenge and the points stay yours. A&D is different. Every team gets the same vulnerable services. You attack everyone else's copy to steal flags every round, and you also have to patch your own copy without breaking it, because the checker keeps testing it. For the first hour we were mostly confused, trying to read code we'd never seen and find the bugs before other teams used them on us.

I took a screenshot of the scoreboard at the end of the day, and it shows pretty clearly what went wrong.

![The final Attack-Defense scoreboard of the 2023 ASEAN Student Contest](/assets/img/posts/asean-2023/scoreboard.webp)
_The final board on November 11, 2023. PTIT.Sn0rlax is 15th (team 115), on the right._

There were four services, petstore, web 1, binary chef and web 2. We finished 15th with 4,881.03 points.

Our SLA was 95.08% on petstore and 100% on the other three, so the services were almost always up. The problem was patching. We lost 482 flags on petstore and 658 on web 1, and captured 120 and 189 on them. The services were running but stayed vulnerable for too long. We didn't get a working exploit for web 2 or binary chef.

What I took from this final is that keeping services up is not enough, they also have to be patched early.

I went back to the same final in 2024 with PTIT.Celebi and got third prize. That one's [here](/posts/ctf-asean-2024-attack-defense/).
