# Literature Review: EEG-based passive brain-computer interfaces for adaptive learning

## Conceptual Foundations of Passive Brain-Computer Interfaces

Passive brain‑computer interfaces (pBCIs) are defined as systems that monitor users’ neural activity without explicit commands, inferring cognitive or emotional states to adapt human‑machine interaction [3]. The early conceptualization of pBCIs emphasized applying brain–computer interface technology to human–machine systems broadly, using passively monitored brain activity to inform system behavior, in contrast to neurofeedback's active self‑modulation paradigm [3]. Subsequent reviews expanded the scope of pBCIs to include hybrid modalities; for example, combining near‑infrared spectroscopy with EEG has been shown to improve motor imagery classification accuracy, suggesting multimodal approaches can enhance BCI performance [5]. Integrating pBCIs with assistive technologies has been identified as a promising avenue, with hybrid architectures proposed to support communication, control, and motor recovery applications [6]. Comprehensive surveys of EEG‑based BCI systems have catalogued typical signal acquisition and classification pipelines, highlighting persistent challenges such as signal variability and real‑time processing constraints [7]. Finally, broader reviews of BCI applications have underscored their potential across domains ranging from medical rehabilitation to education, while noting usability and technical hurdles that remain to be addressed [9].

## Cognitive Load and EEG-Based Workload Estimation

Cognitive load theory, revisited two decades after its original formulation, continues to frame learning as constrained by limited working‑memory resources during instruction [17]. In digital learning, extraneous load arises from design challenges that distract learners while still motivating them, underscoring the need for objective workload metrics [13]. EEG offers a real‑time window into these demands. Meta‑analytic evidence shows that frontal theta and beta power rise with increasing workload, whereas alpha changes are less reliable [19]. An online brain‑load index derived from two frontal channels tracks overload and fatigue during multitasking, with significant increases linked to task count and wakefulness [29]. More recent work demonstrates that subject‑specific neural networks can predict cognitive load during intelligence tests from a small set of electrodes, outperforming generic models and maintaining robustness across channel reductions [20]. These studies collectively illustrate that EEG‑based workload estimation captures dynamic shifts in working‑memory load, providing a foundation for adaptive instruction that modulates content or pacing in response to real‑time neural indicators.

## Machine-Learning Decoding of EEG

Machine‑learning decoding of EEG for passive BCIs has evolved from classical feature–based classifiers to end‑to‑end deep networks. A decade-spanning review of EEG‑BCI classification algorithms found adaptive, matrix/tensor, transfer‑learning, and deep‑learning approaches, with adaptive classifiers generally outperforming static ones [2]. In motor‑imagery BCIs, conventional pipelines combine advanced feature extraction, selection, and classifiers such as support vector machines or random forests, yet these remain limited to specific paradigms [4]. Deep learning has been systematically surveyed for EEG analysis, revealing widespread use of convolutional architectures and emerging trends, though the superiority of deep models over traditional methods remains unresolved due to dataset heterogeneity and reporting gaps [8, 12]. Empirical evidence from a 2017 study shows that a deep convolutional network achieved 84.0 % accuracy versus 82.1 % for the FBCSP baseline, and visualization confirmed that the network learned spectral power modulations from raw EEG [11]. A compact convolutional architecture, EEGNet, demonstrated competitive accuracy across multiple BCI paradigms while remaining highly parameter‑efficient, suggesting potential for generalization beyond single‑paradigm models [1]. These findings collectively illustrate the trajectory from handcrafted feature pipelines to lightweight deep models capable of decoding EEG in adaptive learning contexts.

## Neurofeedback and Memory

