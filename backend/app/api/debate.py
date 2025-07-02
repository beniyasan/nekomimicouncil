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
from ..services.web_search import web_search_service
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

async def run_debate_process(debate_id: str, topic: str, options: list[str], enable_web_search: bool = False):
    """Run the actual multi-round debate process in background"""
    try:
        # Update status
        if debate_id in debates:
            debates[debate_id].status = "in_progress"
            
        # Search for store information if enabled
        search_results = None
        if enable_web_search:
            logger.info(f"Web search enabled for debate {debate_id}")
            detected_stores = await web_search_service.detect_store_names(options)
            
            if detected_stores:
                logger.info(f"Detected stores: {detected_stores}")
                search_results = {}
                successful_searches = 0
                
                for store in detected_stores:
                    logger.info(f"Searching for store: {store}")
                    store_info = await web_search_service.search_store_info(store)
                    if store_info:
                        search_results[store] = store_info
                        successful_searches += 1
                        logger.info(f"✅ Found information for {store}: {store_info.get('info', {}).get('description', 'No description')[:100]}...")
                    else:
                        logger.warning(f"❌ No information found for {store}")
                        # Provide fallback information
                        search_results[store] = {
                            "store_name": store,
                            "search_query": store,
                            "info": {
                                "description": f"{store}に関する詳細情報は見つかりませんでしたが、参加者の経験や知識をもとに議論します。",
                                "location": "場所不明",
                                "status": "検索失敗"
                            },
                            "search_results_count": 0
                        }
                
                logger.info(f"Web search completed: {successful_searches}/{len(detected_stores)} successful")
                
                # Emit search results to frontend
                if sio and search_results:
                    await sio.emit("search_results", {
                        "debate_id": debate_id,
                        "results": search_results,
                        "successful_count": successful_searches,
                        "total_count": len(detected_stores)
                    }, room=f"debate-{debate_id}")
            else:
                logger.info("No stores detected in options")
        
        # Initialize rounds
        rounds = [
            {"round_number": 1, "round_type": "initial_opinions", "description": "初期意見表明"},
            {"round_number": 2, "round_type": "peer_questions", "description": "参加者同士の質疑応答"},
            {"round_number": 3, "round_type": "peer_questions", "description": "質問への回答"},
            {"round_number": 4, "round_type": "officer_questions", "description": "議長からの質問"},
            {"round_number": 5, "round_type": "final_opinions", "description": "最終意見表明"},
            {"round_number": 6, "round_type": "decision", "description": "議長による最終決定"}
        ]
        
        for round_info in rounds:
            debates[debate_id].rounds.append(round_info)
        
        # Emit status update
        if sio:
            await sio.emit("status_update", {
                "debate_id": debate_id,
                "status": "in_progress"
            }, room=f"debate-{debate_id}")
        
        # Load personas
        personas = await load_personas(3)
        logger.info(f"Loaded personas for debate {debate_id}: {[p.name for p in personas]}")
        
        # Create agents with search results context
        debate_agents = []
        for persona in personas:
            try:
                provider = AIProviderFactory.get_default_provider("debate")
                agent = DebateAgent(persona, provider)
                
                # Inject search results into agent context if available
                if search_results:
                    agent.search_context = search_results
                
                debate_agents.append(agent)
            except Exception as e:
                logger.error(f"Failed to create agent for {persona.name}: {str(e)}")
        
        if not debate_agents:
            raise ValueError("No debate agents available")
        
        # Create officer with search context
        officer_provider = AIProviderFactory.get_default_provider("officer")
        officer = OfficerAgent(officer_provider)
        
        # Inject search results into officer context if available
        if search_results:
            officer.search_context = search_results
        
        # === ROUND 1: Initial Opinions ===
        await emit_round_start(debate_id, 1, "初期意見表明")
        
        initial_tasks = []
        for agent in debate_agents:
            task = agent.generate_response(topic, options)
            initial_tasks.append(task)
        
        initial_messages = await asyncio.gather(*initial_tasks, return_exceptions=True)
        valid_initial = await process_round_messages(debate_id, initial_messages, debate_agents, 1)
        
        # === ROUND 2: Peer Questions ===
        await emit_round_start(debate_id, 2, "参加者同士の質疑応答")
        
        question_tasks = []
        for agent in debate_agents:
            task = agent.ask_question(topic, options, valid_initial, 2)
            question_tasks.append(task)
        
        question_messages = await asyncio.gather(*question_tasks, return_exceptions=True)
        valid_questions = await process_round_messages(debate_id, question_messages, debate_agents, 2)
        
        # === ROUND 3: Question Responses ===
        await emit_round_start(debate_id, 3, "質問への回答")
        
        all_messages = valid_initial + [q for q in valid_questions if q is not None]
        response_tasks = []
        
        # Process each valid question and ensure responses
        for question in valid_questions:
            if question and question.target_agent:
                # Find the target agent by agent_id
                target_agent = next((a for a in debate_agents if a.agent_id == question.target_agent), None)
                if target_agent:
                    logger.info(f"Creating response task: {question.agent_name} -> {target_agent.agent_name}")
                    task = target_agent.respond_to_question(topic, options, question, all_messages, 3)
                    response_tasks.append((task, target_agent.agent_name, question.agent_name))
                else:
                    logger.warning(f"Target agent '{question.target_agent}' not found for question from {question.agent_name}")
            else:
                if question:
                    logger.warning(f"Question from {question.agent_name} has no target_agent")
        
        if response_tasks:
            logger.info(f"Processing {len(response_tasks)} response tasks")
            # Extract just the tasks for gathering
            tasks_only = [task[0] for task in response_tasks]
            response_messages = await asyncio.gather(*tasks_only, return_exceptions=True)
            
            # Create agent list for process_round_messages (matching response order)
            responding_agents = [next(a for a in debate_agents if a.agent_name == task[1]) for task in response_tasks]
            
            valid_responses = await process_round_messages(debate_id, response_messages, responding_agents, 3)
            all_messages.extend([r for r in valid_responses if r is not None])
        else:
            logger.warning("No response tasks created - questions may be missing target agents")
        
        # === ROUND 4: Officer Questions ===
        await emit_round_start(debate_id, 4, "議長からの質問")
        
        officer_questions = await officer.ask_clarifying_questions(topic, options, all_messages, 4)
        if officer_questions:
            await process_round_messages(debate_id, officer_questions, [officer], 4)
            
            # Get responses to officer questions
            officer_response_tasks = []
            for question in officer_questions:
                if question.target_agent:
                    target_agent = next((a for a in debate_agents if a.agent_id == question.target_agent), None)
                    if target_agent:
                        task = target_agent.respond_to_question(topic, options, question, all_messages, 4)
                        officer_response_tasks.append(task)
            
            if officer_response_tasks:
                officer_responses = await asyncio.gather(*officer_response_tasks, return_exceptions=True)
                valid_officer_responses = await process_round_messages(debate_id, officer_responses, debate_agents, 4)
                all_messages.extend([r for r in valid_officer_responses if r is not None])
        
        # === ROUND 5: Final Opinions ===
        await emit_round_start(debate_id, 5, "最終意見表明")
        
        final_tasks = []
        for agent in debate_agents:
            task = agent.final_opinion(topic, options, all_messages, 5)
            final_tasks.append(task)
        
        final_messages = await asyncio.gather(*final_tasks, return_exceptions=True)
        valid_finals = await process_round_messages(debate_id, final_messages, debate_agents, 5)
        all_messages.extend([f for f in valid_finals if f is not None])
        
        # === ROUND 6: Officer Decision ===
        await emit_round_start(debate_id, 6, "議長による最終決定")
        
        decision = await officer.generate_decision(topic, options, all_messages)
        
        # Update debate result
        if debate_id in debates:
            debates[debate_id].status = "completed"
            debates[debate_id].completed_at = datetime.utcnow()
            debates[debate_id].final_choice = decision["final_choice"]
            debates[debate_id].summary = decision["summary"]
            debates[debate_id].confidence = decision["confidence"]
            debates[debate_id].current_round = 6
        
        # Emit final decision
        if sio:
            await sio.emit("decision", {
                "final_choice": decision["final_choice"],
                "summary": decision["summary"],
                "confidence": decision["confidence"]
            }, room=f"debate-{debate_id}")
        
        logger.info(f"Multi-round debate {debate_id} completed successfully")
        
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

async def emit_round_start(debate_id: str, round_number: int, description: str):
    """Emit round start event"""
    if sio:
        await sio.emit("round_start", {
            "round_number": round_number,
            "description": description
        }, room=f"debate-{debate_id}")
    
    # Update current round
    if debate_id in debates:
        debates[debate_id].current_round = round_number
    
    # Small delay for better UX
    await asyncio.sleep(1)

async def process_round_messages(debate_id: str, messages, agents, round_number: int):
    """Process and emit messages from a round"""
    valid_messages = []
    
    for i, result in enumerate(messages):
        if isinstance(result, Exception):
            if i < len(agents):
                logger.error(f"Agent {agents[i].agent_name} failed in round {round_number}: {str(result)}")
        elif result is not None:
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
                    "choice": result.choice,
                    "message_type": result.message_type,
                    "target_agent": result.target_agent,
                    "round_number": result.round_number
                }, room=f"debate-{debate_id}")
            
            # Small delay for better UX
            await asyncio.sleep(1.5)
    
    return valid_messages

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
        background_tasks.add_task(run_debate_process, debate_id, request.topic, request.options, request.enable_web_search)
        
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