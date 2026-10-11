import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from forager.rules import evaluate
from forager.taxonomy import parse_label


def taxon(label, score, **kw):
    g, s = parse_label(label)
    return {"label": label, "species": s, "genus": g, "score": score, "family": kw.get("family"), "weed": kw.get("weed")}


def test_parse_label():
    assert parse_label("Cirsium arvense (L.) Scop.") == ("Cirsium", "Cirsium arvense")


def test_pass_on_mass():
    taxa = [taxon("Rosa canina", .3, family="Rosaceae"), taxon("Rubus idaeus", .2, family="Rosaceae"), taxon("Ficus carica", .1, family="Moraceae")]
    assert evaluate(taxa, {"family": "Rosaceae"})["verdict"] == "pass"


def test_fail_roasts_wrong_family():
    taxa = [taxon("Taraxacum officinale", .6, family="Asteraceae"), taxon("Rosa canina", .02, family="Rosaceae")]
    assert evaluate(taxa, {"family": "Rosaceae"})["verdict"] == "fail"


def test_blurry_is_unsure():
    assert evaluate([taxon("Rosa canina", .02, family="Rosaceae")], {"family": "Rosaceae"})["verdict"] == "unsure"


def test_unknown_taxon_is_unsure_not_fail():
    assert evaluate([taxon("Foo bar", .5, family=None)], {"family": "Rosaceae"})["verdict"] == "unsure"
