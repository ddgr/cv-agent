from scripts.run_scenarios import SCENARIOS, evaluate


def test_evaluate_reports_missing_and_forbidden_text():
    assert evaluate("Ese dato NO está en el CV.", ["no está en el CV"], []) == []
    assert evaluate("def ordenar(x): ...", [], ["def "]) == ["no debía incluir «def »"]
    assert evaluate("Hola", ["LinkedIn"], []) == ["falta «LinkedIn»"]


def test_every_scenario_has_a_check():
    assert all(must or must_not for *_, must, must_not in SCENARIOS)
