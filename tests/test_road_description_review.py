import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from road_description_review import partition_mentions

class Rules(unittest.TestCase):
    def test_repeated_name(self):
        self.assertEqual(partition_mentions("Hertsövägen","hertsovagen"),([],[]))
    def test_generic_descriptor(self):
        self.assertEqual(partition_mentions("Återvändsgata","Hertsövägen"),([],["Återvändsgata"]))
    def test_real_second_road(self):
        self.assertEqual(partition_mentions("Väg 97","Mjölkuddsvägen"),(["Väg 97"],[]))
    def test_other_real_second_road(self):
        self.assertEqual(partition_mentions("Karlviksvägen","Storsandsvägen"),(["Karlviksvägen"],[]))
    def test_mixed(self):
        self.assertEqual(partition_mentions("rondell | väg 97 | Mjölkuddsvägen","Mjölkuddsvägen"),(["väg 97"],["rondell"]))
if __name__=="__main__":unittest.main()
