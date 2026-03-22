"""
map_to_canonical.py
────────────────────
Translates raw analyzer output into the canonical schema.
Uses mapping-matrix.yaml as the translation ruleset.
"""
import yaml, logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)
MAPPING_MATRIX_PATH = Path(__file__).parent.parent.parent / "canonical" / "mapping-matrix.yaml"


def apply_transform(value: Any, transform: str) -> Any:
    if transform == "as_is" or not transform:
        return value

    if transform == "parse_party_client":
        for segment in str(value).split("||"):
            if "ROLE::client" in segment:
                for part in segment.split("|"):
                    if part.strip().startswith("PARTY::"):
                        return part.strip().replace("PARTY::", "").strip()
        return value

    if transform == "parse_party_vendor":
        for segment in str(value).split("||"):
            if "ROLE::vendor" in segment:
                for part in segment.split("|"):
                    if part.strip().startswith("PARTY::"):
                        return part.strip().replace("PARTY::", "").strip()
        return value

    if transform == "parse_deliverables_composite":
        if isinstance(value, str):
            items = []
            for line in value.split("\n"):
                if line.strip().startswith("DELIV::"):
                    deliv = line.strip().replace("DELIV::", "").strip()
                    if deliv and deliv.lower() != "null":
                        items.append(deliv)
            return items if items else value
        return value

    if transform == "parse_signers":
        if not value or not str(value).strip():
            return []
        signers = []
        for block in str(value).split("\n\n"):
            signer = {}
            for line in block.strip().split("\n"):
                line = line.strip()
                if line.startswith("SIGNER::"):
                    signer["name"] = line.replace("SIGNER::", "").strip()
                elif line.startswith("PARTY::"):
                    signer["party"] = line.replace("PARTY::", "").strip()
                elif line.startswith("TITLE::"):
                    signer["title"] = line.replace("TITLE::", "").strip()
                elif line.startswith("DATE::"):
                    signer["date"] = line.replace("DATE::", "").strip()
            if signer.get("name"):
                signers.append(signer)
        return signers

    log.warning(f"[Mapper] Unknown transform '{transform}' — using as_is")
    return value


def load_mapping_matrix() -> dict:
    with open(MAPPING_MATRIX_PATH, "r") as f:
        return yaml.safe_load(f)


def set_nested(target: dict, dotted_key: str, value: Any) -> None:
    keys = dotted_key.split(".")
    cursor = target
    for key in keys[:-1]:
        cursor = cursor.setdefault(key, {})
    cursor[keys[-1]] = value


def get_nested(source: dict, dotted_key: str, default=None) -> Any:
    keys = dotted_key.split(".")
    cursor = source
    for key in keys:
        if not isinstance(cursor, dict) or key not in cursor:
            return default
        cursor = cursor[key]
    return cursor


def map_to_canonical(raw_result: dict) -> dict:
    matrix = load_mapping_matrix()
    source = raw_result.get("_source") or raw_result.get("_analyzerUsed", "unknown")
    mappings = matrix.get("mappings", [])

    if not isinstance(mappings, list):
        log.warning("[Mapper] Unexpected mapping format — expected list")
        return {"_raw": raw_result, "_source": source, "_mapped": False}

    canonical = {
        "_source": source,
        "_mapped": True,
        "_confidence": raw_result.get("_confidence", 0.0),
        "_rule_precedence": {},
    }

    for rule in mappings:
        if rule.get("sourceAnalyzer") != source:
            continue
        source_field   = rule.get("sourceField")
        canonical_path = rule.get("canonicalPath")
        transform      = rule.get("transform", "as_is")
        precedence     = rule.get("precedence", 0)

        if not source_field or not canonical_path:
            continue
        value = raw_result.get(source_field)
        if value is None:
            continue

        value = apply_transform(value, transform)
        set_nested(canonical, canonical_path, value)
        canonical["_rule_precedence"][canonical_path] = precedence
        log.debug(f"[Mapper] {source_field} → {canonical_path}")

    return canonical


def build_empty_canonical() -> dict:
    return {
        "parties": {
            "client":  {"name": "", "signatories": []},
            "vendor":  {"name": "", "signatories": []},
            "ndaType": "",
        },
        "dates": {
            "effectiveDate":  "",
            "expirationDate": "",
            "executionDate":  "",
        },
        "scope": {
            "description":   "",
            "deliverables":  [],
            "outOfScope":    [],
            "milestones":    [],
            "sowReferenceId": "",
            "locationAndTravel": "",
        },
        "confidentiality": {
            "term":        "",
            "obligations": [],
            "exceptions":  [],
        },
        "commercials": {
            "totalValue":   "",
            "paymentTerms": "",
            "currency":     "",
            "pricingModel": "",
            "taxes":        "",
            "expenses":     "",
            "invoicing":    "",
        },
        "security": {
            "requirements":          "",
            "dataResidency":         "",
            "complianceStandards":   "",
            "personalDataProcessing":"",
            "privacyRequirements":   "",
        },
        "legal": {
            "governingLaw":            "",
            "jurisdiction":            "",
            "disputeResolution":       "",
            "liabilityCap":            "",
            "ipOwnership":             "",
            "warranties":              "",
            "indemnities":             "",
            "terminationForConvenience":"",
            "terminationForCause":     "",
            "injunctiveRelief":        "",
            "licenseGrants":           "",
            "thirdPartySoftware":      "",
            "msaReference":            "",
            "serviceLevels":           "",
        },
        "projectGovernance": {
            "acceptanceCriteria":  "",
            "acceptanceTimeline":  "",
            "changeControl":       "",
            "issueEscalation":     "",
            "governanceModel":     "",
            "keyPersonnel":        "",
            "dependencies":        "",
            "assumptions":         "",
            "constraints":         "",
        },
        "risks":        [],
        "missingFields":[],
        "conflicts":    [],
        "provenance":   [],
        "review": {
            "status":       "needs_review",
            "reviewReason": [],
            "reviewedBy":   "",
            "reviewedAt":   "",
        },
    }
