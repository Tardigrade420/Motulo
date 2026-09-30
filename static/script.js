// Function to fetch METAR data
async function fetchMetarData() {
    try {
        const response = await fetch('https://api.met.no/weatherapi/tafmetar/1.0/metar.xml?icao=enbr');
        const xmlText = await response.text();
        
        // Parse the XML
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlText, "text/xml");
        
        // Get the latest METAR text
        const metarElements = xmlDoc.getElementsByTagName('metno:metarText');
        const latestMetar = metarElements[metarElements.length - 1].textContent;
        
        // Store the METAR text in a variable that can be accessed globally
        window.latestMetar = latestMetar;
        
        // Update the METAR text in the UI
        const metarElement = document.getElementById('metarText');
        if (metarElement) {
            metarElement.textContent = latestMetar;
        }
        
        // You can also dispatch an event to notify that the data is ready
        const event = new CustomEvent('metarDataLoaded', { detail: { metar: latestMetar } });
        document.dispatchEvent(event);
        
        return latestMetar;
    } catch (error) {
        console.error('Error in fetchMetarData:', error);
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            console.error('CORS Error: The API is blocking requests from your domain. You might need to:');
            console.error('1. Use a CORS proxy');
            console.error('2. Set up a backend server to make the request');
            console.error('3. Contact the API provider for CORS access');
        } else {
            console.error('Error fetching METAR data:', error);
        }
        // Update UI to show error
        const metarElement = document.getElementById('metarText');
        if (metarElement) {
            metarElement.textContent = 'Error loading METAR';
        }
        return null;
    }
}

// Function to fetch TAF data
async function fetchTafData() {
    try {
        const response = await fetch('https://api.met.no/weatherapi/tafmetar/1.0/taf.xml?icao=enbr');
        const xmlText = await response.text();
        
        // Parse the XML
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlText, "text/xml");
        
        // Get the latest TAF text
        const tafElements = xmlDoc.getElementsByTagName('metno:tafText');
        
        if (!tafElements || tafElements.length === 0) {
            throw new Error('No TAF elements found in the response');
        }
        
        const latestTaf = tafElements[tafElements.length - 1].textContent;
        
        // Store the TAF text in a variable that can be accessed globally
        window.latestTaf = latestTaf;
        
        // Update the TAF text in the UI
        const tafElement = document.getElementById('tafText');
        if (tafElement) {
            tafElement.textContent = latestTaf;
        }
        
        // You can also dispatch an event to notify that the data is ready
        const event = new CustomEvent('tafDataLoaded', { detail: { taf: latestTaf } });
        document.dispatchEvent(event);
        
        return latestTaf;
    } catch (error) {
        console.error('Error in fetchTafData:', error);
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            console.error('CORS Error: The API is blocking requests from your domain. You might need to:');
            console.error('1. Use a CORS proxy');
            console.error('2. Set up a backend server to make the request');
            console.error('3. Contact the API provider for CORS access');
        } else {
            console.error('Error fetching TAF data:', error);
        }
        // Update UI to show error
        const tafElement = document.getElementById('tafText');
        if (tafElement) {
            tafElement.textContent = 'Error loading TAF';
        }
        return null;
    }
}

// Function to refresh weather data
function refreshWeatherData() {
    fetchMetarData();
    fetchTafData();
}

// Function to schedule updates at :20 and :50 minutes past each hour
function scheduleUpdates() {
    function getTimeUntilNextUpdate() {
        const now = new Date();
        const minutes = now.getMinutes();
        const seconds = now.getSeconds();
        
        // Calculate minutes until next update (:20 or :50)
        let minutesUntilNext;
        if (minutes < 20) {
            minutesUntilNext = 20 - minutes;
        } else if (minutes < 50) {
            minutesUntilNext = 50 - minutes;
        } else {
            minutesUntilNext = 80 - minutes; // 20 minutes into next hour
        }
        
        // Convert to milliseconds and subtract seconds
        return (minutesUntilNext * 60 - seconds) * 1000;
    }
    
    function scheduleNextUpdate() {
        const delay = getTimeUntilNextUpdate();
        setTimeout(() => {
            refreshWeatherData();
            scheduleNextUpdate();
        }, delay);
    }
    
    // Initial update
    const tafElement = document.getElementById('tafText');
    const windElement = document.getElementById('wind');
    if (tafElement) {
        refreshWeatherData();
        scheduleNextUpdate();
    }

    if (windElement) {
        fetchWindData();
        setInterval(fetchWindData, 60000);
    }
}

async function checkLastUpdate() {
    const lastUpdateElement = document.getElementById('last_update');
    if (lastUpdateElement) {
        // Extract the time string (should be in the format "Sist oppdatert: HH:MM:SS ...")
        const match = lastUpdateElement.textContent.match(/(\d{2}):(\d{2}):(\d{2})/);
        if (match) {
            const serverTime = await fetch('/timestamp');
            const serverTimeText = await serverTime.text();
            const now = new Date(serverTimeText);
            const updateTime = new Date(now);
            updateTime.setHours(parseInt(match[1], 10));
            updateTime.setMinutes(parseInt(match[2], 10));
            updateTime.setSeconds(parseInt(match[3], 10));
            
            // Handle possible day transition (if last update was just before midnight)
            if (updateTime > now) {
                updateTime.setDate(updateTime.getDate() - 1);
            }
            
            const diffMs = now - updateTime;
            const diffMinutes = diffMs / (60 * 1000);

            if (diffMinutes > 10 || lastUpdateElement.textContent.includes('Feilet')) {
                // More than 10 minutes old
                lastUpdateElement.style.backgroundColor = 'red';
            }
        }
    }

}

