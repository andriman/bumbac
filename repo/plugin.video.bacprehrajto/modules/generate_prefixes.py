import re


from typing import List


# generate_prefixes.py
import re
from typing import List


# generate_prefixes.py
import re
from typing import List


# generate_prefixes.py
import re
from typing import List


def generate_prefixes(input_str: str) -> List[str]:
    """
    Return a list of unique reverse-cumulative prefixes (longest first).

    Behaviour
    ---------
    * Leading whitespace is stripped once.
    * Tokens are split on whitespace groups **and** punctuation groups.
    * ``SxxExxx`` → ``Sxx`` + ``Exxx`` (Exxx stays whole for now)
    * **Every** ``Exxx`` token (whether from SxxExxx or standalone) is later split
      into ``E`` + ``xxx`` so we get the ``... E932`` and ``... 932`` steps.
    * Each cumulative prefix is ``.strip()``-ed and deduplicated.
    * Longest first.

    Examples
    --------
    >>> generate_prefixes("abcd efef S02E932")
    ['abcd efef S02E932', 'abcd efef S02', 'abcd efef E932', 'abcd efef 932',
     'abcd efef', 'abcd']

    >>> generate_prefixes("abcd efef E932")
    ['abcd efef E932', 'abcd efef 932', 'abcd efef', 'abcd']
    """
    input_str = input_str.lstrip()
    if not input_str:
        return []

    # ------------------------------------------------------------------ #
    # 1. Tokenise – keep words, whitespace groups, punctuation groups
    # ------------------------------------------------------------------ #
    raw = re.split(r'(\s+|[^\w\s]+)', input_str)
    raw = [t for t in raw if t]

    # ------------------------------------------------------------------ #
    # 2. Split known patterns (SxxExxx → Sxx + Exxx)
    # ------------------------------------------------------------------ #
    tokens: List[str] = []
    i = 0
    while i < len(raw):
        token = raw[i]

        # SxxExxx → Sxx + Exxx
        m_se = re.fullmatch(r'(S\d{1,3})(E\d{1,4})', token, re.I)
        if m_se:
            tokens.append(m_se.group(1))  # S02
            tokens.append(m_se.group(2))  # E932 (kept whole for now)
            i += 1
            continue

        tokens.append(token)
        i += 1

    # ------------------------------------------------------------------ #
    # 3. Build cumulative prefixes
    # ------------------------------------------------------------------ #
    prefixes: List[str] = []
    seen: set[str] = set()
    cur = ""

    for t in tokens:
        cur += t
        cleaned = cur.strip()

        # Add the current prefix
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            prefixes.append(cleaned)

    # ------------------------------------------------------------------ #
    # 4. Add special variants for Exxx patterns in the correct order
    # ------------------------------------------------------------------ #
    final_prefixes = []

    for prefix in prefixes:
        final_prefixes.append(prefix)

        # Check if this prefix ends with standalone Exxx (not part of SxxExxx)
        # We'll check if it ends with Exxx and doesn't have Sxx before it
        if re.search(r'E\d{1,4}$', prefix, re.I) and not re.search(r'S\d{1,3}E\d{1,4}$', prefix, re.I):
            # Add version without E (just numbers)
            without_e = re.sub(r'E(\d{1,4})$', r'\1', prefix, flags=re.I)
            if without_e and without_e not in seen:
                seen.add(without_e)
                final_prefixes.append(without_e)

        # Special case: if we have SxxExxx, we need to insert E932 and 932 after S02
        s_e_match = re.search(r'(S\d{1,3})(E\d{1,4})$', prefix, re.I)
        if s_e_match:
            # Extract the part before Sxx
            before_s = prefix[:-len(s_e_match.group(0))]
            s_part = s_e_match.group(1)  # S02
            e_part = s_e_match.group(2)  # E932

            # Create E932 version (insert between S02E932 and S02)
            e_version = before_s + e_part
            if e_version and e_version not in seen:
                seen.add(e_version)
                final_prefixes.append(e_version)

            # Create 932 version (insert after E932)
            num_version = before_s + e_part[1:]  # Remove the 'E'
            if num_version and num_version not in seen:
                seen.add(num_version)
                final_prefixes.append(num_version)

    final_prefixes.sort(key=lambda x: len(x))

    # Return in reverse order (longest first)
    return final_prefixes[::-1]

# ——— INDIVIDUAL TEST FUNCTIONS ———

