"""Generates conjugated verb forms from a `Language.grammar_config` dict
(app/models/language.py) rather than storing every form per verb -- see
PLAN.md's 2026-08-13 "Conjugation/subjunctive feature design resolved"
decision. Pure function, no DB access; callers pass in the target
language's `grammar_config` already loaded.

Expected `grammar_config["conjugation"]` shape:
    {
      "regular_endings": {"ar": {tense: {mood: {pronoun: ending}}}, "er": {...}, "ir": {...}},
      "irregular_verbs": {
        infinitive: {
          "perfect_auxiliary": str,  # optional, overrides the language default below
          tense: {mood: {pronoun: full_form}}, ...
        }, ...
      },
      "irregular_participles": {infinitive: participle, ...},
      "perfect_auxiliary": str,  # language-wide default auxiliary infinitive for present_perfect
    }

`perfect_auxiliary` exists because compound-tense auxiliaries aren't
universal: Spanish always uses "haber", but Dutch splits by verb (most
verbs use "hebben", motion/change-of-state verbs like "gaan" use "zijn")
-- see PLAN.md's 2026-08-14 "v1 Dutch course" decision. The per-verb
override in `irregular_verbs` covers the exceptions; the language-level
key is the default for everything else.
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

    The regular-rule fallback is Spanish's own suffix pattern specifically,
    not a generic one -- e.g. Dutch participles are "ge-" + stem + "-d"/"-t"
    (prefix and suffix, with the suffix choice itself governed by a
    spelling rule), which this fallback can't produce. Languages where the
    fallback doesn't apply are expected to cover every verb they use via
    `irregular_participles` explicitly instead (see PLAN.md's 2026-08-14
    "v1 Dutch course" decision) -- building a genuinely pluggable
    participle-formation rule is premature with only two languages;
    revisit if a third one also can't use this fallback.
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

    `tense="present_perfect"` is a compound tense, handled separately:
    the result is the auxiliary verb (see module docstring for how it's
    chosen -- per-verb override, else the language default) conjugated
    in the present indicative (a recursive call to this same function,
    so it goes through the exact same irregular-then-regular lookup)
    plus `infinitive`'s past participle. Only `mood="indicative"` is
    supported for it (present perfect subjunctive -- "haya hablado" --
    is out of scope for now); any other mood raises rather than
    silently ignoring the argument.
    """
    conjugation_config = grammar_config.get("conjugation", {})

    if tense == "present_perfect":
        if mood != "indicative":
            raise ConjugationError(
                f"present_perfect only supports mood='indicative', got {mood!r}"
            )
        irregular_entry = conjugation_config.get("irregular_verbs", {}).get(infinitive, {})
        auxiliary_infinitive = irregular_entry.get(
            "perfect_auxiliary", conjugation_config.get("perfect_auxiliary", "haber")
        )
        auxiliary = conjugate(
            grammar_config, auxiliary_infinitive, "present", "indicative", pronoun
        )
        return f"{auxiliary} {_participle(grammar_config, infinitive)}"

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
