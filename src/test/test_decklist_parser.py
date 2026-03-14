from decklist_parser import CardQuery, Printing, parse_decklist


def test_full_card():
    result = parse_decklist("1 Counterspell (CMR) 632")
    assert result == [CardQuery("Counterspell", "CMR", "632")]


def test_full_card_foil():
    result = parse_decklist("1 Counterspell (CMR) 632 *F*")
    assert result == [CardQuery("Counterspell", "CMR", "632", Printing.Foil)]


def test_full_card_etched_foil():
    result = parse_decklist("1 Sol Ring (SLC) 27 *E*")
    assert result == [CardQuery("Sol Ring", "SLC", "27", Printing.EtchedFoil)]


def test_card_no_set_info():
    result = parse_decklist("1 Sol Ring")
    assert result == [CardQuery("Sol Ring")]


def test_card_foil_no_set_info():
    result = parse_decklist("1 Arcane Signet *F*")
    assert result == [CardQuery("Arcane Signet", printing=Printing.Foil)]


def test_double_faced_card():
    result = parse_decklist("1 Agadeem's Awakening / Agadeem, the Undercrypt (ZNR) 90")
    assert result == [CardQuery("Agadeem's Awakening / Agadeem, the Undercrypt", "ZNR", "90")]


def test_quantity_ignored():
    assert parse_decklist("4 Lightning Bolt (M11) 149") == [CardQuery("Lightning Bolt", "M11", "149")]
    assert parse_decklist("1 Lightning Bolt (M11) 149") == [CardQuery("Lightning Bolt", "M11", "149")]


def test_strips_mentions():
    text = "@alice @bob\n1 Sol Ring"
    assert parse_decklist(text) == [CardQuery("Sol Ring")]


def test_full_discord_message():
    text = (
        "@alice @bob\n"
        "1 Teval, Arbiter of Virtue (TDM) 373 *F*\n"
        "1 Agadeem's Awakening / Agadeem, the Undercrypt (ZNR) 90\n"
        "1 Alchemist's Refuge (LCC) 318\n"
        "1 Alhammarret's Archive (SLC) 27 *F*"
    )
    assert parse_decklist(text) == [
        CardQuery("Teval, Arbiter of Virtue", "TDM", "373", Printing.Foil),
        CardQuery("Agadeem's Awakening / Agadeem, the Undercrypt", "ZNR", "90"),
        CardQuery("Alchemist's Refuge", "LCC", "318"),
        CardQuery("Alhammarret's Archive", "SLC", "27", Printing.Foil),
    ]


def test_blank_lines_ignored():
    text = "1 Sol Ring\n\n2 Lightning Bolt (M11) 149"
    assert parse_decklist(text) == [
        CardQuery("Sol Ring"),
        CardQuery("Lightning Bolt", "M11", "149"),
    ]

def test_blank_spaces_ignored():
    text = "    1 Sol Ring\n\n    2 Lightning Bolt (M11) 149"
    assert parse_decklist(text) == [
        CardQuery("Sol Ring"),
        CardQuery("Lightning Bolt", "M11", "149"),
    ]


def test_legacy_search():
    text = "Sol Ring"
    assert parse_decklist(text) == [CardQuery("Sol Ring")]

def test_legacy_search_list():
    text = "Sol Ring | Counterspell | Arcane Signet"
    assert parse_decklist(text) == [
        CardQuery("Sol Ring"),
        CardQuery("Counterspell"),
        CardQuery("Arcane Signet"),
    ]

def test_legacy_search_list_with_si():
    text = "Sol Ring (C17) 223"
    assert parse_decklist(text) == [
        CardQuery("Sol Ring", set_code="C17", collector_number="223"),
    ]
