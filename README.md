# Real Estate Photo Editor — Shared Web App

Simple browser-based tool for photographers in different states.  
They open a link, upload photos (including HDR brackets), enhance, and download.

## Features
- **HDR blending** (exposure fusion of bracketed shots) — primary workflow
- Batch upload for single images
- Auto straighten / perspective
- Brightness, contrast, saturation
- Basic sky replacement
- Download edited JPEGs

## Deploy in 5 minutes (free for the team)

### Option A — Streamlit Community Cloud (easiest)
1. Push these files to a GitHub repo:
   - `app.py`
   - `requirements.txt`
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub and deploy
4. Share the permanent link with your photographers

### Option B — Railway / Render (also free tier)
Upload the same two files and deploy as a Python app.  
Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

## Local test
```bash
pip install -r requirements.txt
streamlit run app.py
```

## How photographers use HDR mode
1. Upload all bracketed exposures of a shot together
2. Switch to “HDR Blend (brackets)”
3. Select the exposures for that scene
4. Click Blend HDR
5. Download the result

## Next upgrades (when ready)
- AI virtual staging (furniture)
- Advanced clutter removal
- Company watermark
