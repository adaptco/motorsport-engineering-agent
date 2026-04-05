from ingest.logs.registry import detect_source, parser_statuses


def test_detect_source_by_extension():
    assert detect_source("session.ibt") == "iracing"
    assert detect_source("session.ld") == "motec"
    assert detect_source("session.xrz") == "aim"
    assert detect_source("session.vbo") == "vbox"


def test_parser_statuses_include_expected_vendors():
    vendors = {item["vendor"] for item in parser_statuses()}
    assert {"motec", "iracing", "aim", "vbox", "pi", "haltech", "aem", "csv_export"}.issubset(vendors)
