# Smart Price Finder

A premium, high‑performance price‑comparison web app that lets users search for a product and instantly see the best offers from multiple e‑commerce platforms.

---

## ✨ Features
- **FastAPI backend** – asynchronous scraping with `httpx` and ScraperAPI proxy to bypass anti‑bot protections.
- **React + Vite frontend** – modern UI built with Tailwind CSS, glass‑morphism cards, skeleton loaders, and Framer Motion animations.
- **Multiple platforms** – Amazon (working out‑of‑the‑box), eBay, Walmart, Best Buy (selectors can be tweaked or swapped for official free APIs).
- **One‑click launcher** – `run.ps1` installs dependencies, kills stray processes, starts both servers, and opens the browser.
- **Health & debug endpoints** – `/health` and `/debug-scrape` for quick diagnostics.

---

## 🛠️ Tech Stack
| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, uvicorn, httpx, beautifulsoup4, lxml |
| **Frontend** | React 18, Vite, Tailwind CSS, Framer Motion, axios |
| **Proxy** | ScraperAPI (key: `1ad339d0ee8948b4170a315f1ea7df28`) |
| **Launcher** | PowerShell script (`run.ps1`) |

---

## 📂 Repository Structure
```
web scraper/
│
├─ price_scraper.py            # FastAPI backend
├─ run.ps1                     # PowerShell launcher (starts both servers)
├─ start.bat (legacy)         # CMD version of the launcher
│
├─ frontend/                   # React application
│   ├─ src/
│   │   ├─ App.jsx
│   │   ├─ main.jsx
│   │   ├─ services/api.js
│   │   ├─ components/…
│   │   └─ constants/platforms.jsx
│   ├─ index.css               # Tailwind + custom badge styles
│   ├─ vite.config.js
│   └─ tailwind.config.js
│
└─ check_deps.py               # Helper to verify Python packages
```

---

## 🚀 Quick Start (Windows)
1. **Open PowerShell** in the project root:
   ```powershell
   cd "C:\Users\Sahitya\OneDrive\Desktop\Python\web scraper"
   ```
2. **Run the launcher** (creates a virtual‑env‑aware environment, installs missing packages, starts both servers, and opens the browser):
   ```powershell
   .\run.ps1
   ```
   The script will:
   - Kill any process still listening on port 8000.
   - Install required Python packages (`fastapi`, `uvicorn[standard]`, `httpx`, `beautifulsoup4`, `lxml`).
   - Start the FastAPI backend at `http://localhost:8000`.
   - Start the Vite dev server at `http://localhost:5173` and open the page in your default browser.
3. **Use the app** – type a product name (e.g., *iPhone 15*) and click **Find Prices**.
4. **API docs** – visit `http://localhost:8000/docs` for the automatically generated OpenAPI UI.

> **If you prefer to start the servers manually:**
> ```powershell
> # Backend
> .\venv\Scripts\python.exe -m uvicorn price_scraper:app --port 8000
> # Frontend (in a second PowerShell window)
> cd frontend
> npm run dev
> ```

---

## 🛠️ Extending / Fixing Scrapers
- **Add a new platform** – create a coroutine in `price_scraper.py` that returns a list of product dicts, add it to `compare_prices`, and add UI metadata in `frontend/src/constants/platforms.jsx`.
- **Fix selectors** – use the `/debug-scrape?product=<term>&site=<site>` endpoint to view raw HTML returned by ScraperAPI and adjust the BeautifulSoup selectors accordingly.
- **Official free APIs (recommended)** – eBay Browse API, Best Buy Open API, Walmart Open API (via RapidAPI). Replace the HTML‑scraping functions with simple JSON calls for rock‑solid reliability.

---

## 📦 Production Build (Optional)
1. Build the React app:
   ```bash
   cd frontend
   npm run build   # creates ./dist
   ```
2. Serve static files from FastAPI (add to `price_scraper.py`):
   ```python
   from fastapi.staticfiles import StaticFiles
   app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
   ```
3. Run the server:
   ```powershell
   uvicorn price_scraper:app --host 0.0.0.0 --port 8000
   ```
   The UI will be available at `http://<host>:8000`.

---

## 📝 License
MIT – feel free to fork, extend, and deploy.

---

## 🙋‍♀️ Support
Open an issue on the repository or contact the author for help with selector updates, API key configuration, or deployment questions.
