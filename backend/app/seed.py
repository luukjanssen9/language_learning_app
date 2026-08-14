"""Populates starter English->Spanish course content: a couple of vocab
skills (proving the generic exercise engine), the "Verb Conjugation"
skill (proving the CONJUGATION exercise type + grammar_config-driven
generation, including the present-perfect compound tense), and the three
subjunctive-trigger skills. Idempotent -- looks up by a natural key
before creating, same convention as `frontend/src/lib/bootstrap.ts`; for
exercises specifically, this means delete-then-recreate (see
`_delete_existing_exercises`) so re-running always converges on exactly
this file's current content rather than silently keeping stale rows from
an earlier version of the script.

Run via: docker compose exec backend python -m app.seed

Uses the ORM directly against `AsyncSessionLocal` rather than going
through the HTTP API (unlike frontend/bootstrap.ts, which has no other
way to reach the backend) -- this is a one-off management script, not
app logic serving a request.
"""

import asyncio

from sqlalchemy import delete, select

from app.database import AsyncSessionLocal
from app.models.course import Course
from app.models.deck import Deck
from app.models.enums import ExerciseType
from app.models.language import Language
from app.models.lesson_exercise import LessonExercise, LessonExerciseVocabulary
from app.models.skill import Skill
from app.models.user import User
from app.models.user_exercise_attempt import UserExerciseAttempt
from app.models.vocabulary import VocabularyItem
from app.services.note_cards import build_cards_for_note

# Matches frontend/src/lib/bootstrap.ts's codes/slug exactly, so the app's
# silent bootstrap and this seed script converge on the same rows instead
# of creating a second, duplicate English/Spanish/course set.
EN_CODE = "en"
ES_CODE = "es"
COURSE_SLUG = "en-es"

# Matches bootstrap.ts's own DEFAULT_USER_EMAIL/DEFAULT_USER_DISPLAY_NAME
# literals exactly, so a note-seeding deck created here (see
# _get_or_create_user below) converges on the same single user the
# frontend's silent bootstrap creates/reuses, rather than a second one.
DEFAULT_USER_EMAIL = "you@example.com"
DEFAULT_USER_DISPLAY_NAME = "Learner"

# Dutch (2026-08-14 "v1 Dutch course" decision): a second language,
# specifically to prove this project's "language-agnostic by design"
# principle against something other than Spanish -- see the three
# hardcoded-to-Spanish spots that decision's PLAN.md entry documents
# finding and fixing along the way.
NL_CODE = "nl"
DUTCH_COURSE_SLUG = "en-nl"

# Chinese (2026-08-14 "Anki-style vocab decks" decision): a third language,
# specifically the one that needed the recognition/production card split
# and transliteration handling the vocab-deck feature was designed around
# -- see grammar_config["vocab_deck"] below and app/services/note_cards.py.
# No lesson/skill content for Chinese (unlike Spanish/Dutch) -- this
# language exists purely to prove the Anki-deck side of the app, per the
# user's own spec, which scopes conjugation/lesson practice out entirely.
ZH_CODE = "zh"
CHINESE_COURSE_SLUG = "en-zh"

# Six-person paradigm. "él" also covers "ella"/"usted" and "ellos" also
# covers "ellas"/"ustedes" -- those pairs conjugate identically in Spanish,
# so this is the one set of internal keys; the frontend's conjugation
# drill displays "usted"/"ustedes" as friendlier labels for those two
# slots without needing separate data.
_PRONOUNS = ("yo", "tú", "él", "nosotros", "vosotros", "ellos")


def _forms(yo: str, tu: str, el: str, nosotros: str, vosotros: str, ellos: str) -> dict:
    """Zips six literal forms onto `_PRONOUNS` -- shorter than repeating
    the six keys at every tense/mood cell below.
    """
    return dict(zip(_PRONOUNS, (yo, tu, el, nosotros, vosotros, ellos), strict=True))


