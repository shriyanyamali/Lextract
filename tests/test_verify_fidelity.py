import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import verify_fidelity as vf


def test_normalise_drops_everything_but_letters():
    assert vf.normalise("Sub -segmented (21) by product,12 categories") == "subsegmentedbyproductcategories"


def test_coverage_verbatim_and_absent():
    source = vf.normalise("(13) In Avnet/Magirus,8 the Commission has defined a market for the wholesale "
                          "distribution of IT products, but left open the question whether the market should be "
                          "further sub -segmented (i) by product categories.")
    record = ("In Avnet/Magirus, the Commission has defined a market for the wholesale distribution of IT "
              "products, but left open the question whether the market should be further sub-segmented (i) by "
              "product categories.")
    cov, missing = vf.coverage(record, source)
    assert cov == 1.0 and missing == 0 and vf.band(cov) == "verbatim"
    cov, _ = vf.coverage("The Commission has in previous decisions distinguished between retail and wholesale "
                         "telecommunications markets, which are national in scope.", source)
    assert vf.band(cov) == "absent"


def test_local_batches_are_used_and_report_written(tmp_path, monkeypatch, capsys):
    batches = tmp_path / "extracted_batches"
    batches.mkdir()
    link = "https://ec.europa.eu/competition/mergers/cases/decisions/m0000_1_3.pdf"
    (batches / "pdf_texts_79_batch_1.txt").write_text(
        f"Case Number: M.0000\nYear: 2020\nPolicy Area: Merger\nLink: {link}\n\n"
        "4. MARKET DEFINITION\n(10) The Commission considers that the market for widgets is national in scope.\n",
        encoding="utf-8")
    output = tmp_path / "output.json"
    output.write_text(json.dumps([
        {"case_number": "M.0000", "year": "2020", "policy_area": "Merger", "link": link,
         "topic": "Widgets", "text": "The Commission considers that the market for widgets is national in scope."},
        {"case_number": "M.0000", "year": "2020", "policy_area": "Merger", "link": link,
         "topic": "Gadgets", "text": "The Commission has previously found that gadgets form a separate product market."},
    ]), encoding="utf-8")
    report = tmp_path / "report.json"
    clean = tmp_path / "clean.json"
    monkeypatch.setattr(sys, "argv", ["verify_fidelity.py", "--input", str(output), "--batches", str(batches),
                                      "--no-download", "--output", str(report), "--drop-absent", str(clean)])
    vf.main()
    rep = json.loads(report.read_text(encoding="utf-8"))
    assert rep["records_checked"] == 2
    assert rep["bands"] == {"verbatim": 1, "absent": 1}
    assert len(json.loads(clean.read_text(encoding="utf-8"))) == 1
    assert "SOURCE-FIDELITY REPORT" in capsys.readouterr().out
