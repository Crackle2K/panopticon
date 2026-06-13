const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  getWeather: () => ipcRenderer.invoke('get-weather'),
  getConfig: () => ipcRenderer.invoke('get-config'),
  setConfig: (patch) => ipcRenderer.invoke('set-config', patch),
  showContextMenu: () => ipcRenderer.invoke('show-context-menu'),
  onConfigChanged: (callback) =>
    ipcRenderer.on('config-changed', (_event, config) => callback(config)),
});
