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
    refreshWeatherData();
    // Schedule next update
    scheduleNextUpdate();
}

// Call the scheduling function when the page loads
document.addEventListener('DOMContentLoaded', scheduleUpdates);
