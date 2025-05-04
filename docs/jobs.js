async function loadJobs() {
    const list = document.getElementById("jobs");
    const loading = document.getElementById("loading");

    // grab every *.json inside jobs/  (works on most static hosts)
    const indexResp = await fetch("jobs/");
    if (!indexResp.ok) { loading.textContent = "No jobs yet."; return; }

    const html = await indexResp.text();
    const files = Array.from(html.matchAll(/href="([^"]+\.json)"/g), m => m[1]);

    const jobs = await Promise.all(files.map(f => fetch("jobs/" + f).then(r => r.json())));

    // newest first
    jobs.sort((a, b) => new Date(b.posted_date) - new Date(a.posted_date));

    loading.remove();
    list.hidden = false;

    for (const j of jobs) {
      if (j.classification !== 'remote_worldwide') {
        continue;
      }
      const li = document.createElement("li");
      li.innerHTML = `
        <div class="job-title"><a href="${j.source_url}" target="_blank">${j.job_title}</a></div>
        <div class="company">${j.company}</div>
        <div>${j.posted_date}</div>
        <span class="badge" style="color: ${j.classification === 'remote_worldwide' ? 'green' : 'inherit'};">${j.classification.replace('_',' ')}</span>
      `;
      // li.onclick = () => window.open(j.source_url, '_blank');
      list.appendChild(li);
    }
  }

  loadJobs();
