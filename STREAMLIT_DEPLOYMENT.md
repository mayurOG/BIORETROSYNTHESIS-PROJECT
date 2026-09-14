# 🚀 Streamlit Cloud Deployment Guide

## Quick Deployment (2 minutes)

### Step 1: Push to GitHub ✅ (Already Done)
All code is already on GitHub: https://github.com/mayurOG/BioRetroSynthesis

### Step 2: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io
   - Sign in with your GitHub account (mayurOG)

2. **Create New App**
   - Click "New app" button
   - Select:
     - Repository: `mayurOG/BioRetroSynthesis`
     - Branch: `main`
     - Main file path: `net_app_functional.py`

3. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Your app will be live!

### Step 3: Share Your App

Your live app URL will be:
```
https://bioretrosynthesis-mayurOG.streamlit.app
```

(Replace with actual URL after deployment)

---

## Deployment Configuration Files

✅ `.streamlit/config.toml` — Streamlit configuration
✅ `.streamlit/secrets.toml` — Environment variables
✅ `requirements-streamlit.txt` — Minimal dependencies
✅ `.gitignore` — Git ignore rules

---

## Features Available

- ✅ Multi-format input (SMILES, names, formulas, CAS)
- ✅ Real-time predictions
- ✅ Molecular properties
- ✅ Validation results
- ✅ Retrosynthesis pathways
- ✅ Export (JSON/CSV)

---

## Troubleshooting

### App won't load?
- Check `.streamlit/config.toml` format
- Verify all dependencies in `requirements-streamlit.txt`

### Performance slow?
- Streamlit Cloud may be on slower hardware
- First load takes 30-60 seconds
- Subsequent loads are faster

### Need to update?
- Make changes locally
- Commit to GitHub
- Streamlit automatically redeploys

---

## Alternative: Docker Deployment

See `dockerfile` for containerized deployment to:
- Google Cloud Run
- AWS ECS
- Docker Hub
- Any cloud provider

---

## Support

- 📖 Streamlit Docs: https://docs.streamlit.io
- 🐛 GitHub Issues: https://github.com/mayurOG/BioRetroSynthesis/issues
- 💬 Streamlit Community: https://discuss.streamlit.io

---

**Status:** Ready for deployment ✅
**Maintainer:** Mayur Nhavalde
