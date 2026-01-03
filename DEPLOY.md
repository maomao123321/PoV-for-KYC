# Streamlit Cloud Deployment Guide

## 🚀 Quick Deploy to Streamlit Cloud

### Step 1: Prepare GitHub Repository

✅ Already done! Your code is at:
```
https://github.com/maomao123321/PoV-for-KYC
```

### Step 2: Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign up" or "Continue with GitHub"
3. Authorize Streamlit to access your GitHub repositories

### Step 3: Deploy Your App

1. Click "New app" button
2. Select:
   - **Repository**: `maomao123321/PoV-for-KYC`
   - **Branch**: `main`
   - **Main file path**: `app.py`
3. Click "Advanced settings..." (Optional)
   - **Python version**: 3.10 or higher
   - **Requirements file**: `requirements-streamlit.txt`

### Step 4: Configure Secrets (API Key)

⚠️ **Important**: Do NOT commit your API key to GitHub!

In Streamlit Cloud dashboard:
1. Go to your app settings (⚙️ icon)
2. Click "Secrets" in the sidebar
3. Add your API key:

```toml
FIREWORKS_API_KEY = "fw_your_actual_key_here"
```

4. Click "Save"

### Step 5: Deploy!

Click "Deploy!" button. Streamlit Cloud will:
- Clone your repository
- Install dependencies from `requirements-streamlit.txt`
- Launch your app
- Provide a public URL (e.g., `https://pov-for-kyc-xxxxx.streamlit.app`)

---

## 📝 Post-Deployment

### Updating Your App

Any push to the `main` branch will automatically redeploy:

```bash
git add .
git commit -m "Update: description of changes"
git push origin main
```

Wait 1-2 minutes for Streamlit Cloud to rebuild.

### Monitoring

- **Logs**: Click "Manage app" → "Logs" to see real-time logs
- **Reboot**: If app crashes, click "Reboot app"
- **Analytics**: View usage stats in Streamlit Cloud dashboard

### Custom Domain (Optional)

Streamlit Cloud provides a free subdomain. For custom domain:
1. Upgrade to Streamlit Cloud Pro (if needed)
2. Go to app settings → "Custom domain"
3. Add your domain and configure DNS

---

## 🔒 Security Best Practices

### Secrets Management

✅ **Do:**
- Store API keys in Streamlit Cloud secrets
- Use `.gitignore` to exclude `.env` and `secrets.toml`
- Rotate keys regularly

❌ **Don't:**
- Commit API keys to GitHub
- Share secrets in public channels
- Use production keys for testing

### Rate Limiting

Consider adding rate limiting for production:

```python
# In app.py, add after imports
import time
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_result(file_hash):
    # Cache results by file hash to avoid reprocessing
    pass
```

---

## 🐛 Troubleshooting

### App Won't Start

**Check:**
1. Logs for dependency errors
2. Python version compatibility
3. Secrets are properly configured

**Fix:**
```bash
# Test locally first
streamlit run app.py
```

### "Module not found" Error

**Fix:** Ensure `requirements-streamlit.txt` includes all dependencies:
```bash
# Add missing package
echo "missing-package>=1.0" >> requirements-streamlit.txt
git add requirements-streamlit.txt
git commit -m "Add missing dependency"
git push origin main
```

### API Key Not Working

**Check:**
1. Secrets syntax (TOML format, no quotes around key name)
2. Key name matches: `FIREWORKS_API_KEY`
3. Reboot app after adding secrets

### Slow Performance

**Options:**
1. Enable caching:
   ```python
   @st.cache_data
   def process_document(image_bytes):
       ...
   ```

2. Upgrade Streamlit Cloud plan for more resources

---

## 📊 Monitoring & Limits

### Streamlit Cloud Free Tier

- **Storage**: 1GB
- **Memory**: 1GB RAM
- **Apps**: 1 public app
- **Uptime**: Auto-sleep after 7 days inactivity

### Usage Tips

- App auto-wakes when visited
- Logs retained for 7 days
- Redeploy on every git push

---

## 🎯 Next Steps

1. **Custom branding**: Update `st.set_page_config()` with logo
2. **Analytics**: Add Google Analytics or Plausible
3. **Authentication**: Add login with `streamlit-authenticator`
4. **Database**: Store results in Supabase/Firebase

---

## 📞 Support

- Streamlit Docs: https://docs.streamlit.io
- Community Forum: https://discuss.streamlit.io
- GitHub Issues: https://github.com/maomao123321/PoV-for-KYC/issues

