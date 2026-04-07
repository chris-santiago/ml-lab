# Benchmark Prompts — v4

*53 cases. Answer-key fields (ground_truth, planted_issues, scoring_targets) omitted.*

---

## eval_scenario_004
**Category:** broken_baseline  
**Difficulty:** easy  
**Correct position:** critique

A streaming platform is reviewing a new offline recommendation stack for homepage videos. The legacy system uses a matrix-factorization candidate generator followed by a gradient boosted reranker. The proposed replacement introduces a two-tower retrieval model and a listwise transformer reranker. In the experiment report, the team compares the legacy stack's NDCG@20 against the new stack's NDCG@20 on a replay dataset built from impression logs. The new stack wins by about 4.5% relative, and the summary slide presents this as a model improvement.

The details section explains that the two-tower retriever returns 500 candidates per user, whereas the legacy retriever returned 200, because the new infrastructure can score more items. The replay evaluation then scores the reranker only on the candidates returned by each system's own retriever. As a result, the transformer reranker is evaluated on the newer 500-item candidate pool and the baseline reranker is evaluated on the legacy 200-item candidate pool. The team did not include a factorial ablation because the retrieval and ranking changes were launched together in code review. They also mention that the evaluation uses a leave-last-week-out split and only 5% of eligible users because older impression logs expire after 30 days, but the sampled users were drawn uniformly from all traffic segments.

Product leadership wants to use the offline gain as evidence that the new ranking model is stronger. Assess the benchmark design and what additional analysis would be needed before interpreting the reported lift.

---

## eval_scenario_005
**Category:** broken_baseline  
**Difficulty:** easy  
**Correct position:** critique

A pharmacy chain is evaluating a new demand-forecasting system for store-item replenishment. The incumbent baseline is an ARIMA-based model maintained by the supply-planning team, and the proposed replacement is a gradient boosting forecast that uses lagged demand, holiday calendars, and promotion plans. The project summary reports that the new model improves weighted absolute percentage error over the baseline by roughly 7% and recommends a phased rollout to all stores.

In the methodology appendix, the team notes that the data engineering group corrected several historical unit-conversion problems after discovering that some pack sizes were recorded inconsistently across vendors. They also backfilled known stockout days using neighboring-store patterns so the learning target reflects latent demand rather than observed zero sales during outages. Those corrections were applied in the new pipeline before training and evaluation. The baseline number, however, is copied from the prior replenishment dashboard, which was computed on the older raw sales series before unit normalization and stockout backfilling. In addition, the dashboard baseline was tracked for one-day-ahead forecasts, whereas the new project reports seven-day-ahead aggregate WAPE because planners place weekly orders. The report also mentions that only 18 months of history were available for some recently acquired stores and that evaluation used rolling-origin backtesting rather than a random split.

Operations leaders want to use the reported WAPE improvement to justify replacing the incumbent forecast. Review whether the benchmark comparison is valid and what a fair comparison would require.

---

## eval_scenario_015
**Category:** metric_mismatch  
**Difficulty:** easy  
**Correct position:** critique

A payments company is reviewing a fraud model before rollout to card-not-present traffic. The modeling team reports that the new system improves offline ROC-AUC from 0.948 to 0.967 on the last six months of labeled transactions and says in the rollout proposal that it should "cut chargebacks by 25% without materially increasing customer friction." Fraud labels arrive only after disputes and investigations, often six to eight weeks after the original transaction. The live system uses a score threshold plus a manual-review queue, and the business has little tolerance for false declines on repeat customers.

The evaluation packet includes ROC and precision-recall curves for the full validation set and shows that the new model is better almost everywhere on those curves. It does not include a threshold-specific simulation of approvals, manual-review load, merchant mix, or customer segment effects under the proposed operating policy. It also does not test how the model performs after intervention, when fraudsters adapt and when some suspicious transactions are blocked before labels can mature. The team argues that because AUC is substantially higher and the gain appears in multiple monthly backtests, the online result should follow. No live shadow test or randomized traffic split has been run yet.

Your task is to evaluate whether the reported evidence supports the proposal's business claim. Focus on whether the metric emphasized in the packet is the right one for the specific promised outcomes, and whether any defensible partial argument exists in favor of the rollout. You may also discuss what additional testing would resolve the disagreement.

---

## eval_scenario_022
**Category:** hidden_confounding  
**Difficulty:** easy  
**Correct position:** critique

A retail analytics vendor is summarizing a computer vision pilot for shelf monitoring. The system uses overhead store cameras to flag likely out-of-stock facings for packaged snacks and beverages. In the report, the vendor compares manual audit discrepancy rates from August and September, when the model was active in 30 stores near large universities, with rates from May and June in those same stores before the pilot. They conclude that the model reduced missed stockouts by 22% and recommend chain-wide rollout.

The report explains that the pilot stores were chosen because they already had camera coverage and store managers who would cooperate with manual audits. It also notes that the chain refreshed planograms and end-cap layouts in late July ahead of the back-to-school season. Traffic in these stores typically rises when students return, especially for snacks and cold drinks, but the report does not include stores outside the pilot group or a prior-year comparison for the same months. All pilot stores used the same camera mounting standard, and the model backbone had been pretrained on a large public retail-image dataset before fine-tuning on store-specific images.

The vendor emphasizes that audit procedures were consistent across periods and that the observed improvement was large enough to matter operationally.

---

## eval_scenario_024
**Category:** hidden_confounding  
**Difficulty:** easy  
**Correct position:** critique

A telecom retention team is assessing a new churn model built with an AutoML platform. Each week, the model ranks postpaid subscribers by predicted cancellation risk. Agents then call the highest-risk customers and can offer discounts or plan changes. After two months, the team reports that contacted customers chosen by the model churned less often over the next 60 days than customers who were not contacted, and it recommends making the workflow permanent.

The operational memo says only customers eligible for retention offers were placed in the calling pool. Prepaid users, accounts already delinquent, and some enterprise lines were excluded because agents could not offer the same save actions to them. Supervisors also allowed agents to override the ranked list for VIP accounts or customers with recent service complaints. The evaluation compared churn among contacted customers versus non-contacted customers during the same period, but did not mention a randomized holdout among eligible accounts. The model used routine account, billing, and service-history features, and the team attached SHAP-style feature summaries to show which variables mattered most.

Leadership likes that the workflow seems practical and interpretable. The question is whether the observed lower churn among contacted users demonstrates that the model and intervention genuinely reduced churn.

---

## eval_scenario_029
**Category:** scope_intent_misunderstanding  
**Difficulty:** easy  
**Correct position:** critique

A regional hospital system is reviewing a machine learning alert built to estimate which admitted adult inpatients are likely to meet sepsis criteria within the next 12 hours. The model was trained on electronic health record data from three hospitals in the system and reached an AUROC of 0.87 on a held-out retrospective test set. In a later silent prospective evaluation at one hospital, where scores were generated but not shown to clinicians, AUROC was 0.84 and the median lead time before documented sepsis recognition was about five hours. The product team now wants a press release and internal funding memo that describe the system as a tool that prevents sepsis deterioration by enabling earlier treatment, and the memo cites potential reductions in ICU transfers and mortality.

During a small operational pilot, clinicians did receive alerts, but there was no mandated treatment protocol, no randomization, and no comparison unit; clinicians could act on the alert, ignore it, or already have been evaluating the patient for sepsis. The pilot dashboard mainly reported alert precision, lead time, and how often clinicians opened the sepsis order set after seeing an alert. Pediatric patients, emergency department encounters, and hospitals outside the system were excluded. The training process oversampled septic cases to address class imbalance, but evaluation used the original event rate. Some leaders argue that if the model reliably flags patients earlier than charted recognition, it is reasonable to describe it as reducing harm. Others argue the current evidence supports prediction in similar inpatient adult settings, but not intervention effects. Assess whether the proposed claim is properly scoped to the evidence described.

---

## eval_scenario_030
**Category:** scope_intent_misunderstanding  
**Difficulty:** easy  
**Correct position:** critique

A recruiting software vendor is presenting results for a resume-screening model intended to assign a talent-fit score before a recruiter decides whom to interview. The model was trained on historical screening outcomes for English-language applications to U.S.-based software engineering roles at one large technology company. Evaluation used applicants from the following two quarters at the same company, and the vendor reports consistent precision-recall performance across those later cohorts. The vendor also reports a fairness analysis for self-reported male and female applicants in the U.S. sample and notes that names, explicit age fields, and gender fields were excluded from training.

The sales team now wants to market the system as a robust talent-fit scorer across roles and regions, including sales hiring in Latin America and customer support hiring in Europe. Internally, some stakeholders view the broader wording as reasonable because the model uses fairly general resume signals such as job titles, years of experience, certifications, and employer history. Others point out that the labels were recruiter decisions at one firm, for one family of jobs, in one language, and under one labor market context. The vendor argues that feature standardization through an external employer-and-school taxonomy should help portability, and that the time-split evaluation is stronger than a random split. The debate is whether the current evidence is enough to support the broader product claim or whether the claim goes beyond what the experiment actually established.

