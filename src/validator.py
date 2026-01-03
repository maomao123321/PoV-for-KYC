from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

from .schemas import DocumentType, ExtractionPayload


PASSPORT_NUMBER_PATTERN = re.compile(r"^[A-Z0-9]{6,9}$")
DRIVER_LICENSE_PATTERN = re.compile(r"^[A-Z0-9\-]{5,20}$")


@dataclass
class ValidationOutcome:
    status: str
    ucs: float
    logic_score: float
    issues: List[str]
    flagged_fields: List[str]


class DocumentValidator:
    def __init__(self) -> None:
        self.success_threshold = 0.9
        self.review_threshold = 0.7

    def assess(
        self, extraction: ExtractionPayload, image_quality: float
    ) -> ValidationOutcome:
        logic_score, issues, flagged = self._logic_checks(extraction)
        ai_prob = max(0.0, min(extraction.ai_confidence, 1.0))
        image_score = max(0.0, min(image_quality / 100.0, 1.0))

        ucs = (ai_prob * 0.4) + (image_score * 0.2) + (logic_score * 0.4)
        status = self._status_from_score(ucs)
        return ValidationOutcome(
            status=status, ucs=ucs, logic_score=logic_score, issues=issues, flagged_fields=flagged
        )

    def _logic_checks(self, extraction: ExtractionPayload) -> Tuple[float, List[str], List[str]]:
        issues: List[str] = []
        flagged: List[str] = []
        penalties = 0.0
        max_penalty = 1.0

        doc = self._select_doc(extraction)
        if doc is None:
            return 0.0, ["Missing document payload"], ["document_type"]

        # Date consistency
        if doc.expiry_date and doc.issue_date:
            if doc.expiry_date <= doc.issue_date:
                issues.append("Expiry must be later than issue date.")
                flagged.append("expiry_date")
                penalties += 0.2

        # Birth date sanity
        if doc.birth_date:
            if doc.expiry_date and doc.birth_date > doc.expiry_date:
                issues.append("Birth date after expiry.")
                flagged.append("birth_date")
                penalties += 0.2

        # Document number pattern
        if doc.document_number:
            if extraction.document_type == DocumentType.passport:
                if not PASSPORT_NUMBER_PATTERN.match(doc.document_number):
                    issues.append("Passport number pattern mismatch.")
                    flagged.append("document_number")
                    penalties += 0.2
            elif extraction.document_type == DocumentType.drivers_license:
                if not DRIVER_LICENSE_PATTERN.match(doc.document_number):
                    issues.append("Driver license number pattern mismatch.")
                    flagged.append("document_number")
                    penalties += 0.2

        # MRZ cross-validation for passports
        if extraction.document_type == DocumentType.passport and doc.mrz_raw:
            mrz_issues = self._validate_mrz_cross_check(doc.mrz_raw, doc)
            if mrz_issues:
                issues.extend(mrz_issues)
                flagged.append("mrz_raw")
                penalties += 0.3

        penalties = min(penalties, max_penalty)
        logic_score = max(0.0, 1.0 - penalties)
        return logic_score, issues, flagged

    def _validate_mrz_cross_check(self, mrz_raw: str, doc) -> List[str]:
        """Parse MRZ and cross-check with visual zone fields."""
        issues = []
        lines = mrz_raw.strip().split("\n")
        if len(lines) < 2:
            issues.append("MRZ incomplete (expected 2+ lines)")
            return issues
        
        # Line 2: document number (pos 0-9), check digit, nationality, birth date, check, sex, expiry, check
        if len(lines) >= 2:
            line2 = lines[1].replace(" ", "")
            if len(line2) >= 44:
                mrz_doc_num = line2[0:9].replace("<", "").strip()
                mrz_birth = line2[13:19]
                mrz_expiry = line2[21:27]
                
                # Cross-check document number
                if doc.document_number and mrz_doc_num:
                    if not doc.document_number.startswith(mrz_doc_num[:6]):
                        issues.append(f"MRZ doc# mismatch: visual={doc.document_number}, MRZ={mrz_doc_num}")
                
                # Cross-check birth date (YYMMDD)
                if doc.birth_date:
                    visual_birth = doc.birth_date.strftime("%y%m%d")
                    if mrz_birth != visual_birth:
                        issues.append(f"MRZ birth mismatch: visual={visual_birth}, MRZ={mrz_birth}")
                
                # Cross-check expiry date
                if doc.expiry_date:
                    visual_expiry = doc.expiry_date.strftime("%y%m%d")
                    if mrz_expiry != visual_expiry:
                        issues.append(f"MRZ expiry mismatch: visual={visual_expiry}, MRZ={mrz_expiry}")
        
        return issues

    @staticmethod
    def _mrz_char_value(char: str) -> int:
        if char.isdigit():
            return int(char)
        if char == "<":
            return 0
        return ord(char) - 55  # 'A' -> 10

    @staticmethod
    def _select_doc(extraction: ExtractionPayload):
        if extraction.document_type == DocumentType.passport:
            return extraction.passport
        if extraction.document_type == DocumentType.drivers_license:
            return extraction.drivers_license
        return extraction.passport or extraction.drivers_license

    def _status_from_score(self, ucs: float) -> str:
        if ucs >= self.success_threshold:
            return "SUCCESS"
        if ucs >= self.review_threshold:
            return "MANUAL_REVIEW"
        return "RETRY_UPLOAD"

