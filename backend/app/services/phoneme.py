import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.phoneme import (
    CoverageReport,
    PhonemeGap,
    CategoryCoverage,
    ChunkSuggestion,
)

ENGLISH_PHONEMES: set[str] = {
    # Stops
    "p", "b", "t", "d", "k", "ɡ",
    # Affricates
    "tʃ", "dʒ",
    # Fricatives
    "f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ", "h",
    # Nasals
    "m", "n", "ŋ",
    # Approximants
    "l", "r", "w", "j",
    # Short vowels
    "ɪ", "ɛ", "æ", "ʌ", "ʊ", "ɒ", "ə",
    # Long vowels
    "iː", "ɑː", "ɔː", "uː", "ɜː",
    # Diphthongs
    "eɪ", "oʊ", "aɪ", "aʊ", "ɔɪ",
}

PHONEME_CATEGORIES: dict[str, list[str]] = {
    "stops":       ["p", "b", "t", "d", "k", "ɡ"],
    "affricates":  ["tʃ", "dʒ"],
    "fricatives":  ["f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ", "h"],
    "nasals":      ["m", "n", "ŋ"],
    "approximants": ["l", "r", "w", "j"],
    "short_vowels": ["ɪ", "ɛ", "æ", "ʌ", "ʊ", "ɒ", "ə"],
    "long_vowels":  ["iː", "ɑː", "ɔː", "uː", "ɜː"],
    "diphthongs":   ["eɪ", "oʊ", "aɪ", "aʊ", "ɔɪ"],
}

PHONEME_EXAMPLES: dict[str, str] = {
    "p": "pat", "b": "bat", "t": "top", "d": "dog", "k": "cat", "ɡ": "go",
    "tʃ": "chair", "dʒ": "judge",
    "f": "fish", "v": "van", "θ": "think", "ð": "the", "s": "sun",
    "z": "zoo", "ʃ": "shoe", "ʒ": "measure", "h": "hat",
    "m": "man", "n": "now", "ŋ": "sing",
    "l": "let", "r": "run", "w": "wet", "j": "yes",
    "ɪ": "bit", "ɛ": "bed", "æ": "cat", "ʌ": "cup", "ʊ": "foot",
    "ɒ": "lot", "ə": "about",
    "iː": "see", "ɑː": "car", "ɔː": "law", "uː": "too", "ɜː": "bird",
    "eɪ": "say", "oʊ": "go", "aɪ": "my", "aʊ": "now", "ɔɪ": "boy",
}

PANGRAM_SUGGESTIONS = [
    "The quick brown fox jumps over the lazy dog.",
    "She sells seashells by the seashore.",
    "That thin cloth breathes with the weather.",
    "Measure your pleasure and leisure together.",
    "Sing a song with a strong long tongue.",
    "Boys enjoy their choice of noise.",
    "The bird heard the word and stirred.",
]


def phoneme_category(p: str) -> str:
    for cat, members in PHONEME_CATEGORIES.items():
        if p in members:
            return cat
    return "other"


def extract_phonemes_from_text(text: str) -> list[str]:
    try:
        from phonemizer.backend import EspeakBackend
        backend = EspeakBackend("en-us", preserve_punctuation=False, with_stress=False)
        ipa = backend.phonemize([text], njobs=1)[0]
        tokens = ipa.split()
        return [t for t in tokens if t in ENGLISH_PHONEMES]
    except Exception:
        return _g2p_fallback(text)


def _g2p_fallback(text: str) -> list[str]:
    try:
        from g2p_en import G2p
        g2p = G2p()
        arpa = g2p(text)
        # Convert ARPAbet to rough IPA equivalents for coverage
        arpa_to_ipa = {
            "P": "p", "B": "b", "T": "t", "D": "d", "K": "k", "G": "ɡ",
            "CH": "tʃ", "JH": "dʒ", "F": "f", "V": "v", "TH": "θ",
            "DH": "ð", "S": "s", "Z": "z", "SH": "ʃ", "ZH": "ʒ", "HH": "h",
            "M": "m", "N": "n", "NG": "ŋ", "L": "l", "R": "r", "W": "w",
            "Y": "j", "IH": "ɪ", "EH": "ɛ", "AE": "æ", "AH": "ʌ", "UH": "ʊ",
            "AA": "ɑː", "AO": "ɔː", "UW": "uː", "ER": "ɜː", "IY": "iː",
            "EY": "eɪ", "OW": "oʊ", "AY": "aɪ", "AW": "aʊ", "OY": "ɔɪ",
        }
        result = []
        for phone in arpa:
            stripped = phone.rstrip("012")
            ipa = arpa_to_ipa.get(stripped)
            if ipa:
                result.append(ipa)
        return result
    except Exception:
        return []


class PhonemeService:
    async def analyze_coverage(self, voice_id: uuid.UUID, db: AsyncSession) -> CoverageReport:
        from app.models.audio_chunk import AudioChunk
        from app.models.audio_sample import AudioSample

        all_chunks_result = await db.execute(
            select(AudioChunk)
            .join(AudioSample, AudioChunk.sample_id == AudioSample.id)
            .where(AudioSample.voice_id == voice_id)
        )
        all_chunks = all_chunks_result.scalars().all()

        selected_chunks = [c for c in all_chunks if c.selected]
        unselected_chunks = [c for c in all_chunks if not c.selected]

        covered: set[str] = set()
        for chunk in selected_chunks:
            if chunk.phonemes:
                covered |= set(chunk.phonemes) & ENGLISH_PHONEMES

        missing = ENGLISH_PHONEMES - covered
        score = len(covered) / len(ENGLISH_PHONEMES)

        by_category: dict[str, CategoryCoverage] = {}
        for cat, members in PHONEME_CATEGORIES.items():
            cat_covered = [p for p in members if p in covered]
            cat_missing = [p for p in members if p not in covered]
            cat_score = len(cat_covered) / len(members) if members else 1.0
            by_category[cat] = CategoryCoverage(
                covered=cat_covered, missing=cat_missing, score=cat_score
            )

        # Greedy set-cover suggestions
        remaining_missing = set(missing)
        suggestions: list[ChunkSuggestion] = []
        for chunk in sorted(
            unselected_chunks,
            key=lambda c: -len((set(c.phonemes or []) & ENGLISH_PHONEMES) & remaining_missing),
        )[:10]:
            chunk_phonemes = set(chunk.phonemes or []) & ENGLISH_PHONEMES
            fills = chunk_phonemes & remaining_missing
            if not fills:
                continue
            suggestions.append(
                ChunkSuggestion(
                    chunk_id=chunk.id,
                    sample_id=chunk.sample_id,
                    start_sec=chunk.start_sec,
                    end_sec=chunk.end_sec,
                    transcript=chunk.transcript,
                    fills_phonemes=sorted(fills),
                    gain=len(fills),
                )
            )
            remaining_missing -= fills

        missing_gaps = [
            PhonemeGap(
                phoneme=p,
                example_word=PHONEME_EXAMPLES.get(p, ""),
                category=phoneme_category(p),
            )
            for p in sorted(missing)
        ]

        suggested_sentences = PANGRAM_SUGGESTIONS[:3] if missing else []

        return CoverageReport(
            voice_id=voice_id,
            score=round(score, 4),
            covered_count=len(covered),
            total_count=len(ENGLISH_PHONEMES),
            covered=sorted(covered),
            missing=missing_gaps,
            by_category=by_category,
            suggestions=suggestions,
            suggested_sentences=suggested_sentences,
        )
