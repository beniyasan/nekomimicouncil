#!/usr/bin/env python3
"""
CLI Proof of Concept for NekoMimi Council
Usage: python scripts/run_cli_poc.py --topic "ランチどこ行く?" --options "寿司A,ラーメンB,カフェC"
"""

import asyncio
import argparse
import json
import random
import sys
import os
from pathlib import Path

# Add backend to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.models.debate import Persona
from backend.app.agents.base import DebateAgent, OfficerAgent
from backend.app.agents.providers import AIProviderFactory
from backend.app.config import settings

async def load_personas(count: int = 3) -> list[Persona]:
    """Load personas from JSON file"""
    personas_file = Path(__file__).parent.parent / "data" / "personas" / "personas.json"
    
    if not personas_file.exists():
        raise FileNotFoundError(f"Personas file not found: {personas_file}")
    
    with open(personas_file, 'r', encoding='utf-8') as f:
        personas_data = json.load(f)
    
    # Convert to Persona objects
    personas = [Persona(**data) for data in personas_data]
    
    # Randomly select the specified number of personas
    selected = random.sample(personas, min(count, len(personas)))
    
    return selected

async def run_debate(topic: str, options: list[str], num_agents: int = 3):
    """Run a complete debate simulation"""
    
    print(f"🐱 NekoMimi Council - CLI PoC")
    print(f"議題: {topic}")
    print(f"選択肢: {', '.join(options)}")
    print(f"エージェント数: {num_agents}")
    print(f"AIプロバイダー: {settings.ai_provider}")
    print("-" * 50)
    
    try:
        # Load personas
        print("📝 人格を読み込み中...")
        personas = await load_personas(num_agents)
        
        # Create debate agents
        print("🤖 AIエージェントを初期化中...")
        debate_agents = []
        
        for persona in personas:
            try:
                provider = AIProviderFactory.get_default_provider("debate")
                agent = DebateAgent(persona, provider)
                debate_agents.append(agent)
                print(f"  ✓ {persona.name} ({persona.id})")
            except Exception as e:
                print(f"  ✗ {persona.name} の初期化に失敗: {str(e)}")
        
        if not debate_agents:
            raise ValueError("使用可能なエージェントがありません")
        
        # Create officer agent
        print("👑 議長を初期化中...")
        try:
            officer_provider = AIProviderFactory.get_default_provider("officer")
            officer = OfficerAgent(officer_provider)
            print("  ✓ 議長 (officer)")
        except Exception as e:
            print(f"  ✗ 議長の初期化に失敗: {str(e)}")
            return
        
        print("\n💭 議論開始...")
        
        # Run debate in parallel
        debate_tasks = []
        for agent in debate_agents:
            task = agent.generate_response(topic, options)
            debate_tasks.append(task)
        
        # Wait for all agents to respond
        debate_messages = await asyncio.gather(*debate_tasks, return_exceptions=True)
        
        # Process results
        valid_messages = []
        for i, result in enumerate(debate_messages):
            if isinstance(result, Exception):
                print(f"  ✗ {debate_agents[i].agent_name}: エラー - {str(result)}")
            else:
                valid_messages.append(result)
                print(f"  💬 {result.agent_name}: {result.message}")
                if result.choice:
                    print(f"     → 選択: {result.choice}")
        
        if not valid_messages:
            print("❌ 有効な議論メッセージがありませんでした")
            return
        
        print("\n👑 議長による最終決定...")
        
        # Officer makes final decision
        try:
            decision = await officer.generate_decision(topic, options, valid_messages)
            
            print("\n" + "=" * 50)
            print("🎉 最終決定")
            print("=" * 50)
            
            result = {
                "final_choice": decision["final_choice"],
                "summary": decision["summary"],
                "confidence": decision["confidence"]
            }
            
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            return result
            
        except Exception as e:
            print(f"❌ 議長の決定に失敗: {str(e)}")
            return None
    
    except Exception as e:
        print(f"❌ 議論の実行に失敗: {str(e)}")
        return None

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="NekoMimi Council CLI PoC")
    parser.add_argument("--topic", required=True, help="議論のトピック")
    parser.add_argument("--options", required=True, help="選択肢（カンマ区切り）")
    parser.add_argument("--agents", type=int, default=3, help="エージェント数 (デフォルト: 3)")
    
    args = parser.parse_args()
    
    # Parse options
    options = [opt.strip() for opt in args.options.split(",") if opt.strip()]
    
    if len(options) < 2:
        print("❌ 選択肢は2つ以上指定してください")
        sys.exit(1)
    
    # Check API keys
    available_providers = AIProviderFactory.get_available_providers()
    if not available_providers:
        print("❌ APIキーが設定されていません")
        print("OpenAI または Anthropic のAPIキーを .env ファイルに設定してください")
        sys.exit(1)
    
    print(f"✓ 利用可能なプロバイダー: {', '.join(available_providers)}")
    
    # Run the debate
    try:
        result = asyncio.run(run_debate(args.topic, options, args.agents))
        
        if result:
            print("\n✅ 議論が正常に完了しました")
            sys.exit(0)
        else:
            print("\n❌ 議論が失敗しました")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  ユーザーによって中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()