# The house rules as blocks: each paragraph its own note in a column surface (the codex team's Studio shape).
# A paragraph needs a title to be a note; I give each the words a person would use to name it.
recorded M1=15 M2=0 M3=3

step write
T do create f01 kind=surface title="House rules" layout=column
T do create f02 kind=note title="rent" text="Rent is split by the nights each of us sleeps here. Utilities and internet the same way."
T do create f02 kind=note title="guests" text="Guests staying more than three nights pay a share of utilities."
T do create f02 kind=note title="cleaning" text="Cleaning is hired from November, 90 a month."
T do create f01 kind=note title="house" tags=lens text="h : column, of in:f02, each b\nb : text \"$text\", role body"
place doc scene house

step split
T read rent
T do rewrite rent text="Rent is split by the nights each of us sleeps here."
T do create f02 kind=note title="utilities" text="Utilities and internet the same way."
T do move utilities after=rent

step move
T do move cleaning before=guests

step join
T read utilities
T do rewrite rent text="Rent is split by the nights each of us sleeps here. Utilities and internet the same way."
T do remove utilities

step together
T~ben look
T~ben read guests
T read cleaning
T~ben do rewrite guests text="Guests staying more than four nights pay a share of utilities."
T do rewrite cleaning text="Cleaning is hired from November, 95 a month."

step comment
T do comment cleaning line="is 95 agreed?"
T do move cleaning after=guests
probe comment-stays

step find
probe search-finds-paragraph
