"""
test_golden.py
──────────────
Golden test suite for the Contract Intelligence Pipeline.

Run fast tests only (no Azure, use before every commit):
    pytest tests/test_golden.py -v -m "not integration"

Run unit tests only:
    pytest tests/test_golden.py -v -m unit

Run PDF tests:
    pytest tests/test_golden.py -v -m pdf

Run integration tests (needs .env with Azure keys):
    pytest tests/test_golden.py -v -m integration

Regenerate golden snapshot files after intentional schema changes:
    pytest tests/test_golden.py -v -m integration --generate-golden
"""

import json
import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

log = logging.getLogger(__name__)


# =============================================================================
# SECTION 1: CANONICAL FIXTURES
# All field paths match build_empty_canonical() in map_to_canonical.py:
#   parties.client.name / parties.vendor.name / parties.ndaType
#   dates.effectiveDate / dates.expirationDate / dates.executionDate
#   scope.description / scope.deliverables / scope.milestones / scope.outOfScope
#   confidentiality.term / confidentiality.obligations / confidentiality.exceptions
#   commercials.totalValue / commercials.currency / commercials.pricingModel / commercials.paymentTerms
#   security.requirements / security.complianceStandards
#   legal.governingLaw / legal.jurisdiction / legal.disputeResolution / legal.liabilityCap
#   legal.ipOwnership / legal.indemnities / legal.licenseGrants
#   projectGovernance.projectTimeline / projectGovernance.governanceModel
#   projectGovernance.dependencies / projectGovernance.assumptions
# =============================================================================

def _empty_canonical() -> dict:
    from orchestration.functions.map_to_canonical import build_empty_canonical
    return build_empty_canonical()


def _nda_candidate() -> dict:
    """Realistic NDA candidate as returned by map_to_canonical() after a CU NDA run."""
    from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
    c = build_empty_canonical()
    c["_source"] = "nda"
    c["_confidence"] = 0.89
    c["_rule_precedence"] = {}
    c["_mapped"] = True
    set_nested(c, "parties.client.name", "Acme Corporation Ltd")
    set_nested(c, "parties.vendor.name", "TechVendor Solutions Ltd")
    set_nested(c, "parties.ndaType", "mutual")
    set_nested(c, "dates.effectiveDate", "2026-01-01")
    set_nested(c, "dates.expirationDate", "2028-01-01")
    set_nested(c, "confidentiality.term", "2 years")
    set_nested(c, "confidentiality.obligations", ["Keep confidential", "Limit to need-to-know"])
    set_nested(c, "confidentiality.exceptions", ["Public domain", "Independently developed"])
    set_nested(c, "legal.governingLaw", "England and Wales")
    set_nested(c, "legal.jurisdiction", "Courts of England and Wales")
    set_nested(c, "legal.disputeResolution", "Litigation")
    set_nested(c, "legal.liabilityCap", "Neither party liable for indirect losses")
    return c


def _sow_candidate() -> dict:
    """Realistic SOW candidate as returned by map_to_canonical() after a CU SOW run."""
    from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
    c = build_empty_canonical()
    c["_source"] = "sow"
    c["_confidence"] = 0.91
    c["_rule_precedence"] = {}
    c["_mapped"] = True
    set_nested(c, "parties.client.name", "GlobalBank PLC")
    set_nested(c, "parties.vendor.name", "DataSystems UK Ltd")
    set_nested(c, "dates.effectiveDate", "2026-04-01")
    set_nested(c, "dates.expirationDate", "2026-09-30")
    set_nested(c, "scope.description", "Migration of legacy core banking data to cloud-native platform.")
    set_nested(c, "scope.deliverables", ["Migrated data", "Reconciliation report", "Data quality dashboard"])
    set_nested(c, "scope.milestones", [
        {"milestone": "Discovery complete", "date": "2026-04-30", "notes": ""},
        {"milestone": "Pilot migration", "date": "2026-05-31", "notes": ""},
        {"milestone": "Full migration", "date": "2026-08-31", "notes": ""},
    ])
    set_nested(c, "scope.outOfScope", ["Business banking division", "International subsidiaries"])
    set_nested(c, "commercials.totalValue", "120000")
    set_nested(c, "commercials.currency", "GBP")
    set_nested(c, "commercials.pricingModel", "Fixed fee")
    set_nested(c, "commercials.paymentTerms", "30% on execution; 40% at pilot; 30% on sign-off")
    set_nested(c, "legal.governingLaw", "England and Wales")
    set_nested(c, "legal.ipOwnership", "Client owns all deliverables")
    set_nested(c, "projectGovernance.projectTimeline", "April 2026 – September 2026")
    set_nested(c, "projectGovernance.governanceModel", "Weekly steering committee")
    return c