---

## eval_scenario_033
**Category:** scope_intent_misunderstanding  
**Difficulty:** easy  
**Correct position:** critique

A software company has trained a language model classifier to flag potentially toxic messages in English-language public social media posts. The model was fine-tuned on a large moderation dataset labeled for abusive or hateful content and reached strong F1 on a held-out test set drawn from the same social platforms. The company now wants to integrate the classifier into enterprise customer-support software and market it as a system that can detect harmful intent in live support chats and reduce agent harassment. Product managers note that support chats are also text conversations and that the model can already identify profanity, slurs, and insults in the public-post benchmark.

The internal review group is less convinced. They note that the benchmark labels concern observable toxicity in public posts, whereas customer-support exchanges involve a different communication setting, more indirect frustration, more domain-specific jargon, and a different moderation objective. In addition, the company’s rollout plan is to surface warning banners or route chats to supervisors when the model score is high, but the proposed materials discuss reducing harassment even though no intervention study has been run. To make the case more persuasive, the product team points out that support agents manually reviewed 200 flagged chats from one beta customer and said many looked genuinely hostile. There was no blinded evaluation on a representative support-chat sample and no controlled test of whether warnings or routing changed agent outcomes. The question is whether the current evidence supports the proposed claim as written, or whether there is a more specific mismatch between what the experiment establishes and what the product messaging implies.

---

## eval_scenario_048
**Category:** defense_wins  
**Difficulty:** easy  
**Correct position:** defense

A retail bank is evaluating a binary classifier that routes card transactions either to auto-approval or to a manual fraud review queue. The new model is compared against a rule-based system on an untouched three-month holdout containing 180,000 transactions. The team reports only recall, false-positive rate, and expected dollar loss at a decision threshold of 0.12, which initially looks unusually low for a fraud model. In the protocol document written before model training, however, the threshold was fixed from a cost matrix supplied by the fraud operations group: a missed fraud event was estimated to cost about 18 times as much as an unnecessary review, and the review team could absorb any policy that sent at most 2.5% of transactions to manual review. The stated objective was not to maximize generic classification accuracy or AUROC; it was to minimize expected fraud loss under the existing review-capacity constraint. The team did not sweep thresholds on the holdout, and all threshold selection was done on an earlier development split using the pre-specified cost matrix. On the final holdout, the new model sends 2.3% of transactions to review, improves recall relative to the rules engine, and reduces expected loss under the same budget. The report also notes that the threshold would be inappropriate for a different bank with different fraud prevalence or review costs. A critic reading the summary may still object that 0.12 is suspiciously low and must have been chosen to make recall look better, but the writeup explicitly frames the evaluation around the operational loss function and fixed queue size.

---

## eval_scenario_049
**Category:** defense_wins  
**Difficulty:** easy  
**Correct position:** defense

A hospital analytics group is evaluating a model that prioritizes chest X-rays for radiologist review. Their external validation report focuses on non-inferiority to the current technician-led priority system rather than superiority. The study uses 620 consecutively collected exams from a partner hospital, which some readers may view as too small for a medical ML validation. The protocol, however, was written before data collection and specified a non-inferiority margin of 0.03 AUROC units based on what the radiology department considered clinically negligible for queue ordering. A power analysis in that same protocol concluded that roughly 600 cases would provide 80% power to rule out performance worse than the current workflow by more than that margin, assuming the partner site's disease prevalence and label noise observed in a pilot month. After lock, the team collected 620 cases, evaluated the frozen model once, and reported a bootstrap confidence interval for the AUROC difference between the model-assisted queue and the existing process. The lower bound stayed above the negative 0.03 margin, so the study supports non-inferiority but not superiority. The report explicitly says the sample is too small for strong subgroup claims and only supports use in hospitals with similar imaging hardware and labeling policy. Because the headline table shows a modest point estimate and a cohort under 1,000 exams, a critic might say the validation is underpowered and therefore uninterpretable, but the design was built around a non-inferiority question with a pre-specified margin and a formal sample-size justification.

---

## eval_scenario_050
**Category:** defense_wins  
**Difficulty:** easy  
**Correct position:** defense

A subscription music service is testing a next-item recommendation model for the homepage shown to existing paying users. The evaluation uses a random interaction split within a 14-day window instead of a chronological split, which can look suspicious because recommendation work often worries about temporal leakage. The team anticipated that objection and included a pre-analysis section before the benchmark numbers. Using three earlier quarters of logs, they compared model rankings under random interaction splits and under week-forward chronological splits for the same stable subscriber population. Across those historical windows, the ranking of candidate models changed minimally and NDCG differed by less than 0.3 points on average. They also documented that 99.5% of evaluation users were already active subscribers before the window began, catalog turnover during the two-week period was negligible, and the deployment target is short-horizon reranking for the same mature user base rather than cold-start recommendation for new users or long-range demand forecasting. Based on that empirical stability analysis, they specified random splitting for the main benchmark because it allowed more efficient use of sparse positive interactions without changing model ordering in this deployment setting. The final report still notes that the results should not be reused to make claims about new-user generalization or rapidly changing catalogs. A critic could nevertheless see the random split and infer leakage or an unrealistically easy test set, but the writeup expressly ties that split choice to a documented i.i.d.-like regime and to the narrow production use case being claimed.

---

## eval_scenario_038
**Category:** real_world_framing  
**Difficulty:** easy  
**Correct position:** critique

An online marketplace is deciding whether to let a new fraud model automatically place certain orders on hold before shipment instead of sending them to the existing analyst queue. The payments team reports that the model achieved an AUC of 0.93 on six months of transaction history and says it captures fraud patterns missed by current rules. The proposed production use is narrow at first: auto-hold orders above a risk threshold for high-value electronics and gift cards during the holiday season, when analyst capacity is tight.

For development, the team labeled fraud using confirmed chargebacks and account takeovers that were resolved within 90 days. Transactions that were already blocked by current rules were excluded because they never reached fulfillment. Approved historical orders were scored retrospectively, and the model's ranking performance looked strong across card brands and regions. The presentation emphasizes that the positive class is rare and that a low false positive rate at the chosen threshold would still reduce analyst workload meaningfully.

Operations leaders ask whether the backtest is sufficient evidence for this production change, given that auto-holds would delay some legitimate orders. They also note that many holiday transactions do not have final dispute outcomes for several weeks, so the team is using the most recent fully matured period. Consider whether the evaluation supports the deployment decision, not just whether the model separates known fraud from known non-fraud in hindsight.

---

## eval_scenario_003
**Category:** broken_baseline  
**Difficulty:** medium  
**Correct position:** critique

A payments company is reviewing a new fraud-ranking model for card-not-present transactions. The legacy baseline is a gradient boosted tree trained on historical authorizations, and the new model is a larger ensemble with merchant and device velocity features. In the quarterly review deck, the baseline precision-recall AUC is listed as 0.214 based on a Q1 evaluation, while the challenger is reported at 0.220 on a Q2 evaluation. The team frames the six-basis-point gain as enough to justify migration because even small improvements affect investigation workload.

The documentation explains that the Q1 baseline score was produced from the standard dashboard, which uses provisional fraud labels available 30 days after authorization. For the challenger, the team waited for a 90-day maturity window because a newer dispute feed is now available and they wanted more complete labels before signing off. They also note that fraud prevalence remains around two-tenths of one percent, that both models were trained with forward-looking temporal splits by week rather than random splits, and that the Q2 evaluation covers a period after a merchant onboarding campaign changed the mix of transaction sizes and geographies. No confidence intervals or paired significance analysis are included in the deck because the absolute gain looks operationally meaningful to the fraud operations lead.

Management wants to treat the PR-AUC difference as evidence that the new model is better. Review whether the benchmark comparison is sound and what evidence would be required to support the migration decision.

---

## eval_scenario_006
**Category:** broken_baseline  
**Difficulty:** medium  
**Correct position:** critique

An insurance analytics group is benchmarking an AutoML system for classifying whether a claim will require special investigation. The baseline is a manually tuned logistic regression with one-hot categorical features and standard missing-value handling. The challenger is an AutoML search over gradient boosting and linear pipelines with target encoding for several high-cardinality fields such as repair shop, policy channel, and assessor ID. The final slide reports a clear win for the AutoML approach on ROC-AUC and a larger lift at the operating threshold used by the investigations team.

