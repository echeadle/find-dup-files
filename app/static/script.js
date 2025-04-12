// Ensure the DOM is fully loaded before running the script
document.addEventListener('DOMContentLoaded', () => {
    const scanDirInput = document.getElementById('scanDir');
    const scanBtn = document.getElementById('scanBtn');
    const statusMessageDiv = document.getElementById('statusMessage');
    const resultsContainer = document.getElementById('resultsContainer');

    // Check if all required elements exist before proceeding
    if (!scanDirInput || !scanBtn || !statusMessageDiv || !resultsContainer) {
        console.error("One or more required HTML elements not found. Script cannot initialize.");
        if (statusMessageDiv) {
             statusMessageDiv.textContent = "Error: UI elements missing. Cannot initialize.";
             statusMessageDiv.style.color = 'red';
        }
        return; // Stop script execution if elements are missing
    }

    // Function to fetch and display duplicates
    async function fetchDuplicates() {
        statusMessageDiv.textContent = 'Status: Fetching duplicates...';
        statusMessageDiv.style.color = '#333'; // Reset color
        resultsContainer.innerHTML = '<h2>Scan Results</h2><p>Loading...</p>'; // Clear previous results

        try {
            // *** Use /api/ prefix ***
            const response = await fetch('/api/duplicates');
            if (!response.ok) {
                // Try to get error details from the response body if available
                let errorMsg = `HTTP error! status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.detail || errorMsg;
                } catch (e) {
                    // Ignore if response body is not JSON or empty
                }
                throw new Error(errorMsg);
            }
            const duplicatesData = await response.json();

            resultsContainer.innerHTML = '<h2>Scan Results</h2>'; // Clear loading message

            let duplicateGroupsFound = 0;
            if (Object.keys(duplicatesData).length > 0) {
                for (const hash in duplicatesData) {
                    const files = duplicatesData[hash];
                    if (files.length > 1) { // Only show groups with actual duplicates
                        duplicateGroupsFound++;
                        const groupDiv = document.createElement('div');
                        groupDiv.className = 'dup-group';

                        const title = document.createElement('h4');
                        // Show partial hash for readability
                        title.innerHTML = `Duplicate Group (Hash: <code>${hash.substring(0, 12)}...</code>)`;
                        groupDiv.appendChild(title);

                        const fileList = document.createElement('ul');
                        files.forEach(filePath => {
                            const listItem = document.createElement('li');
                            listItem.textContent = filePath;
                            fileList.appendChild(listItem);
                        });
                        groupDiv.appendChild(fileList);
                        resultsContainer.appendChild(groupDiv);
                    }
                }
            }

            // Display message if no duplicate groups were rendered
            if (duplicateGroupsFound === 0) {
                resultsContainer.innerHTML += '<p>No duplicate files found in the database.</p>';
            }

            statusMessageDiv.textContent = 'Status: Duplicates loaded successfully.';

        } catch (error) {
            console.error('Error fetching duplicates:', error);
            statusMessageDiv.textContent = `Status: Error fetching duplicates - ${error.message}`;
            statusMessageDiv.style.color = 'red';
            resultsContainer.innerHTML = '<h2>Scan Results</h2><p>Could not load duplicate results.</p>';
        }
    }

    // Event listener for the scan button
    scanBtn.addEventListener('click', async () => {
        const directoryPath = scanDirInput.value.trim();
        if (!directoryPath) {
            statusMessageDiv.textContent = 'Status: Please enter a directory path.';
            statusMessageDiv.style.color = 'orange'; // Use a warning color
            return;
        }

        statusMessageDiv.textContent = `Status: Starting scan for "${directoryPath}"...`;
        statusMessageDiv.style.color = '#333'; // Reset color
        scanBtn.disabled = true; // Disable button during scan
        scanDirInput.disabled = true; // Disable input during scan
        resultsContainer.innerHTML = '<h2>Scan Results</h2><p>Scan in progress...</p>'; // Clear previous results

        try {
            // *** Use /api/ prefix ***
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                // Ensure the key matches what the backend expects (e.g., 'directory_path')
                body: JSON.stringify({ directory_path: directoryPath }),
            });

            const result = await response.json(); // Always try to parse JSON

            if (!response.ok) {
                 // Try to get more specific error from backend response
                const errorMsg = result.detail || `Scan failed. HTTP status: ${response.status}`;
                throw new Error(errorMsg);
            }

            statusMessageDiv.textContent = `Status: ${result.message || 'Scan initiated...'}. Fetching results...`;
            // After scan is initiated (or completed), fetch the duplicates.
            await fetchDuplicates(); // Refresh results

        } catch (error) {
            console.error('Error starting scan:', error);
            statusMessageDiv.textContent = `Status: Error during scan - ${error.message}`;
            statusMessageDiv.style.color = 'red';
            resultsContainer.innerHTML = '<h2>Scan Results</h2><p>Scan failed to start or complete.</p>';
        } finally {
             scanBtn.disabled = false; // Re-enable button
             scanDirInput.disabled = false; // Re-enable input
        }
    });

    // Initial load of duplicates when the page loads
    fetchDuplicates();
});