SPANISH_GRAMMAR_CONFIG = {
    "conjugation": {
        "regular_endings": {
            "ar": {
                "present": {
                    "indicative": _forms("o", "as", "a", "amos", "áis", "an"),
                    "subjunctive": _forms("e", "es", "e", "emos", "éis", "en"),
                },
                "preterite": {
                    "indicative": _forms("é", "aste", "ó", "amos", "asteis", "aron"),
                },
                "imperfect": {
                    "indicative": _forms("aba", "abas", "aba", "ábamos", "abais", "aban"),
                },
                "future": {
                    "indicative": _forms("aré", "arás", "ará", "aremos", "aréis", "arán"),
                },
            },
            "er": {
                "present": {
                    "indicative": _forms("o", "es", "e", "emos", "éis", "en"),
                    "subjunctive": _forms("a", "as", "a", "amos", "áis", "an"),
                },
                "preterite": {
                    "indicative": _forms("í", "iste", "ió", "imos", "isteis", "ieron"),
                },
                "imperfect": {
                    "indicative": _forms("ía", "ías", "ía", "íamos", "íais", "ían"),
                },
                "future": {
                    "indicative": _forms("eré", "erás", "erá", "eremos", "eréis", "erán"),
                },
            },
            "ir": {
                "present": {
                    "indicative": _forms("o", "es", "e", "imos", "ís", "en"),
                    "subjunctive": _forms("a", "as", "a", "amos", "áis", "an"),
                },
                "preterite": {
                    "indicative": _forms("í", "iste", "ió", "imos", "isteis", "ieron"),
                },
                "imperfect": {
                    "indicative": _forms("ía", "ías", "ía", "íamos", "íais", "ían"),
                },
                "future": {
                    "indicative": _forms("iré", "irás", "irá", "iremos", "iréis", "irán"),
                },
            },
        },
        # Only the cells where each verb is actually irregular -- anything
        # not listed here for a given verb falls back to the regular rule
        # for its class (last two letters of the infinitive). Every verb
        # in CONJUGATION_VERBS below is covered for every tense/mood combo
        # in CONJUGATION_TENSE_MOOD_COMBOS, either here or via that
        # fallback, so the seed loop never generates an exercise the
        # config can't resolve.
        "irregular_verbs": {
            "ser": {
                "present": {
                    "indicative": _forms("soy", "eres", "es", "somos", "sois", "son"),
                    "subjunctive": _forms("sea", "seas", "sea", "seamos", "seáis", "sean"),
                },
                "preterite": {
                    "indicative": _forms("fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"),
                },
            },
            "estar": {
                "present": {
                    "indicative": _forms(
                        "estoy", "estás", "está", "estamos", "estáis", "están"
                    ),
                    "subjunctive": _forms(
                        "esté", "estés", "esté", "estemos", "estéis", "estén"
                    ),
                },
                "preterite": {
                    "indicative": _forms(
                        "estuve", "estuviste", "estuvo",
                        "estuvimos", "estuvisteis", "estuvieron",
                    ),
                },
            },
            "tener": {
                "present": {
                    "indicative": _forms(
                        "tengo", "tienes", "tiene", "tenemos", "tenéis", "tienen"
                    ),
                    "subjunctive": _forms(
                        "tenga", "tengas", "tenga", "tengamos", "tengáis", "tengan"
                    ),
                },
                "preterite": {
                    "indicative": _forms(
                        "tuve", "tuviste", "tuvo", "tuvimos", "tuvisteis", "tuvieron"
                    ),
                },
                "future": {
                    "indicative": _forms(
                        "tendré", "tendrás", "tendrá", "tendremos", "tendréis", "tendrán"
                    ),
                },
            },
            "ir": {
                "present": {
                    "indicative": _forms("voy", "vas", "va", "vamos", "vais", "van"),
                    "subjunctive": _forms(
                        "vaya", "vayas", "vaya", "vayamos", "vayáis", "vayan"
                    ),
                },
                "preterite": {
                    "indicative": _forms("fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"),
                },
                "imperfect": {
                    "indicative": _forms("iba", "ibas", "iba", "íbamos", "ibais", "iban"),
                },
            },
            "hacer": {
                "present": {
                    "indicative": _forms(
                        "hago", "haces", "hace", "hacemos", "hacéis", "hacen"
                    ),
                    "subjunctive": _forms(
                        "haga", "hagas", "haga", "hagamos", "hagáis", "hagan"
                    ),
                },
                "preterite": {
                    "indicative": _forms(
                        "hice", "hiciste", "hizo", "hicimos", "hicisteis", "hicieron"
                    ),
                },
                "future": {
                    "indicative": _forms("haré", "harás", "hará", "haremos", "haréis", "harán"),
                },
            },
            "poder": {
                "present": {
                    "indicative": _forms(
                        "puedo", "puedes", "puede", "podemos", "podéis", "pueden"
                    ),
                    "subjunctive": _forms(
                        "pueda", "puedas", "pueda", "podamos", "podáis", "puedan"
                    ),
                },
                "preterite": {
                    "indicative": _forms(
                        "pude", "pudiste", "pudo", "pudimos", "pudisteis", "pudieron"
                    ),
                },
                "future": {
                    "indicative": _forms(
                        "podré", "podrás", "podrá", "podremos", "podréis", "podrán"
                    ),
                },
            },
            "querer": {
                "present": {
                    "indicative": _forms(
                        "quiero", "quieres", "quiere", "queremos", "queréis", "quieren"
                    ),
                    "subjunctive": _forms(
                        "quiera", "quieras", "quiera", "queramos", "queráis", "quieran"
                    ),
                },
                "preterite": {
                    "indicative": _forms(
                        "quise", "quisiste", "quiso", "quisimos", "quisisteis", "quisieron"
                    ),
                },
                "future": {
                    "indicative": _forms(
                        "querré", "querrás", "querrá", "querremos", "querréis", "querrán"
                    ),
                },
            },
            "decir": {
                "present": {
                    "indicative": _forms(
                        "digo", "dices", "dice", "decimos", "decís", "dicen"
                    ),
                    "subjunctive": _forms(
                        "diga", "digas", "diga", "digamos", "digáis", "digan"
                    ),
                },
                "preterite": {
                    "indicative": _forms(
                        "dije", "dijiste", "dijo", "dijimos", "dijisteis", "dijeron"
                    ),
                },
                "future": {
                    "indicative": _forms("diré", "dirás", "dirá", "diremos", "diréis", "dirán"),
                },
            },
            "venir": {
                "present": {
                    "indicative": _forms(
                        "vengo", "vienes", "viene", "venimos", "venís", "vienen"
                    ),
                    "subjunctive": _forms(
                        "venga", "vengas", "venga", "vengamos", "vengáis", "vengan"
                    ),
                },
                "preterite": {
                    "indicative": _forms(
                        "vine", "viniste", "vino", "vinimos", "vinisteis", "vinieron"
                    ),
                },
                "future": {
                    "indicative": _forms(
                        "vendré", "vendrás", "vendrá", "vendremos", "vendréis", "vendrán"
                    ),
                },
            },
            "poner": {
                "present": {
                    "indicative": _forms(
                        "pongo", "pones", "pone", "ponemos", "ponéis", "ponen"
                    ),
                    "subjunctive": _forms(
                        "ponga", "pongas", "ponga", "pongamos", "pongáis", "pongan"
                    ),
                },
                "preterite": {
                    "indicative": _forms(
                        "puse", "pusiste", "puso", "pusimos", "pusisteis", "pusieron"
                    ),
                },
                "future": {
                    "indicative": _forms(
                        "pondré", "pondrás", "pondrá", "pondremos", "pondréis", "pondrán"
                    ),
                },
            },
            "salir": {
                "present": {
                    "indicative": _forms(
                        "salgo", "sales", "sale", "salimos", "salís", "salen"
                    ),
                    "subjunctive": _forms(
                        "salga", "salgas", "salga", "salgamos", "salgáis", "salgan"
                    ),
                },
                "future": {
                    "indicative": _forms(
                        "saldré", "saldrás", "saldrá", "saldremos", "saldréis", "saldrán"
                    ),
                },
            },
            "saber": {
                "present": {
                    "indicative": _forms("sé", "sabes", "sabe", "sabemos", "sabéis", "saben"),
                    "subjunctive": _forms(
                        "sepa", "sepas", "sepa", "sepamos", "sepáis", "sepan"
                    ),
                },
                "preterite": {
                    "indicative": _forms(
                        "supe", "supiste", "supo", "supimos", "supisteis", "supieron"
                    ),
                },
                "future": {
                    "indicative": _forms(
                        "sabré", "sabrás", "sabrá", "sabremos", "sabréis", "sabrán"
                    ),
                },
            },
            "dar": {
                "present": {
                    "indicative": _forms("doy", "das", "da", "damos", "dais", "dan"),
                    "subjunctive": _forms("dé", "des", "dé", "demos", "deis", "den"),
                },
                "preterite": {
                    "indicative": _forms("di", "diste", "dio", "dimos", "disteis", "dieron"),
                },
            },
            "ver": {
                "present": {
                    "indicative": _forms("veo", "ves", "ve", "vemos", "veis", "ven"),
                    "subjunctive": _forms(
                        "vea", "veas", "vea", "veamos", "veáis", "vean"
                    ),
                },
                "preterite": {
                    "indicative": _forms("vi", "viste", "vio", "vimos", "visteis", "vieron"),
                },
                "imperfect": {
                    "indicative": _forms(
                        "veía", "veías", "veía", "veíamos", "veíais", "veían"
                    ),
                },
            },
            "haber": {
                # Present indicative only -- haber is used here purely as
                # the present-perfect auxiliary (see conjugate()'s
                # tense="present_perfect" branch), not drilled on its own.
                "present": {"indicative": _forms("he", "has", "ha", "hemos", "habéis", "han")},
            },
        },
        # Only the four irregulars among CONJUGATION_VERBS -- everything
        # else (including "dar" -> "dado" and "ir" -> "ido", both of
        # which happen to be produced correctly by the regular rule)
        # falls back to stem + "ado"/"ido".
        "irregular_participles": {
            "hacer": "hecho",
            "decir": "dicho",
            "poner": "puesto",
            "ver": "visto",
        },
        # Spanish only ever needs one auxiliary -- explicit here (rather
        # than relying on conjugate()'s Python-level "haber" fallback,
        # which now exists only for backward-compat with small synthetic
        # test fixtures) since Dutch's config declares this too, and
        # per-verb overrides are only possible when a language default
        # exists to override (see PLAN.md's 2026-08-14 "v1 Dutch course"
        # decision).
        "perfect_auxiliary": "haber",
        # Rendered by the conjugation drill (ConjugationDrill.tsx)
        # instead of a hardcoded label array -- "usted"/"ustedes" for the
        # 3rd-person slots since usted/él and ustedes/ellos conjugate
        # identically; the internal keys themselves stay literal Spanish
        # words purely as historical opaque identifiers (see the
        # 2026-08-14 decision for why they aren't renamed).
        "pronoun_labels": {
            "yo": "yo", "tú": "tú", "él": "usted",
            "nosotros": "nosotros", "vosotros": "vosotros", "ellos": "ustedes",
        },
    },
    # Spanish reading/writing isn't a distinct skill the way Chinese
    # recognition/production is (same alphabet the user already knows) --
    # one card per note, read generically by app/services/note_cards.py,
    # not a hardcoded "if language != chinese" anywhere (2026-08-14
    # "Anki-style vocab decks" decision).
    "vocab_deck": {"dual_direction_cards": False},
    # Voice confirmed against a live list_voices() call against the real
    # API (not guessed) -- WaveNet tier specifically, since that's the
    # tier this app's free-tier cost analysis was based on (Chirp/Studio
    # voices are newer/premium and not reliably free).
    "tts": {"language_code": "es-ES", "voice_name": "es-ES-Wavenet-F"},
    # Rendered generically by the frontend (lib/practiceCategories.ts),
    # not hardcoded per-language category names in component logic --
    # `key` matches Skill.specialty_module (None for the plain vocab
    # skills), `slug` is the URL segment (kept distinct from `key`
    # specifically because `key` can be None, which can't go in a URL),
    # `kind` is the small closed set the frontend switches UI shape on.
    "practice_categories": [
        # "vocabulary" retired 2026-08-14 in favor of "reading" -- see
        # PLAN.md's "Vocabulary -> Reading" decision: it duplicated the
        # Anki vocab decks with a weaker (non-SRS) mechanism, and reading
        # passages are generated per-course from known vocabulary rather
        # than pre-authored, so this category needs no matching Skill at
        # all (key stays None). The old Greetings/Family Skill rows are
        # left in place, just unreferenced by the UI -- fully reversible.
        {"slug": "reading", "key": None, "label": "Reading", "kind": "reading_passage"},
        {
            "slug": "verb-conjugation",
            "key": "spanish-verb-conjugation",
            "label": "Verb Conjugation",
            "kind": "conjugation_drill",
        },
        {
            "slug": "subjunctive",
            "key": "spanish-subjunctive-triggers",
            "label": "Subjunctive",
            "kind": "skill_list",
        },
    ],
}


