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

The awards ceremony for the final round of the 2023 ASEAN Student Contest on Information Security took place on November 30, 2023. I played the Attack-Defense final with team PTIT.Sn0rlax, and we came home with a consolation prize. It's the smallest prize on the list, and it's also the one that changed the most about how I play.

## Three teams, three prizes

PTIT sent three teams to the final that year and all three came back with something. PTIT.inj3cted and our PTIT.Sn0rlax each took a consolation prize in the Attack-Defense final, and PTIT.R4c1ngBoizzz took a consolation prize in the Jeopardy final. Nobody from PTIT won the whole thing that year, but three out of three teams on the prize list is a good day for a school, and ISP Club put the results up the same evening.

![ISP Club's congratulations post listing the three PTIT teams and their prizes](/assets/img/posts/asean-2023/ptit-results.webp)
_ISP Club's results post: PTIT.inj3cted and PTIT.Sn0rlax with consolation prizes in Attack-Defense, PTIT.R4c1ngBoizzz with a consolation prize in Jeopardy._

## Learning Attack-Defense the hard way

Before this final, almost everything I knew about CTF came from Jeopardy. You get a board of challenges, you solve them in whatever order you like, and a flag is points in the bank. Attack-Defense doesn't work like that at all. Every team gets the same set of vulnerable services, and every round you try to exploit everyone else's copy to steal flags while you patch your own and keep it running for the checker. Points come in and go out continuously, and the scoreboard never stops moving.

The first hour was mostly confusion. Getting the services up, reading code we'd never seen, figuring out where the bugs were before other teams started using them against us. Then the first exploits arrived, from us and at us, and the game turned into something closer to running a small, very hostile production system. Finding a bug is one thing. Turning it into an exploit that runs against every team every round without falling over, patching it on your own box without breaking the service, and doing both while a teammate tells you the checker just marked something as down, is a different skill entirely. We were learning it live.

We finished on the prize list with a consolation prize. Looking back, the result matters less to me than what the day showed us: how much of Attack-Defense is discipline rather than cleverness, and how quickly a team falls behind when attack and defense aren't both covered all the time.


## A year later

I went back to the same final in 2024 with team PTIT.Celebi and we took a third prize in Attack-Defense. I wrote about that one [here](/posts/ctf-asean-2024-attack-defense/). Without this first round in 2023, I don't think that second result happens.
