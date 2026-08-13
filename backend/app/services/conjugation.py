"""Generates conjugated verb forms from a `Language.grammar_config` dict
(app/models/language.py) rather than storing every form per verb -- see
PLAN.md's 2026-08-13 "Conjugation/subjunctive feature design resolved"
decision. Pure function, no DB access; callers pass in the target
language's `grammar_config` already loaded.

Expected `grammar_config["conjugation"]` shape:
    {
      "regular_endings": {"ar": {tense: {mood: {pronoun: ending}}}, "er": {...}, "ir": {...}},
      "irregular_verbs": {infinitive: {tense: {mood: {pronoun: full_form}}}, ...},
      "irregular_participles": {infinitive: participle, ...}
    }
"""


class ConjugationError(Exception):
    """No rule exists for the requested infinitive/tense/mood/pronoun --
    a config gap or a bad request. Callers must handle this explicitly
    rather than the service guessing or silently returning a wrong form.
    """


def _participle(grammar_config: dict, infinitive: str) -> str:
    """Irregular override first, else the regular rule: stem + "ado" for
    -ar verbs, stem + "ido" for -er/-ir verbs. Participles don't vary by
    person -- in a compound tense, the auxiliary is the only part that
    conjugates.
    """
    conjugation_config = grammar_config.get("conjugation", {})
    irregular = conjugation_config.get("irregular_participles", {})
    if infinitive in irregular:
        return irregular[infinitive]

    verb_class = infinitive[-2:]
    stem = infinitive[:-2]
    suffix = "ado" if verb_class == "ar" else "ido"
    return stem + suffix


def conjugate(grammar_config: dict, infinitive: str, tense: str, mood: str, pronoun: str) -> str:
    """Checks `irregular_verbs` first; falls back to `regular_endings` for
    the infinitive's conjugation class (its last two characters, e.g.
    "ar"). Real irregular verbs are usually irregular in only some
    tenses/moods, so an `irregular_verbs` entry only needs to cover the
    forms that actually differ -- everything else still falls back to the
    regular rule for that verb's class.

    `tense="present_perfect"` is a compound tense, handled separately: the
    result is "haber" conjugated in the present indicative (a recursive
    call to this same function, so it goes through the exact same
    irregular-then-regular lookup) plus `infinitive`'s past participle.
    Only `mood="indicative"` is supported for it (present perfect
    subjunctive -- "haya hablado" -- is out of scope for now); any other
    mood raises rather than silently ignoring the argument.
    """
    if tense == "present_perfect":
        if mood != "indicative":
            raise ConjugationError(
                f"present_perfect only supports mood='indicative', got {mood!r}"
            )
        auxiliary = conjugate(grammar_config, "haber", "present", "indicative", pronoun)
        return f"{auxiliary} {_participle(grammar_config, infinitive)}"

    conjugation_config = grammar_config.get("conjugation", {})

    irregular = conjugation_config.get("irregular_verbs", {}).get(infinitive, {})
    override = irregular.get(tense, {}).get(mood, {}).get(pronoun)
    if override is not None:
        return override

    verb_class = infinitive[-2:]
    stem = infinitive[:-2]
    try:
        ending = conjugation_config["regular_endings"][verb_class][tense][mood][pronoun]
    except KeyError as exc:
        raise ConjugationError(
            f"no conjugation rule for {infinitive!r} ({tense}/{mood}/{pronoun})"
        ) from exc
    return stem + ending
