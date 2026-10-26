import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_road_second_pass import triage

def row(eid,own,other="",place=""):
 return {"event_id":eid,"source":"original","candidate_road":own,"own_field_roads":own,"other_text_roads":other,"place_text":place}

class SecondPassTest(unittest.TestCase):
 def test_junction(self):
  r=triage(row("1","Väg 97 | Mjölkuddsvägen","","vid korsningen"))
  self.assertEqual(r["review_subtype"],"possible_junction")
  self.assertEqual(r["publish"],"NEJ")
 def test_other_reference(self):
  r=triage(row("2","Storsandsvägen","Karlviksvägen"))
  self.assertEqual(r["review_subtype"],"other_road_relation_unclear")
 def test_normal_repeat(self):
  self.assertEqual(triage(row("3","Hertsövägen","hertsovagen"))["qa_status"],"normal")
 def test_unknown_geography_preserved(self):
  self.assertEqual(triage(row("4","Väg 97"))["geography_decision"],"Oförändrad")

if __name__=="__main__":unittest.main()
