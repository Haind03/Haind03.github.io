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

On October 19, 2024 the final round of the ASEAN Student Contest on Information Security took place at the Military Technical Academy in Hanoi. It was the 17th edition of the contest, and I played the Attack-Defense bracket with team PTIT.Celebi. We came out of it with a third prize. PTIT's other team took a third prize in the Jeopardy bracket on the same day, so the school went home with one in each, and the photo of all of us on stage with two "third prize" boards and the ISP flag is still one of my favourites.

![PTIT's two teams on stage with their third prizes and the ISP flag](/assets/img/posts/asean-2024/ptit-teams.webp)
_Both PTIT teams after the awards: third prize in Jeopardy on the left, third prize in Attack-Defense on the right._

## Round two of Attack-Defense

This was only my second time playing Attack-Defense at a big contest. The first was [the same final a year earlier](/posts/ctf-asean-2023-first-attack-defense/), with team PTIT.Sn0rlax, where we got a consolation prize and a very clear lesson in how different this format is from Jeopardy. In Jeopardy you solve puzzles and the points are yours forever. In Attack-Defense every team runs the same vulnerable services, you attack everyone else's copy to steal flags every round, and at the same time you patch your own copy while keeping it alive, because a service the checker can't reach costs you points every single tick. You are attacker, defender and sysadmin all at once, for hours, with the scoreboard moving every few minutes.

I went into 2024 thinking I understood that. The final board says I understood about half of it.

## What the scoreboard says

We finished sixth on the overall board with 6,812.92 points, which was enough for a third prize. There were two services, Linkextractor 2.0 and pepeviewer, and our numbers on them read like two different teams played.

![The Attack-Defense final scoreboard, with PTIT.Celebi highlighted in sixth place](/assets/img/posts/asean-2024/scoreboard.webp)
_The final board. PTIT.Celebi in sixth with 6,812.92 points._

On Linkextractor we were the careful team. Our SLA was 91.30%, so the service stayed up almost all the time, but we only landed 159 flags against everyone else while losing 231 of our own. On pepeviewer we were the aggressive team. We stole 651 flags, but other teams took 433 from us and our SLA dropped to 71.36%. Somewhere in the middle of the day we were so busy hitting everyone else's pepeviewer that our own copy was going down and leaking.

That's the whole game in two lines. Attacking well is not enough if you don't patch fast and keep things running, and staying up is not enough if you never get an exploit out the door. The teams above us were the ones that did both at the same time. KMA.0range on top had huge numbers on both services and kept SLA above 77% even on the hard one.

## The fight

What the numbers don't show is how it felt. Attack-Defense never gives you a quiet minute. There's always a new round, a new tick, a teammate shouting that the service is down, someone else shouting that the exploit finally works and needs to go out against every team right now, and a patch that broke functionality so the checker marks you as faulty. We had all of those. There were stretches where we were climbing and stretches where we were bleeding flags and couldn't see from where, and when it ended I honestly didn't know which side of the prize line we'd land on.

When they read our name for third prize it felt earned in a way the Jeopardy prizes don't, because we'd spent the whole day both fighting and getting hit.

![Team PTIT.Celebi with the ISP flag and the third prize board](/assets/img/posts/asean-2024/team-celebi.webp)
_PTIT.Celebi with the ISP flag and the Attack-Defense third prize._


## Next time

I came out of this with one rule for Attack-Defense: never let the attack side eat the defense side. One person watches our own services at all times, no matter how good the exploit looks. I've tried to play by it in every Attack-Defense game since.
