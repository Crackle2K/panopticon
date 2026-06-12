const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  // We can add IPC calls here later
});
