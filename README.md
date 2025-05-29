# Proxy Checker 🔍⚡
**A high-performance proxy validation tool with async support and detailed analytics**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)

## Features ✨
- **Blazing Fast** ⚡ - Async I/O with configurable concurrency (200+ proxies/sec)
- **Smart Detection** 🔍 - Auto-detects protocol (HTTP/SOCKS5) from format
- **Comprehensive Checks** ✅
  - Connectivity verification
  - Response time measurement
  - Geolocation lookup
  - Protocol validation
- **Rich Output** 🎨 - Beautiful console display with color-coded results
- **Multiple Output Formats** 💾 - TXT, JSON, and CSV support
- **Retry Mechanism** 🔄 - Configurable retries for flaky proxies
- **Progress Tracking** 📊 - Real-time progress bar with Rich

## Installation 📦
```bash
git clone https://github.com/yourusername/proxy-checker.git
cd proxy-checker
pip install -r requirements.txt
```

## Usage 🚀
1. Add proxies to `proxies.txt`:
   ```text
   socks5://user:pass@ip:port
   http://user:pass@ip:port
   user:pass@ip:port  # Auto-detected
   ```

2. Run the checker:
   ```bash
   python proxy_checker.py
   ```

3. Results saved to:
   - `working_proxies.txt` - Verified working proxies
   - `failed_proxies.txt` - Failed proxy list
   - `results.json`/`results.csv` - Detailed check data

## Configuration ⚙️
Customize in code:
```python
checker = ProxyChecker(
    proxy_file="proxies.txt",
    timeout=5,          # Seconds per check
    max_concurrent=200, # Simultaneous connections
    retries=2,          # Retry attempts
    test_url="http://ip-api.com/json" # Verification endpoint
)
```

## Advanced Tips 🧠
- **Boost Speed**:
  ```python
  # Increase concurrency (adjust based on your system)
  checker = ProxyChecker("proxies.txt", max_concurrent=300)
  
  # Use faster test endpoint
  checker = ProxyChecker("proxies.txt", test_url="http://httpbin.org/ip")
  ```

- **Export Formats**:
  ```python
  checker.save_results(format="json")  # json/csv/txt
  ```

## Output Example 📄
![Preview](https://i.postimg.cc/rm630t02/image.png)
