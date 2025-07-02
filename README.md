# 🐱 NekoMimi Council

AI-powered multi-round debate system where multiple AI personas engage in interactive discussions and reach decisions through collaborative reasoning.

## 📋 Overview

NekoMimi Council is a real-time multi-round debate system that features:

- **Interactive Multi-Round Discussions**: 6-stage debate process with questions, responses, and moderation
- **Multiple AI Personas**: 10 unique AI characters with distinct personalities and decision-making preferences
- **Avatar-Enhanced Chat**: Each AI persona has a unique avatar displayed in chat for visual engagement
- **Web Search Integration**: Real store information retrieval for realistic debates about actual places
- **Dual AI Provider Support**: Compatible with both OpenAI and Anthropic APIs
- **Real-time Debate Visualization**: Watch AI personas debate in real-time through a web interface
- **Intelligent Decision Making**: An AI Officer moderates discussions and synthesizes all arguments
- **WebSocket Communication**: Live updates as debates unfold with round-by-round progress

## 🏗️ Architecture

```
Browser (Next.js) ↔ FastAPI + Socket.IO ↔ AI Agents ↔ OpenAI/Anthropic APIs
```

- **Backend**: FastAPI with Socket.IO for real-time communication
- **Frontend**: Next.js 14 with TypeScript
- **AI Agents**: 3 DebateAgents + 1 OfficerAgent with interactive questioning capabilities
- **Storage**: In-memory (MVP) - results persist until server restart

## 🎭 Multi-Round Debate Process

The system conducts debates through 6 interactive rounds:

### Round 1: Initial Opinions (初期意見表明)
Each AI persona presents their initial stance on the topic based on their character traits and priorities.

### Round 2: Peer Questions (参加者同士の質疑応答) 
AI personas ask each other clarifying questions about their positions, diving deeper into specific aspects.

### Round 3: Question Responses (質問への回答)
Personas provide detailed answers to questions, potentially revealing new information or perspectives.

### Round 4: Officer Moderation (議長からの質問)
The AI Officer asks targeted questions to gather additional details needed for the final decision.

### Round 5: Final Opinions (最終意見表明)
After hearing all discussions, each persona presents their final stance, which may have evolved from their initial position.

### Round 6: Final Decision (議長による最終決定)
The AI Officer synthesizes all arguments and renders the final decision with reasoning and confidence level.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key and/or Anthropic API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd NekoMimiCouncil

# Copy environment template
cp .env.template .env
```

### 2. Configure Environment Variables

Edit `.env` file and add your API keys:

```bash
# Choose your AI provider strategy
AI_PROVIDER=mixed  # Options: 'openai', 'anthropic', 'mixed'

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_DEBATE=gpt-4o-mini
OPENAI_MODEL_OFFICER=gpt-o3-pro

# Anthropic Configuration  
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL_DEBATE=claude-3-5-haiku-20241022
ANTHROPIC_MODEL_OFFICER=claude-sonnet-4-20250514
```

### 3. Start the Application

```bash
docker compose up --build
```

### 4. Access the Application

- **Web Interface**: http://localhost:3000/playground
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/api/health

## 🎯 Usage

### Web Interface

1. Navigate to http://localhost:3000/playground
2. Enter a debate topic (e.g., "次の休暇の旅行先を決めよう")
3. Add options separated by commas (e.g., "温泉旅館, 海外リゾート, 都市観光")
4. (Optional) Check "Web検索を有効にする" for real store information
5. Click "議論開始" to start the multi-round debate
6. Watch the 6-round interactive discussion unfold with animated avatars:
   - **Round 1**: Initial opinions from each persona
   - **Round 2-3**: Personas ask questions and provide answers
   - **Round 4**: Officer asks clarifying questions
   - **Round 5**: Final opinions after discussion
   - **Round 6**: Officer's final decision
7. See the comprehensive decision with reasoning and confidence score

### 🎨 Visual Features

- **Persona Avatars**: Each AI character displays with a unique 48x48px avatar
- **Message Type Indicators**: Color-coded badges for different message types
- **Real-time Updates**: Smooth chat feed with typing animations
- **Web Search Results**: Visual notification when store information is retrieved

### CLI Testing

Test the system directly via command line:

```bash
python scripts/run_cli_poc.py \
  --topic "次の休暇の旅行先を決めよう" \
  --options "温泉旅館,海外リゾート,都市観光"
```

### API Usage

Start a debate via REST API:

```bash
curl -X POST http://localhost:8001/api/debate \
  -H "Content-Type: application/json" \
  -d '{"topic": "次の休暇の旅行先を決めよう", "options": ["温泉旅館", "海外リゾート", "都市観光"]}'
