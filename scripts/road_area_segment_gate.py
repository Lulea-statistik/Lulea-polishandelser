"""Conservative evidence gate; never alters published classifications."""
import re
def segment_reason(location,narrative,numbered,areas,shared_place=False,parsed_parent=False):
    if parsed_parent:return "föräldernotis med extraherade underhändelser"
    if shared_place:return "upprepat platsfält hos syskonhändelser"
    for field in (location,narrative):
        if len(numbered(field))>1 or len(areas(field))>1:
            return "flera vägnummer eller områden i samma källfält"
        if re.search(r"\b(?:flera|två|tre|fyra|fem|sex|sju|åtta|nio|tio|\d+)\s+(?:olika\s+)?(?:viltolyckor|trafikolyckor|händelser|olyckor|kontroller|bränder|inbrott)\b",field,re.I):
            return "uttrycklig flerhändelsetext"
    if len(numbered(location)|numbered(narrative))>1 or len(areas(location)|areas(narrative))>1:
        return "konkurrerande geografiska omnämnanden"
    return ""
def local_evidence(location,narrative,road,area,numbered,areas):
    # A long narrative in a place field is not an independent location.
    if len(location)>120 or re.search(r"[.!?]\s+|[\r\n]",location):
        return False
    if road in numbered(location) and area in areas(location):return True
    for sentence in re.split(r"(?<=[.!?])\s+|[\r\n;]+",narrative):
        if road in numbered(sentence) and area in areas(sentence):return True
    # Cross-field evidence is retained only with a short, explicit own place
    # and the complementary mention in the first sentence.
    lead=re.split(r"(?<=[.!?])\s+|[\r\n;]+",narrative,maxsplit=1)[0]
    return bool((road in numbered(location) and area in areas(lead)) or (area in areas(location) and road in numbered(lead)))
