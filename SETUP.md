# ClipNova: full setup guide

ClipNova turns long videos and live streams into captioned vertical clips (YouTube Shorts, Instagram Reels) and
can post them for you. It runs on your own PC, in your browser, at **http://127.0.0.1:8766/app**.

Follow the steps in order. Steps 1 to 4 are needed. Steps 5 to 8 are needed only for posting automatically.

| Step | What | Time |
|---|---|---|
| 1 | Install Python, then double-click `Start ClipNova.bat` | 10 min |
| 2 | Using it day to day | 1 min |
| 3 | AI key (free) | 3 min |
| 4 | Make your first clips | — |
| 5 | Google Cloud project for YouTube | 15 min |
| 6 | Connect your YouTube channel | 2 min |
| 7 | Instagram (optional) | 20 min |
| 8 | Workspaces, auto-posting, recording streamers live | 5 min |

---

## 1. Install (once)

You need **Windows 10/11**, about **3 GB free** (the speech model is 630 MB, plus your videos), and internet.

1. **Python 3.10 or newer**: https://www.python.org/downloads/
   - In the installer, **tick "Add Python to PATH"**.
   - Or in a terminal: `winget install Python.Python.3.12`
2. Put the `ClipNova` folder somewhere with a **short path without spaces**, e.g. `D:\ClipNova`. Very deep folders
   break the speech model on Windows.
3. **Double-click `Start ClipNova.bat`.** That's it. The first time, it sets everything up by itself
   (a few minutes), then starts the app:
   - checks Python and installs **ffmpeg** if it's missing,
   - makes the app's own Python environment (`.venv`) and installs the packages,
   - makes the settings file `.env` with `PEAKCUT_PORT=8766`.

   (`setup.bat` does only the install part, if you ever want to run it by itself or repair an install.)

> The settings use names starting with `PEAKCUT_`. That's normal: ClipNova is built on the open-source
> PeakCut project (MIT licence, see `LICENSE`).

---

## 2. Using it day to day

**Double-click `Start ClipNova.bat`** every time you want to use ClipNova.

- A black window opens. **Keep it open** the whole time: closing it stops ClipNova, including recordings and posting.
- The browser opens **http://127.0.0.1:8766/app** after a few seconds.
- Always use **`127.0.0.1`**, not `localhost`. Google sign-in only works with the exact address it was given.
- **The first time**, the speech model (about 630 MB) downloads by itself. Wait for it.
- **To stop:** close the black window. Clicking `Start ClipNova.bat` while it's already running just opens the browser.

---

## 3. AI key (free)

The AI picks the best moments and writes hooks, titles, descriptions and hashtags. Without a key, clips are
picked by loudness only.

1. Get a free **Gemini** key at https://aistudio.google.com/apikey (sign in with Google, then **Create API key**).
2. In ClipNova: **Settings → AI**.
   - **AI service:** Gemini
   - **Key:** paste it
   - **Model:** press **Find models** and pick `gemini-2.5-flash` (or a `flash-lite` model)
3. Press **Save and test**. It should say the AI is ready.

### Backup AIs (recommended)
Free keys have daily limits. With backups, ClipNova switches to the next AI when one runs out, and carries on
with the same work.

1. **Settings → AI → Backup AI services → Add a backup.**
2. Pick the service, paste the key, press **Find models**, pick a model.
3. Press **Save backups and test**. Each backup shows *Works* or *Failed*.

| Service | Free key | Good model |
|---|---|---|
| Groq | https://console.groq.com/keys | `llama-3.3-70b-versatile` (or `llama-3.1-8b-instant`) |
| OpenRouter | https://openrouter.ai/keys | `google/gemini-2.5-flash` |
| Gemini (another Google account) | https://aistudio.google.com/apikey | `gemini-2.5-flash` |

- **Make main** turns a backup into the main AI, and the old main one becomes a backup. **↑ / ↓** change the order.
- A service that hit its limit rests for 15 minutes, then is used again.
- ⚠️ Pick a **chat** model. Models with `guard`, `whisper` or `tts` in the name don't work for this.

---

## 4. Make clips

On **Home**, paste a YouTube / Twitch / Kick link (or drop a video file), then press **Make clips**.
The options under the box set:
- how many clips and how long,
- **Caption style** and **Caption font** ("AI picks per clip" matches the font to the mood),
- layout and quality.

Finished clips appear on the video's page. You can download them, edit them (text, timing, font) or post them.

---

## 5. Google Cloud project (once, for posting to YouTube)

