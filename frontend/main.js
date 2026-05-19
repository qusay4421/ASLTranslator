const electron = require('electron')
const app = electron.app
const BrowserWindow = electron.BrowserWindow
const path = require('path')
const { spawn } = require('child_process')
const http = require('http')

const isDev = !app.isPackaged && process.env.NODE_ENV !== 'production'

let backendProcess = null
let mainWindow = null

// Resolve paths for Python and the backend entry point.
// In dev: use the venv Python and the source backend/.
// In packaged: use the frozen backend exe bundled by PyInstaller.
function getBackendCommand() {
  if (app.isPackaged) {
    // PyInstaller one-file exe is placed next to the app resources
    const exe = path.join(process.resourcesPath, 'backend', 'backend.exe')
    return { cmd: exe, args: [], cwd: path.join(process.resourcesPath, 'backend') }
  }
  // Dev: venv python running uvicorn
  const python = path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe')
  const backendDir = path.join(__dirname, '..', 'backend')
  return { cmd: python, args: ['-m', 'uvicorn', 'main:app', '--port', '8000'], cwd: backendDir }
}

function startBackend() {
  const { cmd, args, cwd } = getBackendCommand()
  const env = Object.assign({}, process.env, {
    TF_CPP_MIN_LOG_LEVEL: '3',
    TF_ENABLE_ONEDNN_OPTS: '0',
  })
  backendProcess = spawn(cmd, args, { cwd, env, windowsHide: true })
  backendProcess.on('error', err => console.error('Backend spawn error:', err))
  backendProcess.stderr.on('data', d => process.stdout.write(d))
}

function waitForBackend(retries, resolve, reject) {
  http.get('http://localhost:8000/health', res => {
    if (res.statusCode === 200) return resolve()
    retry()
  }).on('error', retry)

  function retry() {
    if (retries <= 0) return reject(new Error('Backend did not start in time'))
    setTimeout(() => waitForBackend(retries - 1, resolve, reject), 500)
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
    mainWindow.show()
  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'))
    mainWindow.once('ready-to-show', () => mainWindow.show())
  }
}

app.whenReady().then(async () => {
  if (!isDev) {
    startBackend()
    try {
      await new Promise((resolve, reject) => waitForBackend(30, resolve, reject))
    } catch (err) {
      console.error('Could not reach backend:', err.message)
    }
  }
  createWindow()
})

app.on('window-all-closed', () => {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
