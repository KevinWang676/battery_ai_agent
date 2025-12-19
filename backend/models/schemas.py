from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class AgentType(str, Enum):
    ORCHESTRATOR = "orchestrator"
    LITERATURE_RAG = "literature_rag"
    PROPERTY_COMPATIBILITY = "property_compatibility"
    PERFORMANCE_PREDICTION = "performance_prediction"
    EXPERIMENT_PLANNING = "experiment_planning"

class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class ElectrolyteComponent(BaseModel):
    name: str
    formula: Optional[str] = None
    concentration: Optional[float] = None
    role: str  # solvent, salt, additive

class MolecularProperties(BaseModel):
    component: str
    molecular_weight: Optional[float] = None
    viscosity: Optional[float] = None
    ionic_conductivity: Optional[float] = None
    electrochemical_window: Optional[tuple] = None
    thermal_stability: Optional[float] = None
    compatibility_notes: Optional[str] = None

class PerformancePrediction(BaseModel):
    capacity_retention: float
    cycle_stability: float
    rate_capability: float
    temperature_range: tuple
    confidence_score: float
    model_notes: str

class ExperimentPlan(BaseModel):
    plan_id: str
    title: str
    formulation: List[ElectrolyteComponent]
    rationale: str
    predicted_performance: PerformancePrediction
    experimental_steps: List[str]
    safety_considerations: List[str]
    estimated_cost: str
    priority_score: float

class AgentResponse(BaseModel):
    agent_type: AgentType
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

class OrchestratorResponse(BaseModel):
    query: str
    agent_responses: List[AgentResponse]
    experiment_plans: List[ExperimentPlan]
    summary: str
    processing_time: float

class DocumentUploadResponse(BaseModel):
    filename: str
    status: str
    chunks_created: int
    message: str

class LiteratureSearchResult(BaseModel):
    title: str
    content: str
    relevance_score: float
    source: str



