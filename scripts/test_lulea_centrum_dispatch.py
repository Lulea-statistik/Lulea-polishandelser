from build_lulea_districts import centrum_dispatch_rescue, district, UNKNOWN
# Synthetic examples; not source quotations.
for description in (
 "Polis beordras till Östermalm med anledning av ett inbrott.",
 "En polispatrull larmades till busstationen i Luleå.",
 "Patrullen åker till Södra hamn efter ett larm.",
 "Polisen skickades till en butik i centrala Luleå.",
 "Larm om brand vid gymnasiebyn.",
 "Inbrott i Stadsviken.",
 "Polisen kallades till järnvägsstationen.",
):
 assert centrum_dispatch_rescue({"title_location":"Luleå","description":description})=="Centrum",description
for description in (
 "Personen sprang mot centrum.",
 "Personen fördes till busstationen.",
 "Polis beordrades till Björkskatans centrum.",
 "Polis beordras till centrum i Boden.",
 "Polis beordrades inte till centrum.",
 "Polis beordrades till centrum på väg 97.",
 "Polis beordras till centrum. Händelsen inträffade i Rutvik.",
 "Polis beordrades till centrum. Personen färdades från Niemisel.",
 "Polis beordras till centrum för övning.",
):
 assert centrum_dispatch_rescue({"description":description})==UNKNOWN,description
assert centrum_dispatch_rescue({"description":"Polis beordras till centrum.","is_summary":"true"})==UNKNOWN
assert centrum_dispatch_rescue({"description":"Polis beordras till centrum.","title_location":"Niemisel"})==UNKNOWN
assert district({"title_location":"Porsön","description":"Polis beordras till centrum."})=="Porsön"
print("Centrum dispatch tests passed")