def _nda_pdf_canonical() -> dict:
    """Merged canonical ready for NDA PDF generation."""
    c = _empty_canonical()
    c["parties"]["client"]["name"] = "Acme Corporation Ltd"
    c["parties"]["vendor"]["name"] = "TechVendor Solutions Ltd"
    c["parties"]["ndaType"] = "mutual"
    c["dates"]["effectiveDate"] = "2026-01-01"
    c["dates"]["expirationDate"] = "2028-01-01"
    c["confidentiality"]["term"] = "2 years"
    c["confidentiality"]["obligations"] = ["Keep confidential", "Limit to need-to-know"]
    c["confidentiality"]["exceptions"] = ["Public domain", "Independently developed"]
    c["legal"]["governingLaw"] = "England and Wales"
    c["legal"]["jurisdiction"] = "Courts of England and Wales"
    c["legal"]["disputeResolution"] = "Litigation"
    c["legal"]["liabilityCap"] = "Neither party liable for indirect losses"
    c["review"]["status"] = "auto"
    c["provenance"] = [{
        "canonicalPath": "legal.governingLaw",
        "value": "England and Wales",
        "sourceDocumentId": "",
        "sourceField": "nda",
        "sourceFamily": "cu_analyzer",
        "confidence": 0.89,
    }]
    return c


def _sow_pdf_canonical() -> dict:
    """Merged canonical ready for SOW PDF generation."""
    c = _empty_canonical()
    c["parties"]["client"]["name"] = "GlobalBank PLC"
    c["parties"]["vendor"]["name"] = "DataSystems UK Ltd"
    c["dates"]["effectiveDate"] = "2026-04-01"
    c["dates"]["expirationDate"] = "2026-09-30"
    c["scope"]["description"] = "Migration of legacy core banking data to cloud-native platform."
    c["scope"]["deliverables"] = ["Migrated data", "Reconciliation report", "Data quality dashboard"]
    c["scope"]["milestones"] = [
        {"milestone": "Discovery complete", "date": "2026-04-30", "notes": ""},
        {"milestone": "Pilot migration", "date": "2026-05-31", "notes": ""},
        {"milestone": "Full migration", "date": "2026-08-31", "notes": ""},
    ]
    c["scope"]["outOfScope"] = ["Business banking division", "International subsidiaries"]
    c["commercials"]["totalValue"] = "120000"
    c["commercials"]["currency"] = "GBP"
    c["commercials"]["pricingModel"] = "Fixed fee"
    c["commercials"]["paymentTerms"] = "30% on execution; 40% at pilot; 30% on sign-off"
    c["legal"]["governingLaw"] = "England and Wales"
    c["legal"]["ipOwnership"] = "Client owns all deliverables"
    c["projectGovernance"]["projectTimeline"] = "April 2026 – September 2026"
    c["projectGovernance"]["governanceModel"] = "Weekly steering committee"
    c["review"]["status"] = "auto"
    return c


# =============================================================================
# SECTION 2: MERGE ENGINE UNIT TESTS
# =============================================================================

