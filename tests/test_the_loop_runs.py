"""The problem-solving loop, run in this domain.

Every stage the engine offers either answers or declines by a name the engine
publishes -- never an exception, never silence. This is one half of a two-domain
test; `bmc-sensor-audit` carries the other, on a domain that shares no noun with
this one. The question both halves answer is about the ENGINE: did running the
loop here need anything it does not offer every domain?

Each stage is asked of the session this package's own feeder builds, with
nothing added for the test, so what passes here is what `detect` meets. The
series is thirty monthly captures -- enough for every arm of the model to answer
-- from the shipped fixture, whose numbers are invented and say so.

The model declares what each stage reads: which way a failure travels
(`hypothesize`), one lever an operator can pull and the rounds a plan may
choose between (`file_action`, `plan`), one coupling with its number withheld
(`learn`), and when a case closes (`open_case`). The coupling cannot be fitted
from a real monthly series for ten years, so on this series `learn` declines by
name, and a labelled-synthetic series of 121 captures shows the fit itself.

Every decline is read by the engine's own walker, from every list the engine
reports one under, and checked against the names it publishes. This file used
to carry its own copy of that walk, reading two of those lists; the copy in the
other domain read four. A refusal from the learn leg arrives under the one this
copy did not read, so the check would have passed over exactly the stage this
file now exercises. A decline outside the published names is one no reader could
switch on.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from arbiter_engine import api
from arbiter_engine.subenvelope import (PUBLISHED_REASONS, declined_reasons,
                                        unpublished_reasons)

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "examples" / "operating.model.yaml"
CAPTURE = ROOT / "examples" / "acme.capture.json"

#: A reporting month, the cadence the feeder assumes, and a fixed instant for
#: the stages that file something and grade it later.
MONTH = timedelta(days=30)
AT = datetime(2026, 9, 1)

#: A department the model declares a causal parent for -- two executives lead it
#: -- and that the series finds a breach on.
LED = "dept-sales"
LEADERS = {"exec-cro", "exec-vp-sales"}


def _series():
    sys.path.insert(0, str(ROOT / "battery"))
    from operating_health_audit import capture
    import make_series

    return make_series.series(capture.load(CAPTURE), 30, transition=True)


def _fresh(at=AT):
    """A session of its own, fed as of `at`, for a stage that files something."""
    from operating_health_audit import feeder

    with api.as_of(at):
        return feeder.open_session(str(MODEL), _series())


@pytest.fixture(scope="module")
def session():
    from operating_health_audit import feeder

    return feeder.open_session(str(MODEL), _series())


@pytest.fixture(scope="module")
def sensed(session):
    return api.check(session).to_dict()


class TestEveryStageAnswersOrDeclinesByName:

    def test_sense(self, sensed):
        assert sensed["findings"], "a thirty-capture series of this fixture finds nothing"
        assert unpublished_reasons(sensed) == []

    def test_model(self, session):
        described = api.model_describe(session).to_dict()
        assert described["model"]["axiom_parameters"]["homeostasis_baseline_days"] == {
            "value": 3650, "source": "declared"}
        assert unpublished_reasons(described) == []

    def test_hypothesize(self, session, sensed):
        """The declared direction reaches the ranking: a breach on a department
        is explained by the executives who lead it, and by nothing undeclared.
        With no strength declared, no candidate carries a posterior."""
        assert LED in {f["entity_id"] for f in sensed["findings"]}
        payload = api.hypothesize(session, LED).to_dict()
        candidates = payload["hypothesis"]["candidates"]
        assert {c["cause"] for c in candidates} == LEADERS
        assert all(c["posterior"] is None for c in candidates)
        assert unpublished_reasons(payload) == []

    def test_the_walk_is_traced_to_the_executives_and_names_no_reading(self, session):
        """Both executives leading the department read over their bound, so the
        walk is traced to them and no reading is left to take (FINDINGS F18):
        ranked by standing, since no strength gives a posterior, and nothing is
        screened, so nothing is stamped for it. No edge declares a delay, so
        every cause is read at the finding's instant and nothing says
        `read_at`. With no strength, forcing a cause answers nothing: `infer`
        would decline, so each carries null."""
        leg = api.hypothesize(session, LED).to_dict()["hypothesis"]
        walk = leg["walk"]
        assert (walk["state"], walk["ranked_by"]) == ("traced", "standing")
        assert {entry["entity"] for entry in walk["frontier"]} == LEADERS
        assert leg["most_discriminating"] is None
        assert leg["most_discriminating_reason"]
        assert "faults_visible_along_channels" not in leg["assumptions"]
        # The type's first declared VALUE: `leads`, a relation, is listed before
        # it, and from engine 0.2.19 a relation is never the reading named
        # (FINDINGS F13). The floor is above that, so it is pinned.
        assert {c["evidence_needed"] for c in leg["candidates"]} == {
            f"{leader}.tenure_years" for leader in LEADERS}
        assert "read_at" not in leg
        assert {c["cause"]: c["path"] for c in leg["candidates"]} == {
            leader: [f"{leader}->{LED}"] for leader in LEADERS}
        assert all(c["do_would_answer"] is None for c in leg["candidates"])

    def test_a_division_is_traced_through_its_departments_to_their_executives(
            self, session):
        """A division's finding can be explained by either department or any
        executive leading one. On thirty captures every one of them reads a
        finding, so the departments are the trail and the three executives the
        frontier, and no reading is left to take."""
        leg = api.hypothesize(session, "div-commercial").to_dict()["hypothesis"]
        standings = {c["cause"]: c["standing"] for c in leg["candidates"]}
        assert standings == {"exec-cmo": "frontier", "exec-cro": "frontier",
                             "exec-vp-sales": "frontier",
                             "dept-marketing": "trail", "dept-sales": "trail"}
        assert leg["walk"]["state"] == "traced"
        assert leg["most_discriminating"] is None

    def test_the_walk_states_by_name(self, session, sensed):
        """Of the units with a finding, where each walk ends: the two
        departments the model declares leaders for are traced, and every other
        unit has no declared cause, so its walk is cut."""
        units = sorted({f["entity_id"] for f in sensed["findings"]})
        states = {unit: api.hypothesize(session, unit).to_dict()["hypothesis"][
            "walk"]["state"] for unit in units}
        assert sorted(u for u, s in states.items() if s == "traced") == [
            "dept-marketing", "dept-sales"]
        assert {s for u, s in states.items()
                if u not in ("dept-marketing", "dept-sales")} == {"cut"}

    def test_the_missing_strength_is_named(self, session):
        """`cpt_missing` is the true answer while nobody has a strength to give,
        and the inference the ranking rests on says so by name."""
        payload = api.infer(session, LED).to_dict()
        assert "cpt_missing" in declined_reasons(payload)
        assert unpublished_reasons(payload) == []

    def test_the_ranking_says_why_it_has_no_number(self, session):
        """F10: the ranking carries the decline its inferences made, and each
        cause names its own. It was a strict xfail until the engine did."""
        payload = api.hypothesize(session, LED).to_dict()
        assert "cpt_missing" in declined_reasons(payload)
        assert all(c["declined"] == ["cpt_missing"]
                   for c in payload["hypothesis"]["candidates"])

    def test_plan(self, session):
        """The model declares an objective and the hiring rounds a plan may
        choose between, so the plan ranks them. The rounds do not tie: a hire
        is scored by how far it moves a department from its own HOMEOSTASIS
        baseline, which is what the objective reads. And it declares how far a
        plan looks -- two rounds at once -- so the plan searches pairs, where it
        used to stop at one round under a stamp saying nobody had chosen."""
        payload = api.plan(session).to_dict()
        leg = payload["plan"]
        assert leg["ranked"] and leg["best"]
        assert "no_objective" not in declined_reasons(payload)
        assert len({c["objective"] for c in leg["candidates"]}) > 1, (
            "every round scored the same; the lever moves nothing the objective reads")
        assert any(f.startswith("imagined_homeostasis") and f.endswith(":headcount")
                   for c in leg["candidates"] for f in c["findings"])
        assert leg["checked"]["max_depth"] == 2
        assert "search_depth_not_declared" not in leg["assumptions"]
        assert any(len(c["actions"]) == 2 for c in leg["candidates"]), (
            "the model declares a depth of two and no pair of rounds was rolled out")
        assert unpublished_reasons(payload) == []

    def test_what_each_round_reaches(self, session):
        """A hire moves a department's headcount, and the one coupling that
        would carry it to the division has its gain withheld: no round's effect
        crosses an edge, every round that acts says so by name, and none claims
        to reach anything. No spread is declared either, so there is no closest
        call and nothing is named as deciding one."""
        leg = api.plan(session).to_dict()["plan"]
        for candidate in leg["candidates"]:
            assert candidate["reaches"] == [], candidate["plan"]
            assert candidate["decisive"] is None and candidate["margin_sigmas"] is None
            if candidate["actions"]:
                assert "gain_not_adopted" in candidate["declines"], candidate["plan"]

    def test_learn(self, session):
        """One coupling is declared, with its gain withheld, and thirty monthly
        captures are twenty-nine changes: far below the 120 the engine fits a
        gain from. So every edge it runs along declines `insufficient_samples`
        by name, under `not_fitted` -- a list the copy this file used to carry
        never read."""
        proposed = api.model_describe(session).to_dict()["model"]["proposed_transitions"]
        assert proposed["fitted"] == []
        assert proposed["checked"]["couplings_seen"] == len(DEPARTMENTS)
        assert set(declined_reasons(proposed)) == {"insufficient_samples"}
        assert unpublished_reasons(proposed) == []


#: The four departments, each reporting into a division along the edge the
#: model's one coupling runs on.
DEPARTMENTS = ("dept-sales", "dept-marketing", "dept-engineering", "dept-support")

#: Two waves of people moving, ORTHOGONAL and of mean zero over four months.
#: The two departments of a division get one each, so neither's movement can be
#: mistaken for the other's and the gain a fit should recover is exactly one.
WAVES = ((2, -2), (1, 1, -1, -1))


def _coupled(count):
    """A LABELLED-SYNTHETIC series, not an organisation's history.

    The shipped capture held still, except that each department's headcount
    moves by one of two fixed waves every month and its division's total moves
    by the same people. Built so the one coupling the model declares has an
    answer known in advance -- a department's hire adds exactly one to its
    division's total -- and so nothing else in it is evidence of anything.
    """
    from operating_health_audit import capture

    baseline = capture.load(CAPTURE)
    parent = {p.name: p.edges.get("reports_to") for p in baseline.points
              if p.unit_type == "Department"}
    wave = {d: WAVES[i % 2]
            for division in sorted(set(parent.values()))
            for i, d in enumerate(sorted(n for n in parent if parent[n] == division))}

    def moved(unit, month):
        return sum(wave[unit][j % len(wave[unit])] for j in range(month))

    series = []
    for month in range(count):
        points = []
        for point in baseline.points:
            values = dict(point.values)
            if point.name in parent:
                values["headcount"] = point.values["headcount"] + moved(point.name, month)
            elif point.unit_type == "Division":
                values["total_headcount"] = point.values["total_headcount"] + sum(
                    moved(d, month) for d, division in parent.items()
                    if division == point.name)
            points.append(capture.Reading(
                name=point.name, unit_type=point.unit_type, path=point.path,
                values=values, state=point.state, edges=dict(point.edges)))
        series.append(capture.Export(points=tuple(points), complete=True,
                                     source=f"synthetic, month {month}"))
    return series


def _proposed(series):
    from operating_health_audit import feeder

    session = feeder.open_session(str(MODEL), series)
    return api.model_describe(session).to_dict()["model"]["proposed_transitions"]


class TestTheCouplingIsFittedOnlyFromEnoughChanges:
    """The learn stage's mechanism, shown on a series built for it. The floor is
    the engine's -- 120 paired changes -- and at a monthly cadence that is ten
    years, so a real series here would decline for that long."""

    def test_one_capture_short_of_the_floor_declines_by_name(self):
        proposed = _proposed(_coupled(120))
        assert proposed["fitted"] == []
        assert set(declined_reasons(proposed)) == {"insufficient_samples"}

    def test_at_the_floor_every_edge_is_fitted_and_nothing_is_written(self):
        before = MODEL.read_bytes()
        proposed = _proposed(_coupled(121))
        assert MODEL.read_bytes() == before, "a proposal was written into the model"
        assert declined_reasons(proposed) == []
        fitted = {f["edge"].split("->")[0]: f for f in proposed["fitted"]}
        assert sorted(fitted) == sorted(DEPARTMENTS)
        for proposal in fitted.values():
            low, high = proposal["interval"]
            assert proposal["n"] == 120
            assert proposal["gain"] == pytest.approx(1.0)
            assert low < 1.0 < high
            assert proposal["response_model"] == "step"
            # No record of what happened to replay against: a refusal carrying
            # its reason, never a zero.
            assert proposal["replay"]["status"] == "replay_unavailable"


def _hire(session, people=10):
    with api.as_of(AT):
        return api.file_action(
            session, {"template": "add_headcount", "entity_id": LED,
                      "parameters": {"people": people}},
            AT, "a hiring plan approved at the September review",
            horizon_s=MONTH.total_seconds(), step_s=MONTH.total_seconds()).to_dict()


class TestAnActionIsFiledAndGradedAgainstTheNextCapture:

    @pytest.mark.parametrize("added, action, no_action", [
        (10, (1, 0), (0, 1)),     # the next capture shows the ten people
        (0, (0, 1), (1, 0)),      # it shows nobody arrived
    ])
    def test_the_next_capture_picks_an_arm(self, added, action, no_action):
        session = _fresh()
        before = session.entities[LED].properties["headcount"]
        payload = _hire(session)
        assert payload["execution"]["checked"]["pairs_filed"] == 1
        assert unpublished_reasons(payload) == []

        later = AT + MONTH
        with api.as_of(later):
            session.add_observations(LED, "headcount", [(later, before + added)])
        with api.as_of(later + timedelta(seconds=session.ledger.grace_s + 1)):
            api.check(session)
        arms = session.ledger.calibration()["executions"]["arms"]
        assert (arms["action"]["confirmed"], arms["action"]["falsified"]) == action
        assert (arms["no_action"]["confirmed"], arms["no_action"]["falsified"]) == no_action


class TestACaseOpensOnAFindingAndResolves:

    SUBJECT = ("proc-sales-cycle", "error_rate_pct")

    def test_two_clean_captures_close_it(self):
        session = _fresh()
        unit, indicator = self.SUBJECT
        with api.as_of(AT):
            api.check(session)
            opened = api.open_case(session, unit, indicator,
                                   basis="a critical error rate at the September review")
            api.check(session)
        payload = opened.to_dict()
        assert unpublished_reasons(payload) == []
        case_id = payload["case"]["case_id"]
        assert (payload["case"]["severity"], payload["case"]["consecutive_checks"]) == (
            "warning", 2)
        for month in (1, 2):
            when = AT + month * MONTH
            with api.as_of(when):
                session.entities[unit].properties[indicator] = 2.0
                session.add_observations(unit, indicator, [(when, 2.0)])
                api.check(session)
        case = session.ledger.case_book.get(case_id)
        assert [e["outcome"] for e in case.stages["check"]] == ["found", "clean", "clean"]
        assert case.status == "resolved"
        book = api.case_book(session).to_dict()["cases"]
        assert (book["opened"], book["resolved"]) == (1, 1)


class TestGapsLocatesWhatTheModelCannotExplain:
    """`gaps` also reads the other way from the rest of the loop: from what was
    observed back to where the declaration fails to explain it."""

    def test_the_connected_series_locates_where_its_walks_end_and_nothing_else(
            self, session, sensed):
        """Only the walk locates anything here (engine 0.2.30): the support
        department, which no executive leads, and the two processes' dependencies,
        a relation this model gives no direction."""
        residuals = api.gaps(session).to_dict()["residuals"]
        assert sorted((h["kind"], h.get("at") or tuple(h["between"]))
                      for h in residuals["hypotheses"]) == [
            ("no_cause_connected", "dept-support"),
            ("undeclared_channel", ("proc-onboarding", "dept-support")),
            ("undeclared_channel", ("proc-sales-cycle", "dept-sales"))]
        # No balance is declared, and how many executions make a pattern is the
        # model's to say. This model does not say, and no number is chosen.
        assert {(d["reason"], d["location"]) for d in residuals["not_checked"]} == {
            ("missing_config", "conservation"), ("missing_config", "gaps.min_cycles")}
        assert unpublished_reasons(residuals) == []

    def test_the_export_as_shipped_locates_every_unit_it_detached(self):
        """The source case study ships its export with the relationships
        removed. Every unit is located once, as detached, with the relation the
        model says it must have and the reading that would settle it."""
        from operating_health_audit import capture, feeder

        shipped = capture.load(ROOT / "examples" / "acme.capture.asshipped.json")
        session = feeder.open_session(str(MODEL), [shipped])
        api.check(session)
        located = api.gaps(session).to_dict()["residuals"]["hypotheses"]
        detached = [h for h in located if h["kind"] == "absent_or_detached"]
        assert {h["at"] for h in detached} == set(session.entities)
        assert len(detached) == len(session.entities) == 14
        assert all(h["evidence_needed"] == f"{h['at']}.{h['relation']}"
                   for h in detached)
        # With no edge left, every department and division has no cause
        # connected by the relation the model says brings one (engine 0.2.30).
        kinds = {unit: entity.type for unit, entity in session.entities.items()}
        assert {(h["kind"], h["at"], h["relation"]) for h in located
                if h["kind"] != "absent_or_detached"} == {
            ("no_cause_connected", unit,
             {"Department": "leads", "Division": "reports_to"}[kind])
            for unit, kind in kinds.items() if kind in ("Department", "Division")}


@pytest.fixture(scope="module")
def shipped():
    """`gaps` on the shipped capture, as the feeder builds its session."""
    from operating_health_audit import capture, feeder

    session = feeder.open_session(str(MODEL), [capture.load(CAPTURE)])
    api.check(session)
    return api.gaps(session).to_dict()["residuals"]


class TestGapsSaysWhereEachWalkEnds:
    """On the shipped capture, `gaps` says where each walk ends (engine 0.2.30):
    the support department nobody leads, and the two processes' dependencies along
    a relation this model gives no direction. Nothing at the expansion project,
    whose division shows nothing."""

    def test_the_department_nobody_leads_has_no_cause_connected(self, shipped):
        [row] = [h for h in shipped["hypotheses"] if h["kind"] == "no_cause_connected"]
        assert (row["at"], row["relation"], row["evidence_needed"]) == (
            "dept-support", "leads", "dept-support.leads")

    def test_both_processes_are_undeclared_channels_on_depends_on(self, shipped):
        assert [(h["between"], h["relation"]) for h in shipped["hypotheses"]
                if h["kind"] == "undeclared_channel"] == [
            (["proc-onboarding", "dept-support"], "depends_on"),
            (["proc-sales-cycle", "dept-sales"], "depends_on")]

    def test_nothing_at_the_expansion_project_nor_on_the_reversed_edge(self, shipped):
        """`funds` reaches a division that shows nothing; and the export's
        `div-commercial reports_to dept-sales` joins two units a causal edge
        already joins."""
        assert not [h for h in shipped["hypotheses"] if "proj-expansion" in str(h)]
        assert not [h for h in shipped["hypotheses"] if h.get("relation") == "reports_to"]

    def test_each_direction_is_counted_and_neither_preferred(self, shipped):
        """The model's comment says a failure runs from the department to the
        process: the smaller count. A count says what a direction would connect."""
        assert shipped["checked"]["undeclared_channels"] == {
            "depends_on": {"instances": 2, "if_cause_is_source": 4,
                           "if_cause_is_target": 2}}

    def test_the_walk_states_of_the_eleven_findings(self, shipped):
        assert shipped["checked"]["walk_states"] == {
            "traced": 1, "partly_traced": 1, "open": 1, "unexplained": 0, "cut": 6}

    @pytest.mark.parametrize("cause,subject,located", [
        ("proc-onboarding", "dept-support", True),
        ("exec-cro", "dept-sales", False)])
    def test_a_cause_confirmed_outside_the_graph_is_located(
            self, tmp_path, cause, subject, located):
        """A confirmation names its cause; one no declared channel connects to
        the finding is located between the two, and a declared ancestor is not."""
        from operating_health_audit import capture, feeder

        session = feeder.open_session(str(MODEL), [capture.load(CAPTURE)],
                                      ledger=str(tmp_path / "book.sqlite"))
        shipped_at = datetime(2026, 9, 15)
        with api.as_of(shipped_at):
            api.check(session)
            case_id = api.open_case(session, subject, "turnover_pct",
                                    basis="turnover over its bound"
                                    ).to_dict()["case"]["case_id"]
            api.attach_stage(session, case_id, "hypothesize",
                             api.hypothesize(session, subject))
        with api.as_of(shipped_at + timedelta(minutes=5)):
            reading = {"proc-onboarding": "error_rate_pct",
                       "exec-cro": "direct_reports"}[cause]
            api.attach_stage(session, case_id, "confirm", reference={
                "cause": cause, "reading": f"{cause}.{reading}",
                "basis": "the operations lead, from the monthly review"})
            residuals = api.gaps(session).to_dict()["residuals"]
        assert residuals["checked"]["confirmations_read"] == 1
        rows = [h for h in residuals["hypotheses"]
                if h["kind"] == "confirmed_outside_graph"]
        assert [(h["between"], h["basis"]) for h in rows] == (
            [([cause, subject], "the operations lead, from the monthly review")]
            if located else [])


class TestAConfirmationSaysWhereTheCauseWasRanked:

    def test_the_book_reads_the_confirmation_against_the_ranking_before_it(self):
        """A person confirms the first executive on the walk's frontier; the
        book says where that executive stood, and that the ranking named no
        reading -- the walk was traced -- counts beside the row, never a rate."""
        session = _fresh()
        with api.as_of(AT):
            api.check(session)
            case_id = api.open_case(session, LED, "headcount",
                                    basis="a headcount breach at the September review"
                                    ).to_dict()["case"]["case_id"]
            ranking = api.hypothesize(session, LED)
            api.attach_stage(session, case_id, "hypothesize", ranking)
            api.attach_stage(session, case_id, "gaps", api.gaps(session))
        leg = ranking.to_dict()["hypothesis"]
        assert leg["most_discriminating"] is None
        named = leg["walk"]["frontier"][0]["entity"]
        causes = [c["cause"] for c in leg["candidates"]]
        with api.as_of(AT + timedelta(minutes=5)):
            attached = api.attach_stage(
                session, case_id, "confirm",
                reference={"cause": named, "reading": f"{named}.performance_rating",
                           "basis": "the October review"}).to_dict()
        assert attached["case"]["checked"]["stages_attached"] == 1
        confirmed = api.case_book(session).to_dict()["cases"]["confirmed"]
        # BY LOOKUP. A row is a record the engine may add keys to in a patch
        # release -- 0.2.20 added three -- and an equality on the whole row
        # broke on the first one.
        [row] = confirmed["rows"]
        assert (row["case_id"], row["cause"], row["rank"], row["of"],
                row["named_reading_settled_it"]) == (
            case_id, named, causes.index(named) + 1, 2, False)
        assert (confirmed["confirmations"], confirmed["ranked"],
                confirmed["not_ranked"]) == (1, 1, 0)
        # Engine 0.2.23 says what that rank rested on, and from 0.2.27 a ranking
        # with no strength is ordered by standing -- a first place here is no
        # posterior's -- and named no reading, so nothing compares with the one
        # the review gave: an unasked question is not a no.
        assert (row["ranked_by"], row["named_by"]) == ("standing", None)
        assert confirmed["ranked_by_posterior"] == 0
        assert (row["settling_reading_was_named"],
                row["settling_entity_was_named"]) == (None, None)
        assert unpublished_reasons(attached) == []


class TestAConfirmationSaysWhereTheCauseStood:
    """On the shipped capture (engine 0.2.31) a case keeps the walk, and the book
    reads a confirmation back against it: where the cause stood, on what walk,
    on whose word, and after how many rankings. Confirmed through `confirm`, on
    a session holding the ledger and nothing else, as a person would."""

    BASIS = "the operations lead, from the monthly review"

    def _confirmed(self, tmp_path, subject, cause, reading):
        from operating_health_audit import capture, feeder

        ledger = str(tmp_path / "book.sqlite")
        session = feeder.open_session(str(MODEL), [capture.load(CAPTURE)],
                                      ledger=ledger)
        shipped_at = datetime(2026, 9, 15)
        with api.as_of(shipped_at):
            api.check(session)
            case_id = api.open_case(session, subject, "turnover_pct",
                                    basis="turnover over its bound"
                                    ).to_dict()["case"]["case_id"]
            api.attach_stage(session, case_id, "hypothesize",
                             api.hypothesize(session, subject))
        with api.as_of(shipped_at + timedelta(minutes=5)):
            out = feeder.confirm(ledger, case_id, cause=cause,
                                 reading=f"{cause}.{reading}", basis=self.BASIS)
        return out["confirmed"], feeder.book(ledger)

    def test_the_cro_confirmed_on_sales_stood_at_the_frontier_of_a_traced_walk(
            self, tmp_path):
        row, book = self._confirmed(tmp_path, LED, "exec-cro", "direct_reports")
        assert (row["standing"], row["walk_state"], row["basis"],
                row["walks_before"]) == ("frontier", "traced", self.BASIS, 1)
        assert (book["confirmed"]["by_standing"]["frontier"],
                book["confirmed"]["confirmed_after_screened"]) == (1, 0)
        assert book["reopened"] == 0

    def test_a_process_confirmed_on_the_department_nobody_leads_is_not_connected(
            self, tmp_path):
        """Its walk is cut, so nothing ranked it -- and nothing declared reaches it
        past the bound either: the process is not connected at all."""
        row, book = self._confirmed(tmp_path, "dept-support", "proc-onboarding",
                                    "error_rate_pct")
        assert (row["standing"], row["walk_state"], row["rank"]) == (
            "not_connected", "cut", None)
        assert book["confirmed"]["by_standing"]["not_connected"] == 1


def _planned(tmp_path, **planning):
    """`plan` over the loop's own series, on a copy of the model whose planning
    block is changed by `planning` -- the shipped file is never written."""
    import yaml
    from operating_health_audit import feeder

    model = yaml.safe_load(MODEL.read_text())
    model["domain"]["planning"].update(planning)
    path = tmp_path / "planned.model.yaml"
    path.write_text(yaml.safe_dump(model, sort_keys=False))
    return api.plan(feeder.open_session(str(path), _series())).to_dict()


class TestTheSearchStopsAtItsBudgetAndSaysSo:
    """`max_rollouts` is a stop, and a stop that cut a search short has to say
    so, with the count of what it left out: a plan chosen from part of the
    field reads exactly like one chosen from all of it. The declared search
    fits inside the default budget, so the shipped model shows only one side of
    that. A copy with the budget set below the field shows the other."""

    def test_the_declared_search_is_rolled_out_whole(self, session):
        payload = api.plan(session).to_dict()
        assert payload["plan"]["checked"]["plans_untested"] == 0
        assert "budget_exhausted" not in declined_reasons(payload)

    def test_a_budget_below_the_field_is_declined_with_its_count(self, session,
                                                                 tmp_path):
        field = api.plan(session).to_dict()["plan"]["checked"]["candidates_evaluated"]
        short = _planned(tmp_path, max_rollouts=field - 4)
        assert "budget_exhausted" in declined_reasons(short)
        assert short["plan"]["checked"]["plans_untested"] == 4
        assert unpublished_reasons(short) == []


def test_the_stage_report_matches_what_the_run_did(session):
    """`model_describe` says, per stage, whether the model declares what that
    stage reads -- and each claim is checked against what the stage then did."""
    stages = {name: row["declared"] for name, row in
              api.model_describe(session).to_dict()["model"]["stages"].items()}
    # Read by lookup, as the engine's compatibility policy asks of every reader:
    # a patch release may add a stage, and one not named here means the engine
    # is newer than this test, not that the model changed.
    named = {"check": True, "hypothesize": True, "plan": True,
             "act": True, "learn": True, "case": True,
             "gaps": True, "confirm": True}
    assert {name: stages.get(name) for name in named} == named
    assert api.hypothesize(session, LED).to_dict()["hypothesis"]["candidates"]
    assert "residuals" in api.gaps(session).to_dict()
    assert api.plan(session).to_dict()["plan"]["ranked"]
    assert _hire(_fresh())["execution"]["checked"]["pairs_filed"] == 1
    learned = api.model_describe(session).to_dict()["model"]["proposed_transitions"]
    assert not learned["fitted"] and "insufficient_samples" in declined_reasons(learned)
    assert "case_id" in api.open_case(_fresh(), "proc-sales-cycle",
                                      "error_rate_pct").to_dict()["case"]


def test_the_vocabularies_are_not_empty():
    """Before believing a negative, prove the probe can produce one."""
    assert "insufficient_samples" in PUBLISHED_REASONS
    assert "no_objective" in PUBLISHED_REASONS
    assert unpublished_reasons({"not_checked": [{"reason": "made_up_here"}]}) == [
        "made_up_here"]


def test_a_refusal_the_learn_leg_names_wrongly_is_caught(session):
    """The incident the shared walker exists for. The learn leg's real answer,
    with one unpublished reason put into `not_fitted`: the walk this file used
    to carry read only `not_checked` and `declines`, and would pass it."""
    proposed = api.model_describe(session).to_dict()["model"]["proposed_transitions"]
    doctored = dict(proposed, not_fitted=list(proposed["not_fitted"]) + [
        {"edge": "dept-sales->div-commercial", "reason": "made_up_here"}])
    assert unpublished_reasons(doctored) == ["made_up_here"]

    def two_lists(node):
        if isinstance(node, dict):
            return [item.get("reason") for key, value in node.items()
                    if key in ("not_checked", "declines") and isinstance(value, list)
                    for item in value if isinstance(item, dict)] + [
                reason for value in node.values() for reason in two_lists(value)]
        if isinstance(node, list):
            return [reason for item in node for reason in two_lists(item)]
        return []

    assert "made_up_here" not in two_lists(doctored)
