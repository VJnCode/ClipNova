# ClipNova

## ▶ To start: double-click `Start ClipNova.bat`

That's all. The first time, it installs everything by itself (a few minutes). After that it starts in seconds and
opens **http://127.0.0.1:8766/app** in your browser. Keep the black window open while you use it; close it to stop.

You only need **Python 3.10+** installed first (https://www.python.org/downloads/, tick "Add Python to PATH").
ffmpeg is installed for you.

> **Next: read [SETUP.md](SETUP.md)** for the AI key, backup AIs, the Google Cloud project, test users and the
> redirect URI, connecting YouTube and Instagram, and recording streamers live.

Turn long videos and live streams into captioned vertical clips, ready to post. It runs on your own computer
with your own AI key, and it's free.

Paste a YouTube, Twitch or Kick link, or upload a file. ClipNova finds the moments worth clipping, cuts them to
9:16, and adds word-by-word captions and a hook. It can post them to your connected accounts too. It can also
record a streamer's live stream and clip the highlights while the stream is still going.

## What it does

- **Clips from any video.** It transcribes the audio and asks an AI which moments would hold a stranger's
  attention. Each moment is rendered with captions in one of three styles.
- **Live clipping.** It records a stream into a rolling buffer and clips as it happens, using loudness, chat
  activity and the transcript.
- **Automatic recording of several streamers.** Turn on "Record automatically when they go live" for each creator.
  ClipNova checks every 2 minutes and starts recording when they go live.
- **Workspaces per creator.** Each creator you clip gets their own channels, clip settings, posting rules and
  activity log.
- **Posting.** Connect YouTube, Instagram and TikTok, then queue finished clips or post them automatically, with
  spacing and daily caps. Every Short posted to YouTube can be added to a playlist for its game, such as
  "Fortnite Shorts". [DEPLOY.md](DEPLOY.md#connecting-youtube-instagram-and-tiktok) has the one-time setup.
- **Your own AI, with backups.** Supported services are Gemini, OpenAI, Grok, Groq, OpenRouter, Claude, a local
  model through Ollama, or anything that speaks the OpenAI chat format. You can add up to 5 backup AIs. When one
  hits its limit, the work moves to the next and carries on. You can also run it with no key at all: clips are
  then picked by loudness.
- **8 caption fonts.** Choose one yourself, or let the AI pick a font that fits each clip's mood.
- **No sign-in on your own computer.** It opens straight into the dashboard.

## Quick start

### 1. Install what it needs

- **Python 3.10 or newer**: https://www.python.org/downloads/ (on Windows, tick "Add Python to PATH").
- **Git**: https://git-scm.com/downloads
- **ffmpeg**:
  - Windows: `winget install Gyan.FFmpeg`
  - Mac: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

  ClipNova finds ffmpeg by itself and tells you in the dashboard if it's missing.

### 2. Download ClipNova

Put it in a short folder that stays put, such as `C:\clipnova` on Windows. Don't put it in a deep or temporary
folder. Windows can't open files whose full path is over 260 characters, and the speech model won't load from a
folder that deep.

On Windows:

```bash
git clone https://github.com/VJnCode/ClipNova.git C:\clipnova
cd C:\clipnova
```

On a Mac or Linux:

```bash
git clone https://github.com/VJnCode/ClipNova.git ~/clipnova
cd ~/clipnova
```

### 3. Install and start

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m studio.server
```

Mac or Linux:

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m studio.server
```

The first start downloads the speech model by itself. It's about 480 MB and only downloads once.

Open **http://127.0.0.1:8765**. Keep the terminal window open while you use ClipNova, because closing it stops the
app, including live recording and auto-posting. To stop it, press `Ctrl+C` or close the window.

To start it again later, open a terminal in the ClipNova folder and run the `python -m studio.server` line again.

### 4. Set up your AI

In the app, go to **Settings → AI**. Pick a service and paste your key. Press **Find models** and choose one, then
press **Save and test**. [Choose your AI](#choose-your-ai) lists free keys that work well.

## Choose your AI

ClipNova needs a chat model that can return JSON. A fast, inexpensive model is the right choice. A one-hour video
takes about four requests.

| Service | Get a key | A model that works |
|---|---|---|
| Google Gemini | https://aistudio.google.com/apikey | `gemini-2.5-flash` |
| Groq | https://console.groq.com/keys | `llama-3.3-70b-versatile` |
| OpenRouter (many models, one key) | https://openrouter.ai/keys | `google/gemini-2.5-flash` |
| OpenAI | https://platform.openai.com/api-keys | |
| Grok (xAI) | https://console.x.ai | |
| Claude | https://console.anthropic.com | |
| Ollama (on your own machine, no key) | https://ollama.com | |

Model names change often, so check the service's current list.

**Backups:** under **Settings → AI → Backup AI services → Add a backup**, add more services the same way. ClipNova
uses the main AI first. When it hits its limit or stops answering, the work moves to the next backup. A service
that hit its limit rests for 15 minutes before it's used again.

Your keys are kept in the data folder on your machine, and the app never shows them again. You pay the AI service
directly for what you use. The **AI usage** page shows how many requests and tokens each video took. Speech-to-text
runs on your own machine, so your audio never leaves it.

If you'd rather use a file, the same settings can go in a `.env` file. What you save in the dashboard takes priority:

```ini
PEAKCUT_AI_PROVIDER=gemini
PEAKCUT_AI_MODELS=gemini-2.5-flash
PEAKCUT_AI_KEY=your-key-here
```

## Daily use

- **Make clips:** paste a link on Home and press **Make clips**.
- **Record streamers when they go live:**
  1. Press **+ New creator**.
  2. Add their Twitch, Kick or YouTube channel link and set the **Game**.
  3. In **Setup**, turn on **Record automatically when they go live**.

  Several streamers can record at once. ClipNova won't start a new recording while your PC is already busy.
- **Caption font:** choose one under the link box, in a creator's **Setup → Clips**, or on a single clip, which then
  renders again. **AI picks per clip** matches the font to the clip's mood.
- **YouTube playlists:** set them in a creator's **Setup → Posting → YouTube playlist for each Short**.
  - `{game} Shorts` is the default.
  - `{creator}` is replaced by the workspace name.
  - Leave it empty for no playlist.
- **Posting:** turn on autopost in **Setup → Posting**. Posts go out spaced by the gap you set.

## Settings

Most settings are in the dashboard. For the rest, copy [`.env.example`](.env.example) to `.env` and edit it. Every
setting in it has a short explanation. The ones you're most likely to change:

| Setting | What it's for |
|---|---|
| `PEAKCUT_PORT` | The port the app uses (default `8765`) |
| `PEAKCUT_DATA` | Where videos, clips and the database are kept (default `./data`) |
| `PEAKCUT_ACCOUNTS` | `1` makes everyone sign in. Use it on any server other people can reach |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Optional: Sign in with Google, and connecting YouTube |

`.env`, the `secrets/` folder and the `data/` folder are ignored by git, so your keys and clips are never uploaded.

## Where your videos and clips are kept

Everything ClipNova keeps is in the `data` folder inside ClipNova: videos, clips, recordings, creators, settings and
the speech model. **Settings → Storage** shows the folder and how much room is left on its drive, and it can move
the folder to another drive. If the drive is nearly full, ClipNova says so and stops taking new videos until there
is room.

## Updating

ClipNova checks this repository while it runs and shows a notice when a newer version is out. To update, run this
in the ClipNova folder, then start it again:

```bash
git pull
.venv\Scripts\pip install -r requirements.txt
```

On a Mac or Linux, use `.venv/bin/pip` instead. Updating doesn't touch your `.env`, keys or clips. To turn the
check off, set `PEAKCUT_UPDATE_CHECK=0`.

## Troubleshooting

| Problem | Fix |
|---|---|
| Browser says it can't connect | ClipNova isn't running. Start it again (step 3) |
| "ffmpeg isn't installed" | Install ffmpeg (step 1), then start again |
| "The AI did not answer" | Settings → AI → test again, or add a backup AI |
| Shorts are private | Google keeps uploads from unverified apps private. Make them public in YouTube Studio |
| No playlist was made | Reconnect YouTube once in Settings → Connected apps, and check the creator has a Game |
| Strange characters crash the server on Windows | Run `set PYTHONIOENCODING=utf-8` before starting |
| Speech model won't load on Windows | Move ClipNova to a short folder such as `C:\clipnova` |

## For developers

| Part | What it is |
|---|---|
| `studio/` | The server: FastAPI, the clip pipeline, live recording, accounts |
| `studio/ai.py` | The only file that talks to an AI service. Add a provider here |
| `web/` | The pages, in plain HTML, CSS and JavaScript with no build step |
| `tests/` | Tests that run against a throwaway copy of the app: `python tests/run.py` |
| `deploy/`, `Dockerfile`, `docker-compose.yml` | Deployment to one server ([DEPLOY.md](DEPLOY.md)) |

ClipNova uses `ffmpeg` and `yt-dlp` for video work. Speech is transcribed with `sherpa-onnx` and the Parakeet model.
[AGENTS.md](AGENTS.md) is a short map of the code. Settings are named `PEAKCUT_*` because ClipNova is built on the
open-source [PeakCut](https://github.com/haziqahmedqasmi/PeakCut) project.

## Security

- With sign-in off, ClipNova listens only on your own computer (`127.0.0.1`). Don't expose it to the internet that
  way. On a server, turn accounts on with `PEAKCUT_ACCOUNTS=1`.
- Passwords are stored only as salted scrypt hashes, and session cookies are HTTP-only.

## Using it responsibly

Only clip videos you made or have permission to use. You're responsible for the rights to what you download, clip
and post. Follow the terms of the sites you fetch from and post to.

## Licence

[MIT](LICENSE). The caption fonts in `studio/fonts/` are under the SIL Open Font License, and the licence texts are
in the same folder.