The methods appendix says the team first assembled a single modeling table from two years of claims and then applied median imputation and target encoding to the full table before creating cross-validation folds for the AutoML search. After selecting the best pipeline, they evaluated it on a held-out test set and chose the score cutoff that achieved 80% recall on that same test set because the investigations queue has a fixed service-level target. The logistic baseline was tuned earlier with nested cross-validation and continues to use the threshold selected from validation data in the original project. The report does not show a rerun of the logistic model under the AutoML preprocessing pipeline because the team considered the newer feature engineering part of the improved system.

A steering committee wants to accept the benchmark and move to implementation. Assess whether the evaluation design fairly demonstrates that AutoML beat the baseline and what comparison would be needed to justify that claim.

---

## eval_scenario_010
**Category:** broken_baseline  
**Difficulty:** medium  
**Correct position:** critique

A digital pathology team is comparing a new slide-level metastasis detector against its older convolutional baseline. The proposed system combines a pretrained foundation encoder with a refreshed image pipeline that performs stain normalization, extracts tiles at a different magnification, and applies a learned quality-control filter before inference. In the internal review, the new model is reported as having the best slide AUC the group has seen, and the summary chart places its result directly beside the baseline score from the previous benchmark cycle.

The implementation notes say the pathology slides are first broken into tiles and then passed through a quality-control network that removes blurry, pen-marked, or mostly background tiles. The new model is evaluated only on slides after that QC filtering stage, whereas the older baseline score being used for comparison was generated on all extracted tiles from the earlier pipeline. The stain-normalization parameters for the refreshed pipeline were estimated once from the full slide archive before the data split. In addition, the cross-validation folds for the new experiment were created at tile level rather than slide or patient level because that matched an older image-processing script. This means different tiles from the same slide or patient can appear in both train and test. The report also notes that an external set of about 600 slides from a second scanner was available and produced a wide but usable confidence interval.

Research leadership is citing the benchmark as evidence that the foundation model is superior. Assess whether the reported comparison is fair and what a corrected evaluation would need to show.

---

## eval_scenario_014
**Category:** metric_mismatch  
**Difficulty:** medium  
**Correct position:** critique

A large company is considering a model to rank internal applicants for promotion interviews. The analytics team reports that the new model improves macro-F1 from 0.71 to 0.78 on historical promotion decisions and writes in the proposal that the system is "fairer across gender groups" than the manual process currently used. The training labels are prior manager recommendations that were later approved or rejected by a committee. The team says names and photos were removed from the feature set, job level was standardized across departments, and the test split was taken from a later time period rather than random rows.

The evaluation packet focuses on overall macro-F1 and a single confusion matrix for the full employee population. It does not show false-positive, false-negative, calibration, or ranking quality broken out by gender or by intersectional subgroup. It also does not specify what notion of fairness the proposal is using: equal opportunity, calibration, demographic parity, or something else. Some executives argue that if predictive performance on historical decisions improved after removing explicit identity fields, then the process is probably fairer in practice. Others are uneasy because the claim being made is specifically about fairness, not just accuracy relative to past decisions.

Your task is to assess whether the evidence supports the fairness claim. Focus on whether the metric reported actually measures the property named in the proposal, and whether any reasonable defense of the current evaluation exists. You may discuss what additional analysis would be needed before the company could responsibly make the stated claim.

---

## eval_scenario_018
**Category:** metric_mismatch  
**Difficulty:** medium  
**Correct position:** critique

A public-safety agency is evaluating an automatic speech recognition system for emergency calls. The vendor reports that average word error rate fell from 13.2% to 8.7% on a held-out corpus of transcribed calls and says the upgrade will "reduce dispatch mistakes and shorten time to action." The benchmark is large, includes multiple accents, and was split by call date to avoid overlap between train and test. The agency is deciding whether that evidence is enough to support procurement messaging about operational improvement.

Dispatch supervisors note that a small number of words often carry most of the operational risk: street numbers, apartment identifiers, medication names, whether a patient is breathing, whether a weapon is present, and other details that may be rare but crucial. The current evaluation packet reports only mean WER and average real-time factor. It does not separately evaluate named entities, critical-slot extraction, speaker turn attribution, interruptions, or whether the transcript becomes available early enough to affect dispatch decisions. The proposed workflow would use transcripts both for live decision support and for downstream NLP models that summarize incident details. The vendor argues that a 4.5-point WER drop on a realistic call set is substantial and that average latency remains within product requirements.

Your task is to assess whether the metric evidence supports the specific operational claim. Focus on whether the reported benchmark aligns with the kinds of mistakes and timing constraints that matter in emergency dispatch. You may discuss whether the benchmark still provides useful evidence, but keep the evaluation tied to the actual claim in the procurement language.

---

## eval_scenario_019
**Category:** metric_mismatch  
**Difficulty:** medium  
**Correct position:** critique

An education company is reviewing an adaptive tutoring policy for middle-school math. The reinforcement-learning team reports that the new policy raises offline expected reward in historical replay and increases immediate next-problem accuracy by 8 percentage points in a simulator built from prior student sessions. The launch memo says the policy will "improve student learning gains by the end of the term." The simulator reward heavily weights whether a student answers the next problem correctly after receiving a hint or worked example.

The company has rich session logs but only sparse delayed assessments, because most classrooms administer common post-tests at the end of units rather than after every lesson. Teachers also vary in how they override recommendations, and some students stop using the product when exercises feel too easy or too hard. The evaluation packet does not report delayed retention, transfer to novel problems, or end-of-unit assessment outcomes. It also does not show whether the replay estimator remains reliable when the new policy would send students into content states that were uncommon under the old policy. The team argues that immediate correctness is the most practical proxy available and that the simulator reproduces historical clickstream statistics well.

Your task is to assess whether the current evidence supports the launch memo's claim. Focus on whether the reported metrics align with the outcome named in the memo and whether the offline evidence is strong enough to justify that statement. You may discuss both what is persuasive in the current packet and what remains unresolved.

---

## eval_scenario_021
**Category:** hidden_confounding  
**Difficulty:** medium  
**Correct position:** critique

A payments company is considering a new fraud model for card-not-present transactions. During a six-week pilot, the model was enabled only for merchants that volunteered for an early access program. Those merchants received model scores and could configure their own approval thresholds, while the rest of the network continued on the legacy rules engine. The results deck highlights that pilot merchants saw a lower fraud-loss rate and fewer customer complaints about false declines than merchants that stayed on the old system.

The deck says the comparison used the same calendar weeks for both groups and that labels came from chargebacks and confirmed fraud investigations. Pilot merchants were mostly large retailers with dedicated risk teams, because they were the ones willing to participate early and integrate the score feed quickly. The company also notes that some pilot merchants had recently adopted stronger checkout authentication features, but this is discussed only as implementation context rather than as part of the model evaluation. The appendix further states that detailed labels are only available for approved transactions, since declined transactions generally do not produce downstream fraud outcomes.

The proposal recommends expanding the model network-wide, arguing that the pilot demonstrates both lower fraud and fewer false positives in real production traffic.

---

## eval_scenario_023
**Category:** hidden_confounding  
**Difficulty:** medium  
**Correct position:** critique

A hospital quality team is evaluating a sepsis risk model intended to prioritize rapid review by a response nurse. The model went live on November 1 in two emergency departments. In a summary to leadership, the team reports that mortality among patients flagged by the model in November and December was lower than mortality among a historical comparison group from July through September, and they present this as evidence that the model is improving care.

The summary explains that the alert itself did not prescribe treatment, but flagged patients were discussed more quickly once the model was active. Around the same time, the hospital opened a winter surge unit and updated its empiric antibiotic guidance for suspected sepsis. The inclusion criteria for the analysis were adults admitted through the emergency department who had a lactate test ordered within the first few hours, because that was the easiest subgroup to extract reliably from the electronic record. The writeup does not include a concurrent control unit or a comparison to the same months in the prior year. It also does not separate whether mortality changes reflected the model, the operational changes, or differences in seasonal patient mix.

The model uses standard bedside vitals and lab values and was internally validated before deployment. Leadership is deciding whether to extend it across the rest of the hospital.

---

## eval_scenario_028
**Category:** hidden_confounding  
**Difficulty:** medium  
**Correct position:** critique

A consumer lender is reviewing a collections model that ranks delinquent accounts by expected near-term recovery. In a board update, the servicing team reports that average recovered balance per assigned account increased by 16% after the model replaced the prior queueing rules. The comparison uses accounts worked from February through April after deployment versus accounts worked from November through January before deployment. The board memo frames the change as evidence that the model is improving collection efficiency.

The later period overlaps tax-refund season, when many borrowers receive temporary liquidity and recovery patterns often change. During the same time, the lender switched to a new dialer vendor that verified more phone numbers and reduced unreachable accounts in the work queue. Managers were also allowed to pull certain hardship or recently promised-to-pay customers to the front of the queue, even if their model rank was lower, because they wanted to manage service-level commitments. The memo does not show a same-period control group, and it does not compare recovery separately for accounts newly reachable under the dialer change. It also does not explain whether agents handled the same number of accounts per shift in both periods.

