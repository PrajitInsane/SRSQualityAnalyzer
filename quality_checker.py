import spacy
import re
from collections import defaultdict

class RequirementAnalyzer:

    PLACEHOLDER_REGEX = re.compile(
        r'\b(TBD|to be decided|to be determined|TBC|to be confirmed|\[placeholder\]|undecided|N\/A|blank values)\b',
        re.IGNORECASE
    )

    AMBIGUOUS_PRONOUNS = {'it', 'they', 'this', 'that', 'these', 'those'}

    def __init__(self, model="en_core_web_lg"):
        try:
            self.nlp = spacy.load(model, disable=["ner"])
        except:
            print("!!Falling back to small spaCy model (en_core_web_sm)")
            self.nlp = spacy.load("en_core_web_sm")

    def _rewrite_missing(self, line):
        return self.PLACEHOLDER_REGEX.sub("<specify required value>", line)

    def _analyze_pronouns(self, doc):
        ambiguous_flags = []
        for token in doc:
            if token.pos_ == "PRON" and token.lower_ in self.AMBIGUOUS_PRONOUNS:
                antecedents = []
                for ant_token in doc[:token.i]:
                    if ant_token.pos_ in ("NOUN", "PROPN"):
                        antecedents.append(ant_token.text)

                if len(antecedents) >= 2:
                    suggested_antecedent = antecedents[-1]
                    other_antecedents = antecedents[:-1]
                    ambiguous_flags.append({
                        'text': token.text,
                        'suggested': suggested_antecedent,
                        'potential_antecedents': other_antecedents
                    })
        return ambiguous_flags

    def _generate_single_rewrite(self, line, pronoun_text, replacement_text):
        return re.sub(rf"\b{re.escape(pronoun_text)}\b", replacement_text, line, 1)

    def get_text_report(self, text, analysis_types): # <-- Added analysis_types parameter
        lines = text.split("\n")
        marked_lines = []
        summary_report = []
        missing_info_count = 0
        ambiguous_pronoun_count = 0
        
        # Check flags for easier comparison
        check_missing = "Missing Info" in analysis_types
        check_pronouns = "Ambiguous Pronouns" in analysis_types

        for i, line in enumerate(lines, start=1):
            original_line = line.strip()
            if not original_line:
                marked_lines.append("")
                continue

            doc = self.nlp(original_line)
            issues = []
            current_line_for_marking = original_line

            # 1. Missing Info Check
            if check_missing and self.PLACEHOLDER_REGEX.search(original_line):
                missing_info_count += 1
                suggested = self._rewrite_missing(original_line)
                issues.append(
                    f" <<XXX>>  Missing Information (Type 1 Issue) — Replace placeholder.\n   @@@ Recommendation: {suggested}"
                )

            # 2. Ambiguous Pronoun Check
            pronoun_flags = []
            if check_pronouns:
                pronoun_flags = self._analyze_pronouns(doc)
            
            if pronoun_flags:
                ambiguous_pronoun_count += len(pronoun_flags)
                
                for flag in pronoun_flags:
                    pronoun = flag['text']
                    all_antecedents = [flag['suggested']] + flag['potential_antecedents']
                    rewrite_suggestions = []
                    for antecedent in all_antecedents:
                        rewritten_line = self._generate_single_rewrite(original_line, pronoun, antecedent)
                        rewrite_suggestions.append(f"   - Replace '{pronoun}' with '{antecedent}': '{rewritten_line}'")

                    antecedents_str = ", ".join(f"'{a}'" for a in all_antecedents)
                    
                    issues.append(
                        f"<<!!!>> Ambiguous Pronoun: '{pronoun}' (Type 2 Issue)\n"
                        f"   - Potential Antecedents: {antecedents_str}\n"
                        f" @@@ Suggested Rewrites to clarify the antecedent:\n"
                        + "\n".join(rewrite_suggestions)
                    )

                    current_line_for_marking = re.sub(
                        rf"\b{re.escape(pronoun)}\b", 
                        f"{pronoun} <<!!!>>",
                        current_line_for_marking, 
                        1
                    )

            if issues:
                marked_lines.append(f"[Line {i}] {current_line_for_marking}")
                summary_report.append(f"Line {i}: {line}\n" + "\n".join(issues) + "\n")
            else:
                marked_lines.append(original_line)

        summary = {
            "missing_info": missing_info_count,
            "ambiguous_pronouns": ambiguous_pronoun_count,
            "total_issues": missing_info_count + ambiguous_pronoun_count
        }

        return "\n".join(marked_lines), "\n".join(summary_report), summary