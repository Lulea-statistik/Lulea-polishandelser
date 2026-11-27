from build_lulea_districts import district, UNKNOWN, EXACT_LOCALITIES
for place in EXACT_LOCALITIES:
    assert district({"title_location":"Luleå","location_string":place+", Luleå, Norrbottens län"})==place, place
    assert district({"title_location":place})==place, place
assert district({"title_location":"En person har omhändertagits"})==UNKNOWN
assert district({"title_location":"person"})==UNKNOWN
assert district({"title_location":"Persön, Ängesbyn"})==UNKNOWN
assert district({"title_location":"Kallax","description":"på väg 580"})==UNKNOWN
assert district({"title_location":"Rutvik","description":"En olycka vid Bensbyn"})==UNKNOWN
assert district({"title_location":"Persön","is_summary":"true"})==UNKNOWN
assert district({"title_location":"Luleå","location_string":"Centrum"})=="Centrum"
print("Exact locality tests passed")
