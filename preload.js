const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  moveWindow: (x, y) => ipcRenderer.send('move-window', { x, y }),
  getWindowPosition: (callback) => ipcRenderer.invoke('get-window-position').then(callback),
});