The model uses standard account, payment-history, and contactability features. Executives agree the metric matters financially, but they want to know whether the observed gain should be treated as strong evidence that the model itself caused better recoveries.

---

## eval_scenario_036
**Category:** scope_intent_misunderstanding  
**Difficulty:** medium  
**Correct position:** critique

A cancer center has trained a pathology-image model to predict six-month progression-free survival for patients with early-stage breast cancer who received treatment at that center over the last decade. The model was evaluated retrospectively on held-out slides from the same institution and appeared to improve risk stratification beyond standard clinical covariates. The translational research team is enthusiastic because the model seems to capture visual patterns not represented in structured pathology reports. A draft slide for hospital leadership says the system can guide adjuvant therapy selection across solid tumors.

Several oncologists are uneasy with that wording. They note that the current label is prognosis under historical treatment patterns at one center, not a direct estimate of treatment benefit for different regimens. They also point out that the study population consists only of early-stage breast cancer cases, while the proposed claim reaches across very different tumor types with distinct biology, therapies, and pathology workflows. In addition, treatment choices in the retrospective data were not randomized; they reflected clinician judgment, patient comorbidities, and evolving standards of care over ten years. Supporters of the broader statement reply that the model is not being pitched as a fully autonomous prescribing system and that any tool improving prognosis estimation is naturally relevant to treatment planning. The debate is whether that logic is enough to justify the cross-tumor therapy-guidance claim, or whether the current evidence supports only a much narrower statement about prognostic enrichment in a specific clinical setting.

---

## eval_scenario_051
**Category:** defense_wins  
**Difficulty:** medium  
**Correct position:** defense

A customer-support team is evaluating an NLP classifier that either sends a templated auto-reply or defers a ticket to a human agent. The paper reports precision, harmful-error rate, and coverage only for tickets above a confidence threshold of 0.92, while all lower-confidence tickets are routed to humans and excluded from the auto-reply error metric. That can look like cherry-picking because the model is not being scored on every incoming ticket. The threshold, however, was written into a pre-registration before model development because legal and operations stakeholders defined a system-level requirement: wrong automated replies had to stay below 1% of auto-resolved tickets, and at least 30% of total ticket volume needed to be eligible for automation to justify launch. The model was then trained, calibrated on a development split, and frozen. On the untouched test set, 37% of tickets exceeded the threshold, the harmful-error rate among auto-resolved tickets was 0.7%, and the remainder were intentionally sent to human agents. The report also provides the abstention rate and states clearly that the claim is about the full selective-prediction system, not about universal classification over all tickets. The authors note that a different support organization with a different tolerance for automation errors would need a different threshold. A critic might still object that excluding abstained cases makes the reported precision artificially high, but the whole product decision is whether the abstaining system safely automates a subset while leaving the rest to people, and that operating point was fixed before the final test.

---

## eval_scenario_052
**Category:** defense_wins  
**Difficulty:** medium  
**Correct position:** defense

A manufacturer is benchmarking a computer-vision defect detector for a production line where positive examples are rare. The dataset contains 9,800 product images, only 410 of which show true defects confirmed by later inspection. To address this imbalance, the training pipeline heavily oversamples positives and applies rotations, flips, and brightness changes that create many near-duplicate images. A reader skimming the methods might worry that the team effectively copied defect images into validation data and inflated performance. The pipeline description is more careful than that summary suggests. The authors use nested cross-validation, and every split is performed at the original-image level before any augmentation occurs. All augmentations are generated on the fly inside the training fold only. Hyperparameters are chosen using inner folds, the selected model is retrained on the full development set with the same fold-local augmentation policy, and it is evaluated once on a final held-out test set consisting of raw images captured during a later production week. The report also states that defect clustering by physical part number was checked so that nearly identical shots from the same physical unit do not cross split boundaries. Because the final claim is limited to this camera setup and this manufacturing process, the authors do not present the result as broad cross-factory generalization. Even so, the presence of aggressive oversampling and many synthetic positives can make the benchmark look contaminated to a critic who assumes augmentation happened before splitting, when the method section actually specifies the opposite order.

---

## eval_scenario_053
**Category:** defense_wins  
**Difficulty:** medium  
**Correct position:** defense

A utility company is evaluating a time-series model that forecasts store-level electricity demand 15 minutes ahead to support intraday balancing. Instead of a standard last-month holdout, the team uses blocked random windows from a six-week evaluation period. That choice can appear wrong because time-series work usually emphasizes chronological backtesting. The methods section explains why they departed from that default. Before final benchmarking, the team ran a pre-analysis on the previous six months of data and found that after conditioning on temperature, weekday, holiday status, and recent lagged load, residual autocorrelation dropped to near zero beyond two hours. They also compared model rankings under rolling-origin evaluation versus blocked random windows across four historical periods and observed less than 1% difference in MAPE and no model-order reversals in the top three candidates. The operational deployment retrains the model nightly and only needs one-step-ahead forecasts for the next 15 minutes, not long-range projections across regime shifts. Based on those empirical checks, the evaluation plan specified blocked random windows to make better use of scarce extreme-weather intervals while preserving the same short-horizon forecasting target. The report explicitly says the results should not be used to claim robustness to seasonal drift or to week-ahead forecasting. A critic might still see the random windows and assume the evaluation ignored temporal dependence, but the justification is that this particular residual process is close to i.i.d. at the chosen horizon after conditioning, and that claim was checked in historical data before the final comparison.

---

## eval_scenario_057
**Category:** defense_wins  
**Difficulty:** medium  
**Correct position:** defense

A clinical ML team developed a sepsis early-warning model at one tertiary hospital and then validated it on data from one partner hospital that uses the same electronic health record vendor and nearly identical bedside documentation templates. Critics often object to single-site external validation, and this study seems vulnerable because the partner cohort is only one institution and some minority subgroups are too small for precise calibration curves. The report is narrower than a casual reading suggests. Before validation, the authors defined success as maintaining acceptable discrimination and calibration after a simple intercept recalibration using the first month of unlabeled prevalence information from the partner hospital. They did not claim universal transport across all hospital types. Instead, the stated question was whether the model could be ported to another site with the same EHR configuration, similar lab panel availability, and comparable nursing documentation cadence. On the held-out partner-hospital cohort, the recalibrated model meets the pre-specified discrimination and calibration targets, and the report explicitly states that subgroup estimates with wide intervals should be treated as descriptive only. It also states that a community hospital with different triage workflows would require a separate validation. A critic could still say that because only one external hospital is included and subgroup power is limited, the entire validation is methodologically unsound. Exonerating the study requires separating two ideas: limited transportability beyond similar hospitals is a real limitation that warrants disclosure, but it does not invalidate the narrower claim that the model was successfully validated for a closely matched site under a prospectively described recalibration procedure.

---

## eval_scenario_058
**Category:** defense_wins  
**Difficulty:** medium  
**Correct position:** defense

A software company built an NLP routing model for customer-support emails and evaluated it only on English messages from its U.S. enterprise customers. That choice can look problematic because the company also serves some multilingual accounts, and the architecture is capable of processing multiple languages. The report, however, is careful about what is and is not being claimed. Product operations had already decided that the first launch would cover only English-language inboxes, with all other languages routed directly to human specialists. The study therefore restricted the dataset, annotation guidelines, and success criteria to English messages. Before training, the team pre-specified that deployment would remain English-only until a separate multilingual annotation effort and language-specific calibration study were completed. The final test set consists of a future month of U.S. enterprise emails, and the model is only claimed to improve routing accuracy and response-time triage in that English workflow. The report openly states that it provides no evidence about other languages, smaller self-serve customers, or non-U.S. legal terminology. It also includes a fairness appendix using available role and account-size labels within the English population, while noting that some demographic dimensions are unobserved. A critic might still argue that because the vendor's overall product is global and demographic coverage is incomplete, the benchmark is invalid or biased on its face. Exonerating the work requires noticing that absence of evidence for unclaimed populations is not the same as evidence against the validity of the explicitly English-only deployment claim, and that missing labels for some fairness dimensions create a disclosure obligation rather than automatically nullifying the in-scope test result.

---

## eval_scenario_060
**Category:** defense_wins  
**Difficulty:** medium  
**Correct position:** defense

