# 🌾 Agricultural Drought Analysis Dashboard — Bangladesh

Interactive web dashboard for analyzing drought conditions in Sapahar Upazila and surrounding areas using Google Earth Engine satellite data.

## 📊 Features

- **NDVI** — Crop health from Sentinel-2
- **Rainfall** — Daily data from CHIRPS
- **Land Surface Temperature** — MODIS 8-day composites
- **Soil Moisture** — NASA SMAP 10km
- **Multi-area comparison** with radar chart
- **Interactive map** with GEE raster overlays
- **CSV export** for all parameters

---

## 🚀 Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/drought-dashboard.git
cd drought-dashboard
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. GEE Authentication (personal account)
```bash
earthengine authenticate
```
This opens a browser, sign in with your GEE-registered Google account.

### 4. Set your GEE Project ID
```bash
export GEE_PROJECT_ID="your-gee-project-id"
```

### 5. Run locally
```bash
streamlit run app.py
```

---

## ☁️ Deploy to Streamlit Cloud

### Step 1 — Create a Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your GEE project
3. **IAM & Admin** → **Service Accounts** → **Create Service Account**
4. Name it (e.g. `drought-dashboard-sa`)
5. Role: **Earth Engine Resource Viewer**
6. **Keys** tab → **Add Key** → **JSON** → Download

### Step 2 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/drought-dashboard.git
git push -u origin main
```
> ⚠️ Make sure `.gitignore` is working — never commit `service-account.json` or `secrets.toml`

### Step 3 — Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repo
3. Set **Main file**: `app.py`
4. Go to **Advanced settings** → **Secrets**
5. Paste the following (fill in your values):

```toml
GEE_SERVICE_ACCOUNT = "drought-dashboard-sa@your-project.iam.gserviceaccount.com"
GEE_PROJECT_ID      = "your-gee-project-id"
GEE_KEY_JSON        = '''
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n",
  "client_email": "...",
  ...
}
'''
```

6. Click **Deploy**!

---

## 📁 Project Structure

```
drought-dashboard/
├── app.py                        # Main Streamlit app
├── config.py                     # Areas, dates, thresholds
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── config.toml               # Theme
│   └── secrets.toml.example      # Template (do not commit actual secrets)
├── gee_auth/
│   └── service-account.json      # NOT committed (in .gitignore)
├── modules/
│   ├── gee_connect.py            # GEE auth
│   ├── ndvi.py                   # NDVI + NDWI
│   ├── rainfall.py               # CHIRPS
│   ├── lst.py                    # MODIS LST
│   └── soil_moisture.py          # SMAP
└── utils/
    ├── chart_utils.py            # Plotly charts
    └── map_utils.py              # Folium map helpers
```

---

## 🛰️ GEE Datasets Used

| Parameter | Dataset | Resolution |
|-----------|---------|------------|
| NDVI | `COPERNICUS/S2_SR_HARMONIZED` | 10m |
| Rainfall | `UCSB-CHG/CHIRPS/DAILY` | ~5km |
| LST | `MODIS/061/MOD11A2` | 1km, 8-day |
| Soil Moisture | `NASA_USDA/HSL/SMAP10KM_soil_moisture` | 10km |

---

## ⚠️ GEE Quota Notes

- GEE free tier: **100 concurrent requests**, plenty for this dashboard
- `@st.cache_data(ttl=3600)` reduces repeated API calls
- Large date ranges (> 2 years) may be slow — use presets for best performance
- SMAP data may not be available for all dates; the app handles this gracefully
