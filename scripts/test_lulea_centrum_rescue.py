from build_lulea_districts import centrum_rescue, district, UNKNOWN
# Synthetic regression examples based on observed wording in audit #6.
for headline in ("Stöld i butik, Innerstaden.", "Stöld i butik, Luleå centrum.", "Centrum, misstänkt fylleri.", "Olovlig körning i Luleå innerstad.", "Brand i centrala Luleå."):
    assert centrum_rescue({"headline":headline,"title_location":"Luleå"})=="Centrum", headline
for headline in ("Fordonet färdades mot centrum.", "Kontroll vid Örnäsets centrum.", "Stöld i butik, Bodens centrum.", "Analys vid nationella forensiska centrum.", "Stöld i butik, Hertsö centrum.", "Riksväg 97 Innerstaden, trafikolycka."):
    assert centrum_rescue({"headline":headline})==UNKNOWN, headline
assert centrum_rescue({"headline":"Stöld i butik, Innerstaden.","content":"Polisen fördes till Rutvik."})==UNKNOWN
assert centrum_rescue({"headline":"Centrum, misstänkt fylleri.","title_location":"Niemisel"})==UNKNOWN
assert centrum_rescue({"headline":"Centrum, misstänkt fylleri.","is_summary":"true"})==UNKNOWN
assert district({"title_location":"Porsön","headline":"Centrum, misstänkt fylleri."})=="Porsön"
print("Centrum rescue regression tests passed")
