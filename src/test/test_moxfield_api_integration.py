from decklist_parser import parse_decklist
from moxfield_api import get_decklist_export

# Test deck: https://moxfield.com/decks/4Ou0PhOgX0ewm2m5g1f2Kw
def test_get_decklist_export():
    deck_id = "4Ou0PhOgX0ewm2m5g1f2Kw"
    actual_export = get_decklist_export(deck_id)
    expected_export = """
        1 _____ (UNH) 23
        1 Busted! (UNF) 41
        1 How Is This a Par Three?! (UNF) 49
        1 Hymn of the Wilds (PLST) CN2-7
        1 Look at Me, I'm R&D (UND) 9
        1 S.N.O.T. (UNH) 111
        1 Ponder (LRW) 79
    """.strip()

    assert set([c.name for c in parse_decklist(actual_export)]) == set([c.name for c in parse_decklist(expected_export)])
