from community_health_bot.services.mock_data import generate_mock_report


def test_generate_mock_report_has_sections():
    report = generate_mock_report("r/example", top_posts_limit=3, unanswered_limit=2)

    assert len(report.top_posts) == 3
    assert len(report.unanswered) == 2
    assert report.metrics.total_posts == 42
    assert report.include_sections["stats"] is True
    assert report.history, "mock history should be populated"