Neurofeedback (NF) is a closed‑loop training that rewards participants for voluntarily modulating specific EEG rhythms, distinct from adaptive scheduling that merely alters instructional timing or content. Empirical studies demonstrate that theta‑band NF can enhance memory consolidation. In a spatial‑memory paradigm, theta up‑regulation significantly improved visuo‑spatial recall after one week relative to both active and passive controls [22]. A similar effect was observed for real‑life episodic memory: post‑encoding theta/beta up‑regulation yielded higher recall after one week compared with controls, indicating early consolidation benefits [24]. Alpha‑band NF also benefits memory; training frontoparietal alpha increased alpha amplitude and duration, accompanied by marked gains in both working and episodic memory in healthy adults [26]. Stroke survivors benefited from NF as well; about 70 % of participants improved NF performance, leading to gains in verbal short‑ and long‑term memory regardless of protocol, while SMR training specifically improved visuo‑spatial short‑term memory [25]. These findings collectively suggest that NF can modulate neural oscillations to support memory processes, though sample sizes and follow‑up durations remain limited. The field’s methodological heterogeneity and lack of standardized reporting are highlighted by the CRED‑nf checklist, which aims to improve future study designs [28]. Finally, reviews underscore the therapeutic potential of NF while noting mixed evidence and the need for rigorous, standardized protocols [21, 23, 27].

Neurofeedback training, a closed‑loop paradigm that rewards participants for voluntarily modulating specific neural oscillations, has been investigated for its potential to enhance memory and broader cognitive functions. In a recent study, SMR (sensorimotor rhythm) neurofeedback was administered to 17 healthy older adults (12 females) with the aim of improving working‑memory performance. Participants who received SMR training demonstrated statistically significant gains in working‑memory accuracy and speed compared with a control group, suggesting that targeted modulation of SMR activity can translate into measurable behavioral benefits [30]. The authors noted that the improvements were observed shortly after the training period, but the study did not report long‑term retention or follow‑up assessments, leaving open questions about the durability of the effect. Despite the limited sample size and short‑term design, this work provides empirical evidence that neurofeedback can positively influence memory‑related cognition in older populations, supporting the broader hypothesis that closed‑loop brain‑computer interfaces can be leveraged to support adaptive learning environments.

## Adaptive and Applied Systems

Adaptive systems that respond to real‑time EEG‑derived mental states have been explored in both operational and educational contexts. In a realistic air‑traffic control simulation, a passive BCI that estimated mental workload triggered adaptive automation and reduced workload [10]. In learning, an EEG‑based passive BCI that modulated instructional speed according to instantaneous cognitive load, combined with motivational cues, produced significantly higher learning gains and a better learning experience than either non‑adaptive or adaptive alone, though no difference was found between adaptive alone and control [14]. These empirical findings align with the broader theoretical discussion of cognitive load theory, which identifies methodological and conceptual challenges in measuring and applying load in instructional design [15]. Recent integrative reviews argue that AI‑driven adaptive learning systems, guided by real‑time EEG/fNIRS measures of cognitive load, can personalize instruction and improve learning efficacy, while also raising privacy concerns [16]. Together, these studies illustrate how passive BCIs can dynamically adjust instructional pacing or automation to match users’ mental states, offering a promising avenue for adaptive learning environments.

## Research Gaps

*Based on abstract-level extraction: a gap means the extracted summaries do not state the item, not that the literature lacks it. Verify against full texts before relying on any item.*

1. **Lab-only / controlled settings, not real-world or naturalistic deployment** (severity: high). No paper's abstract-level summary states this.
2. **No study uses or validates consumer-grade dry EEG (e.g. Muse) for learning** (severity: high). No paper's abstract-level summary states this.
3. **Individual variability in theta/alpha response not addressed** (severity: high). No paper's abstract-level summary states this.
4. **Confounds (fatigue, caffeine, mood, time-of-day) not controlled or reported** (severity: high). No paper's abstract-level summary states this.
5. **No adaptive scheduling policy learned from delayed recall feedback (e.g. bandit / RL)** (severity: high). No paper's abstract-level summary states this.
6. **No EEG-driven closed-loop adaptation of instruction (studies only monitor or decode EEG, or use neurofeedback without adapting what or when material is presented)** (severity: medium). Only papers 14 state this.
7. **No long-term / multi-session retention outcomes (only immediate recall tested)** (severity: medium). Only papers 22, 24 state this.
8. **No comparison against a fixed-interval or non-adaptive baseline** (severity: medium). Only papers 10, 14 state this.
9. **Small subject cohorts (n<15)** (severity: low). n is stated for only 5 of 21 empirical papers. Under 15: paper 10 (n=12). Not stated in the abstract for papers 1, 3, 4, 5, 6, 9, 11, 14, 15, 16, 17, 18, 20, 22, 24, 29.

