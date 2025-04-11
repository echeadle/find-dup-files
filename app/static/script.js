async function fetchDuplicates() {
    const response = await fetch('/api/duplicates');
    if (!response.ok) {
        const errorDiv = document.getElementById('error');
        errorDiv.textContent = `Error fetching duplicates: ${response.statusText}`;
        errorDiv.style.color = 'red';
        return;
    }
    const duplicates = await response.json();

    const tableBody = document.querySelector('#duplicates-table tbody');
    tableBody.innerHTML = ''; // Clear existing rows

    if (duplicates.length === 0) {
        const statusDiv = document.getElementById('status');
        statusDiv.textContent = 'No duplicates found.';
        return;
    }

    duplicates.forEach(file => {
        const row = tableBody.insertRow();
        const pathCell = row.insertCell();
        pathCell.textContent = file.path;
    });
}

async function loadConfigPage() {
    const contentDiv = document.getElementById('content');
    contentDiv.innerHTML = `
        <h2>Configuration</h2>
        <ul id="excluded-directories-list"></ul>
        <form id="add-directory-form">
            <input type="text" id="new-directory" placeholder="New directory to exclude">
            <button type="submit">Add</button>
        </form>
        <button id="save-config">Save</button>
    `;

    const excludedDirectoriesList = document.getElementById('excluded-directories-list');
    const addDirectoryForm = document.getElementById('add-directory-form');
    const saveConfigButton = document.getElementById('save-config');

    async function fetchConfig() {
        const response = await fetch('/api/config');
        const config = await response.json();
        excludedDirectoriesList.innerHTML = '';
        config.excluded_directories.forEach(dir => {
            const li = document.createElement('li');
            li.textContent = dir;
            excludedDirectoriesList.appendChild(li);
        });
    }

    await fetchConfig();

    addDirectoryForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const newDirectory = document.getElementById('new-directory').value;
        const config = await fetch('/api/config').then(res => res.json());
        config.excluded_directories.push(newDirectory);
        await fetch('/api/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        await fetchConfig();
    });

    saveConfigButton.addEventListener('click', async () => {
        const config = await fetch('/api/config').then(res => res.json());
        await fetch('/api/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
    });
}

async function loadHomePage() {
    const contentDiv = document.getElementById('content');
    contentDiv.innerHTML = `
        <form id="scan-form">
            <label for="directory">Directory to Scan:</label>
            <input type="text" id="directory" name="directory" placeholder="Enter directory" required/>
            <button type="submit">Scan</button>
        </form>
        
        <div id="status"></div>
        <div id="error"></div>

        <h2>Duplicate Files</h2>
        <table id="duplicates-table">
            <thead>
                <tr>
                    <th>File Path</th>
                </tr>
            </thead>
            <tbody>
                <!-- Duplicate file entries will be added here -->
            </tbody>
        </table>
    `;
    const scanForm = document.getElementById('scan-form');
    scanForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission

        const directory = document.getElementById('directory').value;
        const statusDiv = document.getElementById('status');
        const errorDiv = document.getElementById('error');
        statusDiv.textContent = 'Scanning...';
        errorDiv.textContent = ''; // Clear any previous errors

        try {
            const response = await fetch(`/api/scan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ directory })
            });

            if (!response.ok) {
                const errorData = await response.json();
                errorDiv.textContent = `Error: ${errorData.detail}`;
                errorDiv.style.color = 'red';
                return;
            }

            const data = await response.json();
            statusDiv.textContent = data.message;
            fetchDuplicates(); // Refresh the duplicates table
        } catch (error) {
            errorDiv.textContent = `An unexpected error occurred: ${error.message}`;
            errorDiv.style.color = 'red';
        }
    });
    fetchDuplicates();
}

window.addEventListener('load', async () => {
    const path = window.location.pathname;
    if (path === '/config') {
        await loadConfigPage();
    } else {
        await loadHomePage();
    }
});
