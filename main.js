const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  const { screen } = require('electron');
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width } = primaryDisplay.bounds;

  mainWindow = new BrowserWindow({
    width: 400,
    height: 50,
    minWidth: 400,
    minHeight: 50,
    maxWidth: 400,
    maxHeight: 50,
    x: Math.floor(width / 2) - 250,
    y: 20,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    roundedCorners: true,
  });

  mainWindow.loadFile(path.join(__dirname, 'src', 'index.html'));
}

ipcMain.handle('get-weather', async () => {
  try {
    const fetch = (await import('node-fetch')).default;

    const geoRes = await fetch('http://ip-api.com/json/');
    const geo = await geoRes.json();

    if (geo.status !== 'success') return null;

    const { lat, lon, city } = geo;

    const weatherRes = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weathercode&temperature_unit=celsius`
    );
    const weather = await weatherRes.json();

    const temp = Math.round(weather.current.temperature_2m);
    const code = weather.current.weathercode;

    const category = weatherCodeToCategory(code);

    return { temp, category };
  } catch (error) {
    console.error('Error fetching weather:', error);
    return null;
  }
});

function weatherCodeToCategory(code) {
  if (code === 0) return 'clear';
  if (code <= 2) return 'partly-cloudy';
  if (code === 3) return 'cloudy';
  if (code <= 49) return 'fog';
  if (code <= 67) return 'rain';
  if (code <= 77) return 'snow';
  if (code <= 82) return 'rain';
  if (code <= 86) return 'snow';
  if (code <= 99) return 'thunderstorm';
  return 'clear';
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) createWindow();
});
