const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  moveWindow: (x, y) => ipcRenderer.send('move-window', { x, y }),
  getWindowPosition: (callback) => ipcRenderer.invoke('get-window-position').then(callback),
  getSpotifyTrack: () => ipcRenderer.invoke('get-spotify-track'),
  openSpotifyAuth: () => ipcRenderer.invoke('open-spotify-auth'),
});
