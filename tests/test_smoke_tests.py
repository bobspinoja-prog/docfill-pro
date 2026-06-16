from tests.smoke_tests import (
    test_example_document_if_available,
    test_marker_docx_roundtrip,
    test_marker_split_across_runs_is_replaced,
    test_history_suggestions_cover_matching_and_conflicts,
    test_history_manager_records_and_filters_documents,
    test_repeated_marker_is_fully_replaced,
    test_mapping_priority_and_filename,
    test_mapping_seed_and_build_files_are_present,
    test_safe_semantic_replacements_allow_unique_cpf_and_dates,
    test_safe_semantic_replacements_block_ambiguous_name,
    test_structured_logger_writes_jsonl,
    test_semantic_template_detection_and_persistence,
    test_template_profile_store_tracks_corrections,
    test_user_settings_store_tracks_autosave_and_history,
    test_ui_layout,
    test_history_suggestion_widget_toggles_visibility,
)


def test_smoke_suite() -> None:
    test_marker_docx_roundtrip()
    test_marker_split_across_runs_is_replaced()
    test_repeated_marker_is_fully_replaced()
    test_mapping_priority_and_filename()
    test_safe_semantic_replacements_block_ambiguous_name()
    test_safe_semantic_replacements_allow_unique_cpf_and_dates()
    test_mapping_seed_and_build_files_are_present()
    test_user_settings_store_tracks_autosave_and_history()
    test_history_manager_records_and_filters_documents()
    test_history_suggestions_cover_matching_and_conflicts()
    test_template_profile_store_tracks_corrections()
    test_structured_logger_writes_jsonl()
    test_ui_layout()
    test_history_suggestion_widget_toggles_visibility()
    test_example_document_if_available()
    test_semantic_template_detection_and_persistence()
