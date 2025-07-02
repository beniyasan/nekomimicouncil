from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json
import asyncio
import logging
from .providers import AIProvider, AIProviderFactory
from ..models.debate import Persona, AgentMessage
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(
        self, 
        agent_id: str,
        agent_name: str,
        provider: Optional[AIProvider] = None,
        max_retries: int = 3
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.provider = provider or AIProviderFactory.get_default_provider("debate")
        self.max_retries = max_retries
    
    @abstractmethod
    async def generate_response(
        self, 
        topic: str, 
        options: List[str], 
        context: Dict[str, Any] = None
    ) -> AgentMessage:
        """Generate agent response for the given topic and options"""
        pass
    
    @abstractmethod
    def _build_prompt(
        self, 
        topic: str, 
        options: List[str], 
        context: Dict[str, Any] = None
    ) -> str:
        """Build the prompt for the AI model"""
        pass
    
    async def _generate_with_retry(
        self, 
        prompt: str, 
        max_tokens: int = 128,
        **kwargs
    ) -> str:
        """Generate response with retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = await self.provider.generate_response(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                if response and response.strip():
                    return response
                else:
                    raise ValueError("Empty response from AI provider")
                    
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1} failed for agent {self.agent_id}: {str(e)}"
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
        
        logger.error(f"All retry attempts failed for agent {self.agent_id}")
        raise last_error
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response with error handling"""
        try:
            # Try to extract JSON from response if it's wrapped in text
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # Fallback: try to parse the entire response
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            raise ValueError(f"Invalid JSON response: {str(e)}")
    
    def _create_agent_message(
        self, 
        message: str, 
        choice: Optional[str] = None
    ) -> AgentMessage:
        """Create an AgentMessage object"""
        return AgentMessage(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            message=message,
            timestamp=datetime.utcnow(),
            choice=choice
        )

class DebateAgent(BaseAgent):
    """Agent that participates in debates based on a persona"""
    
    def __init__(
        self, 
        persona: Persona,
        provider: Optional[AIProvider] = None,
        max_retries: int = 3
    ):
        super().__init__(
            agent_id=persona.id,
            agent_name=persona.name,
            provider=provider,
            max_retries=max_retries
        )
        self.persona = persona
    
    async def generate_response(
        self, 
        topic: str, 
        options: List[str], 
        context: Dict[str, Any] = None
    ) -> AgentMessage:
        """Generate debate response based on persona"""
        try:
            prompt = self._build_prompt(topic, options, context)
            
            response = await self._generate_with_retry(
                prompt=prompt,
                max_tokens=128,
                temperature=0.7
            )
            
            # Parse the structured response
            parsed = self._parse_json_response(response)
            
            message = parsed.get('message', '')
            choice = parsed.get('choice', '')
            
            if not message:
                raise ValueError("No message in response")
            
            logger.info(f"Agent {self.agent_id} generated response: {choice}")
            
            return self._create_agent_message(message, choice)
            
        except Exception as e:
            logger.error(f"Error generating response for {self.agent_id}: {str(e)}")
            # Fallback response
            return self._create_agent_message(
                f"申し訳ありません、技術的な問題で意見を述べることができません。",
                options[0] if options else None
            )
    
    def _build_prompt(
        self, 
        topic: str, 
        options: List[str], 
        context: Dict[str, Any] = None
    ) -> str:
        """Build prompt for debate agent"""
        options_str = "、".join(options)
        
        prompt = f"""あなたは「{self.persona.name}」として議論に参加してください。

キャラクター設定:
- 名前: {self.persona.name}
- 性格: {self.persona.persona}
- 話し方: {self.persona.speech_style}
- 重視する要素: {json.dumps(self.persona.weights, ensure_ascii=False)}

議題: {topic}
選択肢: {options_str}

以下のJSON形式で回答してください:
{{
    "message": "あなたの意見や理由を100文字程度で述べてください。キャラクターの性格と話し方を反映させてください。",
    "choice": "選択肢の中から1つを選んでください"
}}

キャラクターになりきって、自然で個性的な回答をしてください。"""
        
        return prompt

class OfficerAgent(BaseAgent):
    """Agent that makes final decisions based on debate results"""
    
    def __init__(
        self, 
        provider: Optional[AIProvider] = None,
        max_retries: int = 3
    ):
        super().__init__(
            agent_id="officer",
            agent_name="議長",
            provider=provider or AIProviderFactory.get_default_provider("officer"),
            max_retries=max_retries
        )
    
    async def generate_decision(
        self, 
        topic: str, 
        options: List[str], 
        debate_messages: List[AgentMessage]
    ) -> Dict[str, Any]:
        """Generate final decision based on debate messages"""
        try:
            prompt = self._build_decision_prompt(topic, options, debate_messages)
            
            response = await self._generate_with_retry(
                prompt=prompt,
                max_tokens=256,
                temperature=0.3
            )
            
            # Parse the structured response
            parsed = self._parse_json_response(response)
            
            final_choice = parsed.get('final_choice', '')
            summary = parsed.get('summary', '')
            confidence = parsed.get('confidence', 0.5)
            
            if not final_choice or final_choice not in options:
                # Fallback: choose the option mentioned most frequently
                final_choice = self._fallback_choice(options, debate_messages)
            
            logger.info(f"Officer decided: {final_choice} (confidence: {confidence})")
            
            return {
                'final_choice': final_choice,
                'summary': summary,
                'confidence': float(confidence)
            }
            
        except Exception as e:
            logger.error(f"Error generating decision: {str(e)}")
            # Fallback decision
            return {
                'final_choice': self._fallback_choice(options, debate_messages),
                'summary': '技術的な問題により、簡単な集計に基づいて決定しました。',
                'confidence': 0.3
            }
    
    def _build_decision_prompt(
        self, 
        topic: str, 
        options: List[str], 
        debate_messages: List[AgentMessage]
    ) -> str:
        """Build prompt for decision making"""
        options_str = "、".join(options)
        
        # Format debate messages
        debate_summary = ""
        for msg in debate_messages:
            debate_summary += f"- {msg.agent_name}: {msg.message}"
            if msg.choice:
                debate_summary += f" (選択: {msg.choice})"
            debate_summary += "\n"
        
        prompt = f"""議論の内容を総合的に判断し、最終決定を行ってください。

議題: {topic}
選択肢: {options_str}

議論の内容:
{debate_summary}

各参加者の意見を公平に検討し、以下のJSON形式で最終決定を行ってください:

{{
    "final_choice": "選択肢の中から1つを選択",
    "summary": "決定理由を150文字程度で説明してください。各参加者の意見をどう考慮したかを含めてください。",
    "confidence": 0.8
}}

confidence は 0.0 から 1.0 の間で、この決定への確信度を示してください。
全体的なバランスを考慮した、公正で合理的な判断をしてください。"""
        
        return prompt
    
    def _fallback_choice(
        self, 
        options: List[str], 
        debate_messages: List[AgentMessage]
    ) -> str:
        """Fallback choice selection based on frequency"""
        choice_counts = {option: 0 for option in options}
        
        for msg in debate_messages:
            if msg.choice and msg.choice in choice_counts:
                choice_counts[msg.choice] += 1
        
        # Return the most frequently chosen option
        return max(choice_counts, key=choice_counts.get)
    
    async def generate_response(
        self, 
        topic: str, 
        options: List[str], 
        context: Dict[str, Any] = None
    ) -> AgentMessage:
        """Not used for OfficerAgent - use generate_decision instead"""
        raise NotImplementedError("OfficerAgent uses generate_decision method")
    
    def _build_prompt(
        self, 
        topic: str, 
        options: List[str], 
        context: Dict[str, Any] = None
    ) -> str:
        """Not used for OfficerAgent"""
        raise NotImplementedError("OfficerAgent uses _build_decision_prompt method")