// Handle form submission
document.getElementById('scan-form').addEventListener('submit', async (event) => {
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

    duplicates.forEach(group => {
        group.forEach(file => {
            const row = tableBody.insertRow();
            const pathCell = row.insertCell();
            const sizeCell = row.insertCell();
            const hashCell = row.insertCell();

            pathCell.textContent = file.path;
            sizeCell.textContent = file.size;
            hashCell.textContent = file.hash;
        });
        // Add a separator row between duplicate groups
        const separatorRow = tableBody.insertRow();
        separatorRow.innerHTML = '<td colspan="3"><hr></td>';
    });
}
