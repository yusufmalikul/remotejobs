import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.golangprojects.com"
LIST_URL = f"{BASE_URL}/golang-remote-jobs.html"

def latest_golang_remote_jobs(n: int = 10) -> list[str]:
    """Return the first *n* job-post URLs from the remote-jobs page."""
    resp = requests.get(LIST_URL, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    links = []
    # Job links all start with “/golang-go-job-…”
    for a in soup.select("a[href^='/golang-go-job-']"):
        href = a["href"]
        full_url = urljoin(BASE_URL, href)
        if full_url not in links:
            links.append(full_url)
        if len(links) == n:
            break
    return links

if __name__ == "__main__":
    for url in latest_golang_remote_jobs():
        print(url)
