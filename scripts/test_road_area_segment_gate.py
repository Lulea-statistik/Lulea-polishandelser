import re
from road_area_segment_gate import segment_reason,local_evidence
def roads(s):return set(re.findall(r'E(?:45|4)\b',s))
def areas(s):return {a for a in ("Råneå","Rutvik") if a in s}
# Synthetic regression cases.
mixed="Fyra viltolyckor rapporterades. På E45 och på E4 vid Råneå."
assert segment_reason(mixed,"",roads,areas)
assert segment_reason("",mixed,roads,areas)
assert segment_reason("E4 vid Råneå","",roads,areas,parsed_parent=True)
assert not segment_reason("E4 vid Råneå","",roads,areas)
assert local_evidence("E4 vid Råneå","","E4","Råneå",roads,areas)
assert not local_evidence("","E4 nämns. Råneå nämns.","E4","Råneå",roads,areas)
assert local_evidence("Råneå","Olycka på E4.","E4","Råneå",roads,areas)
print("Road-area segment tests passed")