def test_season_episode_pattern():
    inp = "abcd efef S02E932"
    expected = [
        "abcd efef S02E932",
        "abcd efef E932",
        "abcd efef 932",
        "abcd efef S02",
        "abcd efef",
        "abcd"
    ]
    result = generate_prefixes(inp)
    assert result == expected, f"\nGot:  {result}\nWant: {expected}"
    print("test_season_episode_pattern: PASS")


def test_episode_only():
    inp = "abcd efef E932"
    expected = [
        "abcd efef E932",
        "abcd efef 932",
        "abcd efef",
        "abcd"
    ]
    result = generate_prefixes(inp)
    assert result == expected, f"\nGot:  {result}\nWant: {expected}"
    print("test_episode_only: PASS")

def test_basic_comma_apostrophe():
    inp = "Now you see me, now you don't"
    expected = [
        "Now you see me, now you don't",
        "Now you see me, now you don'",
        "Now you see me, now you don",
        "Now you see me, now you",
        "Now you see me, now",
        "Now you see me,",
        "Now you see me",
        "Now you see",
        "Now you",
        "Now"
    ]
    result = generate_prefixes(inp)
    assert result == expected, f"\nGot:  {result}\nWant: {expected}"
    print("test_basic_comma_apostrophe: PASS")

def test_hello_world_punctuation():
    inp = "Hello: world! How are you?"
    expected = [
        "Hello: world! How are you?",
        "Hello: world! How are you",
        "Hello: world! How are",
        "Hello: world! How",
        "Hello: world!",
        "Hello: world",
        "Hello:",
        "Hello"
    ]
    result = generate_prefixes(inp)
    assert result == expected, f"\nGot:  {result}\nWant: {expected}"
    print("test_hello_world_punctuation: PASS")

def test_hyphenated():
    inp = "One-two-three"
    expected = [
        "One-two-three",
        "One-two-",
        "One-two",
        "One-",
        "One"
    ]
    result = generate_prefixes(inp)
    assert result == expected, f"\nGot:  {result}\nWant: {expected}"
    print("test_hyphenated: PASS")

def test_no_punctuation():
    inp = "NoPunctuationHere"
    expected = ["NoPunctuationHere"]
    result = generate_prefixes(inp)
    assert result == expected, f"\nGot:  {result}\nWant: {expected}"
    print("test_no_punctuation: PASS")

def test_leading_trailing_spaces():
    inp = "  Leading   spaces  "
    expected = [
        "Leading   spaces",
        "Leading",
    ]
    result = generate_prefixes(inp)
    assert result == expected, f"\nGot:  {result}\nWant: {expected}"
    print("test_leading_trailing_spaces: PASS")

def test_empty_string():
    inp = ""
    expected = []
    result = generate_prefixes(inp)
    assert result == expected, f"\nGot:  {result}\nWant: {expected}"
    print("test_empty_string: PASS")

def test_complex_punctuation():
    inp = "A... B--C!! D???"
    expected = [
        "A... B--C!! D???",
        "A... B--C!! D",
        "A... B--C!!",
        "A... B--C",
        "A... B--",
        "A... B",
        "A...",
        "A"
    ]
    result = generate_prefixes(inp)
    assert result == expected, f"\nGot:  {result}\nWant: {expected}"
    print("test_complex_punctuation: PASS")

def test_multiple_spaces_punctuation():
    inp = "Hi,  there!!  How???"
    expected = [
        "Hi,  there!!  How???",
        "Hi,  there!!  How",
        "Hi,  there!!",
        "Hi,  there",
        "Hi,",
        "Hi"
    ]
    result = generate_prefixes(inp)
    assert result == expected, f"\nGot:  {result}\nWant: {expected}"
    print("test_multiple_spaces_punctuation: PASS")


# ——— RUN ALL TESTS ———
def run_all_tests():
    print("Running generate_prefixes tests...\n")
    tests = [
        test_season_episode_pattern,
        test_episode_only,
        test_basic_comma_apostrophe,
        test_hello_world_punctuation,
        test_hyphenated,
        test_no_punctuation,
        test_leading_trailing_spaces,
        test_empty_string,
        test_complex_punctuation,
        test_multiple_spaces_punctuation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"{test.__name__}: FAIL")
            print(e)
            failed += 1
        except Exception as e:
            print(f"{test.__name__}: ERROR - {e}")
            failed += 1
        print("-" * 50)

    print(f"\nSummary: {passed} PASSED, {failed} FAILED")
    if failed == 0:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED.")


# Run when executed directly
if __name__ == "__main__":
    run_all_tests()