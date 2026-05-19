const electron = require('electron')
const app = electron.app
const BrowserWindow = electron.BrowserWindow

console.log('app type:', typeof app)
console.log('BrowserWindow type:', typeof BrowserWindow)

if (app) {
  app.whenReady().then(() => {
    console.log('Electron ready! isPackaged:', app.isPackaged)
    app.quit()
  })
} else {
  console.log('app is undefined - electron module returned:', typeof electron, JSON.stringify(electron).slice(0, 100))
  process.exit(1)
}
