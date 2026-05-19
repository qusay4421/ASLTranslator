import React, { useEffect, useRef, useState } from 'react'
import Peer from 'peerjs'

const FRAME_INTERVAL_MS = 100

function makeRoomId() {
  return Math.random().toString(36).substring(2, 8).toUpperCase()
}

export default function VideoCall({ isCameraOn, isMuted, onFrame, onStart }) {
  const [peerId, setPeerId] = useState('')
  const [remotePeerId, setRemotePeerId] = useState('')
  const [callStatus, setCallStatus] = useState('idle') // idle | calling | connected
  const [copied, setCopied] = useState(false)

  const localVideoRef = useRef(null)
  const remoteVideoRef = useRef(null)
  const streamRef = useRef(null)
  const peerRef = useRef(null)
  const callRef = useRef(null)
  const canvasRef = useRef(document.createElement('canvas'))
  const intervalRef = useRef(null)

  useEffect(() => {
    startCamera().then(() => {
      const peer = new Peer(makeRoomId())
      peerRef.current = peer

      peer.on('open', id => setPeerId(id))

      peer.on('call', incoming => {
        if (!streamRef.current) return
        incoming.answer(streamRef.current)
        callRef.current = incoming
        setCallStatus('connected')
        incoming.on('stream', remote => {
          if (remoteVideoRef.current) remoteVideoRef.current.srcObject = remote
        })
        incoming.on('close', () => {
          setCallStatus('idle')
          if (remoteVideoRef.current) remoteVideoRef.current.srcObject = null
        })
      })

      peer.on('error', err => console.error('PeerJS error:', err))
    })

    onStart()

    return () => {
      clearInterval(intervalRef.current)
      streamRef.current?.getTracks().forEach(t => t.stop())
      peerRef.current?.destroy()
    }
  }, [])

  useEffect(() => {
    streamRef.current?.getVideoTracks().forEach(t => { t.enabled = isCameraOn })
    streamRef.current?.getAudioTracks().forEach(t => { t.enabled = !isMuted })
  }, [isCameraOn, isMuted])

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      streamRef.current = stream
      if (localVideoRef.current) localVideoRef.current.srcObject = stream
      startFrameCapture()
    } catch (err) {
      console.error('Camera error:', err)
    }
  }

  const startFrameCapture = () => {
    intervalRef.current = setInterval(() => {
      const video = localVideoRef.current
      if (!video || !isCameraOn || video.readyState < 2) return
      const canvas = canvasRef.current
      canvas.width = video.videoWidth || 640
      canvas.height = video.videoHeight || 480
      canvas.getContext('2d').drawImage(video, 0, 0)
      onFrame(canvas.toDataURL('image/jpeg', 0.7).split(',')[1])
    }, FRAME_INTERVAL_MS)
  }

  const startCall = () => {
    if (!remotePeerId.trim() || !peerRef.current || !streamRef.current) return
    const call = peerRef.current.call(remotePeerId.trim(), streamRef.current)
    callRef.current = call
    setCallStatus('calling')
    call.on('stream', remote => {
      if (remoteVideoRef.current) remoteVideoRef.current.srcObject = remote
      setCallStatus('connected')
    })
    call.on('close', () => {
      setCallStatus('idle')
      if (remoteVideoRef.current) remoteVideoRef.current.srcObject = null
    })
    call.on('error', () => setCallStatus('idle'))
  }

  const hangUp = () => {
    callRef.current?.close()
    if (remoteVideoRef.current) remoteVideoRef.current.srcObject = null
    setCallStatus('idle')
  }

  const copyId = () => {
    navigator.clipboard.writeText(peerId).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: '#111' }}>
      {/* Remote video — full screen during call */}
      <video
        ref={remoteVideoRef}
        autoPlay
        playsInline
        style={{
          width: '100%', height: '100%', objectFit: 'cover',
          display: callStatus === 'connected' ? 'block' : 'none',
        }}
      />

      {/* Lobby screen */}
      {callStatus !== 'connected' && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex',
          flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          color: '#fff', gap: 24,
        }}>
          <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: 1 }}>ASL Translator</div>
          <div style={{ fontSize: 13, opacity: 0.55 }}>
            Share your Room ID with the person you want to call
          </div>

          {/* Your room ID */}
          <div style={{
            background: 'rgba(255,255,255,0.08)', padding: '16px 36px',
            borderRadius: 12, textAlign: 'center', cursor: 'pointer',
            border: '1px solid rgba(255,255,255,0.15)',
          }} onClick={copyId} title="Click to copy">
            <div style={{ fontSize: 11, opacity: 0.5, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 2 }}>
              Your Room ID
            </div>
            <div style={{ fontFamily: 'monospace', fontSize: 28, letterSpacing: 6, fontWeight: 700 }}>
              {peerId || '…'}
            </div>
            <div style={{ fontSize: 11, opacity: 0.4, marginTop: 6 }}>
              {copied ? '✓ Copied!' : 'Click to copy'}
            </div>
          </div>

          {/* Call input */}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input
              value={remotePeerId}
              onChange={e => setRemotePeerId(e.target.value.toUpperCase())}
              onKeyDown={e => e.key === 'Enter' && startCall()}
              placeholder="Enter partner's Room ID"
              maxLength={6}
              style={{
                padding: '11px 16px', borderRadius: 8,
                border: '1px solid rgba(255,255,255,0.25)',
                background: 'rgba(255,255,255,0.08)', color: '#fff',
                fontSize: 15, width: 230, outline: 'none',
                fontFamily: 'monospace', letterSpacing: 3, textTransform: 'uppercase',
              }}
            />
            <button
              onClick={startCall}
              disabled={callStatus === 'calling' || !remotePeerId.trim()}
              style={{
                padding: '11px 24px', borderRadius: 8, border: 'none',
                background: callStatus === 'calling' ? '#555' : '#22c55e',
                color: '#fff', fontSize: 14, cursor: callStatus === 'calling' ? 'default' : 'pointer',
                fontWeight: 600,
              }}
            >
              {callStatus === 'calling' ? 'Calling…' : '📞 Call'}
            </button>
          </div>
        </div>
      )}

      {/* Local video — picture-in-picture */}
      <video
        ref={localVideoRef}
        autoPlay
        muted
        playsInline
        style={{
          position: 'absolute', bottom: 90, right: 16,
          width: 192, height: 144, objectFit: 'cover',
          borderRadius: 10, border: '2px solid rgba(255,255,255,0.25)',
          background: '#000',
        }}
      />

      {/* Hang up */}
      {callStatus === 'connected' && (
        <button onClick={hangUp} title="Hang up" style={{
          position: 'absolute', top: 16, right: 16,
          background: 'rgba(220,38,38,0.9)', border: 'none',
          borderRadius: '50%', width: 46, height: 46,
          color: '#fff', fontSize: 20, cursor: 'pointer',
        }}>
          ✕
        </button>
      )}
    </div>
  )
}