ClipNova posts through **your own** Google Cloud app. It's free.

### 5a. Project and API
1. Go to https://console.cloud.google.com and sign in with the Google account that owns (or manages) the YouTube channel.
2. At the top: **project picker → New project**, name it e.g. `ClipNova`, then **Create**, then select it.
3. **APIs & Services → Library** → search **YouTube Data API v3** → **Enable**.

### 5b. OAuth consent screen and test users
Google may show this as **"Google Auth Platform"**, with the tabs *Branding*, *Audience* and *Clients*.

1. **APIs & Services → OAuth consent screen** (or **Google Auth Platform → Get started**).
2. **App name:** `ClipNova`. **User support email:** your email. **Audience / User type:** **External**.
   **Contact email:** your email. Agree, then **Create**.
3. **Test users** (under *Audience*, or on the consent screen page): **+ Add users** and add **every Google
   account that will connect a YouTube channel**. You can add up to 100.
   - ⚠️ An account that isn't on this list gets **"Access blocked"**, even if everything else is right.
4. Leave **Publishing status** on **Testing**.

### 5c. OAuth client (the redirect URI)
1. **APIs & Services → Credentials → + Create credentials → OAuth client ID** (or **Clients → Create client**).
2. **Application type: Web application.** Name: `ClipNova`.
3. **Authorized redirect URIs → + Add URI** and paste **exactly**:
   ```
   http://127.0.0.1:8766/oauth/youtube/callback
   ```
   It must be `http` (not https), `127.0.0.1` (not localhost) and port `8766`, with no slash at the end.
   If you change the port in `.env`, change it here too.
4. Click **Create**. Copy the **Client ID** and **Client secret**, and keep them private.
5. Wait about 5 minutes. A new redirect URI takes a little while to work.

---

## 6. Connect your YouTube channel

1. In ClipNova: **Settings → Connected apps → YouTube → Set up**. Paste the **Client ID** and **Client secret**, then save.
2. Press **Connect**.
   - Google shows **Choose an account**. Pick the account that's a **test user**. For a Brand-account channel,
     pick the channel on the next screen.
   - "Google hasn't verified this app": click **Continue**. That's your own app in testing.
   - **Tick every permission box.** "Manage your YouTube account" is needed for the per-game playlists.
3. You're back in ClipNova and the channel is listed. Done.

### Good to know about Google
- **Uploads are private** until your Google app passes Google's audit. That's Google's rule for unverified apps.
  Make them public in YouTube Studio, or apply for the audit (YouTube API Services → Audit and quota extension form).
- **In "Testing" mode, Google signs you out after 7 days.** If posting fails with a sign-in error, go to
  Settings → Connected apps → YouTube → **Connect** again. To stop this, set **Publishing status → In production**
  (OAuth consent screen / Audience). Connecting then shows the "unverified app" warning, and you click **Continue**.
- **Quota:** the free YouTube quota is about **6 uploads a day** per Google Cloud project (10,000 units; an upload
  costs 1,600). Ask Google for more in the audit form if you need it.

### Errors
| Error from Google | Fix |
|---|---|
| `Error 400: redirect_uri_mismatch` | The redirect URI in step 5c doesn't match exactly. Use `http://127.0.0.1:8766/oauth/youtube/callback`, open ClipNova at `127.0.0.1` (not localhost), and wait 5 minutes after saving |
| `Access blocked: ... has not completed the Google verification process` / `access_denied` | That Google account isn't a **test user** (step 5b) |
| Can't choose another account | Sign out of Google in the browser, or use a private window, then Connect |
| `The request cannot be completed because you have exceeded your quota` | Daily YouTube quota used up: wait until tomorrow (resets at midnight Pacific time) |
| Playlist not made | Connect YouTube again and tick every box. The workspace needs a **Game** |

---

## 7. Instagram (optional)

Instagram needs a **public https address** for ClipNova: Meta redirects to it and downloads each Reel from it.
Use a free **ngrok** static domain.

### 7a. ngrok (a public address for your PC)
1. Sign up at https://ngrok.com (free). Under **Domains**, claim your free static domain, e.g. `yourname.ngrok-free.app`.
2. Install it with `winget install ngrok.ngrok`, then run `ngrok config add-authtoken <your token>` (the token is on the ngrok dashboard).
3. Start the tunnel (keep this window open whenever Reels post):
   ```
   ngrok http --url=yourname.ngrok-free.app 8766
   ```