## References

[1] Vernon J Lawhern, Amelia J Solon, Nicholas R Waytowich, Stephen M Gordon, Chou P Hung, Brent J Lance (2018). EEGNet: a compact convolutional neural network for EEG-based brain–computer interfaces. doi:10.1088/1741-2552/aace8c
[2] Fabien Lotte, Laurent Bougrain, Andrzej S Cichocki, Maureen Clerc, Marco Congedo, Alain Rakotomamonjy et al. (2018). A review of classification algorithms for EEG-based brain–computer interfaces: a 10 year update. doi:10.1088/1741-2552/aab2f2
[3] Thorsten O. Zander, Christian Andreas Kothe (2011). Towards passive brain–computer interfaces: applying brain–computer interface technology to human–machine systems in general. doi:10.1088/1741-2560/8/2/025005
[4] Natasha Padfield, Jaime Zabalza, Huimin Zhao, Valentín Masero, Jinchang Ren (2019). EEG-Based Brain-Computer Interfaces Using Motor-Imagery: Techniques and Challenges. doi:10.3390/s19061423
[5] Siamac Fazli, Jan Mehnert, Jens M. Steinbrink, Gabriel Curio, Arno Villringer, Klaus‐Robert Müller et al. (2011). Enhanced performance by a hybrid NIRS–EEG brain computer interface. doi:10.1016/j.neuroimage.2011.07.084
[6] José del R. Millán (2010). Combining brain-computer interfaces and assistive technologies: state-of-the-art and challenges. doi:10.3389/fnins.2010.00161
[7] Mamunur Rashid, Norizam Sulaiman, Anwar P. P. Abdul Majeed, Rabiu Muazu Musa, Ahmad Fakhri Ab. Nasir, Bifta Sama Bari et al. (2020). Current Status, Challenges, and Possible Solutions of EEG-Based Brain-Computer Interface: A Comprehensive Review. doi:10.3389/fnbot.2020.00025
[8] Yannick Roy, Hubert J. Banville, Isabela Albuquerque, Alexandre Gramfort, Tiago Henrique Falk, Jocelyn Faubert (2019). Deep learning-based electroencephalography analysis: a systematic review. doi:10.1088/1741-2552/ab260c
[9] Sarah N. Abdulkader, Ayman Atia, Mostafa-Sami M. Mostafa (2015). Brain computer interfacing: Applications and challenges. doi:10.1016/j.eij.2015.06.002
[10] Pietro Aricò, Gianluca Borghini, Gianluca Di Flumeri, Alfredo Colosimo, Stefano Bonelli, Alessia Golfetti et al. (2016). Adaptive Automation Triggered by EEG-Based Mental Workload Index: A Passive Brain-Computer Interface Application in Realistic Air Traffic Control Environment. doi:10.3389/fnhum.2016.00539
[11] Robin Tibor Schirrmeister, Jost Tobias Springenberg, Lukas D. J. Fiederer, Martin Glasstetter, Katharina Eggensperger, Michael Tangermann et al. (2017). Deep learning with convolutional neural networks for EEG decoding and visualization. doi:10.1002/hbm.23730
[12] Alexander Craik, Yongtian He, Jose Luis Contreras-Vidal (2019). Deep learning for electroencephalogram (EEG) classification tasks: a review. doi:10.1088/1741-2552/ab0ab5
[13] Alexander Skulmowski, Kate M. Xu (2021). Understanding Cognitive Load in Digital and Online Learning: a New Perspective on Extraneous Cognitive Load. doi:10.1007/s10648-021-09624-7
[14] Noémie Beauchemin, Patrick Charland, Alexander John Karran, Jared Boasen, Bella Tadson, Sylvain Sénécal et al. (2024). Enhancing learning experiences: EEG-based passive BCI system adapts learning speed to cognitive load in real-time, with motivation as catalyst. doi:10.3389/fnhum.2024.1416683
[15] Ton de Jong (2009). Cognitive load theory, educational research, and instructional design: some food for thought. doi:10.1007/s11251-009-9110-0
[16] Evgenia Gkintoni, Hera Antonopoulou, Andrew Sortwell, Constantinos Halkiopoulos (2025). Challenging Cognitive Load Theory: The Role of Educational Neuroscience and Artificial Intelligence in Redefining Learning Efficacy. doi:10.3390/brainsci15020203
[17] John Sweller, Jeroen J. G. van Merriënboer, FRED G. W. C. PAAS (2019). Cognitive Architecture and Instructional Design: 20 Years Later. doi:10.1007/s10648-019-09465-5
[18] Mark D’Esposito, Bradley R. Postle (2014). The Cognitive Neuroscience of Working Memory. doi:10.1146/annurev-psych-010814-015031
[19] Samy Chikhi, Nadine Matton, Sophie Anne Blanchet (2022). EEG power spectral measures of cognitive workload: A meta‐analysis. doi:10.1111/psyp.14009
[20] Nir Friedman, Tomer Fekete, Kobi Gal, Oren Shriki (2019). EEG-Based Prediction of Cognitive Load in Intelligence Tests. doi:10.3389/fnhum.2019.00191
[21] Stefanie Enriquez‐Geppert, Rene Jürgen Huster, Christoph Siegfried Herrmann (2017). EEG-Neurofeedback as a Tool to Modulate Cognition and Behavior: A Review Tutorial. doi:10.3389/fnhum.2017.00051
[22] Limor Shtoots, Tom Dagan, Josh Levine, Aryeh Rothstein, Liran Shati, Daniel A. Levy (2020). The Effects of Theta EEG Neurofeedback on the Consolidation of Spatial Memory. doi:10.1177/1550059420973107
[23] D. Corydon Hammond (2011). What is Neurofeedback: An Update. doi:10.1080/10874208.2011.623090
[24] Roman Rozengurt, Ілля Кузнєцов, Tetіana Kachynska, Nataliia Kozachuk, Olha Abramchuk, Оleksandr Zhuravlov et al. (2023). Theta EEG neurofeedback promotes early consolidation of real life-like episodic memory. doi:10.3758/s13415-023-01125-0
[25] Silvia Erika Kober, Daniela Schweiger, Matthias Witte, Johanna Louise Reichert, Peter Grieshofer, Christa Neuper et al. (2015). Specific effects of EEG based neurofeedback training on memory functions in post-stroke victims. doi:10.1186/s12984-015-0105-6
[26] Jen-Jui Hsueh, Tzu-Shan Chen, Jia‐Jin Chen, Fu‐Zen Shaw (2016). Neurofeedback training of EEG alpha rhythm enhances episodic and working memory. doi:10.1002/hbm.23201
[27] Nina Omejc, Bojan Rojc, Piero Paolo Battaglini, Uroš Marušič (2018). Review of the therapeutic neurofeedback method using electroencephalography: EEG Neurofeedback. doi:10.17305/bjbms.2018.3785
[28] Tomas Ros, Stefanie Enriquez‐Geppert, Vadim S. Zotev, Kymberly D. Young, Guilherme Maia de Oliveira Wood, Susan Whitfield‐Gabrieli et al. (2020). Consensus on the reporting and experimental design of clinical and cognitive-behavioural neurofeedback studies (CRED-nf checklist). doi:10.1093/brain/awaa009
[29] Anu Holm, Kristian Lukander, Jussi Korpela, Mikael Sallinen, Kiti Müller (2009). Estimating Brain Load from the EEG. doi:10.1100/tsw.2009.83
[30] Valeska Kouzak Campos da Paz, Ana Garcia, Aloysio Campos da Paz Neto, Carlos Alberto Bezerra Tomaz (2018). SMR Neurofeedback Training Facilitates Working Memory Performance in Healthy Older Adults: A Behavioral and EEG Study. doi:10.3389/fnbeh.2018.00321

---
*Citation check:*
```json
{
  "all_citations_valid": true,
  "invalid_citation_indices": [],
  "papers_never_cited": [
    18
  ],
  "total_citations_found": 29,
  "total_papers": 30
}
```