```

## 🎭 AI Personas

The system includes 10 diverse personas:

| Persona | Characteristics | Priority Factors |
|---------|----------------|------------------|
| 美食家マリア | Gourmet food lover | Taste (70%), Quality |
| 節約家タケシ | Budget-conscious | Price (60%), Quantity |
| ヘルシー志向のユリ | Health-focused | Health (50%), Nutrition |
| トレンド好きアイ | Trend follower | Trendiness (40%), Atmosphere |
| 伝統派のイチロウ | Traditional values | Tradition (50%), Craftsmanship |
| 忙しいサラリーマン サトウ | Time-conscious | Convenience (50%), Speed |
| ファミリー重視のママ ハナコ | Family-oriented | Family-friendly (40%), Safety |
| 冒険家ケン | Adventure seeker | Novelty (50%), Exploration |
| ロマンチックなミユキ | Romantic atmosphere | Atmosphere (50%), Romance |
| 地元愛のジロウ | Local community supporter | Local support (40%), Community |

## 🔧 AI Provider Configuration

### Model Selection Strategies

- **Cost-optimized**: OpenAI GPT-4o-mini for debates, GPT-o3-pro for decisions
- **Quality-optimized**: Anthropic Claude 4.0 Sonnet for OfficerAgent, Claude-3.5-Sonnet for DebateAgents
- **Mixed**: Use different providers for different roles (recommended)

### Fallback Support

The system automatically falls back between providers if one becomes unavailable.

## 💬 Example Multi-Round Discussion

Here's what a typical debate looks like:

**Topic**: "次の休暇の旅行先を決めよう"  
**Options**: 温泉旅館, 海外リゾート, 都市観光

**Round 1** - Initial Opinions:
- 👩‍👧‍👦 ハナコ: "家族みんなで温泉旅館がいいなぁ！"
- 💰 タケシ: "コスパ重視やな！温泉旅館が一番えええと思うで！" 
- 🏠 ジロウ: "やっぱり地元の温泉でゆっくりしたいわけよ。"

**Round 2** - Questions:
- ハナコ→タケシ: "温泉旅館の食事って具体的にどんなメニューがあるん？"
- タケシ→ハナコ: "コスパ的に見てどうなん？"

**Round 3** - Responses:
- タケシ: "鮮魚の刺身や焼き魚、天ぷら、そしてお味噌汁が多いで。子供には..."

**Round 4** - Officer Questions:
- 👑 議長: "ハナコさん、お子様の年齢に応じた遊び場の詳細を教えていただけますか？"

**Round 5** - Final Opinions:
- ハナコ: "やっぱり温泉旅館、家族みんなでゆっくりできるし..."

**Round 6** - Decision:
- 👑 議長: "全員の意見を総合し、温泉旅館を選択します。（信頼度：85%）"

## 📁 Project Structure

```
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── models/         # Pydantic models
│   │   ├── agents/         # AI agent implementations
│   │   ├── api/           # FastAPI routes and Socket.IO
│   │   ├── services/      # Avatar and web search services
│   │   ├── config.py      # Configuration management
│   │   └── main.py        # Application entry point
│   └── requirements.txt   # Python dependencies
├── frontend/               # Next.js application
│   ├── src/
│   │   ├── pages/         # Next.js pages
│   │   ├── components/    # React components
│   │   └── hooks/         # Custom React hooks
│   ├── package.json       # Node.js dependencies
│   └── tsconfig.json      # TypeScript configuration
├── data/
│   ├── personas/          # AI persona definitions
│   └── icon/              # Avatar images (48x48px auto-resized)
├── docker/                # Dockerfiles
├── scripts/               # Utility scripts
├── docker-compose.yml     # Development environment
└── CLAUDE.md             # Claude Code development guide
```

## 🔌 API Endpoints

### REST API

- `POST /api/debate` - Start new debate session
- `GET /api/debate/{id}` - Get debate results
- `GET /api/avatar/{persona_id}` - Get persona avatar image
- `GET /api/avatars` - List all available avatars
- `GET /api/health` - Health check

### WebSocket Events

- `agent_message` - Real-time agent contributions with message type and round information
- `round_start` - New debate round beginning notification
- `decision` - Final decision from OfficerAgent
- `search_results` - Web search results notification
- `status_update` - Debate status changes
- `error` - Error notifications

#### Enhanced Message Structure

Each `agent_message` now includes:
- `message_type`: initial_opinion, question, response, final_opinion, officer_question, decision
- `target_agent`: For questions/responses, indicates the target participant
- `round_number`: Current debate round (1-6)

## 🧪 Development

### Running Tests

```bash
# CLI test
python scripts/run_cli_poc.py --topic "テストトピック" --options "選択肢1,選択肢2"

# API test
curl -X POST http://localhost:8001/api/debate \
  -H "Content-Type: application/json" \
  -d '{"topic": "テスト", "options": ["A", "B"]}'
```

### Adding New Personas

Edit `data/personas/personas.json` to add new AI personas:

```json
{
  "id": "new_persona",
  "name": "新しいペルソナ",
  "persona": "性格の説明",
  "speech_style": "話し方の特徴",
  "weights": {
    "factor1": 0.5,
    "factor2": 0.3
  }
}
```

## 📊 Performance Targets

- **Response Time**: <60 seconds per complete 6-round debate
- **Round Duration**: ~8-12 seconds per round
- **Cost**: <$0.15 per complete debate session (due to increased interaction complexity)
- **Reliability**: 99% uptime during operation
- **Concurrency**: Up to 5 simultaneous debates

## 🛠️ Troubleshooting

### Common Issues

1. **Port already in use**: Change ports in `docker-compose.yml`
2. **API key errors**: Verify keys in `.env` file
3. **Container startup failures**: Check Docker logs with `docker compose logs`
4. **Avatar images not loading**: Ensure avatar files exist in `data/icon/` directory
5. **Web search not working**: Check internet connectivity and search service status

### Debug Mode

Enable debug logging:

```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🚧 Future Enhancements

- [ ] PostgreSQL for persistent storage
- [ ] User authentication (Auth0)
- [ ] Expand to 5 debate agents and 100 personas
- [ ] Custom avatar upload functionality
- [ ] Animated avatar expressions based on emotion analysis
- [ ] Enhanced web search with more data sources
- [ ] PWA capabilities
- [ ] WebSocket reconnection handling
- [ ] Multi-language support
- [ ] Advanced analytics dashboard

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Built with Claude Code (claude.ai/code)
- Powered by OpenAI and Anthropic AI models
- Inspired by collaborative decision-making systems

---

**Generated with Claude Code** 🤖