async function fetchWindData() {
    try {
        const response = await fetch('/wind_fedje');
        const data = await response.json();
        
        if (!data) {
            throw new Error('Invalid wind data format');
        };

        const vind = data["2"].Value.toFixed(1)
        const kast = data["3"].Value.toFixed(1)
        const retning = data["1"].Value.toFixed(0)
        const tid = new Date(data["2"].Timestamp).toLocaleTimeString('nb-NO', { 
            timeZone: 'Europe/Oslo',
            hour: '2-digit',
            minute: '2-digit'
        });

        const windElement = document.getElementById('wind');
        if (windElement) {
            windElement.textContent = `Vind Fedje kl ${tid}: ${vind} m/s, ${String(retning).padStart(3, '0')}°, ${kast} m/s i kastene`;
        }

        return null;    
    } catch (error) {
        console.error('Error fetching wind data:', error);
        return null;
    }
}


function formatDistanceValue(key, value) {
    if (value === null || value === undefined || value === '') {
        return '—';
    }
    if (key === 'dist') {
        return `${value} nm`;
    }
    if (key === 'sog') {
        return `${value} kn`;
    }
    if (key === 'cog' || key === 'hdg' || key === 'tgt_cog' || key === 'diff_cog') {
        return `${value}°`;
    }
    if (key === 'msgtime') {
        const date = new Date(value);
        if (!Number.isNaN(date.getTime())) {
            return date.toLocaleString('nb-NO', {
                timeZone: 'Europe/Oslo',
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }
    return String(value);
}

function distLabelForDest(dest) {
    if (dest === 'mon') {
        return 'Distanse til Mongstad';
    }
    if (dest === 'stu') {
        return 'Distanse til Sture';
    }
    return 'Distanse til grunnlinje';
}

function renderDistanceData(data, dest) {
    const labels = {
        name: 'Skip',
        dist: distLabelForDest(dest),
        sog: 'Fart over grunn',
        ttg: 'Tid igjen rett linje (t:m)',
        hdg: 'Heading',
        cog: 'Kurs over grunn',
        tgt_cog: 'Kurs mot mål',
        diff_cog: 'Kursavvik',
        age: 'Oppdatert for:'
    };
    const order = ['dist', 'sog', 'ttg', 'hdg', 'cog', 'tgt_cog', 'diff_cog', 'age'];
    const rows = order
        .filter((key) => Object.prototype.hasOwnProperty.call(data, key))
        .map((key) => `
            <tr>
                <th class="fw-normal text-muted pe-2">${labels[key] || key}</th>
                <td class="text-end">${formatDistanceValue(key, data[key])}</td>
            </tr>
        `)
        .join('');
    return `<table class="table table-sm table-borderless mb-0">${rows}</table>`;
}

function initDistanceLinks() {
    const modalElement = document.getElementById('distanceModal');
    const modalBody = document.getElementById('distanceModalBody');
    const modalTitle = document.getElementById('distanceModalLabel');
    if (!modalElement || !modalBody) {
        return;
    }

    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

    document.querySelectorAll('.distance-link').forEach((link) => {
        link.addEventListener('click', async (event) => {
            event.preventDefault();
            const callsign = link.dataset.callsign;
            const dest = link.dataset.dest || 'hg';
            const shipName = link.dataset.name || '';
            modalTitle.textContent = callsign ? `${shipName} (${callsign})` : shipName;
            modalBody.innerHTML = '<p class="mb-0 text-muted">Laster…</p>';
            modal.show();

            try {
                const response = await fetch(`/distance?callsign=${encodeURIComponent(callsign)}&dest=${encodeURIComponent(dest)}`);
                const payload = await response.json();
                if (!response.ok || payload.error) {
                    modalBody.innerHTML = `<p class="mb-0 text-danger">${payload.error || 'Kunne ikke hente distanse'}</p>`;
                    return;
                }
                if (!payload.distance) {
                    modalBody.innerHTML = '<p class="mb-0 text-danger">Ingen AIS-data funnet</p>';
                    return;
                }
                modalBody.innerHTML = renderDistanceData(payload.distance, dest);
            } catch (error) {
                console.error('Error fetching distance:', error);
                modalBody.innerHTML = '<p class="mb-0 text-danger">Kunne ikke hente distanse</p>';
            }
        });
    });
}

// Call the scheduling function when the page loads
document.addEventListener('DOMContentLoaded', () => {
    scheduleUpdates();
    checkLastUpdate();
    setInterval(checkLastUpdate, 60000); // Check every minute
    initDistanceLinks();
});