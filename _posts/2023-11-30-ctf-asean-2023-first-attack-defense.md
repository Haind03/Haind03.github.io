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

PTIT sent three teams and all three got something: PTIT.inj3cted and us with consolation prizes in Attack-Defense, and PTIT.R4c1ngBoizzz with a consolation prize in Jeopardy.

![ISP Club's congratulations post listing the three PTIT teams and their prizes](/assets/img/posts/asean-2023/ptit-results.webp)
_Results of the three PTIT teams._

Before this I had basically only played Jeopardy, where you solve a challenge and the points stay yours. A&D is different. Every team gets the same vulnerable services. You attack everyone else's copy to steal flags every round, and you also have to patch your own copy without breaking it, because the checker keeps testing it. For the first hour we were mostly confused, trying to read code we'd never seen and find the bugs before other teams used them on us.

I took a screenshot of the scoreboard at the end of the day, and it shows pretty clearly what went wrong.

![The final Attack-Defense scoreboard of the 2023 ASEAN Student Contest](/assets/img/posts/asean-2023/scoreboard.webp)
_The final board on November 11, 2023. PTIT.Sn0rlax is 15th (team 115), on the right._

There were four services: petstore, web 1, binary chef and web 2. We finished 15th with 4,881.03 points, one spot behind PTIT.inj3cted. UIT.Wolf_Brigade won with 19,801.95.

Our uptime was fine, 95.08% on petstore and 100% on the other three. The problem was patching. We lost 482 flags on petstore and 658 on web 1, and only stole 120 and 189. So the services were running, but they were still vulnerable for way too long and other teams kept taking flags from us. For comparison, the winners were at +705/-25 on web 1. We never got an exploit working on web 2, and on binary chef nobody in the top 20 got a single flag either way, so I don't feel too bad about that one.

Main thing I learned: keeping the service up is not enough, you have to patch fast.

I went back to the same final in 2024 with PTIT.Celebi and got third prize. That one's [here](/posts/ctf-asean-2024-attack-defense/).
