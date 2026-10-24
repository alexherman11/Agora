> Written by `scenario/evening.py` (sign-in story a13313). Every line below was printed by the run; nothing is edited by hand. **ran**, 23 Oct 2026 18:43.

# An evening of joining

**49 of 49 checks passed.** 29 neighbours joined at phone width in a hidden browser, each in a browser of their own; a bot flooded one link (14 bot accounts got in before the freeze); the kernel read everyone's answers back.

## Checks

- PASS: Alex lands on home
- PASS: the flyer's QR code carries the flyer's invite link (http://127.0.0.1:62552/join/dppxGRdtVFzR)
- PASS: Alex's account is joined to his kernel person (the steward)
- PASS: Maya R. gets in through Instagram (home)
- PASS: Jordan P. gets in through Instagram (home)
- PASS: Priya S. gets in through Instagram (home)
- PASS: Luis M. gets in through Instagram (home)
- PASS: Hannah K. gets in through Instagram (home)
- PASS: Dev A. gets in through Instagram (home)
- PASS: Grace L. gets in through Instagram (home)
- PASS: Omar F. gets in through Instagram (home)
- PASS: Tess W. gets in through Instagram (home)
- PASS: Ken O. gets in through Instagram (home)
- PASS: Bea N. gets in through Instagram (home)
- PASS: Sol V. gets in through Instagram (home)
- PASS: Carmen D. gets in through the flyer (home)
- PASS: Pat G. gets in through the flyer (home)
- PASS: Rich B. gets in through the flyer (home)
- PASS: Yuki M. gets in through the flyer (home)
- PASS: Abel S. gets in through the flyer (home)
- PASS: June H. gets in through the flyer (home)
- PASS: Sam gets in through his direct link (home)
- PASS: a one-use link turns away a second person
- PASS: Ana C. still gets in while the bot is at it (home)
- PASS: Will T. still gets in while the bot is at it (home)
- PASS: the flooded link is marked busy on the first screen, without scrolling
- PASS: the bot is stopped by the freeze: it meets a closed link ({'joined': 14, 'closed': 3, 'slowed': 0, 'refused': 0, 'no_link': 0})
- PASS: nobody comes in through Instagram after the freeze (0 late)
- PASS: Instagram shows as frozen
- PASS: Rosa's request from before the freeze is turned away
- PASS: Rosa gets in through the flyer instead (home)
- PASS: a newcomer on the frozen link is told it is paused
- PASS: Theo gets in through the flyer (home)
- PASS: Nora E. gets in through the flyer after the freeze (home)
- PASS: Felix Q. gets in through the flyer after the freeze (home)
- PASS: Iris J. gets in through the flyer after the freeze (home)
- PASS: Marco Z. gets in through the flyer after the freeze (home)
- PASS: Lena U. gets in through the flyer after the freeze (home)
- PASS: Hugo I. gets in through the flyer after the freeze (home)
- PASS: the phone says the laptop can use the code instead
- PASS: the laptop is signed in
- PASS: the phone is still signed in too
- PASS: both devices answer to the kernel as Maya
- PASS: every neighbour's answers are facts the kernel holds (29/29)
- PASS: a leader sees a member's answers
- PASS: another member does not
- PASS: signing out on every device ends the phone's session
- PASS: the kernel stops honouring it within its 30 s cache
- PASS: every account that answered the questions has a kernel person (44 persons)

## What happened

```
   1.2s  setup      entry service, Google stand-in and a headless msedge on loopback; data in a temporary folder
   8.0s  Alex       signed in on his phone by emailed link and answered the questions
   8.8s  Alex       made three invites: Instagram (no limit), the meeting flyer (QR, 7 days), Sam (one use)
   9.0s  phone      a camera reads the printed flyer's QR code: http://127.0.0.1:62552/join/dppxGRdtVFzR
   9.6s  kernel     world founded with Alex as steward, on its own loopback port: {'ok': True, 'records': 1}
  10.6s  Maya R.    Instagram link, link: home
  11.4s  Jordan P.  Instagram link, google: home
  12.2s  Priya S.   Instagram link, code: home
  13.3s  Luis M.    Instagram link, link: home
  14.6s  Hannah K.  Instagram link, google: home
  15.5s  Dev A.     Instagram link, code: home
  16.6s  Grace L.   Instagram link, link: home
  17.3s  Omar F.    Instagram link, google: home
  18.0s  Tess W.    Instagram link, link: home
  18.6s  Ken O.     Instagram link, code: home
  19.4s  Bea N.     Instagram link, google: home
  20.1s  Sol V.     Instagram link, link: home
  21.1s  Carmen D.  scanned the flyer at the meeting, code: home
  22.4s  Pat G.     scanned the flyer at the meeting, google: home
  24.2s  Rich B.    scanned the flyer at the meeting, code: home
  25.2s  Yuki M.    scanned the flyer at the meeting, link: home
  26.0s  Abel S.    scanned the flyer at the meeting, code: home
  26.8s  June H.    scanned the flyer at the meeting, google: home
  27.9s  Sam        Alex's direct link: home
  28.5s  Sam's friend opens the link Sam forwarded: it has been used
  28.5s  bot        finds the Instagram link and starts making accounts
  29.8s  Ana C.     Instagram link during the flood, code: home
  30.5s  Will T.    Instagram link during the flood, google: home
  30.8s  Rosa       asks for a sign-in email on the Instagram link
  31.0s  Alex       opens Invites on his phone: Instagram Link · made by Alex H. · until 22 Nov 2026 Open 26 joined 26 in the last hour
  31.1s  Alex       opens Instagram's invite: 13 'FREE CRYPTO' names among who came through
  31.3s  Alex       freezes the Instagram link
  31.3s  bot        gives up: {'joined': 14, 'closed': 3, 'slowed': 0, 'refused': 0, 'no_link': 0}
  31.5s  Rosa       types her code after the freeze: We couldn't sign you in This invite link has closed. Ask whoever sent it for a new one. Back to sign in Made b
  32.0s  Rosa       a neighbour shows her the flyer; she scans it: home
  32.8s  Theo       Instagram says paused; he uses the flyer: home
  33.5s  Nora E.    scanned the flyer after the freeze, code: home
  34.3s  Felix Q.   scanned the flyer after the freeze, link: home
  35.1s  Iris J.    scanned the flyer after the freeze, code: home
  35.8s  Marco Z.   scanned the flyer after the freeze, google: home
  36.8s  Lena U.    scanned the flyer after the freeze, code: home
  37.6s  Hugo I.    scanned the flyer after the freeze, link: home
  38.3s  Maya       on her laptop asks for a sign-in email; opens it on her phone
  38.6s  Maya       types the code on the laptop
  39.1s  kernel     read back each person's answers as that person: 29 of 29 match
  39.1s  kernel     Alex (a leader) reads Maya: Maya R. (sb16), a person · answers: display_name=Maya R., help=['meetings', 'research'], neighbourhood=Seabright
  39.1s  kernel     Bea (a member) reads Maya: Maya R. (sb16), a person
  70.3s  kernel     Maya's old phone session, 31 s later: {'status': 401, 'error': 'this session is not signed in (or has ended); sign in again'}
  70.3s  count      29 neighbours plus Alex; uses per link: {'Instagram': 28, 'Flyer, Galt Elementary meeting': 14, 'Direct: Sam': 1}; bots that got in before the freeze: 14
```

## Screenshots

- [01-public-site.jpg](01-public-site.jpg)
- [02-flyer-poster.jpg](02-flyer-poster.jpg)
- [03-maya-join.jpg](03-maya-join.jpg)
- [04-maya-check-email.jpg](04-maya-check-email.jpg)
- [05-maya-welcome.jpg](05-maya-welcome.jpg)
- [06-maya-home.jpg](06-maya-home.jpg)
- [07-sams-link-used-up.jpg](07-sams-link-used-up.jpg)
- [08-leader-sees-the-flood.jpg](08-leader-sees-the-flood.jpg)
- [09-who-came-through-instagram.jpg](09-who-came-through-instagram.jpg)
- [10-instagram-frozen.jpg](10-instagram-frozen.jpg)
- [11-rosa-turned-away.jpg](11-rosa-turned-away.jpg)
- [12-theo-finds-instagram-paused.jpg](12-theo-finds-instagram-paused.jpg)
- [13-maya-link-on-the-other-device.jpg](13-maya-link-on-the-other-device.jpg)
- [14-maya-laptop-signed-in.jpg](14-maya-laptop-signed-in.jpg)
