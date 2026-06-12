const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

let mainWindow;
let spotifyAccessToken = null;
let spotifyRefreshToken = null;

const CLIENT_ID = process.env.SPOTIFY_CLIENT_ID;
const CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET;
const REDIRECT_URI = 'http://localhost:3000/callback';

function createWindow() {
  const { screen } = require('electron');
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width } = primaryDisplay.bounds;

  mainWindow = new BrowserWindow({
    width: 400,
    height: 250,
    x: Math.floor(width / 2) - 200,
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
  });

  mainWindow.loadFile(path.join(__dirname, 'src', 'index.html'));
}

async function getSpotifyCurrentTrack() {
  if (!spotifyAccessToken) return null;

  try {
    const fetch = (await import('node-fetch')).default;
    const response = await fetch('https://api.spotify.com/v1/me/player/currently-playing', {
      headers: {
        'Authorization': `Bearer ${spotifyAccessToken}`,
      },
    });

    if (response.status === 401) {
      spotifyAccessToken = null;
      return null;
    }

    if (!response.ok || response.status === 204) return null;

    const data = await response.json();
    if (!data.item) return null;

    return {
      name: data.item.name,
      artist: data.item.artists.map(a => a.name).join(', '),
      uri: data.item.uri,
    };
  } catch (error) {
    console.error('Error fetching Spotify track:', error);
    return null;
  }
}

ipcMain.on('move-window', (event, { x, y }) => {
  mainWindow.setPosition(x, y);
});

ipcMain.handle('get-window-position', async () => {
  const [x, y] = mainWindow.getPosition();
  return [x, y];
});

ipcMain.handle('get-spotify-track', async () => {
  return await getSpotifyCurrentTrack();
});

ipcMain.handle('open-spotify-auth', async () => {
  if (!CLIENT_ID || !CLIENT_SECRET) {
    shell.openExternal('https://developer.spotify.com/dashboard/applications');
    return;
  }

  const scopes = 'user-read-currently-playing';
  const authUrl = `https://accounts.spotify.com/authorize?client_id=${CLIENT_ID}&response_type=code&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&scope=${encodeURIComponent(scopes)}`;
  shell.openExternal(authUrl);
});

app.on('ready', createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
