import { useState, useEffect, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'

interface AgentMessage {
  agent_id: string
  agent_name: string
  message: string
  timestamp: string
  choice?: string
  message_type: string
  target_agent?: string
  round_number: number
}

interface RoundStart {
  round_number: number
  description: string
}

interface DebateResult {
  final_choice?: string
  summary?: string
  confidence?: number
}

export function useDebate() {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isDebating, setIsDebating] = useState(false)
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [result, setResult] = useState<DebateResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [rounds, setRounds] = useState<RoundStart[]>([])
  const [currentRound, setCurrentRound] = useState<number>(0)

  useEffect(() => {
    const newSocket = io(process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000', {
      transports: ['websocket', 'polling']
    })

    newSocket.on('connect', () => {
      console.log('Connected to server')
      setIsConnected(true)
      setError(null)
    })

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server')
      setIsConnected(false)
    })

    newSocket.on('connect_error', (err) => {
      console.error('Connection error:', err)
      setError('サーバーに接続できません')
      setIsConnected(false)
    })

    newSocket.on('agent_message', (message: AgentMessage) => {
      console.log('Received agent message:', message)
      setMessages(prev => [...prev, message])
    })

    newSocket.on('round_start', (roundInfo: RoundStart) => {
      console.log('Round started:', roundInfo)
      setCurrentRound(roundInfo.round_number)
      
      // Add round separator message
      const roundMessage: AgentMessage = {
        agent_id: 'system',
        agent_name: '📢 システム',
        message: `${roundInfo.description}を開始します`,
        timestamp: new Date().toISOString(),
        message_type: 'round_start',
        round_number: roundInfo.round_number
      }
      setMessages(prev => [...prev, roundMessage])
    })

    newSocket.on('decision', (decision: DebateResult) => {
      console.log('Received decision:', decision)
      setResult(decision)
      setIsDebating(false)
      setCurrentRound(6)
    })

    newSocket.on('error', (errorMessage: string) => {
      console.error('Debate error:', errorMessage)
      setError(errorMessage)
      setIsDebating(false)
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [])

  const startDebate = useCallback(async (topic: string, options: string[]) => {
    if (!socket || !isConnected) {
      setError('サーバーに接続されていません')
      return
    }

    try {
      setIsDebating(true)
      setMessages([])
      setResult(null)
      setError(null)
      setCurrentRound(0)
      setRounds([])

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/debate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic, options }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log('Debate started:', data)

      // Join the debate room
      socket.emit('join_room', `debate-${data.id}`)

    } catch (err) {
      console.error('Error starting debate:', err)
      setError('議論の開始に失敗しました')
      setIsDebating(false)
    }
  }, [socket, isConnected])

  return {
    isConnected,
    isDebating,
    messages,
    result,
    error,
    rounds,
    currentRound,
    startDebate
  }
}