A lender is testing a tabular risk model that predicts whether a consumer loan application will become 90-days delinquent. The feature list includes several missingness indicators, such as whether income documentation was absent at submission and whether the external bureau returned a thin-file code. Those variables can look suspicious because critics often associate missingness with target leakage or with hidden use of downstream manual-review outcomes. The study's methods section draws a sharper line. All missingness indicators are computed at the moment the application packet is submitted, before any underwriting decision or collection outcome is observed. The model does not use manual-review notes, final approval decisions, or any post-decision interventions. The reason for keeping the indicators is operational: incomplete documentation and bureau thin files are genuinely available at scoring time and affect near-term default risk in this underwriting workflow. The benchmark evaluates the frozen model on a future quarter of applications using exactly the information available at submission time. The report also includes a fairness audit over the bank's monitored protected-class proxies and states clearly that a different institution with different document-collection practices would need separate validation. A critic might still argue that because the model uses missingness patterns, it is necessarily leaking downstream process information or is methodologically invalid as a credit model. Exonerating the work requires distinguishing between a legitimate predictive feature available at decision time and an impermissible post-outcome proxy. The study may still deserve disclosure about workflow dependence and fairness monitoring, but those concerns do not by themselves invalidate the in-scope predictive evaluation described here.

---

## eval_scenario_040
**Category:** real_world_framing  
**Difficulty:** medium  
**Correct position:** critique

A public health network is considering deploying a diabetic retinopathy model in mobile screening vans that visit rural communities. Nurses would capture retinal photos, and patients above the model threshold would be referred for in-person ophthalmology follow-up within two weeks. The health network currently relies on a rule that sends many unreadable or borderline images for referral, creating long waits at the regional eye clinic. The modeling team reports strong retrospective sensitivity and specificity on 60,000 prior images collected at the network's hospital eye centers and says the model could reduce unnecessary referrals by one-third.

In the historical dataset, ophthalmologists assigned the final disease labels after reviewing images from patients who completed specialty exams. Many of those patients were originally sent for follow-up because a clinician or an earlier screening rule considered them suspicious. The mobile program would use lower-cost cameras and staff with less ophthalmic training, but the vendor says the imaging protocol is similar. The deployment plan keeps a quality-control rule: any image judged unreadable by the capture software still goes to manual review, which some board members think may hide a problem. The team also notes that disease prevalence in the rural program is expected to be lower than at the referral centers where the model was studied.

Program leaders ask whether the retrospective hospital-center results justify using the model to determine who gets scarce follow-up appointments in the mobile setting. Consider what the labels and workflow imply for prospective deployment.

---

## eval_scenario_041
**Category:** real_world_framing  
**Difficulty:** medium  
**Correct position:** critique

A city emergency communications agency is evaluating an ML model that predicts which incoming non-English 911 calls are likely to require a live interpreter within the first minute. The current process connects every such call to an interpreter service by default, which adds cost and occasionally increases answer time. The proposed deployment would instead let dispatchers delay interpreter connection for low-risk calls while continuing immediately for higher-risk ones. The vendor presents retrospective results from archived call audio and transcripts, claiming the model could cut interpreter usage by 35% with minimal impact on high-acuity incidents.

Historical labels come from whether an interpreter was actually joined to the call and whether supervisors later marked the call as having a communication problem. Over the study period, dispatcher practices changed across shifts: some teams almost always brought interpreters in early, while others relied on bilingual staff or caller family members. The evaluation reports aggregate precision and recall but does not separate chest pain, domestic violence, welfare checks, and low-priority property incidents. The agency plans to keep a rule that any caller who sounds distressed, disconnected repeatedly, or cannot confirm location still gets an immediate interpreter, regardless of model score. Some reviewers have focused on whether background noise and accent variation will reduce transcription quality, while the vendor argues the audio model does not rely entirely on ASR output.

Agency leadership asks whether the retrospective evidence justifies using the model to delay interpreter connection in production. Consider the deployment framing, not just whether historical labels are predictable.

---

## eval_scenario_045
**Category:** real_world_framing  
**Difficulty:** medium  
**Correct position:** critique

A national health insurer is deciding whether to deploy a model that automatically approves common oncology prior-authorization requests while sending others to manual review or denial. The business case is that oncologists are frustrated by delays, nurses spend large amounts of time on status calls, and medical-review staff are stretched thin. The model was trained on several years of historical authorization requests, diagnosis and regimen codes, prior approvals, and subsequent claims. The vendor's retrospective validation highlights high agreement with past approvals and says the system could auto-approve a majority of standard requests.

Under the proposed workflow, requests the model deems low-risk would be approved immediately, while the rest would either be escalated to clinical review or, for some out-of-policy regimens, denied more quickly than today. Historical labels are based on final authorization outcomes after medical-review staff applied payer policy in effect at the time. Over the study period, however, oncology policies changed repeatedly as guidelines evolved, new biosimilars entered use, and some therapies moved from inpatient to outpatient billing pathways. Urgent cases were also sometimes handled outside the standard queue with expedited physician-to-physician review, leaving less structured documentation. The validation deck reports high historical agreement and short simulated turnaround times, but it does not show performance by cancer type, line of therapy, or policy vintage.

The utilization-management committee asks whether this retrospective evidence justifies automated approvals and faster denials in production, or whether the framing of the evidence misses something important about how oncology authorization actually works.

---

## eval_scenario_007
**Category:** broken_baseline  
**Difficulty:** hard  
**Correct position:** mixed

A health-system analytics team is preparing to replace its ICU deterioration model with a newer temporal transformer for early sepsis escalation. The incumbent baseline is an LSTM originally developed on admissions from two hospitals, and the proposed system is trained from the same EHR warehouse but under a refreshed cohort-building pipeline. In the comparison memo, the new model is reported as outperforming the baseline on AUROC and early-warning recall, and the authors describe the refresh as part of the platform modernization effort rather than as a separate study variable.

The updated pipeline merges ICU transfers that occur within four hours into a single care episode, backfills serum creatinine timestamps from charted time to specimen collection time when the lab interface provides both, and labels a positive case as septic shock onset within 12 hours. The earlier baseline study used separate admissions, relied on charted times, and predicted a broader severe-sepsis endpoint within 24 hours. For the new benchmark, the team trained and evaluated all episodes using a random encounter-level split across the full warehouse. Because some patients have multiple ICU stays over several years, the same patient can contribute episodes to both train and test. The report also includes a small external set of about 1,100 ICU episodes from Hospital B that the authors say was powered for AUROC estimation, and they note that variables such as lactate and vasopressor exposure are included only if observed before the prediction cutoff.

Clinical leadership is treating the comparison as evidence that the transformer is better than the incumbent. Review the evaluation design and argue whether that conclusion is already supported, partially supported, or unsupported.

---

## eval_scenario_008
**Category:** broken_baseline  
**Difficulty:** hard  
**Correct position:** mixed

A subscription business is evaluating a new targeting policy for sending retention offers at renewal risk. The incumbent baseline is a logistic response model that ranks customers by probability of accepting a discount. The proposed replacement is a causal forest trained to estimate incremental profit from contacting each customer. In the offline policy review, the team reports that the new policy would have produced higher profit than the baseline on a completed randomized discount experiment, and finance is preparing to adopt it for the next campaign cycle.

The analysis package says the older baseline had historically been judged on 14-day renewal retention, while the new policy review emphasizes 28-day net contribution margin after discounts and support costs. To evaluate the causal forest, the team computes doubly robust scores using nuisance models and a propensity model fit once on the full experiment log, including the final slice used for headline reporting. They then choose the contact cutoff that maximizes estimated incremental profit on that same final reporting slice. Treatment rates differed by region because campaign budgets were capped locally, but assignment was randomized within each region and week. The memo does not include a rerun of the logistic baseline under the 28-day margin target; instead it compares the old model's contact rule under its prior cutoff with the new policy under the profit-maximizing cutoff selected from the final slice.

Commercial leadership reads the deck as proof that the causal policy is superior. Assess whether the benchmark already establishes that conclusion and what additional test would settle the dispute.

---

## eval_scenario_009
**Category:** broken_baseline  
**Difficulty:** hard  
**Correct position:** critique

A card-network risk team is assessing whether to replace its production fraud detector with a new graph-based model. The production baseline is a gradient boosted tree scored on an authorization stream, and the challenger adds graph embeddings plus a new merchant-normalization pipeline that merges aliases thought to refer to the same merchant. In the migration deck, the new system is shown with better precision at a fixed alert volume and a modest gain in PR-AUC on the most recent quarter. The team describes the pipeline changes as part of a data quality upgrade completed during the same release cycle.

The details reveal that the challenger evaluation excludes transactions whose disputes were still unresolved after 60 days so that labels are cleaner at reporting time. It also evaluates on an authorizations-only feed after deduplicating PAN, merchant, amount, and timestamp combinations using the new merchant-normalization rules. The baseline number, by contrast, is copied from the production dashboard on the raw transaction feed, which includes later-resolved disputes and does not apply the new alias-merging deduplication. The alert threshold for the graph model was then tuned on the same Q4 quarter used for final reporting because investigators wanted exactly 18,000 alerts per week. The report does not rerun the production baseline on the deduplicated feed or with the same 60-day label rule.

Risk leadership is leaning toward approving the migration based on the benchmark deck. Review whether the evaluation design fairly establishes that the graph model is better than the existing detector.

