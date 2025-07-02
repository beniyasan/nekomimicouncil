from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import uuid

class DebateRequest(BaseModel):
    """Request model for starting a debate"""
    topic: str = Field(..., description="The topic to debate")
    options: List[str] = Field(..., description="List of options to choose from", min_items=2)

class DebateStartResponse(BaseModel):
    """Response model for debate start"""
    id: str = Field(..., description="Unique debate ID")

class AgentMessage(BaseModel):
    """Message from an AI agent during debate"""
    agent_id: str = Field(..., description="ID of the agent")
    agent_name: str = Field(..., description="Display name of the agent")
    message: str = Field(..., description="The agent's message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    choice: Optional[str] = Field(None, description="Agent's preferred choice")
    message_type: Literal["initial_opinion", "question", "response", "final_opinion", "officer_question", "decision"] = Field(..., description="Type of message")
    target_agent: Optional[str] = Field(None, description="Target agent ID for questions/responses")
    round_number: int = Field(..., description="Discussion round number")

class DebateRound(BaseModel):
    """Information about a debate round"""
    round_number: int = Field(..., description="Round number")
    round_type: Literal["initial_opinions", "peer_questions", "officer_questions", "final_opinions", "decision"] = Field(..., description="Type of round")
    description: str = Field(..., description="Description of what happens in this round")

class DebateResult(BaseModel):
    """Complete debate result"""
    id: str = Field(..., description="Unique debate ID")
    topic: str = Field(..., description="The debate topic")
    options: List[str] = Field(..., description="Available options")
    status: Literal["started", "in_progress", "completed", "failed"] = Field(..., description="Debate status")
    created_at: datetime = Field(..., description="When the debate was created")
    completed_at: Optional[datetime] = Field(None, description="When the debate was completed")
    messages: List[AgentMessage] = Field(default_factory=list, description="All messages during the debate")
    rounds: List[DebateRound] = Field(default_factory=list, description="Debate rounds information")
    current_round: int = Field(default=1, description="Current round number")
    final_choice: Optional[str] = Field(None, description="Final decision from Officer")
    summary: Optional[str] = Field(None, description="Summary of the debate")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")

class Persona(BaseModel):
    """AI agent persona definition"""
    id: str = Field(..., description="Unique persona ID")
    name: str = Field(..., description="Display name")
    persona: str = Field(..., description="Personality description")
    speech_style: str = Field(..., description="How the persona speaks")
    weights: dict = Field(default_factory=dict, description="Decision factor weights")