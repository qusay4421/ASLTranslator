import React, { useState, useRef } from 'react'
import VideoCall from './components/VideoCall'
import Translator from './components/Translator'
import Controls from './components/Controls'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

export default function App() {
  const [translation, setTranslation] = useState({ sign: '', confidence: 0, sentence: '' })
  const [isMuted, setIsMuted] = useState(false)
  const [isCameraOn, setIsCameraOn] = useState(true)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef(null)

  const connectWebSocket = () => {
    const ws = new WebSocket(WS_URL)
    ws.onopen = () => setIsConnected(true)
    ws.onclose = () => setIsConnected(false)
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'translation') {
        setTranslation({ sign: data.sign, confidence: data.confidence, sentence: data.sentence })
      }
    }
    wsRef.current = ws
  }

  const sendFrame = (base64Frame) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'frame', data: base64Frame }))
    }
  }

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', background: '#111' }}>
      <VideoCall
        isCameraOn={isCameraOn}
        isMuted={isMuted}
        onFrame={sendFrame}
        onStart={connectWebSocket}
      />
      <Translator translation={translation} isConnected={isConnected} />
      <Controls
        isMuted={isMuted}
        isCameraOn={isCameraOn}
        onToggleMute={() => setIsMuted(m => !m)}
        onToggleCamera={() => setIsCameraOn(c => !c)}
      />
    </div>
  )
}
