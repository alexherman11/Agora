# What counts as a read, after 1758e14. Each probe builds its own things in one shared in-memory world.
# 1937b5c recorded M3=3 M4=2 (three printers over-refused, two blind rewrites accepted); all five fixed in 5bb7f7f.
recorded M3=0 M4=0

step shown
probe view-is-a-read
probe lens-is-a-read
probe table-is-a-read
probe read-shows-props

step unseen
probe blind-after-look
probe blind-after-find
