from app.domain.toys import refresh_offsets_hours


def test_discovery_and_selected_video_monitoring_policy_stay_bounded() -> None:
    assert refresh_offsets_hours(
        lifecycle="Insufficient evidence", opportunity_score=20
    ) == (24,)
    assert refresh_offsets_hours(lifecycle="Emerging", opportunity_score=55) == (6, 24)
    assert refresh_offsets_hours(lifecycle="Breakout", opportunity_score=80) == (
        1,
        6,
        24,
        72,
    )
    assert refresh_offsets_hours(lifecycle="Saturated", opportunity_score=80) == ()
    assert refresh_offsets_hours(
        lifecycle="Saturated", opportunity_score=80, saved=True
    ) == (24,)
    assert refresh_offsets_hours(
        lifecycle="Emerging", opportunity_score=55, availability="private"
    ) == (24,)
    assert refresh_offsets_hours(
        lifecycle="Emerging",
        opportunity_score=55,
        availability="private",
        terminal_confirmed=True,
    ) == ()