DUTCH_GRAMMAR_CONFIG = {
    "conjugation": {
        # Best-effort simple present-tense rule, kept for architectural
        # completeness -- not actually exercised by DUTCH_CONJUGATION_VERBS
        # below, all of which are fully specified via irregular_verbs
        # instead. Dutch has real spelling rules (open/closed-syllable
        # vowel doubling, e.g. "wonen" -> stem "woon" not "won") that a
        # naive infinitive-minus-two-letters stem can't reproduce -- see
        # _participle()'s docstring for the same issue on the participle
        # side. Every verb chosen for this course avoids the doubling
        # trap for present tense specifically, but relying on that by
        # convention rather than modeling the rule felt too fragile to
        # extend to new verbs later, so nothing here actually depends on
        # this fallback resolving correctly.
        "regular_endings": {
            "en": {
                "present": {"indicative": _forms("", "t", "t", "en", "en", "en")},
            },
        },
        "irregular_verbs": {
            "zijn": {
                "perfect_auxiliary": "zijn",
                "present": {
                    "indicative": _forms("ben", "bent", "is", "zijn", "zijn", "zijn"),
                },
                "past": {
                    "indicative": _forms("was", "was", "was", "waren", "waren", "waren"),
                },
            },
            "hebben": {
                "present": {
                    "indicative": _forms(
                        "heb", "hebt", "heeft", "hebben", "hebben", "hebben"
                    ),
                },
                "past": {
                    "indicative": _forms(
                        "had", "had", "had", "hadden", "hadden", "hadden"
                    ),
                },
            },
            "gaan": {
                "perfect_auxiliary": "zijn",
                "present": {
                    "indicative": _forms("ga", "gaat", "gaat", "gaan", "gaan", "gaan"),
                },
                "past": {
                    "indicative": _forms(
                        "ging", "ging", "ging", "gingen", "gingen", "gingen"
                    ),
                },
            },
            "komen": {
                "perfect_auxiliary": "zijn",
                "present": {
                    "indicative": _forms(
                        "kom", "komt", "komt", "komen", "komen", "komen"
                    ),
                },
                "past": {
                    "indicative": _forms(
                        "kwam", "kwam", "kwam", "kwamen", "kwamen", "kwamen"
                    ),
                },
            },
            "werken": {
                "present": {
                    "indicative": _forms(
                        "werk", "werkt", "werkt", "werken", "werken", "werken"
                    ),
                },
                # "werk" ends in "k" (a "'t kofschip" consonant) -> "-te",
                # not the "-de" that "wonen"/"spelen" below take. Same
                # spelling-rule shape as Spanish's kofschip-adjacent
                # accent overrides -- a per-verb override, not a second
                # regular class, since the infinitive ending alone
                # ("-en") can't distinguish the two.
                "past": {
                    "indicative": _forms(
                        "werkte", "werkte", "werkte",
                        "werkten", "werkten", "werkten",
                    ),
                },
            },
            "maken": {
                "present": {
                    "indicative": _forms(
                        "maak", "maakt", "maakt", "maken", "maken", "maken"
                    ),
                },
                "past": {
                    "indicative": _forms(
                        "maakte", "maakte", "maakte",
                        "maakten", "maakten", "maakten",
                    ),
                },
            },
            "wonen": {
                "present": {
                    "indicative": _forms(
                        "woon", "woont", "woont", "wonen", "wonen", "wonen"
                    ),
                },
                "past": {
                    "indicative": _forms(
                        "woonde", "woonde", "woonde",
                        "woonden", "woonden", "woonden",
                    ),
                },
            },
            "spelen": {
                "present": {
                    "indicative": _forms(
                        "speel", "speelt", "speelt", "spelen", "spelen", "spelen"
                    ),
                },
                "past": {
                    "indicative": _forms(
                        "speelde", "speelde", "speelde",
                        "speelden", "speelden", "speelden",
                    ),
                },
            },
        },
        # Every verb this course drills provides its participle here --
        # see _participle()'s docstring for why Dutch doesn't use the
        # regular-fallback rule at all (it's Spanish's own suffix
        # pattern, not a generic one).
        "irregular_participles": {
            "zijn": "geweest",
            "hebben": "gehad",
            "gaan": "gegaan",
            "komen": "gekomen",
            "werken": "gewerkt",
            "maken": "gemaakt",
            "wonen": "gewoond",
            "spelen": "gespeeld",
        },
        # Most Dutch verbs take "hebben"; motion/change-of-state verbs
        # (gaan, komen, and zijn itself) override to "zijn" above -- see
        # conjugate()'s module docstring for how the two combine.
        "perfect_auxiliary": "hebben",
        "pronoun_labels": {
            "yo": "ik", "tú": "jij", "él": "hij",
            "nosotros": "wij", "vosotros": "jullie", "ellos": "zij",
        },
    },
    # Dutch uses the same Latin alphabet the user already knows -- no
    # recognition/production split needed, same reasoning as Spanish's.
    "vocab_deck": {"dual_direction_cards": False},
    # No "subjunctive" entry -- Dutch's subjunctive is archaic/non-
    # productive in modern usage, not a gap in the app (2026-08-14
    # decision, on request).
    "practice_categories": [
        # "vocabulary" -> "reading" retired the same way as Spanish's --
        # see that config's comment just above for the full reasoning.
        {"slug": "reading", "key": None, "label": "Reading", "kind": "reading_passage"},
        {
            "slug": "verb-conjugation",
            "key": "dutch-verb-conjugation",
            "label": "Verb Conjugation",
            "kind": "conjugation_drill",
        },
    ],
}