@pytest.mark.unit
class TestMergeEngine:

    def test_single_candidate_passes_through(self):
        from orchestration.functions.merge_engine import merge_results
        result = merge_results([_nda_candidate()])
        assert result["legal"]["governingLaw"] == "England and Wales"
        assert result["dates"]["effectiveDate"] == "2026-01-01"
        assert result["parties"]["client"]["name"] == "Acme Corporation Ltd"
        assert result["conflicts"] == []

    def test_two_agreeing_sources_no_conflict(self):
        from orchestration.functions.merge_engine import merge_results
        from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
        c1 = build_empty_canonical()
        c1["_source"] = "nda"
        c1["_confidence"] = 0.90
        set_nested(c1, "legal.governingLaw", "England and Wales")
        c2 = build_empty_canonical()
        c2["_source"] = "llm_audio"
        c2["_confidence"] = 0.75
        set_nested(c2, "legal.governingLaw", "England and Wales")
        result = merge_results([c1, c2])
        assert result["legal"]["governingLaw"] == "England and Wales"
        assert result["conflicts"] == []

    def test_conflict_cu_beats_audio(self):
        from orchestration.functions.merge_engine import merge_results
        from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
        cu = build_empty_canonical()
        cu["_source"] = "nda"
        cu["_confidence"] = 0.90
        set_nested(cu, "legal.governingLaw", "England and Wales")
        audio = build_empty_canonical()
        audio["_source"] = "llm_audio"
        audio["_confidence"] = 0.75
        set_nested(audio, "legal.governingLaw", "Scotland")
        result = merge_results([cu, audio])
        assert result["legal"]["governingLaw"] == "England and Wales"
        assert any(c["field"] == "legal.governingLaw" for c in result["conflicts"])

    def test_conflict_alternatives_recorded(self):
        from orchestration.functions.merge_engine import merge_results
        from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
        cu = build_empty_canonical()
        cu["_source"] = "nda"
        cu["_confidence"] = 0.90
        set_nested(cu, "parties.ndaType", "mutual")
        audio = build_empty_canonical()
        audio["_source"] = "llm_audio"
        audio["_confidence"] = 0.72
        set_nested(audio, "parties.ndaType", "unilateral")
        result = merge_results([cu, audio])
        assert result["parties"]["ndaType"] == "mutual"
        conflict = next(c for c in result["conflicts"] if c["field"] == "parties.ndaType")
        assert any("unilateral" in str(a["value"]) for a in conflict["alternatives"])

    def test_audio_only_field_preserved(self):
        from orchestration.functions.merge_engine import merge_results
        from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
        cu = build_empty_canonical()
        cu["_source"] = "nda"
        cu["_confidence"] = 0.90
        set_nested(cu, "legal.governingLaw", "England and Wales")
        # CU does NOT set confidentiality.term
        audio = build_empty_canonical()
        audio["_source"] = "llm_audio"
        audio["_confidence"] = 0.75
        set_nested(audio, "legal.governingLaw", "England and Wales")
        set_nested(audio, "confidentiality.term", "2 years")  # audio-only
        result = merge_results([cu, audio])
        assert result["confidentiality"]["term"] == "2 years"
        assert result["conflicts"] == []

    def test_list_field_not_wiped_by_empty_source(self):
        from orchestration.functions.merge_engine import merge_results
        from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
        cu = build_empty_canonical()
        cu["_source"] = "sow"
        cu["_confidence"] = 0.91
        set_nested(cu, "scope.deliverables", ["Migrated data", "Reconciliation report"])
        audio = build_empty_canonical()
        audio["_source"] = "llm_audio"
        audio["_confidence"] = 0.70
        # audio has no deliverables
        result = merge_results([cu, audio])
        assert result["scope"]["deliverables"] == ["Migrated data", "Reconciliation report"]

    def test_missing_fields_populated(self):
        from orchestration.functions.merge_engine import merge_results
        from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
        c = build_empty_canonical()
        c["_source"] = "nda"
        c["_confidence"] = 0.88
        set_nested(c, "legal.governingLaw", "England and Wales")
        result = merge_results([c])
        assert "dates.effectiveDate" in result["missingFields"]

    def test_review_auto_when_all_critical_fields_present(self):
        from orchestration.functions.merge_engine import merge_results
        from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
        c = build_empty_canonical()
        c["_source"] = "nda"
        c["_confidence"] = 0.92
        set_nested(c, "parties.client.name", "Acme Ltd")
        set_nested(c, "parties.vendor.name", "TechVendor Ltd")
        set_nested(c, "dates.effectiveDate", "2026-01-01")
        result = merge_results([c])
        assert result["review"]["status"] == "auto"
        assert result["review"]["reviewReason"] == []

    def test_review_needs_review_on_conflict(self):
        from orchestration.functions.merge_engine import merge_results
        from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
        c1 = build_empty_canonical()
        c1["_source"] = "nda"
        c1["_confidence"] = 0.90
        set_nested(c1, "parties.ndaType", "mutual")
        c2 = build_empty_canonical()
        c2["_source"] = "llm_audio"
        c2["_confidence"] = 0.72
        set_nested(c2, "parties.ndaType", "unilateral")
        result = merge_results([c1, c2])
        assert result["review"]["status"] == "needs_review"
        assert len(result["review"]["reviewReason"]) > 0

    def test_review_needs_review_on_critical_missing(self):
        from orchestration.functions.merge_engine import merge_results
        from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
        c = build_empty_canonical()
        c["_source"] = "nda"
        c["_confidence"] = 0.85
        set_nested(c, "legal.governingLaw", "England and Wales")
        # parties and dates intentionally empty
        result = merge_results([c])
        assert result["review"]["status"] == "needs_review"

    def test_empty_candidates_returns_valid_structure(self):
        from orchestration.functions.merge_engine import merge_results
        result = merge_results([])
        for key in ("parties", "dates", "scope", "confidentiality", "commercials",
                    "legal", "projectGovernance", "missingFields", "conflicts",
                    "provenance", "review"):
            assert key in result
        assert len(result["missingFields"]) > 0

    def test_provenance_recorded_for_resolved_fields(self):
        from orchestration.functions.merge_engine import merge_results
        from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested
        c = build_empty_canonical()
        c["_source"] = "nda"
        c["_confidence"] = 0.88
        set_nested(c, "legal.governingLaw", "England and Wales")
        set_nested(c, "dates.effectiveDate", "2026-01-01")
        result = merge_results([c])
        paths = {p["canonicalPath"] for p in result["provenance"]}
        assert "legal.governingLaw" in paths
        assert "dates.effectiveDate" in paths

    def test_review_fields_not_in_missing_fields(self):
        from orchestration.functions.merge_engine import merge_results
        result = merge_results([])
        review_leaks = [f for f in result["missingFields"] if f.startswith("review.")]
        assert review_leaks == []


