const { contextBridge } = require('electron')

// Expose a minimal API surface to the renderer.
// WebSocket communication goes directly through the browser's WebSocket API,
// so no IPC bridge is needed for the translation stream.
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
})