---

## eval_scenario_013
**Category:** metric_mismatch  
**Difficulty:** hard  
**Correct position:** mixed

An automotive company is reviewing a perception update for its advanced driver-assistance system. The vision team reports that the new pedestrian detector raises benchmark mAP@0.5 from 61 to 69 on a held-out set collected from the fleet. In the launch memo, they want to say the update will make the car "safer at night during emergency braking scenarios involving pedestrians." The benchmark includes mixed daytime and nighttime frames from urban and suburban roads, with roughly 70% of frames captured during daylight. Ground-truth labels are 2D bounding boxes.

The new model runs on the same camera hardware as the previous model but adds about 80 milliseconds of average inference latency. The team argues that this is acceptable because mAP increased at all object sizes. They also report that the nighttime slice of mAP improved, though the memo still emphasizes the overall headline number. No end-to-end braking simulations or closed-track safety tests are included in the packet. The system's downstream planner triggers braking only when detections are sufficiently early and stable across consecutive frames. The evaluation does not report first-detection distance, frame-to-frame stability, or recall for near-field pedestrians in low-light conditions.

Your task is to judge whether the benchmark evidence supports the safety claim in the memo. Focus on whether the chosen metric matches the specific statement being made about nighttime emergency braking. You may discuss what parts of the evidence are still useful, what stronger evidence would be needed, and whether any defense of the existing evaluation is reasonable.

---

## eval_scenario_016
**Category:** metric_mismatch  
**Difficulty:** hard  
**Correct position:** mixed

A streaming platform is deciding whether to advance a recommendation model from offline evaluation to an online experiment. The ranking team reports a 7% gain in NDCG@20 on replay logs and says the model will "likely improve next-day watch time." Their packet includes inverse-propensity-weighted replay estimates with bootstrap confidence intervals, plus a chart showing that over the last four launches, offline NDCG changes were positively correlated with online watch-time lift. One past launch involving a cold-start catalog expansion did not follow the same pattern.

The candidate model changes how the top of the slate is ordered but does not alter the candidate-generation pool. The evaluation data come from recent traffic, and the team stratified the offline analysis by region and device type. They also report that diversity scores are roughly unchanged. Critics inside the company point out that watch time is affected by slate interactions, novelty, creator supply, and feedback loops that replay logs may not fully capture. Supporters respond that the company has historically used NDCG as a launch gate and that the observed offline-to-online relationship is stronger here than in many previous launches. No A/B test has been run yet, but the team is asking whether the current evidence is enough to state that the model is likely beneficial rather than merely worth testing.

Your task is to assess the strength of the argument. Focus on whether the metric evidence is sufficient for the specific claim being made about watch time, and whether a nuanced position is more appropriate than a simple yes-or-no answer.

---

## eval_scenario_017
**Category:** metric_mismatch  
**Difficulty:** hard  
**Correct position:** mixed

A hospital system is evaluating an LLM that drafts radiology reports from chest X-rays. The vendor's deck emphasizes two numbers: a large increase in label-extraction F1 on CheXpert-style findings and a reduction in edit distance to attending-written reports. Based on those results, the vendor says the system is "clinically acceptable enough to reduce radiologist editing time." A small internal pilot at one site found that cases with better finding-label agreement tended to require less editing, but the pilot involved only one modality and did not include a controlled comparison against the current dictation workflow.

The benchmark labels cover common findings such as pleural effusion, cardiomegaly, and consolidation, but not every nuance that matters in a report, such as uncertainty phrasing, interval change, recommendation wording, comparison to prior studies, or whether a critical but rare incidental finding was omitted. The edit-distance metric is computed against one reference report per study even though radiologists at the institution often use different but equally acceptable wording. The evaluation packet includes confidence intervals and notes that human inter-rater agreement on some finding labels is below perfection, which the vendor cites as evidence that the model is nearing expert performance. No blinded study measures actual editing time, clinically important omission rate, or downstream effect on report acceptance.

Your task is to assess whether the current evidence supports the stated deployment claim. Focus on whether the reported metrics are adequate for the specific claim about clinical acceptability and reduced editing burden, and whether a balanced debate could reasonably end with a request for additional empirical testing rather than a simple accept-or-reject decision.

---

## eval_scenario_025
**Category:** hidden_confounding  
**Difficulty:** hard  
**Correct position:** mixed

A regional electric utility is deciding whether to replace its day-ahead load forecasting vendor. The analytics team reports that the new model produced a mean absolute percentage error of 6.9% during its first three months in production, compared with 7.8% for the prior vendor over the preceding three months. The recommendation memo says the reduction is large enough to improve generation scheduling and imbalance costs, so the utility should sign a multiyear contract.

The old vendor's forecasts were used from January through March, while the new vendor's forecasts were used from April through June. The memo notes that April through June had milder temperatures and no major storm-related outages, whereas the earlier quarter included several cold snaps and two grid events that required emergency operating actions. The new vendor ingests standard weather forecasts and feeder-level history, and it can optionally refresh intraday features before finalizing the day-ahead file. The memo does not show both vendors generating forecasts for the same dates, does not report whether the forecast submission cutoff was normalized between vendors, and does not compare performance by weather regime or outage days. Instead, it presents the quarter-level average error numbers side by side and states that the new model performed better in live conditions.

Finance and operations leaders are aligned that even a modest forecasting gain would matter, but they want to know how much confidence to place in the apparent improvement.

---

## eval_scenario_026
**Category:** hidden_confounding  
**Difficulty:** hard  
**Correct position:** mixed

A hiring marketplace is evaluating a machine-learning feature that recommends a shortlist of candidates to employers. Employers can open a new "smart shortlist" tab inside the recruiting dashboard, review the ranked suggestions, and invite candidates directly from that view. In the quarterly business review, the product team reports that employers who used the tab had an 18% higher interview-to-application rate than employers who did not use it, and it argues that the model is improving matching quality.

The feature was introduced in January, and adoption rose steadily through March. Those months also coincide with the platform's graduate recruiting season, when large employers post more structured early-career roles and interview volume typically changes. The review notes that employers with an applicant-tracking-system integration adopted the tab earlier because activation was simpler for them, and that regional sales teams rolled out enablement training on different weeks. The analysis compares employers that used the tab at least once during the quarter with employers that never used it, controlling for company size and industry in a regression. It does not mention any randomized exposure, encouragement design, or comparison of outcomes before and after adoption relative to a matched non-adopter set. The model retrains weekly on recent application and interview signals.

Leadership agrees that the metric is commercially relevant, but wants to know whether the observed difference is enough to support broad rollout and pricing changes.

---

## eval_scenario_027
**Category:** hidden_confounding  
**Difficulty:** hard  
**Correct position:** critique

A bank's internal audit group is evaluating an anomaly-detection model that scores journal entries for possible misstatement or fraud. According to a presentation for the audit committee, the model's precision improved from 11% in the second quarter to 19% in the fourth quarter after it was embedded into the auditors' review queue. The presentation suggests that the model is now mature enough to become the primary screening mechanism for manual review.

In the second quarter, auditors reviewed journal entries using a legacy rules list and their normal sampling plan. In the fourth quarter, after the model was introduced, the bank was also in year-end close, when journal volume rises and many legitimate manual adjustments occur. During that same period, the bank implemented a new dual-approval policy for large nonstandard entries. The presentation states that model precision was measured using the share of reviewed items that were ultimately escalated by auditors for deeper investigation or adjustment. It does not show a parallel holdout where the old screening method and the new model were applied to the same quarter, and it does not discuss whether embedding model scores into the queue changed which items auditors chose to inspect closely. A note in the appendix mentions that staffing was temporarily increased for the year-end close.

Committee members want to know whether the apparent precision gain should be treated as evidence that the model itself is materially better than the prior screening process.

---

## eval_scenario_032
**Category:** scope_intent_misunderstanding  
**Difficulty:** hard  
**Correct position:** mixed

A payments company has developed a gradient-boosted fraud model for card-not-present transactions. Training data came from one issuing bank’s e-commerce portfolio, and the team evaluated the model on the next six months of transactions plus a later sample from a partner bank that serves many of the same online merchants. Reported lift and calibration were similar across the two issuer datasets, and the deployment proposal explicitly says the model should rank transactions for analyst review rather than automatically decline them. The system was not evaluated on point-of-sale transactions or on merchant segments such as travel and buy-now-pay-later financing that were rare in the original data.

The business team wants marketing language saying the model can be used to prioritize review queues for national e-commerce merchants. Some analysts argue that this is adequately scoped because the claim is only about triage for card-not-present commerce, not about universal fraud prevention or autonomous decision-making. Others argue that the phrase national e-commerce merchants is still too broad because the evidence comes from issuer-side data concentrated in a subset of merchant categories, and the partner-bank check does not prove robustness across very different transaction mixes. A further complication is that fraud labels are chargebacks and confirmed fraud investigations, which are influenced by bank and merchant policies. The debate is whether the claim is already appropriately bounded for a practical triage use case, or whether it still overgeneralizes in a specific way that should be narrowed before release.