# =============================================================================
# SECTION 3: MAP_TO_CANONICAL UNIT TESTS
# =============================================================================

@pytest.mark.unit
class TestMapToCanonical:

    def test_set_nested_two_levels(self):
        from orchestration.functions.map_to_canonical import set_nested
        d = {}
        set_nested(d, "legal.governingLaw", "England and Wales")
        assert d["legal"]["governingLaw"] == "England and Wales"

    def test_set_nested_three_levels(self):
        from orchestration.functions.map_to_canonical import set_nested
        d = {}
        set_nested(d, "parties.client.name", "Acme Ltd")
        assert d["parties"]["client"]["name"] == "Acme Ltd"

    def test_get_nested_hit(self):
        from orchestration.functions.map_to_canonical import get_nested
        d = {"legal": {"governingLaw": "England and Wales"}}
        assert get_nested(d, "legal.governingLaw") == "England and Wales"

    def test_get_nested_miss_returns_none(self):
        from orchestration.functions.map_to_canonical import get_nested
        assert get_nested({}, "legal.governingLaw") is None

    def test_get_nested_miss_returns_default(self):
        from orchestration.functions.map_to_canonical import get_nested
        assert get_nested({}, "legal.governingLaw", "fallback") == "fallback"

    def test_build_empty_canonical_top_level_keys(self):
        from orchestration.functions.map_to_canonical import build_empty_canonical
        result = build_empty_canonical()
        for key in ("parties", "dates", "scope", "confidentiality", "commercials",
                    "security", "legal", "projectGovernance", "risks",
                    "missingFields", "conflicts", "provenance", "review"):
            assert key in result

    def test_build_empty_canonical_parties_structure(self):
        from orchestration.functions.map_to_canonical import build_empty_canonical
        r = build_empty_canonical()
        assert "client" in r["parties"] and "vendor" in r["parties"]
        assert "name" in r["parties"]["client"]
        assert "name" in r["parties"]["vendor"]

    def test_apply_transform_as_is(self):
        from orchestration.functions.map_to_canonical import apply_transform
        assert apply_transform("hello", "as_is") == "hello"
        assert apply_transform("hello", "") == "hello"
        assert apply_transform("hello", None) == "hello"

    def test_apply_transform_parse_party_client(self):
        from orchestration.functions.map_to_canonical import apply_transform
        value = "PARTY::Acme Ltd|ROLE::client||PARTY::TechVendor|ROLE::vendor"
        assert apply_transform(value, "parse_party_client") == "Acme Ltd"

    def test_apply_transform_parse_party_vendor(self):
        from orchestration.functions.map_to_canonical import apply_transform
        value = "PARTY::Acme Ltd|ROLE::client||PARTY::TechVendor|ROLE::vendor"
        assert apply_transform(value, "parse_party_vendor") == "TechVendor"

    def test_apply_transform_parse_deliverables(self):
        from orchestration.functions.map_to_canonical import apply_transform
        value = "DELIV::Migrated data\nDELIV::Reconciliation report\nDELIV::null"
        result = apply_transform(value, "parse_deliverables_composite")
        assert isinstance(result, list)
        assert "Migrated data" in result
        assert "Reconciliation report" in result
        assert not any("null" in str(i).lower() for i in result)

    def test_apply_transform_parse_signers(self):
        from orchestration.functions.map_to_canonical import apply_transform
        value = "SIGNER::Jane Smith\nPARTY::Acme Ltd\nTITLE::CEO\nDATE::2026-01-01"
        result = apply_transform(value, "parse_signers")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "Jane Smith"
        assert result[0]["title"] == "CEO"

    def test_apply_transform_unknown_returns_value(self):
        from orchestration.functions.map_to_canonical import apply_transform
        assert apply_transform("some value", "nonexistent_transform") == "some value"


