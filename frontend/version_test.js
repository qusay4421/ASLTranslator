console.log('node:', process.version)
console.log('electron:', process.versions.electron)
console.log('chrome:', process.versions.chrome)
setTimeout(() => process.exit(0), 100)
