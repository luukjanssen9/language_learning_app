import esBands from "@/data/frequencyBands/es.json";
import nlBands from "@/data/frequencyBands/nl.json";
import zhBands from "@/data/frequencyBands/zh.json";

export interface FrequencyBand {
  index: number;
  label: string;
  words: string[];
}

interface FrequencyBandData {
  languageCode: string;
  source: string;
  bands: FrequencyBand[];
}

// Spanish/Dutch: hermitdave/FrequencyWords (2018 OpenSubtitles-derived),
// CC-BY-SA-4.0, rank-split into 10 even bands. Chinese: drkameleon/
// complete-hsk-vocabulary (HSK 3.0 official level lists), MIT, banded 1:1
// by real HSK level (levels 7-9 combined into one "advanced" band, since
// HSK 3.0 itself doesn't split them further). See each JSON file's own
// `source` field for the full attribution string.
const BANDS_BY_LANGUAGE_CODE: Record<string, FrequencyBandData> = {
  es: esBands,
  nl: nlBands,
  zh: zhBands,
};

// A plain lookup keyed by the language's own `code` -- no per-language
// branching. `null` means no bundled data exists for this language (e.g.
// nothing sourced yet for a future language), which is how the
// known-vocabulary page decides whether to show the placement-check entry
// point at all -- same graceful-degradation shape as `grammar_config.tts`
// being absent for a language.
export function getFrequencyBands(languageCode: string): FrequencyBand[] | null {
  return BANDS_BY_LANGUAGE_CODE[languageCode]?.bands ?? null;
}
