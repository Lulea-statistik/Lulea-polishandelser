import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_all_road_candidates import classify

def row(primary,other="",eid="1"):
 return {"event_id":eid,"source":"original","own_field_roads":primary,"other_text_roads":other}

class TestGeneralRoadReview(unittest.TestCase):
 def test_same_road_repeated(self):
  self.assertEqual(classify(row("Hertsövägen","hertsovagen"))["manual_review"],"STICKPROV")
 def test_generic_descriptor(self):
  self.assertEqual(classify(row("Hertsövägen","återvändsgata"))["manual_review"],"STICKPROV")
 def test_two_distinct_roads(self):
  self.assertEqual(classify(row("Mjölkuddsvägen","Väg 97"))["qa_status"],"other_road_reference")
 def test_two_in_place(self):
  self.assertEqual(classify(row("Mjölkuddsvägen | Väg 97"))["qa_status"],"multiple_roads_in_own_place")
 def test_never_publishes(self):
  for x in [row("Hertsövägen"),row("Hertsövägen","Väg 97")]:
   self.assertEqual(classify(x)["publish"],"NEJ")

if __name__ == "__main__": unittest.main()
