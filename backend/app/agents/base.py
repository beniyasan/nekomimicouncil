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
        self.search_context = None  # Web search results context
    
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
        choice: Optional[str] = None,
        message_type: str = "initial_opinion",
        target_agent: Optional[str] = None,
        round_number: int = 1
    ) -> AgentMessage:
        """Create an AgentMessage object"""
        return AgentMessage(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            message=message,
            timestamp=datetime.utcnow(),
            choice=choice,
            message_type=message_type,
            target_agent=target_agent,
            round_number=round_number
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
            
            return self._create_agent_message(
                message, 
                choice, 
                message_type="initial_opinion",
                round_number=1
            )
            
        except Exception as e:
            logger.error(f"Error generating response for {self.agent_id}: {str(e)}")
            # Fallback response
            return self._create_agent_message(
                f"申し訳ありません、技術的な問題で意見を述べることができません。",
                options[0] if options else None,
                message_type="initial_opinion",
                round_number=1
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
選択肢: {options_str}"""

        # Add web search context if available
        if self.search_context:
            prompt += "\n\n実際の店舗情報（Web検索結果）:\n"
            for store_name, store_data in self.search_context.items():
                info = store_data.get('info', {})
                prompt += f"\n【{store_name}】\n"
                if info.get('description'):
                    prompt += f"- 概要: {info['description']}\n"
                if info.get('location'):
                    prompt += f"- 場所: {info['location']}\n"
                if info.get('hours'):
                    prompt += f"- 営業時間: {info['hours']}\n"
                if info.get('price_range'):
                    prompt += f"- 価格帯: {info['price_range']}\n"
                if info.get('rating'):
                    prompt += f"- 評価: {info['rating']}\n"

        prompt += """

以下のJSON形式で回答してください:
{
    "message": "あなたの意見や理由を100文字程度で述べてください。キャラクターの性格と話し方を反映させてください。",
    "choice": "選択肢の中から1つを選んでください"
}

キャラクターになりきって、自然で個性的な回答をしてください。"""
        
        return prompt
    
    async def ask_question(
        self,
        topic: str,
        options: List[str],
        other_messages: List[AgentMessage],
        round_number: int = 2
    ) -> AgentMessage:
        """Ask a question to another agent based on their previous statements"""
        try:
            prompt = self._build_question_prompt(topic, options, other_messages)
            
            response = await self._generate_with_retry(
                prompt=prompt,
                max_tokens=128,
                temperature=0.8
            )
            
            parsed = self._parse_json_response(response)
            question = parsed.get('question', '')
            target_agent = parsed.get('target_agent', '')
            
            if not question:
                raise ValueError("No question generated")
            
            # Ensure target_agent is set - fallback to first available agent
            if not target_agent and other_messages:
                available_agents = [msg.agent_id for msg in other_messages 
                                  if msg.agent_id != self.agent_id and msg.message_type == "initial_opinion"]
                if available_agents:
                    target_agent = available_agents[0]
                    logger.info(f"No target_agent specified, falling back to {target_agent}")
            
            return self._create_agent_message(
                question,
                message_type="question",
                target_agent=target_agent,
                round_number=round_number
            )
            
        except Exception as e:
            logger.error(f"Error generating question for {self.agent_id}: {str(e)}")
            return None
    
    async def respond_to_question(
        self,
        topic: str,
        options: List[str],
        question_message: AgentMessage,
        all_messages: List[AgentMessage],
        round_number: int = 3
    ) -> AgentMessage:
        """Respond to a question from another agent"""
        try:
            prompt = self._build_response_prompt(topic, options, question_message, all_messages)
            
            response = await self._generate_with_retry(
                prompt=prompt,
                max_tokens=128,
                temperature=0.7
            )
            
            parsed = self._parse_json_response(response)
            answer = parsed.get('answer', '')
            choice = parsed.get('choice', '')
            
            if not answer:
                raise ValueError("No answer generated")
            
            return self._create_agent_message(
                answer,
                choice=choice,
                message_type="response",
                target_agent=question_message.agent_id,
                round_number=round_number
            )
            
        except Exception as e:
            logger.error(f"Error responding to question for {self.agent_id}: {str(e)}")
            return self._create_agent_message(
                f"申し訳ありません、質問にお答えできません。",
                message_type="response",
                target_agent=question_message.agent_id,
                round_number=round_number
            )
    
    async def final_opinion(
        self,
        topic: str,
        options: List[str],
        all_messages: List[AgentMessage],
        round_number: int = 5
    ) -> AgentMessage:
        """Give final opinion after hearing all discussions"""
        try:
            prompt = self._build_final_opinion_prompt(topic, options, all_messages)
            
            response = await self._generate_with_retry(
                prompt=prompt,
                max_tokens=128,
                temperature=0.6
            )
            
            parsed = self._parse_json_response(response)
            message = parsed.get('message', '')
            choice = parsed.get('choice', '')
            
            if not message:
                raise ValueError("No final opinion generated")
            
            return self._create_agent_message(
                message,
                choice=choice,
                message_type="final_opinion",
                round_number=round_number
            )
            
        except Exception as e:
            logger.error(f"Error generating final opinion for {self.agent_id}: {str(e)}")
            return self._create_agent_message(
                f"申し訳ありません、最終意見を述べることができません。",
                choice=options[0] if options else None,
                message_type="final_opinion",
                round_number=round_number
            )
    
    def _build_question_prompt(
        self,
        topic: str,
        options: List[str],
        other_messages: List[AgentMessage]
    ) -> str:
        """Build prompt for asking questions"""
        options_str = "、".join(options)
        
        # Format other agents' messages with agent_id for targeting
        other_opinions = ""
        available_agents = []
        for msg in other_messages:
            if msg.agent_id != self.agent_id and msg.message_type == "initial_opinion":
                other_opinions += f"- {msg.agent_name} (ID: {msg.agent_id}): {msg.message}"
                if msg.choice:
                    other_opinions += f" (選択: {msg.choice})"
                other_opinions += "\n"
                available_agents.append(f"{msg.agent_id} ({msg.agent_name})")
        
        available_agents_str = "、".join(available_agents)
        
        prompt = f"""あなたは「{self.persona.name}」として議論に参加しています。

キャラクター設定:
- 名前: {self.persona.name}
- 性格: {self.persona.persona}
- 話し方: {self.persona.speech_style}

議題: {topic}
選択肢: {options_str}

他の参加者の意見:
{other_opinions}

他の参加者の意見を聞いて、あなたのキャラクターとして疑問に思った点や詳しく聞きたい点について質問してください。

質問可能な参加者: {available_agents_str}

以下のJSON形式で回答してください:
{{
    "question": "質問内容を80文字程度で。キャラクターの話し方で自然に。",
    "target_agent": "質問したい相手のagent_id (上記のIDから必ず選択)"
}}

建設的で興味深い質問をしてください。"""
        
        return prompt
    
    def _build_response_prompt(
        self,
        topic: str,
        options: List[str],
        question_message: AgentMessage,
        all_messages: List[AgentMessage]
    ) -> str:
        """Build prompt for responding to questions"""
        options_str = "、".join(options)
        
        prompt = f"""あなたは「{self.persona.name}」として議論に参加しています。

キャラクター設定:
- 名前: {self.persona.name}
- 性格: {self.persona.persona}
- 話し方: {self.persona.speech_style}

議題: {topic}
選択肢: {options_str}

{question_message.agent_name}からの質問:
「{question_message.message}」

この質問にあなたのキャラクターとして答えてください。

以下のJSON形式で回答してください:
{{
    "answer": "質問への回答を100文字程度で。キャラクターの話し方で自然に。",
    "choice": "現時点での選択肢（変更があれば更新）"
}}

誠実かつキャラクターらしい回答をしてください。"""
        
        return prompt
    
    def _build_final_opinion_prompt(
        self,
        topic: str,
        options: List[str],
        all_messages: List[AgentMessage]
    ) -> str:
        """Build prompt for final opinion"""
        options_str = "、".join(options)
        
        # Summarize the discussion
        discussion_summary = ""
        for msg in all_messages:
            if msg.agent_id != self.agent_id:
                discussion_summary += f"- {msg.agent_name} ({msg.message_type}): {msg.message[:50]}...\n"
        
        prompt = f"""あなたは「{self.persona.name}」として議論に参加しています。

キャラクター設定:
- 名前: {self.persona.name}
- 性格: {self.persona.persona}
- 話し方: {self.persona.speech_style}

議題: {topic}
選択肢: {options_str}

これまでの議論:
{discussion_summary}

全ての議論を聞いた上で、あなたの最終的な意見を述べてください。
他の人の意見で考えが変わった部分があれば言及してください。

以下のJSON形式で回答してください:
{{
    "message": "最終意見を120文字程度で。他の人の意見への反応も含めて。",
    "choice": "最終的な選択肢"
}}

熟慮した最終判断を示してください。"""
        
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
    
    async def ask_clarifying_questions(
        self,
        topic: str,
        options: List[str],
        debate_messages: List[AgentMessage],
        round_number: int = 4
    ) -> List[AgentMessage]:
        """Ask clarifying questions to specific agents"""
        questions = []
        
        # Find agents with unclear or conflicting positions
        agent_positions = {}
        for msg in debate_messages:
            if msg.message_type in ["initial_opinion", "response"]:
                agent_positions[msg.agent_id] = msg
        
        for agent_id, msg in agent_positions.items():
            try:
                question = await self._generate_officer_question(topic, options, msg, debate_messages)
                if question:
                    questions.append(question)
            except Exception as e:
                logger.error(f"Error generating officer question for {agent_id}: {str(e)}")
        
        return questions
    
    async def _generate_officer_question(
        self,
        topic: str,
        options: List[str],
        target_message: AgentMessage,
        all_messages: List[AgentMessage]
    ) -> Optional[AgentMessage]:
        """Generate a clarifying question for a specific agent"""
        try:
            prompt = self._build_officer_question_prompt(topic, options, target_message, all_messages)
            
            response = await self._generate_with_retry(
                prompt=prompt,
                max_tokens=128,
                temperature=0.5
            )
            
            parsed = self._parse_json_response(response)
            question = parsed.get('question', '')
            
            if not question:
                return None
            
            return self._create_agent_message(
                question,
                message_type="officer_question",
                target_agent=target_message.agent_id,
                round_number=4
            )
            
        except Exception as e:
            logger.error(f"Error generating officer question: {str(e)}")
            return None
    
    def _build_officer_question_prompt(
        self,
        topic: str,
        options: List[str],
        target_message: AgentMessage,
        all_messages: List[AgentMessage]
    ) -> str:
        """Build prompt for officer questions"""
        options_str = "、".join(options)
        
        prompt = f"""あなたは議論の議長として、最終決定を下すために必要な情報を収集しています。

議題: {topic}
選択肢: {options_str}

{target_message.agent_name}の発言:
「{target_message.message}」
選択: {target_message.choice}

この発言について、最終決定のためにより詳しく知りたい点や明確にしたい点があれば質問してください。

以下のJSON形式で回答してください:
{{
    "question": "議長として聞きたい質問を80文字程度で。丁寧で公正な口調で。"
}}

建設的で公平な質問をしてください。不要な場合は空文字を返してください。"""
        
        return prompt
    
    def _build_prompt(
        self, 
        topic: str, 
        options: List[str], 
        context: Dict[str, Any] = None
    ) -> str:
        """Not used for OfficerAgent"""
        raise NotImplementedError("OfficerAgent uses _build_decision_prompt method")