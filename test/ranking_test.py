from sundowner import ranking


# _delta_day_offset ------------------------------------------------------------

def _day_offset_diff_to_score(diff):
    """The delta function returns a normalised score (0-1) which is difficult
    for a human to interpret in this context. It would be easier to work with
    actual second differences, so this function converts a second difference
    to the score that it would return from the _delta_day_offset function.
    """
    return 1 - (float(diff) / (ranking._SECONDS_PER_DAY / 2.0))

def _to_test_vector(val, offset):
    """Generate a vector for testing with the index identified by 'offset' 
    containing the value 'val'.
    """
    vec = [None] * (offset + 1)
    vec[offset] = val
    return vec

def test_delta_day_offset():
    """Incrementally move through a 2 day period, one hour at a time, and 
    compare the day offset against a fixed time that falls in the middle of
    the range.
    """

    a_start =   1356998400 # 1 Jan 2013 00:00:00 GMT
    a_end =     1357171200 # 3 Jan 2013 00:00:00 GMT
    b =         1357084800 # 2 Jan 2013 00:00:00 GMT

    vector_b = _to_test_vector(b, ranking._DAY_OFFSET)
    seconds_per_hour = 3600
    expected_hour_diff = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,
                          12,11,10, 9, 8, 7, 6, 5, 4, 3, 2, 1,
                           0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,
                          12,11,10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

    for i, a in enumerate(range(a_start, a_end, seconds_per_hour)): 
        vector_a = _to_test_vector(a, ranking._DAY_OFFSET)
        expected_diff = expected_hour_diff[i] * seconds_per_hour
        expected_score = _day_offset_diff_to_score(expected_diff)
        actual_score = ranking._delta_day_offset(vector_a, vector_b)
        assert expected_score == actual_score