CHINESE_GRAMMAR_CONFIG = {
    # No "conjugation" key -- Chinese has no pre-authored lesson content in
    # this app (yet); it exists specifically to prove the Anki-deck
    # feature's recognition/production split and transliteration handling
    # generalize to a language that actually needs them, per the user's
    # own spec (2026-08-14 "Anki-style vocab decks" decision).
    #
    # "practice_categories" DOES get an entry, though (2026-08-14, "reading
    # passage generation") -- reading passages are generated per-course
    # from known vocabulary, not pre-authored Skill/LessonExercise content,
    # so they need zero lesson-content investment to work. This is the
    # first practice content Chinese gets in this app, and specifically
    # tests that the reading-passage feature generalizes to a language
    # with no Skills at all.
    "practice_categories": [
        {"slug": "reading", "key": None, "label": "Reading", "kind": "reading_passage"},
    ],
    "vocab_deck": {
        "dual_direction_cards": True,
        "needs_transliteration": True,
        "transliteration_label": "Pinyin",
        # A production card unlocks once EITHER condition is met, not
        # both: a fast learner shouldn't have to wait out the clock, and a
        # slow-but-persistent one shouldn't stay stuck forever short of
        # the review count. See api/routes/cards.py's list_due_cards for
        # where this is read and checked.
        "production_gate": {
            "min_successful_recognition_reviews": 5,
            "min_days_since_note_added": 14,
        },
    },
    # Mandarin's tones are the whole reason this feature exists -- WaveNet
    # tier, verified against a live list_voices() call (see Spanish's tts
    # key above for why WaveNet specifically).
    "tts": {"language_code": "cmn-CN", "voice_name": "cmn-CN-Wavenet-A"},
}


async def _get_or_create_language(session, code: str, name: str) -> Language:
    result = await session.execute(select(Language).where(Language.code == code))
    language = result.scalar_one_or_none()
    if language is None:
        language = Language(code=code, name=name)
        session.add(language)
        await session.flush()
    return language


async def _get_or_create_course(
    session, base: Language, target: Language, *, name: str, slug: str
) -> Course:
    result = await session.execute(
        select(Course).where(
            Course.base_language_id == base.id, Course.target_language_id == target.id
        )
    )
    course = result.scalar_one_or_none()
    if course is None:
        course = Course(
            base_language_id=base.id,
            target_language_id=target.id,
            name=name,
            slug=slug,
        )
        session.add(course)
        await session.flush()
    return course


async def _get_or_create_skill(
    session,
    course: Course,
    *,
    slug: str,
    name: str,
    order_index: int,
    prerequisite: Skill | None = None,
    specialty_module: str | None = None,
) -> Skill:
    result = await session.execute(
        select(Skill).where(Skill.course_id == course.id, Skill.slug == slug)
    )
    skill = result.scalar_one_or_none()
    if skill is None:
        skill = Skill(
            course_id=course.id,
            name=name,
            slug=slug,
            order_index=order_index,
            prerequisite_skill_id=prerequisite.id if prerequisite else None,
            specialty_module=specialty_module,
        )
        session.add(skill)
        await session.flush()
    return skill


async def _delete_existing_exercises(session, skill: Skill) -> None:
    """Deletes this skill's existing exercises -- and any
    UserExerciseAttempt/LessonExerciseVocabulary rows referencing them --
    before regenerating. Makes the seed script fully idempotent and
    convergent on this file's current content, rather than the previous
    "skip if anything already exists" check, which meant a content change
    here would silently never reach an already-seeded dev DB. This does
    mean re-running after a content change wipes practice history tied to
    that skill's old exercise rows -- acceptable for dev seed content
    (see PLAN.md's "dev DB accumulates test debris" note), not real user
    data.
    """
    result = await session.execute(
        select(LessonExercise.id).where(LessonExercise.skill_id == skill.id)
    )
    exercise_ids = [row[0] for row in result.all()]
    if not exercise_ids:
        return
    await session.execute(
        delete(UserExerciseAttempt).where(UserExerciseAttempt.exercise_id.in_(exercise_ids))
    )
    await session.execute(
        delete(LessonExerciseVocabulary).where(
            LessonExerciseVocabulary.lesson_exercise_id.in_(exercise_ids)
        )
    )
    await session.execute(delete(LessonExercise).where(LessonExercise.id.in_(exercise_ids)))
    await session.flush()


