from tests.smoke_tests import (
    test_example_document_if_available,
    test_marker_docx_roundtrip,
    test_marker_split_across_runs_is_replaced,
    test_repeated_marker_is_fully_replaced,
    test_mapping_priority_and_filename,
    test_ui_layout,
)


def test_smoke_suite() -> None:
    test_marker_docx_roundtrip()
    test_marker_split_across_runs_is_replaced()
    test_repeated_marker_is_fully_replaced()
    test_mapping_priority_and_filename()
    test_ui_layout()
    test_example_document_if_available()