---

## eval_scenario_034
**Category:** scope_intent_misunderstanding  
**Difficulty:** hard  
**Correct position:** mixed

A city public-health team has built a neighborhood-week forecasting model for overdose spikes. The model combines wastewater measurements, EMS dispatch data, weather, mobility proxies, and recent overdose history to predict which neighborhoods will have unusually high overdose burden the following week. In retrospective evaluation over two years, the model showed useful ranking performance, and a spatial holdout analysis on neighborhoods omitted from training retained somewhat lower but still promising accuracy. The department wants to use the model to decide where to place a mobile naloxone and outreach van each week. A draft grant proposal says the system can direct van placement to reduce overdose deaths in urban neighborhoods.

Complicating the debate, the historical outcome labels are overdose deaths geocoded by the decedent’s residence, while the van would be sent to where overdoses are expected to occur and where people might accept services. During a one-month soft launch, the team informally sent the van to several high-score areas, but neighborhood partners differed in staffing, local trust, and available follow-up services, so outreach intensity was inconsistent and no counterfactual was maintained. Some staff argue that if the model can predict where burden will rise, it is already reasonable to say it can direct resources to reduce deaths, because targeting is the main policy decision. Others argue that the route from prediction to mortality reduction depends on service uptake, movement patterns, and the mismatch between residence-based labels and event-location operations. The model may be genuinely useful, but the dispute is whether the current claim is already justified, or whether a narrower claim or further study is needed before saying the system reduces overdose deaths.

---

## eval_scenario_056
**Category:** defense_wins  
**Difficulty:** hard  
**Correct position:** defense

A retail chain ran a city-level ad experiment to estimate whether a new local ranking model for search ads increases in-store visits. Only 24 metropolitan areas were available for the test, and the treated and control cities are not perfectly balanced on raw baseline traffic by chance. A quick read could therefore conclude that the experiment is too small and too imbalanced to support any causal claim. The protocol is more careful than that. Before assignment, the analysts constructed 12 matched pairs of cities using the previous eight weeks of store-visit volume, search volume, and seasonality indicators. Within each pair, treatment was randomly assigned. Because the number of clusters is modest, the pre-analysis plan did not rely on large-sample asymptotic standard errors. Instead, it specified a randomization-inference test on the matched-pair assignment and a pair-weighted estimate of average lift. The final report uses exactly that design, shows the assignment mechanism, and presents the distribution of all possible within-pair treatment reassignments under the null. The estimated lift is positive and the randomization-inference p-value falls below the pre-specified threshold. The report also states that the result should be interpreted for large metro areas similar to those tested and not as a universal estimate for small rural markets. A critic could still focus on the low number of cities, the visible baseline imbalance in the aggregate table, or the absence of a standard regression p-value and claim the experiment is invalid. Exonerating the work requires noticing that the inference procedure was chosen for a small matched-cluster design, and that limited transportability beyond similar metros is a disclosure issue rather than a reason to reject the internal validity of the causal estimate.

---

## eval_scenario_059
**Category:** defense_wins  
**Difficulty:** hard  
**Correct position:** defense

An e-commerce team wants to compare a new recommendation reranker against the current production policy using only logged historical interactions, so it uses an offline counterfactual evaluation rather than an immediate live experiment. The main estimator is self-normalized inverse propensity scoring with weight clipping at 20. Critics often view clipped IPS as suspicious because clipping introduces bias, and the setup can look even worse because some products were rarely shown under the historical policy. The report addresses this before presenting any model comparison. In a pre-analysis stage on older logs, the team checked overlap and found that the candidate reranker would only be evaluated on a restricted product shortlist where all items had non-negligible exposure under the logging policy. They also simulated variance-bias tradeoffs across clipping thresholds and selected a threshold of 20 before the final benchmark because unclipped IPS had unstable variance with occasional extreme weights, while clipping in the restricted-overlap regime changed estimates only modestly. The final report includes overlap diagnostics, effective sample size, and a sensitivity table for clipping thresholds 10, 20, and 50; the model ordering is stable across those settings. The claim is not that the exact effect size is unbiased in every possible catalog region. The narrower claim is that, on the supported shortlist with adequate overlap, the new reranker is preferred to baseline by standard off-policy estimators with stable diagnostics. A critic might still say that any clipped IPS estimate is invalid by construction. Exonerating the work requires recognizing that clipping can be a justified variance-control device when overlap is checked, support is restricted, sensitivity is reported, and the conclusion is correspondingly narrow.

---

## eval_scenario_039
**Category:** real_world_framing  
**Difficulty:** hard  
**Correct position:** mixed

A mid-sized bank wants to expand a machine-learning underwriting model for unsecured personal loans to applicants with variable gig-income histories. The credit policy team currently relies on bureau scores plus manual review for many of these applicants, which slows turnaround and limits volume. Model developers present a retrospective validation on three years of prior applications. Among applicants who were approved and booked, the model predicts 12-month serious delinquency substantially better than the bank's scorecard and appears especially strong on self-employed and platform-worker segments. Executives are considering using the model to approve some borderline applicants automatically and to decline others without manual review.

The historical data include application features, bank transaction summaries for customers who linked accounts, and repayment outcomes for booked loans. For declined applications, there is no repayment label. The validation deck shows calibration plots and profitability estimates based on historical loss assumptions, and it notes that the model was trained on a period with low unemployment and relatively stable household cash flows. Compliance staff point out that the bank would still run standard fair-lending reviews before launch. Some committee members worry that using linked-account cash-flow features could create noisy or seasonal signals, but the modeling team says those features materially improve ranking.

The lending committee asks whether the retrospective validation is enough to justify deploying the model for prospective approval and decline decisions in this new applicant segment. Consider both statistical performance and the framing of the real production decision.

---

## eval_scenario_042
**Category:** real_world_framing  
**Difficulty:** hard  
**Correct position:** critique

A large property insurer wants to deploy a computer-vision model that triages roof-damage claims after hailstorms. The current process sends a field adjuster to most claims, which creates long delays after major weather events. The proposed workflow would automatically route low-risk claims to desk review with satellite imagery and contractor photos, while reserving scarce field adjusters for claims the model predicts are likely to involve structural damage or fraud indicators. The vendor presents retrospective results on 40,000 prior claims and says the model could reduce field inspections by nearly half.

The labels used in training come from final claim dispositions and estimated repair severity in the insurer's internal system. However, field inspections were historically assigned partly by simple rules such as roof age, claim amount, region, and whether the first notice of loss mentioned interior water. Claims sent only to desk review often received less extensive documentation. The retrospective validation compares model scores to final severity labels and reports strong precision at the threshold selected for desk-review routing. It does not separately report outcomes for catastrophe periods, when independent adjusters and emergency tarping vendors are heavily involved. The operations team also notes that the model uses different photo sources in production than in some historical claims, because new self-service upload tools were introduced this year.

Claims leadership asks whether the backtest is enough to justify routing some future roof claims away from field inspection. Consider the production decision and the kinds of mistakes the insurer most needs to avoid.

---

## eval_scenario_043
**Category:** real_world_framing  
**Difficulty:** hard  
**Correct position:** mixed

A children's hospital is considering deploying an early-deterioration model on its general pediatric wards. The score would run continuously and page the rapid-response nurse when a patient crosses threshold twice within an hour. Hospital leaders are interested because several recent safety reviews found delayed escalation before some ICU transfers. The data science team presents a retrospective validation on four years of ward admissions showing substantially better discrimination than the hospital's bedside warning score for the endpoint of ICU transfer or ward cardiac arrest within the next 12 hours. A neighboring hospital in the same network reports similar retrospective performance.

The proposed deployment is advisory rather than fully automated, but a page from the system is expected to trigger an in-person assessment and could influence when residents call attendings. Historical training features include vital signs, oxygen settings, nursing documentation, and medication administrations. During the study period, however, some units already used proactive rapid-response rounding for high-risk patients, and clinicians occasionally transferred patients early based on concern before documented vital-sign deterioration. Patients with complex chronic conditions were overrepresented in the retrospective positives. The evaluation emphasizes AUROC and lead time, with a brief sensitivity analysis by service line, but it does not estimate how many pages per shift the chosen threshold would create or whether alerts would remain predictive once they begin changing clinician behavior. The hospital also plans to suppress pages for patients on end-of-life pathways and for those already receiving one-to-one ICU outreach, which a few committee members view as suspicious customization.

The safety committee asks whether the evidence is strong enough to turn on paging, whether only a silent phase is justified, or whether the model should not move forward at all. Consider the clinical deployment context rather than just the retrospective ranking result.

