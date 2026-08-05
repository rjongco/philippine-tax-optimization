"""Scenario read/write and the documentation endpoint."""

from typing import List

from fastapi import APIRouter

from .. import store
from ..docs_meta import CONCEPT_DOCS, PARAMETER_DOCS, ConceptDoc, ParameterDoc
from ..schemas import ScenarioIn, ScenarioOut

router = APIRouter(prefix="/api", tags=["scenario"])


@router.get("/scenario", response_model=ScenarioOut)
def get_scenario() -> ScenarioOut:
    return ScenarioOut.of(store.load())


@router.put("/scenario", response_model=ScenarioOut)
def put_scenario(payload: ScenarioIn) -> ScenarioOut:
    scenario = payload.to_engine()
    store.save(scenario)
    return ScenarioOut.of(scenario)


@router.post("/scenario/reset", response_model=ScenarioOut)
def reset_scenario() -> ScenarioOut:
    """Restore the seeded workbook values."""
    return ScenarioOut.of(store.reset())


@router.get("/parameters/meta", response_model=List[ParameterDoc])
def get_parameter_docs() -> List[ParameterDoc]:
    return PARAMETER_DOCS


@router.get("/concepts", response_model=List[ConceptDoc])
def get_concept_docs() -> List[ConceptDoc]:
    return CONCEPT_DOCS