async def _get_or_create_vocab(
    session, course: Course, target_text: str, base_text: str, part_of_speech: str | None = None
) -> VocabularyItem:
    result = await session.execute(
        select(VocabularyItem).where(
            VocabularyItem.course_id == course.id, VocabularyItem.target_text == target_text
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        item = VocabularyItem(
            course_id=course.id,
            target_text=target_text,
            base_text=base_text,
            part_of_speech=part_of_speech,
        )
        session.add(item)
        await session.flush()
    return item


async def _get_or_create_user(session) -> User:
    """Reuses whichever user already exists (same "just take the first
    one" convention as bootstrap.ts's own `users[0] ?? create(...)`),
    creating the same placeholder bootstrap.ts would if neither has run
    yet -- avoids this script and the frontend's silent bootstrap ever
    creating two different single users.
    """
    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=DEFAULT_USER_EMAIL, display_name=DEFAULT_USER_DISPLAY_NAME)
        session.add(user)
        await session.flush()
    return user


async def _get_or_create_deck(session, user: User, course: Course, *, name: str) -> Deck:
    result = await session.execute(
        select(Deck).where(Deck.course_id == course.id, Deck.name == name)
    )
    deck = result.scalar_one_or_none()
    if deck is None:
        deck = Deck(user_id=user.id, course_id=course.id, name=name)
        session.add(deck)
        await session.flush()
    return deck


async def _seed_note(
    session,
    course: Course,
    deck: Deck,
    target_language: Language,
    *,
    target_text: str,
    base_text: str,
    part_of_speech: str | None = None,
    source: str | None = None,
    example_sentence: str | None = None,
    example_sentence_translation: str | None = None,
    tags: list[str] | None = None,
    attributes: dict | None = None,
) -> VocabularyItem:
    """Like _get_or_create_vocab, but for real-input Anki-deck notes: also
    populates the note-specific fields (source, example sentence, tags)
    and generates this note's Card(s) via the same
    build_cards_for_note() the live quick-add endpoint uses (see
    api/routes/cards.py), so seeded content is verified through the real
    card-generation path, not a hand-rolled shortcut. Only runs
    build_cards_for_note() the first time a note is created -- re-running
    the seed script must stay idempotent and not spawn duplicate cards
    for a note that already exists.
    """
    result = await session.execute(
        select(VocabularyItem).where(
            VocabularyItem.course_id == course.id, VocabularyItem.target_text == target_text
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        item = VocabularyItem(
            course_id=course.id,
            target_text=target_text,
            base_text=base_text,
            part_of_speech=part_of_speech,
            source=source,
            example_sentence=example_sentence,
            example_sentence_translation=example_sentence_translation,
            tags=tags or [],
            attributes=attributes or {},
        )
        session.add(item)
        await session.flush()
        session.add_all(build_cards_for_note(deck.id, item.id, target_language))
    return item


async def _add_exercise(
    session,
    skill: Skill,
    exercise_type: ExerciseType,
    prompt: dict,
    order_index: int,
    *,
    vocab: VocabularyItem | None = None,
    specialty_module: str | None = None,
) -> None:
    exercise = LessonExercise(
        skill_id=skill.id,
        exercise_type=exercise_type,
        prompt=prompt,
        order_index=order_index,
        specialty_module=specialty_module,
    )
    session.add(exercise)
    await session.flush()
    if vocab is not None:
        session.add(
            LessonExerciseVocabulary(lesson_exercise_id=exercise.id, vocabulary_item_id=vocab.id)
        )


async def _seed_greetings_skill(session, course: Course) -> Skill:
    skill = await _get_or_create_skill(
        session, course, slug="greetings", name="Greetings", order_index=0
    )
    await _delete_existing_exercises(session, skill)

    hola = await _get_or_create_vocab(session, course, "hola", "hello")
    adios = await _get_or_create_vocab(session, course, "adiós", "goodbye")
    gracias = await _get_or_create_vocab(session, course, "gracias", "thank you")

    await _add_exercise(
        session, skill, ExerciseType.MULTIPLE_CHOICE,
        {
            "question": "How do you say 'hello'?",
            "options": ["hola", "adiós", "gracias"],
            "correct_index": 0,
        },
        0, vocab=hola,
    )
    await _add_exercise(
        session, skill, ExerciseType.TRANSLATION,
        {"source_text": "goodbye", "correct_answer": "adiós"},
        1, vocab=adios,
    )
    await _add_exercise(
        session, skill, ExerciseType.FILL_IN_BLANK,
        {"sentence": "Muchas ___ por tu ayuda.", "correct_answer": "gracias"},
        2, vocab=gracias,
    )
    # FREE_TEXT: LLM-graded, not exact-match, since a full sentence has
    # more than one natural correct phrasing (unlike TRANSLATION above,
    # fine for a single word) -- see PLAN.md's 2026-08-14 "Free-text
    # grading" decision. Two sub-kinds, distinguished by prompt shape.
    await _add_exercise(
        session, skill, ExerciseType.FREE_TEXT,
        {"source_text": "Thank you very much for your help."},
        3,
    )
    await _add_exercise(
        session, skill, ExerciseType.FREE_TEXT,
        {"question_text": "¿Cómo te llamas?"},
        4,
    )
    return skill


async def _seed_family_skill(session, course: Course, prerequisite: Skill) -> Skill:
    skill = await _get_or_create_skill(
        session, course, slug="family", name="Family", order_index=1, prerequisite=prerequisite
    )
    await _delete_existing_exercises(session, skill)

    madre = await _get_or_create_vocab(session, course, "madre", "mother")
    padre = await _get_or_create_vocab(session, course, "padre", "father")
    hermano = await _get_or_create_vocab(session, course, "hermano", "brother")

    await _add_exercise(
        session, skill, ExerciseType.MULTIPLE_CHOICE,
        {
            "question": "How do you say 'mother'?",
            "options": ["padre", "madre", "hermano"],
            "correct_index": 1,
        },
        0, vocab=madre,
    )
    await _add_exercise(
        session, skill, ExerciseType.TRANSLATION,
        {"source_text": "father", "correct_answer": "padre"},
        1, vocab=padre,
    )
    await _add_exercise(
        session, skill, ExerciseType.FILL_IN_BLANK,
        {"sentence": "Mi ___ es mayor que yo.", "correct_answer": "hermano"},
        2, vocab=hermano,
    )
    return skill


# Regular examples (hablar/comer/vivir, one per conjugation class) plus
# every verb with an irregular_verbs entry above. Every combination of
# these verbs x CONJUGATION_TENSE_MOOD_COMBOS x _PRONOUNS resolves to a
# real form -- via the irregular table where a verb is irregular, else
# the regular rule -- so the generator loop below never produces an
# exercise conjugate() can't answer.
CONJUGATION_VERBS = (
    "hablar", "comer", "vivir",
    "ser", "estar", "tener", "ir", "hacer", "poder", "querer", "decir",
    "venir", "poner", "salir", "saber", "dar", "ver",
)

CONJUGATION_TENSE_MOOD_COMBOS = (
    ("present", "indicative"),
    ("preterite", "indicative"),
    ("imperfect", "indicative"),
    ("future", "indicative"),
    ("present", "subjunctive"),
    ("present_perfect", "indicative"),
)


async def _seed_conjugation_skill(session, course: Course, prerequisite: Skill) -> Skill:
    skill = await _get_or_create_skill(
        session,
        course,
        slug="verb-conjugation",
        name="Verb Conjugation",
        order_index=2,
        prerequisite=prerequisite,
        specialty_module="spanish-verb-conjugation",
    )
    await _delete_existing_exercises(session, skill)

    order = 0
    for infinitive in CONJUGATION_VERBS:
        for tense, mood in CONJUGATION_TENSE_MOOD_COMBOS:
            for pronoun in _PRONOUNS:
                await _add_exercise(
                    session, skill, ExerciseType.CONJUGATION,
                    {
                        "infinitive": infinitive,
                        "tense": tense,
                        "mood": mood,
                        "pronoun": pronoun,
                    },
                    order, specialty_module="spanish-verb-conjugation",
                )
                order += 1

    return skill


# Dutch content -- parallel functions/constants alongside the Spanish
# ones above, rather than a shared parameterized framework. Two
# languages don't justify that abstraction yet; a third would be the
# right trigger (2026-08-14 "v1 Dutch course" decision).


async def _seed_dutch_greetings_skill(session, course: Course) -> Skill:
    skill = await _get_or_create_skill(
        session, course, slug="greetings", name="Greetings", order_index=0
    )
    await _delete_existing_exercises(session, skill)

    hallo = await _get_or_create_vocab(session, course, "hallo", "hello")
    tot_ziens = await _get_or_create_vocab(session, course, "tot ziens", "goodbye")
    dank_je_wel = await _get_or_create_vocab(session, course, "dank je wel", "thank you")

    await _add_exercise(
        session, skill, ExerciseType.MULTIPLE_CHOICE,
        {
            "question": "How do you say 'hello'?",
            "options": ["hallo", "tot ziens", "dank je wel"],
            "correct_index": 0,
        },
        0, vocab=hallo,
    )
    await _add_exercise(
        session, skill, ExerciseType.TRANSLATION,
        {"source_text": "goodbye", "correct_answer": "tot ziens"},
        1, vocab=tot_ziens,
    )
    await _add_exercise(
        session, skill, ExerciseType.FILL_IN_BLANK,
        {"sentence": "___ voor je hulp!", "correct_answer": "dank je wel"},
        2, vocab=dank_je_wel,
    )
    return skill


async def _seed_dutch_family_skill(session, course: Course, prerequisite: Skill) -> Skill:
    skill = await _get_or_create_skill(
        session, course, slug="family", name="Family", order_index=1, prerequisite=prerequisite
    )
    await _delete_existing_exercises(session, skill)

    moeder = await _get_or_create_vocab(session, course, "moeder", "mother")
    vader = await _get_or_create_vocab(session, course, "vader", "father")
    broer = await _get_or_create_vocab(session, course, "broer", "brother")

    await _add_exercise(
        session, skill, ExerciseType.MULTIPLE_CHOICE,
        {
            "question": "How do you say 'mother'?",
            "options": ["vader", "moeder", "broer"],
            "correct_index": 1,
        },
        0, vocab=moeder,
    )
    await _add_exercise(
        session, skill, ExerciseType.TRANSLATION,
        {"source_text": "father", "correct_answer": "vader"},
        1, vocab=vader,
    )
    await _add_exercise(
        session, skill, ExerciseType.FILL_IN_BLANK,
        {"sentence": "Mijn ___ is ouder dan ik.", "correct_answer": "broer"},
        2, vocab=broer,
    )
    return skill


# All 8 verbs are fully specified in DUTCH_GRAMMAR_CONFIG's irregular_verbs
# (see that config's comments for why) -- every combination below resolves
# through the irregular table, never the regular-endings fallback.
DUTCH_CONJUGATION_VERBS = (
    "zijn", "hebben", "gaan", "komen", "werken", "maken", "wonen", "spelen",
)

# No preterite/imperfect split (Dutch has one simple past, not two), no
# future (periphrastic -- "zullen" + infinitive, a different compound
# shape than present perfect's auxiliary + participle), no subjunctive
# (archaic/non-productive) -- a smaller tense set than Spanish's six, not
# a simplification of any one tense (2026-08-14 decision).
DUTCH_CONJUGATION_TENSE_MOOD_COMBOS = (
    ("present", "indicative"),
    ("past", "indicative"),
    ("present_perfect", "indicative"),
)


async def _seed_dutch_conjugation_skill(session, course: Course, prerequisite: Skill) -> Skill:
    skill = await _get_or_create_skill(
        session,
        course,
        slug="verb-conjugation",
        name="Verb Conjugation",
        order_index=2,
        prerequisite=prerequisite,
        specialty_module="dutch-verb-conjugation",
    )
    await _delete_existing_exercises(session, skill)

    order = 0
    for infinitive in DUTCH_CONJUGATION_VERBS:
        for tense, mood in DUTCH_CONJUGATION_TENSE_MOOD_COMBOS:
            for pronoun in _PRONOUNS:
                await _add_exercise(
                    session, skill, ExerciseType.CONJUGATION,
                    {
                        "infinitive": infinitive,
                        "tense": tense,
                        "mood": mood,
                        "pronoun": pronoun,
                    },
                    order, specialty_module="dutch-verb-conjugation",
                )
                order += 1

    return skill


TRIGGER_MODULE = "spanish-subjunctive-triggers"

# Each entry: skill slug, name, intro (explanation + examples), and a list
# of MULTIPLE_CHOICE exercises. Option strings are hand-authored here, not
# computed via conjugate() -- multiple-choice grading only ever compares a
# selected index, so these don't depend on grammar_config's coverage the
# way CONJUGATION exercises do; they just need to be correct Spanish.
TRIGGER_SKILLS = [
    {
        "slug": "subjunctive-doubt",
        "name": "Doubt",
        "intro": {
            "explanation": (
                "Expressions of doubt or uncertainty -- dudar que, no creer que, "
                "es posible que -- trigger the subjunctive in the clause that "
                "follows. The speaker isn't stating a fact, just a possibility, "
                "so Spanish marks that with mood, not just vocabulary."
            ),
            "examples": [
                {
                    "target_text": "Dudo que ella tenga razón.",
                    "base_text": "I doubt that she's right.",
                },
                {"target_text": "No creo que sea fácil.", "base_text": "I don't think it's easy."},
            ],
        },
        "exercises": [
            {
                "question": "Dudo que ella ___ la verdad. (decir)",
                "options": ["dice", "diga", "dijo"],
                "correct_index": 1,
            },
            {
                "question": "No creo que ellos ___ razón. (tener)",
                "options": ["tienen", "tengan", "tuvieron"],
                "correct_index": 1,
            },
            {
                "question": "Es posible que él ___ tarde. (llegar)",
                "options": ["llega", "llegue", "llegó"],
                "correct_index": 1,
            },
        ],
    },
    {
        "slug": "subjunctive-desire",
        "name": "Desire / Wish",
        "intro": {
            "explanation": (
                "Wanting, hoping, or wishing something for someone else -- "
                "querer que, esperar que, ojalá que -- triggers the subjunctive, "
                "because you're describing a desired outcome, not a fact. (When "
                "the subject wants something for themselves there's no que "
                "clause and no subjunctive: quiero estudiar, not quiero que "
                "estudie.)"
            ),
            "examples": [
                {
                    "target_text": "Quiero que vengas a la fiesta.",
                    "base_text": "I want you to come to the party.",
                },
                {
                    "target_text": "Espero que todo salga bien.",
                    "base_text": "I hope everything turns out well.",
                },
            ],
        },
        "exercises": [
            {
                "question": "Quiero que tú ___ más. (estudiar)",
                "options": ["estudias", "estudies", "estudiaste"],
                "correct_index": 1,
            },
            {
                "question": "Espero que (tú) ___ bien en el examen. (salir)",
                "options": ["sales", "salgas", "saliste"],
                "correct_index": 1,
            },
            {
                "question": "Ojalá que ___ pronto. (venir)",
                "options": ["vienes", "vengas", "viniste"],
                "correct_index": 1,
            },
        ],
    },
    {
        "slug": "subjunctive-emotion",
        "name": "Emotion",
        "intro": {
            "explanation": (
                "Emotional reactions -- me alegra que, es triste que, temo que "
                "-- trigger the subjunctive in what follows, since you're "
                "reacting to something rather than stating it as neutral fact."
            ),
            "examples": [
                {
                    "target_text": "Me alegra que estés aquí.",
                    "base_text": "I'm glad that you're here.",
                },
                {
                    "target_text": "Es triste que se vaya.",
                    "base_text": "It's sad that he's leaving.",
                },
            ],
        },
        "exercises": [
            {
                "question": "Me alegra que ___ aquí. (estar)",
                "options": ["estás", "estés", "estuviste"],
                "correct_index": 1,
            },
            {
                "question": "Es triste que ella no ___ venir. (poder)",
                "options": ["puede", "pueda", "pudo"],
                "correct_index": 1,
            },
            {
                "question": "Temo que ___ tarde. (ser)",
                "options": ["es", "sea", "fue"],
                "correct_index": 1,
            },
        ],
    },
]


async def _seed_subjunctive_trigger_skills(session, course: Course, prerequisite: Skill) -> None:
    """Chains the three trigger-category skills one after another (doubt ->
    desire/wish -> emotion) -- an arbitrary but simple linear order, not a
    claim that doubt is a prerequisite for understanding desire (nothing
    reads this chain for gating anymore -- see PLAN.md's "removing
    lock/unlock" note -- it's just an ordering hint now).
    """
    for offset, entry in enumerate(TRIGGER_SKILLS):
        skill = await _get_or_create_skill(
            session,
            course,
            slug=entry["slug"],
            name=entry["name"],
            order_index=3 + offset,
            prerequisite=prerequisite,
            specialty_module=TRIGGER_MODULE,
        )
        skill.intro_content = entry["intro"]
        prerequisite = skill

        await _delete_existing_exercises(session, skill)
        for order, prompt in enumerate(entry["exercises"]):
            await _add_exercise(
                session, skill, ExerciseType.MULTIPLE_CHOICE, prompt, order,
                specialty_module=TRIGGER_MODULE,
            )


# Real, sourced vocab notes for the Anki-style deck feature (2026-08-14
# "Anki-style vocab decks" decision) -- distinct from the Greetings/
# Family lesson-exercise vocab above, which has no source/example-
# sentence fields and generates LessonExercises, not Cards. A handful of
# hand-verified entries per language, run through the real
# build_cards_for_note() path (via _seed_note), not hand-built Card rows.
SPANISH_VOCAB_NOTES = [
    {
        "target_text": "madrugar",
        "base_text": "to get up early",
        "part_of_speech": "verb",
        "source": "Podcast: SpanishPod101 - Daily Routines",
        "example_sentence": "Tengo que madrugar mañana para el vuelo.",
        "example_sentence_translation": "I have to get up early tomorrow for the flight.",
        "tags": ["daily-life"],
    },
    {
        "target_text": "de vez en cuando",
        "base_text": "once in a while",
        "part_of_speech": "phrase",
        "source": "Movie: Roma",
        "example_sentence": "Voy al gimnasio de vez en cuando.",
        "example_sentence_translation": "I go to the gym once in a while.",
        "tags": ["frequency"],
    },
    {
        "target_text": "aprovechar",
        "base_text": "to make the most of",
        "part_of_speech": "verb",
        "source": "Podcast: Notes in Spanish",
        "example_sentence": "Vamos a aprovechar el buen tiempo hoy.",
        "example_sentence_translation": "Let's make the most of the good weather today.",
        "tags": ["daily-life"],
    },
    # 15 more, added 2026-08-14 -- user-authored A2/B1 connectors, verbs,
    # and set phrases, imported via the same _seed_note path as the three
    # above (see PLAN.md's 2026-08-14 "Second vocab-seed batch" decision).
    {
        "target_text": "aunque",
        "base_text": "although / even though",
        "source": "manual seed - A2/B1 connector words",
        "example_sentence": "Aunque llueva, voy a salir.",
        "example_sentence_translation": "Even though it's raining, I'm going out.",
        "tags": ["connector", "b1"],
    },
    {
        "target_text": "sin embargo",
        "base_text": "however / nevertheless",
        "source": "manual seed - A2/B1 connector words",
        "example_sentence": "Estudié mucho; sin embargo, no aprobé el examen.",
        "example_sentence_translation": "I studied a lot; however, I didn't pass the exam.",
        "tags": ["connector", "b1"],
    },
    {
        "target_text": "lograr",
        "base_text": "to manage to / to achieve",
        "source": "manual seed - A2/B1 verbs",
        "example_sentence": "Por fin logré terminar el proyecto.",
        "example_sentence_translation": "I finally managed to finish the project.",
        "tags": ["verb", "b1"],
    },
    {
        "target_text": "extrañar",
        "base_text": "to miss (someone/something)",
        "source": "manual seed - A2/B1 verbs",
        "example_sentence": "Extraño mucho a mi familia.",
        "example_sentence_translation": "I miss my family a lot.",
        "tags": ["verb", "a2"],
    },
    {
        "target_text": "arreglar",
        "base_text": "to fix / to arrange",
        "source": "manual seed - A2/B1 verbs",
        "example_sentence": "Necesito arreglar mi bicicleta.",
        "example_sentence_translation": "I need to fix my bike.",
        "tags": ["verb", "a2"],
    },
    {
        "target_text": "atreverse a",
        "base_text": "to dare to",
        "source": "manual seed - A2/B1 reflexive verbs",
        "example_sentence": "No me atrevo a hablar en público.",
        "example_sentence_translation": "I don't dare speak in public.",
        "tags": ["verb", "reflexive", "b1"],
    },
    {
        "target_text": "darse cuenta de",
        "base_text": "to realize",
        "source": "manual seed - A2/B1 common phrases",
        "example_sentence": "Me di cuenta de que había olvidado las llaves.",
        "example_sentence_translation": "I realized I had forgotten the keys.",
        "tags": ["phrase", "b1"],
    },
    {
        "target_text": "a pesar de",
        "base_text": "despite / in spite of",
        "source": "manual seed - A2/B1 connector words",
        "example_sentence": "A pesar del tráfico, llegamos a tiempo.",
        "example_sentence_translation": "Despite the traffic, we arrived on time.",
        "tags": ["connector", "b1"],
    },
    {
        "target_text": "el/la desconocido/a",
        "base_text": "stranger / unknown person",
        "source": "manual seed - A2/B1 nouns",
        "example_sentence": "Un desconocido me ayudó con las maletas.",
        "example_sentence_translation": "A stranger helped me with my suitcases.",
        "tags": ["noun", "b1"],
    },
    {
        "target_text": "de repente",
        "base_text": "suddenly",
        "source": "manual seed - A2/B1 common phrases",
        "example_sentence": "De repente empezó a llover.",
        "example_sentence_translation": "It suddenly started raining.",
        "tags": ["phrase", "a2"],
    },
    {
        "target_text": "ponerse (+ adjetivo)",
        "base_text": "to become / to get (a state)",
        "source": "manual seed - A2/B1 change-of-state verbs",
        "example_sentence": "Me puse nervioso antes del examen.",
        "example_sentence_translation": "I got nervous before the exam.",
        "tags": ["verb", "reflexive", "b1"],
    },
    {
        "target_text": "estar harto/a de",
        "base_text": "to be fed up with",
        "source": "manual seed - A2/B1 common phrases",
        "example_sentence": "Estoy harto de esperar el autobús.",
        "example_sentence_translation": "I'm fed up with waiting for the bus.",
        "tags": ["phrase", "b1"],
    },
    {
        "target_text": "por lo tanto",
        "base_text": "therefore / thus",
        "source": "manual seed - A2/B1 connector words",
        "example_sentence": "No tenía dinero; por lo tanto, no fui al cine.",
        "example_sentence_translation": "I had no money; therefore, I didn't go to the movies.",
        "tags": ["connector", "b1"],
    },
    {
        "target_text": "echar de menos",
        "base_text": "to miss (someone/something) - Spain usage",
        "source": "manual seed - A2/B1 common phrases",
        "example_sentence": "Echo de menos mi ciudad natal.",
        "example_sentence_translation": "I miss my hometown.",
        "tags": ["phrase", "a2"],
    },
    {
        "target_text": "cuanto antes",
        "base_text": "as soon as possible",
        "source": "manual seed - A2/B1 common phrases",
        "example_sentence": "Necesito la respuesta cuanto antes.",
        "example_sentence_translation": "I need the answer as soon as possible.",
        "tags": ["phrase", "b1"],
    },
]

# Pinyin uses diacritic tone marks (nǐ hǎo), not tone numerals (ni3 hao3)
# -- per the user's own spec, diacritics train the visual/audio
# association better. Kept deliberately small and to extremely common,
# unambiguous vocabulary: unlike the Spanish grammar rules elsewhere in
# this file (verified programmatically via the resolution-check scripts
# from the Dutch course decision), tone-mark accuracy here can't be
# cross-checked by running code -- worth a human sanity check before
# treating this as a template for adding more.
CHINESE_VOCAB_NOTES = [
    {
        "target_text": "你好",
        "base_text": "hello",
        "part_of_speech": "word",
        "source": "Podcast: ChinesePod - Greetings",
        "example_sentence": "你好，很高兴认识你。",
        "example_sentence_translation": "Hello, nice to meet you.",
        "tags": ["greetings"],
        "attributes": {
            "transliteration": "nǐ hǎo",
            "example_sentence_transliteration": "Nǐ hǎo, hěn gāoxìng rènshi nǐ.",
        },
    },
    {
        "target_text": "谢谢",
        "base_text": "thank you",
        "part_of_speech": "word",
        "source": "Podcast: ChinesePod - Basics",
        "example_sentence": "谢谢你的帮助。",
        "example_sentence_translation": "Thank you for your help.",
        "tags": ["greetings"],
        "attributes": {
            "transliteration": "xièxie",
            "example_sentence_transliteration": "Xièxie nǐ de bāngzhù.",
        },
    },
    {
        "target_text": "慢慢来",
        "base_text": "take your time",
        "part_of_speech": "set phrase",
        "source": "Podcast: ChinesePod - Everyday Expressions",
        "example_sentence": "没关系，慢慢来。",
        "example_sentence_translation": "It's okay, take your time.",
        "tags": ["daily-life"],
        "attributes": {
            "transliteration": "màn màn lái",
            "example_sentence_transliteration": "Méi guānxi, màn màn lái.",
        },
    },
    # 12 more, added 2026-08-14 -- user-authored beginner survival phrases/
    # verbs/nouns, deliberately excluding the four words already seeded
    # above (see PLAN.md's 2026-08-14 "Second vocab-seed batch" decision).
    {
        "target_text": "多少钱",
        "base_text": "how much money / how much does it cost",
        "source": "manual seed - beginner survival phrases",
        "example_sentence": "这个多少钱？",
        "example_sentence_translation": "How much is this?",
        "tags": ["phrase", "beginner"],
        "attributes": {"transliteration": "duōshǎo qián"},
    },
    {
        "target_text": "没关系",
        "base_text": "it's okay / no problem",
        "source": "manual seed - beginner survival phrases",
        "example_sentence": "对不起！没关系。",
        "example_sentence_translation": "Sorry! It's okay.",
        "tags": ["phrase", "beginner"],
        "attributes": {"transliteration": "méi guānxi"},
    },
    {
        "target_text": "我不明白",
        "base_text": "I don't understand",
        "source": "manual seed - beginner survival phrases",
        "example_sentence": "对不起，我不明白。",
        "example_sentence_translation": "Sorry, I don't understand.",
        "tags": ["phrase", "beginner"],
        "attributes": {"transliteration": "wǒ bù míngbái"},
    },
    {
        "target_text": "请问",
        "base_text": "excuse me / may I ask",
        "source": "manual seed - beginner survival phrases",
        "example_sentence": "请问，洗手间在哪儿？",
        "example_sentence_translation": "Excuse me, where's the restroom?",
        "tags": ["phrase", "beginner"],
        "attributes": {"transliteration": "qǐngwèn"},
    },
    {
        "target_text": "喜欢",
        "base_text": "to like",
        "source": "manual seed - beginner verbs",
        "example_sentence": "我喜欢咖啡。",
        "example_sentence_translation": "I like coffee.",
        "tags": ["verb", "beginner"],
        "attributes": {"transliteration": "xǐhuan"},
    },
    {
        "target_text": "朋友",
        "base_text": "friend",
        "source": "manual seed - beginner nouns",
        "example_sentence": "他是我的朋友。",
        "example_sentence_translation": "He is my friend.",
        "tags": ["noun", "beginner"],
        "attributes": {"transliteration": "péngyou"},
    },
    {
        "target_text": "现在",
        "base_text": "now",
        "source": "manual seed - beginner time words",
        "example_sentence": "我现在很忙。",
        "example_sentence_translation": "I'm busy right now.",
        "tags": ["time", "beginner"],
        "attributes": {"transliteration": "xiànzài"},
    },
    {
        "target_text": "已经",
        "base_text": "already",
        "source": "manual seed - beginner adverbs",
        "example_sentence": "我已经吃饭了。",
        "example_sentence_translation": "I already ate.",
        "tags": ["adverb", "beginner"],
        "attributes": {"transliteration": "yǐjīng"},
    },
    {
        "target_text": "还是",
        "base_text": "or (in questions) / still",
        "source": "manual seed - beginner function words",
        "example_sentence": "你要茶还是咖啡？",
        "example_sentence_translation": "Do you want tea or coffee?",
        "tags": ["function_word", "beginner"],
        "attributes": {"transliteration": "háishi"},
    },
    {
        "target_text": "觉得",
        "base_text": "to think / to feel (an opinion)",
        "source": "manual seed - beginner verbs",
        "example_sentence": "我觉得这个很好。",
        "example_sentence_translation": "I think this is good.",
        "tags": ["verb", "beginner"],
        "attributes": {"transliteration": "juéde"},
    },
    {
        "target_text": "地方",
        "base_text": "place",
        "source": "manual seed - beginner nouns",
        "example_sentence": "这是一个好地方。",
        "example_sentence_translation": "This is a good place.",
        "tags": ["noun", "beginner"],
        "attributes": {"transliteration": "dìfang"},
    },
    {
        "target_text": "为什么",
        "base_text": "why",
        "source": "manual seed - beginner question words",
        "example_sentence": "你为什么迟到了？",
        "example_sentence_translation": "Why are you late?",
        "tags": ["question_word", "beginner"],
        "attributes": {"transliteration": "wèishénme"},
    },
]


async def _seed_spanish_vocab_notes(
    session, course: Course, deck: Deck, language: Language
) -> None:
    for note in SPANISH_VOCAB_NOTES:
        await _seed_note(session, course, deck, language, **note)


async def _seed_chinese_vocab_notes(
    session, course: Course, deck: Deck, language: Language
) -> None:
    for note in CHINESE_VOCAB_NOTES:
        await _seed_note(session, course, deck, language, **note)


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        english = await _get_or_create_language(session, EN_CODE, "English")
        spanish = await _get_or_create_language(session, ES_CODE, "Spanish")
        dutch = await _get_or_create_language(session, NL_CODE, "Dutch")
        chinese = await _get_or_create_language(session, ZH_CODE, "Chinese")
        # Always overwrite: this is seed/dev content with one canonical
        # source (this file), not user data -- re-running should converge
        # on exactly this config, not accumulate drift.
        spanish.grammar_config = SPANISH_GRAMMAR_CONFIG
        dutch.grammar_config = DUTCH_GRAMMAR_CONFIG
        chinese.grammar_config = CHINESE_GRAMMAR_CONFIG

        course = await _get_or_create_course(
            session, english, spanish, name="English to Spanish", slug=COURSE_SLUG
        )
        dutch_course = await _get_or_create_course(
            session, english, dutch, name="English to Dutch", slug=DUTCH_COURSE_SLUG
        )
        chinese_course = await _get_or_create_course(
            session, english, chinese, name="English to Chinese", slug=CHINESE_COURSE_SLUG
        )

        greetings = await _seed_greetings_skill(session, course)
        family = await _seed_family_skill(session, course, prerequisite=greetings)
        conjugation = await _seed_conjugation_skill(session, course, prerequisite=family)
        await _seed_subjunctive_trigger_skills(session, course, prerequisite=conjugation)

        dutch_greetings = await _seed_dutch_greetings_skill(session, dutch_course)
        dutch_family = await _seed_dutch_family_skill(
            session, dutch_course, prerequisite=dutch_greetings
        )
        await _seed_dutch_conjugation_skill(session, dutch_course, prerequisite=dutch_family)

        # Anki-style vocab-deck notes, real content run through the actual
        # build_cards_for_note() path -- see the 2026-08-14 "Anki-style
        # vocab decks" decision. One shared user/deck-per-course
        # convention (_get_or_create_user/_get_or_create_deck), converging
        # on the same single user bootstrap.ts creates/reuses.
        user = await _get_or_create_user(session)
        spanish_vocab_deck = await _get_or_create_deck(session, user, course, name="Spanish Vocab")
        await _seed_spanish_vocab_notes(session, course, spanish_vocab_deck, spanish)
        chinese_vocab_deck = await _get_or_create_deck(
            session, user, chinese_course, name="Chinese Vocab"
        )
        await _seed_chinese_vocab_notes(session, chinese_course, chinese_vocab_deck, chinese)

        await session.commit()
        print(f"Seeded course {course.slug!r} (id={course.id})")
        print(f"Seeded course {dutch_course.slug!r} (id={dutch_course.id})")
        print(f"Seeded course {chinese_course.slug!r} (id={chinese_course.id})")
        print(f"Seeded vocab decks {spanish_vocab_deck.name!r}, {chinese_vocab_deck.name!r}")


if __name__ == "__main__":
    asyncio.run(seed())
