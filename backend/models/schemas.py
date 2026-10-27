from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class ComponentScores(BaseModel):
    formatting: float
    keywords: float
    content: float
    skill_validation: float
    ats_compatibility: float

class JDComparison(BaseModel):
    match_percentage: float
    semantic_similarity: float
    matched_keywords: List[str]
    missing_keywords: List[str]
    skills_gap: List[str]

class SkillValidationDetails(BaseModel):
    validated: List[Dict[str, Any]] = []       # [{'skill': str, 'projects': [str]}]
    unvalidated: List[str] = []                # ['Flask', 'A/B Testing', ...]
    total: int = 0
    validated_count: int = 0
    validation_pct: float = 0.0

class IssueDetail(BaseModel):
    issue_title: str
    severity_level: str
    ats_impact: str
    explanation: str
    where_it_appears: str
    how_to_fix: str
    action_items: List[str] = []
    example_improvement: str

class AnalysisResponse(BaseModel):
    ATS_score: float
    component_scores: ComponentScores
    issues_summary: List[str]
    detailed_feedback: List[IssueDetail]
    jd_match_analysis: Optional[JDComparison] = None
    skill_validation_details: Optional[SkillValidationDetails] = None

    ats_score: float
    keyword_match: float = 0.0
    missing_keywords: List[str] = []
    matched_keywords: List[str] = []
    suggestions: List[str] = []
    strengths: List[str] = []
    critical_issues: List[str] = []
    skills: List[str] = []
    jd_comparison: Optional[JDComparison] = None
    warnings: List[str] = []
    interpretation: str = ""

    # Parsed resume text (summary, skills, experience, projects, education) for the Resume Coach
    resume_sections: Optional[Dict[str, Any]] = None

class CoachMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(..., min_length=1, max_length=4000)

class CoachRequest(BaseModel):
    messages: List[CoachMessage] = Field(..., min_length=1, max_length=30)
    analysis: Dict[str, Any]      # the AnalysisResponse the user is asking about

class CoachResponse(BaseModel):
    answer: str
    steps: List[Dict[str, Any]] = []   # [{'tool': str, 'args': dict}] in the order they ran
    sources: List[str] = []            # guide sections the agent retrieved