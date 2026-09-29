# -*- coding: utf-8 -*-
"""
Applies the 9 claim-verification fixes to literature_review.md by exact
string replacement, so nothing gets retyped or lost through the terminal.

Run from the lit_review folder:
    python fix_review.py
"""

REPLACEMENTS = [
    (
        "The early conceptualization of pBCIs emphasized real\u2011time decoding of "
        "EEG signals to provide systems with insights into user workload, fatigue, "
        "or engagement, thereby enabling adaptive instruction scheduling rather "
        "than neurofeedback training, which rewards self\u2011modulation of brain "
        "activity [3].",
        "The early conceptualization of pBCIs emphasized applying brain\u2013computer "
        "interface technology to human\u2013machine systems broadly, using passively "
        "monitored brain activity to inform system behavior, in contrast to "
        "neurofeedback's active self\u2011modulation paradigm [3].",
    ),
    (
        "combining near\u2011infrared spectroscopy with EEG has been shown to improve "
        "motor imagery classification accuracy, suggesting that multimodal pBCIs "
        "can enhance performance while still operating passively [5].",
        "combining near\u2011infrared spectroscopy with EEG has been shown to improve "
        "motor imagery classification accuracy, suggesting multimodal approaches "
        "can enhance BCI performance [5].",
    ),
    (
        "More recent comprehensive surveys of EEG\u2011based BCI systems have traced "
        "the evolution of pBCIs, cataloguing typical signal acquisition and "
        "classification pipelines, and highlighting persistent challenges such as "
        "signal variability and real\u2011time processing constraints [7].",
        "Comprehensive surveys of EEG\u2011based BCI systems have catalogued typical "
        "signal acquisition and classification pipelines, highlighting persistent "
        "challenges such as signal variability and real\u2011time processing "
        "constraints [7].",
    ),
    (
        "Finally, broader reviews of BCI applications have underscored the "
        "potential of passive monitoring in domains ranging from medical "
        "rehabilitation to education, while noting usability and technical "
        "hurdles that remain to be addressed [9].",
        "Finally, broader reviews of BCI applications have underscored their "
        "potential across domains ranging from medical rehabilitation to "
        "education, while noting usability and technical hurdles that remain to "
        "be addressed [9].",
    ),
    (
        "Cognitive load theory frames learning as a balance between intrinsic, "
        "extraneous, and germane demands that compete for limited "
        "working\u2011memory resources [17].",
        "Cognitive load theory, revisited two decades after its original "
        "formulation, continues to frame learning as constrained by limited "
        "working\u2011memory resources during instruction [17].",
    ),
    (
        "Early reviews highlighted a shift toward adaptive, matrix/tensor, "
        "transfer\u2011learning, and deep\u2011learning approaches, with adaptive "
        "classifiers generally outperforming static ones [2].",
        "A decade-spanning review of EEG\u2011BCI classification algorithms found "
        "adaptive, matrix/tensor, transfer\u2011learning, and deep\u2011learning "
        "approaches, with adaptive classifiers generally outperforming static "
        "ones [2].",
    ),
    (
        "Deep learning has been systematically surveyed across domains, "
        "revealing widespread use of convolutional and recurrent architectures, "
        "data\u2011augmentation strategies, and emerging trends, though the "
        "superiority of deep models over traditional methods remains unresolved "
        "due to heterogeneity and reporting gaps [8, 12].",
        "Deep learning has been systematically surveyed for EEG analysis, "
        "revealing widespread use of convolutional architectures and emerging "
        "trends, though the superiority of deep models over traditional methods "
        "remains unresolved due to dataset heterogeneity and reporting "
        "gaps [8, 12].",
    ),
    (
        "In a realistic air\u2011traffic control simulation, a passive BCI that "
        "estimated mental workload triggered adaptive automation, reducing "
        "workload while preserving performance [10].",
        "In a realistic air\u2011traffic control simulation, a passive BCI that "
        "estimated mental workload triggered adaptive automation and reduced "
        "workload [10].",
    ),
    (
        "Recent integrative reviews argue that AI\u2011driven adaptive learning "
        "systems, guided by real\u2011time EEG/fNIRS measures of cognitive load, can "
        "personalize instruction and improve learning efficacy, while also "
        "revealing challenges such as protocol heterogeneity and privacy "
        "concerns [16].",
        "Recent integrative reviews argue that AI\u2011driven adaptive learning "
        "systems, guided by real\u2011time EEG/fNIRS measures of cognitive load, can "
        "personalize instruction and improve learning efficacy, while also "
        "raising privacy concerns [16].",
    ),
]


def main():
    path = "literature_review.md"
    with open(path, encoding="utf-8") as f:
        text = f.read()

    applied, missing = 0, []
    for old, new in REPLACEMENTS:
        if old in text:
            text = text.replace(old, new, 1)
            applied += 1
        else:
            missing.append(old[:80] + "...")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Applied {applied}/9 replacements.")
    if missing:
        print("NOT FOUND (paste your current file back to Claude instead of re-running):")
        for m in missing:
            print("  -", m)


if __name__ == "__main__":
    main()