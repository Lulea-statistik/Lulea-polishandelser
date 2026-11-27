from build_lulea_districts import road_locality_rescue, UNKNOWN
for text,name in [("Trafikolycka på E4 i Rutvik.","Rutvik"),("E4 Persön, trafikolycka.","Persön"),("Riksväg 97, Södra Sunderbyn.","Sunderbyn"),("LV383 i Smedsbyn.","Smedsbyn"),("E4 Jämtön, trafikolycka.","Jämtön")]:
 assert road_locality_rescue({"description":text})==name,text
for text in ("E4 i höjd med Rutvik.","E4 Rutvik, på väg 97.","E4 Rutvik, norr om Rutvik.","E4 Persön, mot Ängesbyn.","Väg 97 Rutvik.","E4 person."):
 assert road_locality_rescue({"description":text})==UNKNOWN,text
assert road_locality_rescue({"description":"E4 Persön.","location_string":"Persön, Ängesbyn, Luleå, Norrbottens län"})==UNKNOWN
assert road_locality_rescue({"description":"E4 Rutvik.","is_summary":"true"})==UNKNOWN
print("Road locality tests passed")
