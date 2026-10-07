---
title: "M*CTF 2025: champions in Moscow, after 180 rounds of Attack-Defense"
image:
  path: /assets/img/covers/ctf-mctf-2025-moscow.webp
  alt: "M*CTF 2025: champions in Moscow, after 180 rounds of Attack-Defense"
date: 2025-12-08 22:00:00 +0700
categories: ["CTF Journey"]
tags: [ctf, attack-defense, mctf, russia, ptit]
render_with_liquid: false
---

In December 2025 four of us flew to Moscow in matching red PTIT jackets to play M\*CTF 2025, an international Attack-Defense competition hosted by MTUCI, the Moscow Technical University of Communications and Informatics. When round 180 of 180 ended, the board had PTIT at the top. We won it.

I've written before about my [first Attack-Defense final](/posts/ctf-asean-2023-first-attack-defense/) and my [second one](/posts/ctf-asean-2024-attack-defense/), and both of those posts end with a lesson. This is the post where the lessons paid off.

![The PTIT team in front of the M*CTF 2025 banner](/assets/img/posts/mctf-2025/team-banner.webp)
_The four of us in front of the M\*CTF 2025 banner, before it all started._

## The game

The format was classic Attack-Defense: every team runs the same set of vulnerable services, every round you try to steal flags from everyone else while patching your own copies and keeping them alive for the checker. This time there were four services, pupocer, qrb, erpdotnet and arasaka, and 180 rounds to play them over. Nine teams made the final board, from Russian universities including MTUCI itself, and from Vietnam and other countries.

Two ASEAN finals had taught me the same thing from two different directions. In 2023 we kept our services up and bled flags because we patched too slowly. In 2024 we attacked hard and let our own services fall over. So we came to Moscow with a very boring plan: patch first, keep everything green, and only then go hunting. One of us always watched our own services, no matter what was happening on the attack side.

## What the board says

Here's the final scoreboard, taken right after round 180.

![The final M*CTF 2025 scoreboard with PTIT in first place](/assets/img/posts/mctf-2025/scoreboard.webp)
_Round 180/180 ended. PTIT first with 19,477.14, MTUCI second with 18,056.53, UTT third with 17,741.54._

Look at our row. On pupocer and qrb we sat at 100.00% SLA for the whole game, and on arasaka at 85.56%. On none of those three did anyone get a flag out of us. The only service where flags actually moved was erpdotnet, and there we traded evenly, plus 20 and minus 20, while staying up 91.39% of the time.

That's not a flashy line. MTUCI, who finished second, stole 92 flags on erpdotnet without losing any, which is a better attack number than ours. But their SLA dropped to 90.28% and 86.94% on the first two services and 77.50% on erpdotnet, and in a game that runs for 180 rounds every percent of uptime is worth points, round after round. We won it by being the team that almost never went down and almost never got robbed. After two years of learning that lesson the hard way, it was a strange and wonderful feeling to win with defense.

![The PTIT team with players from MTUCI in front of the final scoreboard](/assets/img/posts/mctf-2025/with-mtuci.webp)
_With players from MTUCI in front of the final board. Great opponents, and great hosts._

## Moscow

The contest was the reason for the trip, but Moscow in December gave us more than a scoreboard. There was snow, which for someone from Vietnam is still a small miracle, and we did the things you're supposed to do. We stood in front of St. Basil's Cathedral on Red Square with snow on the cobblestones, and in front of the main building of Moscow State University, which looks even bigger in person than in photos.

![Red Square and St. Basil's Cathedral in the snow](/assets/img/posts/mctf-2025/red-square.webp)
_Red Square, St. Basil's Cathedral, and a lot of very cold air._

![Moscow State University's main building in winter](/assets/img/posts/mctf-2025/msu-snow.webp)
_The main building of Moscow State University, on an icy December day._

MTUCI also showed us its drone arena, a big sports hall wrapped in safety nets where students fly and race drones, and we got to try it ourselves. For a group of people who spend their days breaking software, getting to play with hardware that actually flies was a very good change of pace. It's also where we posed with the diploma.

![The team in MTUCI's drone arena with the diploma](/assets/img/posts/mctf-2025/drone-arena.webp)
_MTUCI's drone arena, with the diploma and a robot that wanted to be in the photo too._

## Going home

On December 7 we were at the airport under the big globe in the departure hall, tired, a bit sad to leave, and very happy. Two years earlier I had stood on a stage with a consolation prize in my first Attack-Defense final, not completely sure what had happened to us. This time I knew exactly what had happened, round by round, and I got to bring a championship home.

![The PTIT delegation at the airport in Moscow before flying home](/assets/img/posts/mctf-2025/airport.webp)
_At the airport on December 7, 2025, on the way home._
