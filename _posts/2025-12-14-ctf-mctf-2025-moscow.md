---
title: "M*CTF 2025: first place in Moscow"
image:
  path: /assets/img/covers/ctf-mctf-2025-moscow.webp
  alt: "M*CTF 2025: first place in Moscow"
date: 2025-12-14 22:00:00 +0700
categories: ["CTF Journey"]
tags: [ctf, attack-defense, mctf, russia, ptit]
render_with_liquid: false
---

When I started with CTF I just wanted to learn some security, try the challenges, and see how far I could get. Flying to Moscow to win an international Attack-Defense final was not on any list I had. But in December 2025 that is where four of us from PTIT ended up, at M\*CTF 2025, an international A&D hosted by MTUCI (Moscow Technical University of Communications and Informatics), and we won it.

## An invitation we did not expect

The invitation to play in Russia came out of nowhere, and it meant more when I set it against where all this started. A few years back, just reaching an A&D final felt huge. [My first one, at the ASEAN contest in 2023](/posts/ctf-asean-2023-first-attack-defense/), ended in a consolation prize and a long list of things to fix. Now I was walking into another A&D room, this time in Moscow, against teams from several countries.

We landed on December 7. Moscow in December was cold and deep in snow, nothing like the trips before it.

![The PTIT delegation at the airport in Moscow after arriving](/assets/img/posts/mctf-2025/airport.webp)
_Arriving in Moscow, December 7, 2025._

![The PTIT team in front of the M*CTF 2025 banner](/assets/img/posts/mctf-2025/team-banner.webp)
_The four of us at M\*CTF 2025._

## Defense first, this time

I had played A&D twice before, both at the ASEAN contest, and they taught the same lesson from opposite sides. That first final in 2023, our services stayed up but we patched too slowly, so other teams kept farming flags off us. [The next year, in 2024](/posts/ctf-asean-2024-attack-defense/), we attacked well but let our own services fall over.

A&D is not a race to grab the most flags. Every team attacks and defends at the same time, and a strong attack means nothing if your own services keep leaking or going down. So this time we flipped our priority. Keep the services safe and stable first, close the holes, and only then chase points off everyone else. The things that had cost us before became the plan for this one.

## 180 rounds

Nine teams made the final board, from Russia, Vietnam and a few other countries. The game ran 180 rounds over four services, pupocer, qrb, erpdotnet and arasaka. Over that many rounds it is not only about finding a bug and firing an exploit. You are watching service health the whole time, handling whatever breaks, and making sure your systems keep answering the checker round after round.

We put defense first and held to it, and by the end the board showed why.

![The final M*CTF 2025 scoreboard with PTIT in first place](/assets/img/posts/mctf-2025/scoreboard.webp)
_Round 180/180. PTIT 1st with 19,477.14, MTUCI 2nd with 18,056.53, UTT 3rd with 17,741.54._

You can read it in our row. 100% SLA on pupocer and qrb, 85.56% on arasaka, and nobody pulled a single flag from us on those three. erpdotnet was the only service where flags really moved, and there we went +20/-20 at 91.39% uptime. Over 180 rounds uptime is worth a lot, and that is where most of our points came from.

After 180 rounds PTIT finished 1st with 19,477.14 points, ahead of MTUCI on 18,056.53 and UTT on 17,741.54. We had won M\*CTF 2025, and taking it mainly through defense, after the two ASEAN finals, felt exactly right.

![The M*CTF 2025 1st place award](/assets/img/posts/mctf-2025/trophy.webp)
_The 1st place award, M\*CTF 2025._

![The PTIT team with players from MTUCI in front of the final scoreboard](/assets/img/posts/mctf-2025/with-mtuci.webp)
_With players from MTUCI after the final._

## Moscow outside the contest room

A trip like this is never only the result. Moscow in winter was its own experience for all of us. We went to Red Square and St. Basil's Cathedral, and to Moscow State University, places I had only seen in photos before.

![Red Square and St. Basil's Cathedral in the snow](/assets/img/posts/mctf-2025/red-square.webp)
_Red Square and St. Basil's._

![Moscow State University's main building in winter](/assets/img/posts/mctf-2025/msu-snow.webp)
_Moscow State University._

MTUCI also has a drone arena, a big sports hall strung with nets, and we got to fly the drones there between the serious parts. That is also where we took the photo with the diploma.

![The team in MTUCI's drone arena with the diploma](/assets/img/posts/mctf-2025/drone-arena.webp)
_In the MTUCI drone arena._

## From 15th to 1st

Here is the part that gets me when I look back. Two years earlier, at my first A&D final, we finished 15th with a consolation prize, short on experience and with no real balance between attack and defense. At M\*CTF 2025 we finished 1st.

The two contests are not the same size or the same field, so I would not read too much into the raw ranking. But for me the change still means a lot. Progress did not arrive as one big leap. 2023 taught us to patch faster, 2024 taught us that attacking well is not enough, and by 2025 we walked into an international final knowing exactly what to prioritize. The win was the sum of those lessons, including the ones that came from losing.

I do not know how many more CTFs I will play, or whether I will stay on Attack-Defense. But M\*CTF 2025 will always be one I remember most. From a consolation prize in my first A&D final to first place in Moscow, that is a stretch of road I am proud of.
