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

This was my first time playing Attack-Defense at a real final. The ASEAN Student Contest on Information Security 2023 held its A&D final on November 11, and I played it with team PTIT.Sn0rlax. We finished with a consolation prize, handed out on November 30. PTIT sent three teams and all three placed, two in Attack-Defense (PTIT.inj3cted and us) and one in Jeopardy (PTIT.R4c1ngBoizzz).

![ISP Club's congratulations post listing the three PTIT teams and their prizes](/assets/img/posts/asean-2023/ptit-results.webp)
_Results of the three PTIT teams._

Up to then I had basically only played Jeopardy, where challenges are independent and a solved one stays solved. A&D does not work like that. Every team gets the same vulnerable services and has to do two things at once, steal flags from everyone else's copy each round and patch its own copy without breaking it, because a checker keeps testing that the service still runs. For the first hour we were mostly lost, reading code we had never seen and trying to find the bugs before other teams used them on us.

Because I had spent the past year on reverse engineering, I gravitated to the pwnable services. The part that actually helped was less about exploiting from scratch and more about watching the wire. I did not know the dedicated A&D tooling yet, so I started from something I could pick up on the spot, `tcpdump`. I captured the attack traffic other teams were sending, pulled their payloads back out of the packets, and read them in the context of the service. For the pwn payloads that was familiar ground, the same input-and-behavior thinking I had built up doing RE, except now I had real attacks to study instead of a blank binary. A few of the payloads I recovered were web requests carrying flags, so I handed those to teammates and we replayed them together. That was the moment A&D clicked for me as a team format. One person's capture can be another person's exploit.

![The final Attack-Defense scoreboard of the 2023 ASEAN Student Contest](/assets/img/posts/asean-2023/scoreboard.webp)
_The final board on November 11, 2023. PTIT.Sn0rlax is 15th (team 115), on the right._

The scoreboard at the end of the day shows what went wrong, though. There were four services, petstore, web 1, binary chef and web 2, and we finished 15th with 4,881.03 points. Our SLA was 95.08% on petstore and 100% on the other three, so the services were almost always up. Patching was the problem. We lost 482 flags on petstore and 658 on web 1 while capturing only 120 and 189 back, and we never landed a working exploit on web 2 or binary chef. The services stayed alive but stayed vulnerable for too long.

That is the real lesson from this final. Keeping a service up is only half the job. A checker reporting green does not mean you are safe, it means the service answers, and the other teams can still be walking out with your flags. You have to patch, and patch early.

I went back to the same final in 2024 with PTIT.Celebi and got third prize. That one is [here](/posts/ctf-asean-2024-attack-defense/).