# =============================================================================
# SECTION 4: SCHEMA VALIDATOR UNIT TESTS
# =============================================================================

@pytest.mark.unit
class TestSchemaValidator:

    def test_returns_bool_and_list(self):
        from validators.schema_validator import validate_canonical_package
        r = validate_canonical_package(_empty_canonical())
        assert isinstance(r[0], bool) and isinstance(r[1], list)

    def test_empty_canonical_runs_without_exception(self):
        from validators.schema_validator import validate_canonical_package
        validate_canonical_package(_empty_canonical())  # must not raise

    def test_nda_canonical_runs_without_exception(self):
        from validators.schema_validator import validate_canonical_package
        validate_canonical_package(_nda_pdf_canonical())

    def test_sow_canonical_runs_without_exception(self):
        from validators.schema_validator import validate_canonical_package
        validate_canonical_package(_sow_pdf_canonical())

    def test_missing_schema_file_graceful(self, monkeypatch, tmp_path):
        import validators.schema_validator as sv
        monkeypatch.setattr(sv, "SCHEMA_PATH", tmp_path / "nonexistent.json")
        is_valid, errors = sv.validate_canonical_package(_empty_canonical())
        assert is_valid is True and errors == []

    def test_missing_jsonschema_graceful(self, monkeypatch):
        import builtins, importlib
        real = builtins.__import__
        def mock(name, *a, **kw):
            if name == "jsonschema":
                raise ImportError("mocked")
            return real(name, *a, **kw)
        monkeypatch.setattr(builtins, "__import__", mock)
        import validators.schema_validator as sv
        importlib.reload(sv)
        is_valid, errors = sv.validate_canonical_package(_empty_canonical())
        assert is_valid is True and errors == []


# =============================================================================
# SECTION 5: PDF GENERATION TESTS
# =============================================================================

