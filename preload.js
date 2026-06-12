const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  getWeather: () => ipcRenderer.invoke('get-weather'),
});
