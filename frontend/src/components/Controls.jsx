import React from 'react'

const btnStyle = (active) => ({
  background: active ? 'rgba(255,255,255,0.15)' : 'rgba(220,38,38,0.85)',
  border: 'none',
  borderRadius: '50%',
  width: 52,
  height: 52,
  color: '#fff',
  fontSize: 20,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  transition: 'background 0.2s',
})

export default function Controls({ isMuted, isCameraOn, onToggleMute, onToggleCamera }) {
  return (
    <div style={{
      position: 'absolute',
      bottom: 24,
      left: 0,
      right: 0,
      display: 'flex',
      justifyContent: 'center',
      gap: 16,
    }}>
      <button style={btnStyle(!isMuted)} onClick={onToggleMute} title={isMuted ? 'Unmute' : 'Mute'}>
        {isMuted ? '🔇' : '🎤'}
      </button>
      <button style={btnStyle(isCameraOn)} onClick={onToggleCamera} title={isCameraOn ? 'Camera off' : 'Camera on'}>
        {isCameraOn ? '📷' : '🚫'}
      </button>
    </div>
  )
}
