import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from road_mentions_qa import normalize,distinct_mentions,has_distinct_road
class RoadMentionTests(unittest.TestCase):
    def test_exact_repeat(self):
        self.assertEqual(distinct_mentions("väderleden","Väderleden"),[])
    def test_unicode_and_case(self):
        self.assertEqual(distinct_mentions("HERTSÖVÄGEN | hertsovagen","Hertsövägen"),[])
    def test_different_road_remains(self):
        self.assertEqual(distinct_mentions("Väg 97 | Mjölkuddsvägen","Mjölkuddsvägen"),["Väg 97"])
    def test_empty(self):
        self.assertFalse(has_distinct_road("","E4"))
    def test_distinct_not_approved(self):
        self.assertTrue(has_distinct_road("Karlviksvägen","Storsandsvägen"))
if __name__=="__main__":
    unittest.main()
