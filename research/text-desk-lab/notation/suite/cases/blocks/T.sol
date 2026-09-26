# The house rules as one text (a doc whose lines are paragraphs), edited by whole-value rewrite.
recorded M1=10 M2=1 M3=0

step write
T do create f01 kind=doc title="House rules" text="Rent is split by the nights each of us sleeps here. Utilities and internet the same way.\nGuests staying more than three nights pay a share of utilities.\nCleaning is hired from November, 90 a month."
T do create f01 kind=note title="house" tags=lens text="h : column, the kind:doc as d\n  b : text \"$d.text\", role body"
place doc scene house

step split
T read "House rules"
T do rewrite "House rules" text="Rent is split by the nights each of us sleeps here.\nUtilities and internet the same way.\nGuests staying more than three nights pay a share of utilities.\nCleaning is hired from November, 90 a month."

step move
T do rewrite "House rules" text="Rent is split by the nights each of us sleeps here.\nUtilities and internet the same way.\nCleaning is hired from November, 90 a month.\nGuests staying more than three nights pay a share of utilities."

step join
T do rewrite "House rules" text="Rent is split by the nights each of us sleeps here. Utilities and internet the same way.\nCleaning is hired from November, 90 a month.\nGuests staying more than three nights pay a share of utilities."

step together
T~ben look
T~ben read "House rules"
T read "House rules"
T~ben do rewrite "House rules" text="Rent is split by the nights each of us sleeps here. Utilities and internet the same way.\nCleaning is hired from November, 90 a month.\nGuests staying more than four nights pay a share of utilities."
T do rewrite "House rules" text="Rent is split by the nights each of us sleeps here. Utilities and internet the same way.\nCleaning is hired from November, 95 a month.\nGuests staying more than three nights pay a share of utilities."
R read "House rules"
R do rewrite "House rules" text="Rent is split by the nights each of us sleeps here. Utilities and internet the same way.\nCleaning is hired from November, 95 a month.\nGuests staying more than four nights pay a share of utilities."

step comment
T do comment "House rules" line="Cleaning: is 95 agreed?"
T do rewrite "House rules" text="Rent is split by the nights each of us sleeps here. Utilities and internet the same way.\nGuests staying more than four nights pay a share of utilities.\nCleaning is hired from November, 95 a month."
probe comment-stays

step find
probe search-finds-paragraph