@pytest.mark.pdf
class TestPDFGeneration:

    def test_nda_pdf_created(self, tmp_path):
        from generation.generate_contract_pdf import generate_pdf
        out = str(tmp_path / "nda.pdf")
        result = generate_pdf(_nda_pdf_canonical(), "nda", out)
        assert Path(out).exists()
        assert Path(out).stat().st_size > 1000
        assert result == str(Path(out).resolve())

    def test_sow_pdf_created(self, tmp_path):
        from generation.generate_contract_pdf import generate_pdf
        out = str(tmp_path / "sow.pdf")
        generate_pdf(_sow_pdf_canonical(), "sow", out)
        assert Path(out).exists()
        assert Path(out).stat().st_size > 1000

    def test_empty_canonical_generates_without_crash(self, tmp_path):
        from generation.generate_contract_pdf import generate_pdf
        generate_pdf(_empty_canonical(), "nda", str(tmp_path / "empty.pdf"))
        assert (tmp_path / "empty.pdf").exists()

    def test_output_dir_auto_created(self, tmp_path):
        from generation.generate_contract_pdf import generate_pdf
        out = str(tmp_path / "a" / "b" / "c" / "out.pdf")
        generate_pdf(_nda_pdf_canonical(), "nda", out)
        assert Path(out).exists()

    def test_sow_with_milestones(self, tmp_path):
        from generation.generate_contract_pdf import generate_pdf
        c = _sow_pdf_canonical()
        c["scope"]["milestones"] = [
            {"milestone": "Kickoff", "date": "2026-04-01", "notes": ""},
            {"milestone": "Phase 1", "date": "2026-06-30", "notes": "Review gate"},
            {"milestone": "Final delivery", "date": "2026-09-30", "notes": ""},
        ]
        generate_pdf(c, "sow", str(tmp_path / "sow-milestones.pdf"))
        assert (tmp_path / "sow-milestones.pdf").exists()

    def test_nda_with_conflicts_in_appendix(self, tmp_path):
        from generation.generate_contract_pdf import generate_pdf
        c = _nda_pdf_canonical()
        c["conflicts"] = [{
            "field": "legal.governingLaw",
            "chosen": "England and Wales",
            "chosenSource": "nda",
            "alternatives": [{"value": "Scotland", "source": "llm_audio"}],
        }]
        c["review"]["status"] = "needs_review"
        generate_pdf(c, "nda", str(tmp_path / "nda-conflicts.pdf"))
        assert (tmp_path / "nda-conflicts.pdf").exists()

    def test_sow_with_risk_register(self, tmp_path):
        from generation.generate_contract_pdf import generate_pdf
        c = _sow_pdf_canonical()
        c["risks"] = [
            {"text": "Timeline risk if legacy data quality is poor.",
             "category": "delivery", "sourceDocumentId": "", "confidence": 0.80},
        ]
        generate_pdf(c, "sow", str(tmp_path / "sow-risks.pdf"))
        assert (tmp_path / "sow-risks.pdf").exists()

    def test_partial_audio_canonical_generates_pdf(self, tmp_path):
        from generation.generate_contract_pdf import generate_pdf
        c = _empty_canonical()
        c["parties"]["client"]["name"] = "Acme Corp"
        c["parties"]["vendor"]["name"] = "TechVendor"
        c["dates"]["effectiveDate"] = "2026-01-01"
        c["confidentiality"]["term"] = "2 years"
        c["legal"]["governingLaw"] = "England and Wales"
        c["review"]["status"] = "needs_review"
        generate_pdf(c, "nda", str(tmp_path / "audio-nda.pdf"))
        assert (tmp_path / "audio-nda.pdf").exists()


# =============================================================================
# SECTION 6: GOLDEN SNAPSHOT TESTS
# =============================================================================

