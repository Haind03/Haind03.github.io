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

The Attack-Defense final of the 2023 ASEAN Student Contest on Information Security was played on November 11, 2023, and the awards ceremony followed on November 30. I played the Attack-Defense final with team PTIT.Sn0rlax, and we came home with a consolation prize. It's the smallest prize on the list, and it's also the one that changed the most about how I play.

## Three teams, three prizes

PTIT sent three teams to the final that year and all three came back with something. PTIT.inj3cted and our PTIT.Sn0rlax each took a consolation prize in the Attack-Defense final, and PTIT.R4c1ngBoizzz took a consolation prize in the Jeopardy final. Nobody from PTIT won the whole thing that year, but three out of three teams on the prize list is a good day for a school, and ISP Club put the results up the same evening.

![ISP Club's congratulations post listing the three PTIT teams and their prizes](/assets/img/posts/asean-2023/ptit-results.webp)
_ISP Club's results post: PTIT.inj3cted and PTIT.Sn0rlax with consolation prizes in Attack-Defense, PTIT.R4c1ngBoizzz with a consolation prize in Jeopardy._

## Learning Attack-Defense the hard way

Before this final, almost everything I knew about CTF came from Jeopardy. You get a board of challenges, you solve them in whatever order you like, and a flag is points in the bank. Attack-Defense doesn't work like that at all. Every team gets the same set of vulnerable services, and every round you try to exploit everyone else's copy to steal flags while you patch your own and keep it running for the checker. Points come in and go out continuously, and the scoreboard never stops moving.

The first hour was mostly confusion. Getting the services up, reading code we'd never seen, figuring out where the bugs were before other teams started using them against us. Then the first exploits arrived, from us and at us, and the game turned into something closer to running a small, very hostile production system. Finding a bug is one thing. Turning it into an exploit that runs against every team every round without falling over, patching it on your own box without breaking the service, and doing both while a teammate tells you the checker just marked something as down, is a different skill entirely. We were learning it live.

## What the scoreboard says

I kept a screenshot of the final board from that evening, and it explains the day better than my memory does. There were four services: petstore, web 1, binary chef and web 2. We finished 15th with 4,881.03 points, one place behind PTIT.inj3cted, while UIT.Wolf_Brigade won it with 19,801.95.

![The final Attack-Defense scoreboard of the 2023 ASEAN Student Contest](/assets/img/posts/asean-2023/scoreboard.webp)
_The final board from final.ascis.vn on November 11, 2023. PTIT.Sn0rlax is 15th, team 115, on the right._

Our line is the story of a team that kept the lights on and left the doors open. Availability was fine: 95.08% SLA on petstore and a full 100% on the other three, so the checker almost never caught us down. But we lost 482 flags on petstore and 658 on web 1, while only landing 120 and 189 against everyone else. We were keeping services alive without patching them fast enough, and every round other teams walked in and took flags. On web 2 we never got an exploit out at all, and on binary chef nobody in the top 20 scored a single flag in either direction, which tells you how hard that one was.

The teams at the top did the opposite of us on the two web services. They patched early, so the minus column stayed small, and they kept exploiting everyone else all day. That gap between +189/-658 and something like +705/-25 is the whole difference between 15th and 1st.

We still ended up on the prize list with a consolation prize, and looking back the result matters less to me than what that board showed us: in Attack-Defense, staying up is the easy part. Patching is where you win or lose.

## A year later

I went back to the same final in 2024 with team PTIT.Celebi and we took a third prize in Attack-Defense. I wrote about that one [here](/posts/ctf-asean-2024-attack-defense/). Without this first round in 2023, I don't think that second result happens.
