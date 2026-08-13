"""Pure unit tests for the conjugation service -- no DB, no HTTP client.
`grammar_config` is a small hand-built fixture covering just enough of the
regular/irregular shape to exercise both code paths.
"""

import pytest

from app.services.conjugation import ConjugationError, conjugate

GRAMMAR_CONFIG = {
    "conjugation": {
        "regular_endings": {
            "ar": {
                "present": {
                    "indicative": {"yo": "o", "tú": "as", "él": "a"},
                    "subjunctive": {"yo": "e", "tú": "es", "él": "e"},
                },
            },
            "er": {
                "present": {
                    "indicative": {"yo": "o", "tú": "es", "él": "e"},
                    "subjunctive": {"yo": "a", "tú": "as", "él": "a"},
                },
            },
        },
        "irregular_verbs": {
            "ser": {
                "present": {
                    "indicative": {"yo": "soy", "tú": "eres", "él": "es"},
                    # Deliberately no "subjunctive" entry: exercises the
                    # regular-rule fallback for a tense/mood an irregular
                    # verb doesn't override.
                },
            },
            "haber": {
                "present": {"indicative": {"yo": "he", "tú": "has", "él": "ha"}},
            },
        },
        "irregular_participles": {"hacer": "hecho"},
    },
}


def test_regular_ar_verb_present_indicative():
    assert conjugate(GRAMMAR_CONFIG, "hablar", "present", "indicative", "tú") == "hablas"


def test_regular_ar_verb_present_subjunctive():
    assert conjugate(GRAMMAR_CONFIG, "hablar", "present", "subjunctive", "yo") == "hable"


def test_regular_er_verb_present_indicative():
    assert conjugate(GRAMMAR_CONFIG, "comer", "present", "indicative", "él") == "come"


def test_irregular_verb_override_takes_precedence():
    # Regular -er rule would produce "seo"; the irregular table wins.
    assert conjugate(GRAMMAR_CONFIG, "ser", "present", "indicative", "yo") == "soy"


def test_irregular_verb_falls_back_to_regular_rule_for_unlisted_form():
    # "ser" has no subjunctive override in this fixture -- falls back to
    # the regular -er rule, same as any other -er verb. (This fixture is
    # a minimal synthetic shape for exercising the fallback mechanism,
    # not a claim about real Spanish -- "ser" is irregular in subjunctive
    # too; the actual seed grammar_config covers that properly.)
    assert conjugate(GRAMMAR_CONFIG, "ser", "present", "subjunctive", "yo") == "sa"


def test_missing_rule_raises_conjugation_error():
    with pytest.raises(ConjugationError):
        conjugate(GRAMMAR_CONFIG, "hablar", "future", "indicative", "yo")


def test_missing_conjugation_class_raises_conjugation_error():
    # "ir" class has no entry at all in the fixture's regular_endings.
    with pytest.raises(ConjugationError):
        conjugate(GRAMMAR_CONFIG, "vivir", "present", "indicative", "yo")


def test_present_perfect_with_regular_participle():
    # "hablar" has no irregular_participles entry -- falls back to the
    # regular stem + "ado" rule. Auxiliary "he" is haber's irregular yo
    # form.
    assert conjugate(GRAMMAR_CONFIG, "hablar", "present_perfect", "indicative", "yo") == (
        "he hablado"
    )


def test_present_perfect_with_irregular_participle():
    # "hacer" -> "hecho" via the irregular_participles override, not the
    # regular -er "ido" rule (which would wrongly give "hacido").
    assert conjugate(GRAMMAR_CONFIG, "hacer", "present_perfect", "indicative", "tú") == (
        "has hecho"
    )


def test_present_perfect_rejects_non_indicative_mood():
    with pytest.raises(ConjugationError):
        conjugate(GRAMMAR_CONFIG, "hablar", "present_perfect", "subjunctive", "yo")


def test_present_perfect_uses_language_default_auxiliary():
    # A language-level perfect_auxiliary other than the "haber" fallback
    # is honored -- proves this is config-driven, not just the Python
    # default (see PLAN.md's 2026-08-14 "v1 Dutch course" decision).
    config = {
        "conjugation": {
            "regular_endings": {},
            "irregular_verbs": {"hebben": {"present": {"indicative": {"yo": "heb"}}}},
            "irregular_participles": {"werken": "gewerkt"},
            "perfect_auxiliary": "hebben",
        },
    }
    assert conjugate(config, "werken", "present_perfect", "indicative", "yo") == "heb gewerkt"


def test_present_perfect_per_verb_auxiliary_override_wins_over_language_default():
    config = {
        "conjugation": {
            "regular_endings": {},
            "irregular_verbs": {
                "hebben": {"present": {"indicative": {"yo": "heb"}}},
                "zijn": {
                    "perfect_auxiliary": "zijn",
                    "present": {"indicative": {"yo": "ben"}},
                },
                "gaan": {"perfect_auxiliary": "zijn"},
            },
            "irregular_participles": {"gaan": "gegaan"},
            "perfect_auxiliary": "hebben",
        },
    }
    # "gaan" overrides its auxiliary to "zijn" even though the language
    # default is "hebben" -- "ben gegaan", not the wrong "heb gegaan".
    assert conjugate(config, "gaan", "present_perfect", "indicative", "yo") == "ben gegaan"


def test_verb_irregular_in_one_tense_falls_back_regularly_in_another():
    # "ser" is irregular in present (soy) but the fixture gives it no
    # preterite override -- falls back to the regular -er preterite rule
    # for this synthetic fixture (not a real-Spanish claim, same caveat
    # as the subjunctive fallback test above).
    regular_endings_er_preterite = {
        "indicative": {"yo": "í", "tú": "iste", "él": "ió"},
    }
    config = {
        "conjugation": {
            **GRAMMAR_CONFIG["conjugation"],
            "regular_endings": {
                **GRAMMAR_CONFIG["conjugation"]["regular_endings"],
                "er": {
                    **GRAMMAR_CONFIG["conjugation"]["regular_endings"]["er"],
                    "preterite": regular_endings_er_preterite,
                },
            },
        },
    }
    assert conjugate(config, "ser", "preterite", "indicative", "yo") == "sí"