@pytest.mark.golden
class TestGoldenSnapshots:

    GOLDEN_DIR = ROOT / "tests" / "golden-cases"
    FIXTURES_DIR = ROOT / "tests" / "fixtures"

    def _load_golden(self, name):
        p = self.GOLDEN_DIR / f"{name}.json"
        return json.load(open(p)) if p.exists() else None

    def _save_golden(self, name, data):
        self.GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        json.dump(data, open(self.GOLDEN_DIR / f"{name}.json", "w"), indent=2)

    @pytest.mark.unit
    def test_nda_merge_golden(self):
        from orchestration.functions.merge_engine import merge_results
        result = merge_results([_nda_candidate()])
        assert result["parties"]["client"]["name"] == "Acme Corporation Ltd"
        assert result["parties"]["vendor"]["name"] == "TechVendor Solutions Ltd"
        assert result["parties"]["ndaType"] == "mutual"
        assert result["dates"]["effectiveDate"] == "2026-01-01"
        assert result["confidentiality"]["term"] == "2 years"
        assert result["legal"]["governingLaw"] == "England and Wales"
        assert result["conflicts"] == []

    @pytest.mark.unit
    def test_sow_merge_golden(self):
        from orchestration.functions.merge_engine import merge_results
        result = merge_results([_sow_candidate()])
        assert result["parties"]["client"]["name"] == "GlobalBank PLC"
        assert result["scope"]["deliverables"] == [
            "Migrated data", "Reconciliation report", "Data quality dashboard"
        ]
        assert result["commercials"]["currency"] == "GBP"
        assert result["commercials"]["totalValue"] == "120000"
        assert len(result["scope"]["milestones"]) == 3
        assert result["conflicts"] == []

    @pytest.mark.unit
    def test_multi_source_nda_plus_audio_golden(self):
        """CU wins on conflict; audio-only field preserved; no false conflict on agreed field."""
        from orchestration.functions.merge_engine import merge_results
        from orchestration.functions.map_to_canonical import build_empty_canonical, set_nested

        cu = _nda_candidate()

        audio = build_empty_canonical()
        audio["_source"] = "llm_audio"
        audio["_confidence"] = 0.72
        set_nested(audio, "legal.governingLaw", "Scotland")           # CONFLICT — CU wins
        set_nested(audio, "confidentiality.term", "2 years")           # AGREES — no conflict
        set_nested(audio, "commercials.totalValue", "50000")           # audio-only field

        result = merge_results([cu, audio])

        assert result["legal"]["governingLaw"] == "England and Wales"
        assert result["commercials"]["totalValue"] == "50000"
        conflict_fields = [c["field"] for c in result["conflicts"]]
        assert "legal.governingLaw" in conflict_fields
        assert "confidentiality.term" not in conflict_fields

    @pytest.mark.integration
    def test_deal_intake_fixture_full_pipeline(self, request):
        fixture = self.FIXTURES_DIR / "deal-intake-sample-structured.pdf"
        if not fixture.exists():
            pytest.skip(f"Fixture not found: {fixture}")
        from orchestration.functions.run_pipeline import run_pipeline
        result = run_pipeline(str(fixture), contract_type="auto", upload_to_blob=False)
        assert isinstance(result, dict)
        for key in ("parties", "dates", "legal", "missingFields", "provenance", "review"):
            assert key in result
        assert result["review"]["status"] in ("auto", "needs_review", "approved")
        if request.config.getoption("--generate-golden", default=False):
            self._save_golden("deal_intake_pipeline", result)
        else:
            golden = self._load_golden("deal_intake_pipeline")
            if golden:
                from orchestration.functions.map_to_canonical import get_nested
                for path in ["legal.governingLaw", "parties.ndaType", "commercials.currency"]:
                    if get_nested(golden, path):
                        assert get_nested(result, path) == get_nested(golden, path)

    @pytest.mark.integration
    def test_sow_email_fixture_full_pipeline(self, request):
        fixture = self.FIXTURES_DIR / "sow_email.pdf"
        if not fixture.exists():
            pytest.skip(f"Fixture not found: {fixture}")
        from orchestration.functions.run_pipeline import run_pipeline
        result = run_pipeline(str(fixture), contract_type="sow", upload_to_blob=False)
        assert "scope" in result
        assert result["review"]["status"] in ("auto", "needs_review", "approved")
        if request.config.getoption("--generate-golden", default=False):
            self._save_golden("sow_email_pipeline", result)

    @pytest.mark.integration
    def test_audio_fixture_full_pipeline(self, request):
        candidates = (
            list(self.FIXTURES_DIR.glob("*.m4a")) +
            list(self.FIXTURES_DIR.glob("*.mp3")) +
            list(ROOT.glob("meeting_sow.m4a"))
        )
        if not candidates:
            pytest.skip("No audio fixture found")
        from orchestration.functions.run_pipeline import run_pipeline
        result = run_pipeline(str(candidates[0]), contract_type="auto", upload_to_blob=True)
        assert "missingFields" in result and "provenance" in result
        assert result["review"]["status"] in ("auto", "needs_review")
        if request.config.getoption("--generate-golden", default=False):
            self._save_golden("audio_pipeline", result)


