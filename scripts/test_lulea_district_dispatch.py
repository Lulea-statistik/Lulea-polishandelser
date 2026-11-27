from build_lulea_districts import district_dispatch_rescue, district, UNKNOWN
for name in ("Hertsön","Örnäset","Skurholmen","Porsön","Björkskatan","Notviken","Bergnäset","Sunderbyn","Gammelstad","Råneå","Storheden","Persön","Rutvik"):
 assert district_dispatch_rescue({"description":f"Polis beordras till {name} med anledning av ett bråk."})==name,name
for sentence in ("Polis beordras till person.", "Personen sprang mot Hertsön.", "Personen fördes till Sunderby sjukhus.", "Polis beordras till Hertsön. Händelsen inträffade på Porsön.", "Polis beordras till Rutvik på väg 97.", "Polis beordras till Kronan.", "Polis beordras till Örnäset för övning."):
 assert district_dispatch_rescue({"description":sentence})==UNKNOWN,sentence
assert district({"title_location":"Centrum","description":"Polis beordras till Hertsön."})=="Centrum"
assert district_dispatch_rescue({"is_summary":"true","description":"Polis beordras till Hertsön."})==UNKNOWN
print("District dispatch tests passed")