4. Add this line to ClipNova's `.env` and restart ClipNova:
   ```
   PEAKCUT_PUBLIC_URL=https://yourname.ngrok-free.app
   ```
   ⚠️ Once `PEAKCUT_PUBLIC_URL` is set, the YouTube redirect URI also becomes
   `https://yourname.ngrok-free.app/oauth/youtube/callback`. **Add that one in Google Cloud too** (step 5c), and open
   ClipNova at the https address when connecting.

### 7b. Instagram account
Instagram app → **Settings → Account type and tools → Switch to professional account** (Creator or Business).

### 7c. Meta app
1. Go to https://developers.facebook.com/apps → **Create app**. Pick **Other**, then the type **Business** (or the
   "Manage messaging & content on Instagram" use case).
2. **Add product → Instagram → API setup with Instagram login.**
3. **Business login settings → OAuth redirect URIs**, and add:
   ```
   https://yourname.ngrok-free.app/oauth/instagram/callback
   ```
4. **App roles → Roles → Add people → Instagram Tester**, and enter the Instagram username.
   Then accept the invite in Instagram: **Settings → Website permissions → Apps and websites → Tester invites**
   (or on the web: instagram.com → Settings → Apps and websites).
5. Copy the **Instagram app ID** and **Instagram app secret** (on the Instagram API setup page, not the Facebook app ID).

### 7d. Connect
In ClipNova (opened at `https://yourname.ngrok-free.app/app`): **Settings → Connected apps → Instagram → Set up**.
Paste the ID and secret, press **Connect**, log in and allow everything.

---

## 8. Workspaces, auto-posting and live streamers

A **creator workspace** holds one streamer's settings, clips and posting rules.

1. Sidebar → **+ New creator**. Add the streamer's **channel link**, not a single stream:
   - `https://www.twitch.tv/name`
   - `https://kick.com/name`
   - `https://www.youtube.com/@handle`
2. **Setup**:
   - **Game:** e.g. `GTA 6`. This sets game hashtags, the AI's rules, and the playlist name.
   - **Record automatically when they go live:** on. ClipNova checks every 2 minutes, records the stream,
     and clips the best moments while it's still live. Add as many streamers as you like; several can record at
     once, depending on your PC.
   - **Clips:** caption style, **caption font** ("AI picks per clip"), layout and lengths.
   - **Posting:**
     - turn on autopost and tick the accounts,
     - minimum AI score, the gap between posts, the most posts a day,
     - a line added under every post (credit or campaign tag),
     - **YouTube playlist for each Short:** `{game} Shorts` makes "Grand Theft Auto VI Shorts", "Fortnite Shorts"…
       automatically. Leave it empty for no playlist.
3. ClipNova must stay running (the black window open, the PC not asleep) to catch streams and post on time.

---

## Daily use
- Start: double-click `Start ClipNova.bat`. Stop: close the black window.
- **Activity** (inside a workspace) shows what was recorded, clipped and posted, and any errors.
- **AI usage** (account menu) shows tokens used today.

## Troubleshooting
| Problem | Fix |
|---|---|
| Python not found | Install Python and tick "Add Python to PATH", then open a **new** window |
| Browser: can't connect | The black window isn't open: double-click `Start ClipNova.bat` |
| "ffmpeg isn't installed" | `winget install Gyan.FFmpeg`, then start again |
| "Open ClipNova by its own address" | Use `http://127.0.0.1:8766/app` (or your ngrok https address), not localhost |
| "The AI did not answer" | Settings → AI → Test again. Add a backup AI. Check the model is a chat model |
| Speech model download fails | Check the internet and free disk space, then try again (it resumes from scratch, 630 MB) |
| Shorts are private | Normal for an unverified Google app (see step 6) |
| Posting stopped after a week | Google testing-mode sign-in expired: Connect YouTube again (step 6) |
| A streamer isn't recorded | The workspace needs their **channel** link (not a video link), auto-record on, and ClipNova running |

---

## Sharing ClipNova (read before sending this folder to anyone)
Your keys and logins live in two places. **Never send them:**
- **`data\`** has your AI keys, your Google client secret, your YouTube/Instagram sign-ins, and all your videos and clips.
- **`.env`** has your settings and addresses.

Also leave out **`.venv\`**. It only works on the PC that made it; on another PC, `Start ClipNova.bat` makes a new one.

To share it, send the folder **without `data`, `.env` and `.venv`**. Or with git: `data/`, `.env` and `.venv/` are
already in `.gitignore`, so `git add -A` leaves them out. Check with `git status` before you push. Each person
makes their own AI keys, Google Cloud app and test users by following this guide.