---

## eval_scenario_044
**Category:** real_world_framing  
**Difficulty:** hard  
**Correct position:** mixed

A global bank's financial-crime unit wants to deploy a machine-learning system that suppresses some low-risk anti-money-laundering alerts before they reach human investigators. Today, a rules engine generates a very large queue of transaction-monitoring alerts, and analysts close most of them as non-suspicious after brief review. The proposed model would sit after the rules engine and automatically close the lowest-risk portion of alerts, while sending the rest through the usual investigative workflow. The vendor shows retrospective results on two years of historical alerts, claiming the model could reduce analyst workload by 40% while preserving nearly all suspicious activity report (SAR) filings.

Training labels are based on final investigator dispositions, escalation decisions, and whether an alert family eventually led to a SAR. During the study period, alert-handling practices changed after an enforcement action: documentation requirements increased, some scenarios were re-tuned, and investigators were instructed to escalate more aggressively for certain jurisdictions. The model was validated by comparing suppression candidates against eventual SAR linkage and investigator close rates. Compliance leaders note that the bank would still keep sanctions screening, politically exposed person reviews, and high-risk geography rules unchanged. Some executives argue that because the model only acts after the existing rules engine, any false negative risk is limited. Others point out that the highest-risk cost is missing suspicious activity that never gets investigated deeply enough to be linked to a SAR.

The model risk committee asks whether the retrospective evidence is sufficient to deploy automated alert suppression, whether only a narrow pilot is defensible, or whether the approach is not supportable in this setting. Consider both ML evidence and the financial-crime deployment context.

---

## eval_scenario_046
**Category:** real_world_framing  
**Difficulty:** hard  
**Correct position:** critique

A state wildfire agency is evaluating a vision model that detects new smoke plumes from mountaintop camera feeds. The agency is considering using the model to reduce overnight staffing at a regional monitoring center by having one dispatcher supervise multiple camera districts, with human escalation only when the model or a neighboring center flags likely smoke. The vendor presents a retrospective study from the last two fire seasons showing high frame-level detection and faster average time-to-flag than manual monitoring on archived incidents. Budget pressure makes the staffing change attractive before the next dry season.

The historical evaluation used confirmed wildfire and prescribed-burn incident logs to label positive windows on archived camera feeds. Small ignitions that self-extinguished, were obscured by weather, or were never officially logged are not represented directly. Cameras were upgraded during the study period, and some districts now have different vegetation patterns, tourism traffic, and construction haze than they did in the retrospective set. The agency's proposed operations concept assumes that when the model stays silent, the reduced overnight team will not watch every feed continuously. The validation deck reports false-positive rates per camera-hour and event-level recall for logged incidents, but it does not estimate how often model silence would delay first awareness compared with current staffing on marginal overnight starts. Some managers are focused on the model's variable performance near sunrise and sunset, while others point out that those periods are already handled by shift overlap and may not drive the main risk.

Agency leadership asks whether the retrospective evidence is sufficient to justify staffing changes tied to model monitoring. Consider the decision framing, the missing counterfactuals, and the operational asymmetry between missed and extra alerts.

---

## broken_baseline_051
**Category:** broken_baseline  
**Difficulty:** medium  
**Correct position:** mixed

A large e-commerce marketplace is deciding whether to replace its search ranking model for product search. The current production stack is a gradient-boosted reranker using handcrafted lexical and behavioral features. The proposed replacement is a transformer-based ranker that consumes the query text, product title, and catalog attributes directly. In the project review, the search team reports that the new model improves offline NDCG@10 by 6.3% and improves add-to-cart rate on the top ten results by 4.1% in replay evaluation, and they describe the result as evidence that the ranking model is better.

The appendix shows that the baseline number was copied from the search dashboard used in early October, when the company tracked desktop web searches and excluded brand-name queries because those were treated as navigational. The challenger was evaluated on the most recent four weeks of traffic after a mobile-app redesign placed the search box on the home screen, which increased mobile traffic and changed the mix toward more brand and long-tail queries. The challenger replay also used a newer query-normalization service that expands abbreviations and unit expressions before retrieval and feature generation, while the baseline replay reused the older raw logged query text because the previous normalization output was not stored. The team notes that catalog size increased for the holiday assortment between the two periods, but each replay used the items that were actually active at the time of each query.

Supporters of the launch argue that the improvement is probably real because a quick check on the 1,000 most frequent non-brand queries still showed a smaller positive gain, and the retrieval stack and business rules were otherwise unchanged. Critics argue the benchmark is not apples to apples. Assess the benchmark design and what test would settle the disagreement.

---

## metric_mismatch_052
**Category:** metric_mismatch  
**Difficulty:** medium  
**Correct position:** mixed

An online learning platform is reviewing a new recommendation model that chooses each student's next algebra activity. The current system mostly recommends the next lesson in a fixed curriculum path. The proposed model uses recent mistakes, pace, and confidence estimates to choose among practice sets, short videos, and review checks. In the rollout memo, the team says the model improves learning outcomes because students exposed to it completed 14% more recommended activities, spent 11% more minutes practicing, and were 7% more likely to keep a seven-day learning streak during a four-week experiment.

The details section explains that the new policy often recommends shorter skill checks and recap videos when the model predicts confusion, so the average recommended activity length fell from about 11 minutes to 7 minutes. The platform does have end-of-unit mastery quizzes and a weekly mixed-topic review meant to test cumulative understanding, but only 38% of active students reached a mastery quiz within the experiment window, so the headline deck omitted those outcomes. On that subset, mastery-quiz scores were about 1.8 percentage points higher under the new model, but the interval was wide enough that the team described it as directional rather than conclusive. The report also does not include any delayed retention measure, such as whether students still solved similar problems one or two weeks later without hints.

Product managers argue that more practice and higher persistence are reasonable proxies for learning, especially because the early quiz readout was at least not negative. Critics respond that the team promised better learning outcomes, not just more clicks or more short tasks. Evaluate whether the current evidence supports the claim and what study would settle it.

---

## hidden_confounding_053
**Category:** hidden_confounding  
**Difficulty:** medium  
**Correct position:** mixed

A manufacturing group is reviewing a machine-learning system that predicts which printed circuit boards should receive an extra X-ray inspection before final electrical test. The existing process inspects boards according to fixed rules based on product family and occasional operator escalation. The proposed model uses machine telemetry, solder-paste inspection images, and placement history to prioritize boards that are most likely to contain hidden solder defects. In the project summary, the team reports that final-test defect rate on Surface-Mount Line 3 fell from 2.4% in the six weeks before launch to 1.5% in the six weeks after launch, and they present that drop as evidence that the model reduced defects.

The operations log notes two other changes that happened around the same time. First, maintenance crews completed a scheduled stencil replacement and reflow-oven recalibration on Line 3 three days before the model went live. Second, during the launch window the plant temporarily shifted a complex controller-board family to another site, so Line 3 produced a higher share of simpler two-layer boards than in the earlier six-week period. The team says inspector headcount, acceptance thresholds, and the budget for extra X-ray checks stayed the same. They also report that boards flagged by the model were materially more likely to fail downstream inspection than boards selected by the old rules, which supporters cite as evidence that the model is adding value even if the overall defect drop has other contributors. The vision backbone had been pretrained on archived plant images from the prior year.

Assess whether the reported defect-rate improvement is already convincing and what comparison would resolve the dispute.

---

## real_world_framing_054
**Category:** real_world_framing  
**Difficulty:** medium  
**Correct position:** mixed

A parcel-delivery company is evaluating a route-optimization model for urban same-day deliveries. Dispatchers currently assign stops to drivers by territory and use a heuristic route planner, with manual edits for traffic, building access, and late-arriving orders. The proposed model jointly chooses stop order and route adjustments within each driver's territory. In a retrospective review across 14 depots, the data science team reports that replaying last quarter's delivery manifests through the optimizer would have reduced driven miles by 9% while keeping the historical on-time-delivery rate essentially unchanged. Operations leaders are treating the result as evidence that the system is ready for deployment.

The simulation assumes the optimizer receives the full list of stops for the day at 8:00 a.m. and then computes one recommended route plan per driver. In actual operations, roughly 22% of same-day orders are added after 8:00 a.m., and dispatchers insert them throughout the day. The replay also scores the optimizer using the actual service times and travel times observed on the historical routes, including apartment access delays, parking luck, and temporary road conditions that would not be known perfectly at dispatch time. Drivers in production are allowed to ignore suggested resequencing when building access rules or customer requests conflict with the app. Supporters argue that the benchmark is still informative because about 70% of daily volume is known by 8:00 a.m., driver territories stay fixed, and the optimizer looked especially strong on dense downtown routes where stop order matters most.

Assess whether the retrospective evidence already supports deployment readiness and what test would fairly settle the disagreement.

---