# =============================================================================
# SECTION 7: PDF UTILITY UNIT TESTS
# =============================================================================

@pytest.mark.unit
class TestPDFUtilities:

    def test_clean_date_iso(self):
        from generation.generate_contract_pdf import clean_date
        assert clean_date("2026-01-01") == "2026-01-01"

    def test_clean_date_natural(self):
        from generation.generate_contract_pdf import clean_date
        r = clean_date("January 1, 2026")
        assert "Jan" in r or "January" in r

    def test_clean_date_empty_and_none(self):
        from generation.generate_contract_pdf import clean_date
        assert clean_date("") == "" and clean_date(None) == ""

    def test_clean_text_whitespace(self):
        from generation.generate_contract_pdf import clean_text
        assert clean_text("  hello   world  ") == "hello world"

    def test_clean_text_empty_and_none(self):
        from generation.generate_contract_pdf import clean_text
        assert clean_text("") == "" and clean_text(None) == ""

    def test_has_value_truthy(self):
        from generation.generate_contract_pdf import has_value
        assert has_value("hello") and has_value(["a"]) and has_value(1)

    def test_has_value_falsy(self):
        from generation.generate_contract_pdf import has_value
        assert not has_value(None)
        assert not has_value("")
        assert not has_value("   ")
        assert not has_value([])

    def test_normalise_term_with_unit(self):
        from generation.generate_contract_pdf import normalise_term
        assert "month" in normalise_term("6 months").lower()
        assert "year" in normalise_term("2 years").lower()

    def test_normalise_term_bare_small_number(self):
        from generation.generate_contract_pdf import normalise_term
        assert "year" in normalise_term("2").lower()

    def test_normalise_term_bare_large_number(self):
        from generation.generate_contract_pdf import normalise_term
        assert "month" in normalise_term("24").lower()

    def test_normalise_term_empty(self):
        from generation.generate_contract_pdf import normalise_term
        assert normalise_term("") == "" and normalise_term(None) == ""

    def test_split_list_from_list(self):
        from generation.generate_contract_pdf import split_list
        assert split_list(["a", "b"]) == ["a", "b"]

    def test_split_list_from_semicolons(self):
        from generation.generate_contract_pdf import split_list
        assert len(split_list("a; b; c")) == 3

    def test_split_list_empty(self):
        from generation.generate_contract_pdf import split_list
        assert split_list("") == [] and split_list(None) == []

    def test_parse_milestones_from_dicts(self):
        from generation.generate_contract_pdf import parse_milestones
        r = parse_milestones([{"milestone": "Kickoff", "date": "2026-04-01", "notes": ""}])
        assert r[0]["milestone"] == "Kickoff"

    def test_parse_milestones_from_text(self):
        from generation.generate_contract_pdf import parse_milestones
        r = parse_milestones("Discovery: 2026-04-30; Pilot: 2026-05-31")
        assert len(r) >= 1
        assert all("milestone" in m and "date" in m for m in r)

    def test_parse_milestones_empty(self):
        from generation.generate_contract_pdf import parse_milestones
        assert parse_milestones(None) == [] and parse_milestones([]) == []


# =============================================================================
# SECTION 8: PYTEST CONFIGURATION
# =============================================================================

def pytest_addoption(parser):
    try:
        parser.addoption(
            "--generate-golden",
            action="store_true",
            default=False,
            help="Regenerate golden output files instead of comparing",
        )
    except ValueError:
        pass


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: fast, no external dependencies")
    config.addinivalue_line("markers", "golden: snapshot tests against saved outputs")
    config.addinivalue_line("markers", "pdf: PDF generation tests, needs reportlab")
    config.addinivalue_line("markers", "integration: requires Azure credentials and network")
