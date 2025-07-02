from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import uuid
import asyncio
import json
import random
from datetime import datetime
from pathlib import Path
from ..models.debate import DebateRequest, DebateStartResponse, DebateResult, Persona
from ..agents.base import DebateAgent, OfficerAgent
from ..agents.providers import AIProviderFactory
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for debates
debates: Dict[str, DebateResult] = {}

# Socket.IO instance (will be injected)
sio = None

def set_socketio(socketio_instance):
    """Set the Socket.IO instance for real-time events"""
    global sio
    sio = socketio_instance

async def load_personas(count: int = 3) -> list[Persona]:
    """Load random personas for debate"""
    try:
        personas_file = Path(__file__).parent.parent.parent.parent / "data" / "personas" / "personas.json"
        
        with open(personas_file, 'r', encoding='utf-8') as f:
            personas_data = json.load(f)
        
        personas = [Persona(**data) for data in personas_data]
        return random.sample(personas, min(count, len(personas)))
        
    except Exception as e:
        logger.error(f"Error loading personas: {str(e)}")
        # Fallback personas
        return [
            Persona(
                id="fallback1",
                name="一般ユーザー1",
                persona="バランス重視",
                speech_style="普通",
                weights={}
            ),
            Persona(
                id="fallback2", 
                name="一般ユーザー2",
                persona="実用重視",
                speech_style="普通",
                weights={}
            ),
            Persona(
                id="fallback3",
                name="一般ユーザー3", 
                persona="コスパ重視",
                speech_style="普通",
                weights={}
            )
        ][:count]

async def run_debate_process(debate_id: str, topic: str, options: list[str]):
    """Run the actual debate process in background"""
    try:
        # Update status
        if debate_id in debates:
            debates[debate_id].status = "in_progress"
            
            # Emit status update
            if sio:
                await sio.emit("status_update", {
                    "debate_id": debate_id,
                    "status": "in_progress"
                }, room=f"debate-{debate_id}")
        
        # Load personas
        personas = await load_personas(3)
        logger.info(f"Loaded personas for debate {debate_id}: {[p.name for p in personas]}")
        
        # Create agents
        debate_agents = []
        for persona in personas:
            try:
                provider = AIProviderFactory.get_default_provider("debate")
                agent = DebateAgent(persona, provider)
                debate_agents.append(agent)
            except Exception as e:
                logger.error(f"Failed to create agent for {persona.name}: {str(e)}")
        
        if not debate_agents:
            raise ValueError("No debate agents available")
        
        # Create officer
        officer_provider = AIProviderFactory.get_default_provider("officer")
        officer = OfficerAgent(officer_provider)
        
        # Run debate
        debate_tasks = []
        for agent in debate_agents:
            task = agent.generate_response(topic, options)
            debate_tasks.append(task)
        
        # Wait for all agents
        debate_messages = await asyncio.gather(*debate_tasks, return_exceptions=True)
        
        # Process results and emit messages
        valid_messages = []
        for i, result in enumerate(debate_messages):
            if isinstance(result, Exception):
                logger.error(f"Agent {debate_agents[i].agent_name} failed: {str(result)}")
            else:
                valid_messages.append(result)
                
                # Store message
                if debate_id in debates:
                    debates[debate_id].messages.append(result)
                
                # Emit real-time message
                if sio:
                    await sio.emit("agent_message", {
                        "agent_id": result.agent_id,
                        "agent_name": result.agent_name,
                        "message": result.message,
                        "timestamp": result.timestamp.isoformat(),
                        "choice": result.choice
                    }, room=f"debate-{debate_id}")
                
                # Small delay for better UX
                await asyncio.sleep(1)
        
        if not valid_messages:
            raise ValueError("No valid debate messages")
        
        # Officer decision
        decision = await officer.generate_decision(topic, options, valid_messages)
        
        # Update debate result
        if debate_id in debates:
            debates[debate_id].status = "completed"
            debates[debate_id].completed_at = datetime.utcnow()
            debates[debate_id].final_choice = decision["final_choice"]
            debates[debate_id].summary = decision["summary"]
            debates[debate_id].confidence = decision["confidence"]
        
        # Emit final decision
        if sio:
            await sio.emit("decision", {
                "final_choice": decision["final_choice"],
                "summary": decision["summary"],
                "confidence": decision["confidence"]
            }, room=f"debate-{debate_id}")
        
        logger.info(f"Debate {debate_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in debate process {debate_id}: {str(e)}")
        
        # Update status to failed
        if debate_id in debates:
            debates[debate_id].status = "failed"
        
        # Emit error
        if sio:
            await sio.emit("error", {
                "message": f"議論中にエラーが発生しました: {str(e)}"
            }, room=f"debate-{debate_id}")

@router.post("/debate", response_model=DebateStartResponse)
async def start_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    """Start a new debate session"""
    try:
        debate_id = str(uuid.uuid4())
        
        # Validate request
        if len(request.options) < 2:
            raise HTTPException(status_code=400, detail="At least 2 options required")
        
        if len(request.topic.strip()) == 0:
            raise HTTPException(status_code=400, detail="Topic cannot be empty")
        
        # Create initial debate result
        debate_result = DebateResult(
            id=debate_id,
            topic=request.topic,
            options=request.options,
            status="started",
            created_at=datetime.utcnow(),
            messages=[],
            final_choice=None,
            summary=None,
            confidence=None
        )
        
        # Store in memory
        debates[debate_id] = debate_result
        
        # Start debate process in background
        background_tasks.add_task(run_debate_process, debate_id, request.topic, request.options)
        
        logger.info(f"Started debate {debate_id} with topic: {request.topic}")
        
        return DebateStartResponse(id=debate_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting debate: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start debate")

@router.get("/debate/{debate_id}", response_model=DebateResult)
async def get_debate(debate_id: str):
    """Get debate results by ID"""
    if debate_id not in debates:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    return debates[debate_id]