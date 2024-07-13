document.getElementById('invoice-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);
    const response = await fetch('/generate-invoice', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
            'Content-Type': 'application/json'
        }
    });
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'invoice.pdf';
    document.body.appendChild(a);
    a.click();
    a.remove();

    // Update document list
    const listItem = document.createElement('li');
    listItem.textContent = 'invoice.pdf - ' + new Date().toLocaleString();
    document.getElementById('document-list').appendChild(listItem);
});

async function fetchLogs() {
    const response = await fetch('/get-logs');
    const logs = await response.json();
    const documentList = document.getElementById('document-list');
    logs.forEach(log => {
        const listItem = document.createElement('li');
        listItem.textContent = `${log.filename} - ${log.timestamp}`;
        documentList.appendChild(listItem);
    });
}

document.addEventListener('DOMContentLoaded', fetchLogs);
