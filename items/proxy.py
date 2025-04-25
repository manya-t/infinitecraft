from selenium import webdriver

# Setup proxy for Mitmproxy
proxy = "127.0.0.1:8080"  # Adjust to match Mitmproxy's address
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"--proxy-server={proxy}")  

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://neal.fun/infinite-craft/")
