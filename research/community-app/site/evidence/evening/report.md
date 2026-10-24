> Written by `scenario/evening.py` (sign-in story a13313). Every line below was printed by the run; nothing is edited by hand. **ran**, 23 Oct 2026 19:37.

# An evening of joining

**49 of 49 checks passed.** 29 neighbours joined at phone width in a hidden browser, each in a browser of their own; a bot flooded one link (14 bot accounts got in before the freeze); the kernel read everyone's answers back.

## Checks

- PASS: Alex lands on home
- PASS: the flyer's QR code carries the flyer's invite link (http://127.0.0.1:52410/join/TNCqQSzzrUHm)
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
   0.9s  setup      entry service, Google stand-in and a headless msedge on loopback; data in a temporary folder
   6.0s  Alex       signed in on his phone by emailed link and answered the questions
   6.6s  Alex       made three invites: Instagram (no limit), the meeting flyer (QR, 7 days), Sam (one use)
   6.9s  phone      a camera reads the printed flyer's QR code: http://127.0.0.1:52410/join/TNCqQSzzrUHm
   7.4s  kernel     world founded with Alex as steward, on its own loopback port: {'ok': True, 'records': 1}
   8.2s  Maya R.    Instagram link, link: home
   8.8s  Jordan P.  Instagram link, google: home
   9.5s  Priya S.   Instagram link, code: home
  10.2s  Luis M.    Instagram link, link: home
  10.8s  Hannah K.  Instagram link, google: home
  11.5s  Dev A.     Instagram link, code: home
  12.2s  Grace L.   Instagram link, link: home
  13.0s  Omar F.    Instagram link, google: home
  13.7s  Tess W.    Instagram link, link: home
  14.7s  Ken O.     Instagram link, code: home
  15.4s  Bea N.     Instagram link, google: home
  16.1s  Sol V.     Instagram link, link: home
  16.8s  Carmen D.  scanned the flyer at the meeting, code: home
  17.4s  Pat G.     scanned the flyer at the meeting, google: home
  18.1s  Rich B.    scanned the flyer at the meeting, code: home
  18.7s  Yuki M.    scanned the flyer at the meeting, link: home
  19.3s  Abel S.    scanned the flyer at the meeting, code: home
  19.8s  June H.    scanned the flyer at the meeting, google: home
  20.5s  Sam        Alex's direct link: home
  20.8s  Sam's friend opens the link Sam forwarded: it has been used
  20.8s  bot        finds the Instagram link and starts making accounts
  21.6s  Ana C.     Instagram link during the flood, code: home
  22.2s  Will T.    Instagram link during the flood, google: home
  22.6s  Rosa       asks for a sign-in email on the Instagram link
  22.9s  Alex       opens Invites on his phone: Instagram Link · made by Alex H. · until 22 Nov 2026 Open 26 joined 26 in the last hour
  23.0s  Alex       opens Instagram's invite: 13 'FREE CRYPTO' names among who came through
  23.2s  Alex       freezes the Instagram link
  23.2s  bot        gives up: {'joined': 14, 'closed': 3, 'slowed': 0, 'refused': 0, 'no_link': 0}
  23.3s  Rosa       types her code after the freeze: We couldn't sign you in This invite link has closed. Ask whoever sent it for a new one. Back to sign in Made b
  23.8s  Rosa       a neighbour shows her the flyer; she scans it: home
  24.6s  Theo       Instagram says paused; he uses the flyer: home
  25.3s  Nora E.    scanned the flyer after the freeze, code: home
  26.1s  Felix Q.   scanned the flyer after the freeze, link: home
  26.8s  Iris J.    scanned the flyer after the freeze, code: home
  28.1s  Marco Z.   scanned the flyer after the freeze, google: home
  28.7s  Lena U.    scanned the flyer after the freeze, code: home
  29.4s  Hugo I.    scanned the flyer after the freeze, link: home
  29.7s  Maya       on her laptop asks for a sign-in email; opens it on her phone
  30.0s  Maya       types the code on the laptop
  30.4s  kernel     read back each person's answers as that person: 29 of 29 match
  30.5s  kernel     Alex (a leader) reads Maya: Maya R. (sb21), a person · answers: display_name=Maya R., help=['meetings', 'research'], neighbourhood=Seabright
  30.5s  kernel     Bea (a member) reads Maya: Maya R. (sb21), a person
  61.6s  kernel     Maya's old phone session, 31 s later: {'status': 401, 'error': 'this session is not signed in (or has ended); sign in again'}
  61.6s  count      29 neighbours plus Alex; uses per link: {'Direct: Sam': 1, 'Instagram': 28, 'Flyer, Galt Elementary meeting': 14}; bots that got in before the freeze: 14
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
