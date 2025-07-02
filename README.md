# 🐱 NekoMimi Council

AI-powered debate system where multiple AI personas discuss topics and reach decisions through collaborative reasoning.

## 📋 Overview

NekoMimi Council is a real-time debate system that features:

- **Multiple AI Personas**: 10 unique AI characters with distinct personalities and decision-making preferences
- **Dual AI Provider Support**: Compatible with both OpenAI and Anthropic APIs
- **Real-time Debate Visualization**: Watch AI personas debate in real-time through a web interface
- **Intelligent Decision Making**: An AI Officer synthesizes all arguments to reach final conclusions
- **WebSocket Communication**: Live updates as debates unfold

## 🏗️ Architecture

```
Browser (Next.js) ↔ FastAPI + Socket.IO ↔ AI Agents ↔ OpenAI/Anthropic APIs
```

- **Backend**: FastAPI with Socket.IO for real-time communication
- **Frontend**: Next.js 14 with TypeScript
- **AI Agents**: 3 DebateAgents + 1 OfficerAgent powered by LLM APIs
- **Storage**: In-memory (MVP) - results persist until server restart

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
2. Enter a debate topic (e.g., "今日のランチはどこにする？")
3. Add options separated by commas (e.g., "寿司屋A, ラーメン店B, カフェC")
4. Click "議論開始" to start the debate
5. Watch AI personas discuss in real-time
6. See the final decision with reasoning and confidence score

### CLI Testing

Test the system directly via command line:

```bash
python scripts/run_cli_poc.py \
  --topic "今日のランチはどこにする？" \
  --options "寿司屋A,ラーメン店B,カフェC"
```

### API Usage

Start a debate via REST API:

```bash
curl -X POST http://localhost:8001/api/debate \
  -H "Content-Type: application/json" \
  -d '{"topic": "今日のランチはどこにする？", "options": ["寿司屋A", "ラーメン店B", "カフェC"]}'
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

## 📁 Project Structure

```
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── models/         # Pydantic models
│   │   ├── agents/         # AI agent implementations
│   │   ├── api/           # FastAPI routes and Socket.IO
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
│   └── personas/          # AI persona definitions
├── docker/                # Dockerfiles
├── scripts/               # Utility scripts
├── docker-compose.yml     # Development environment
└── CLAUDE.md             # Claude Code development guide
```

## 🔌 API Endpoints

### REST API

- `POST /api/debate` - Start new debate session
- `GET /api/debate/{id}` - Get debate results
- `GET /api/health` - Health check

### WebSocket Events

- `agent_message` - Real-time agent contributions
- `decision` - Final decision from OfficerAgent
- `status_update` - Debate status changes
- `error` - Error notifications

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

- **Response Time**: <10 seconds per debate
- **Cost**: <$0.05 per debate session  
- **Reliability**: 99% uptime during operation
- **Concurrency**: Up to 5 simultaneous debates

## 🛠️ Troubleshooting

### Common Issues

1. **Port already in use**: Change ports in `docker-compose.yml`
2. **API key errors**: Verify keys in `.env` file
3. **Container startup failures**: Check Docker logs with `docker compose logs`

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