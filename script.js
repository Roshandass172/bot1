// Handle the send button click event for the chat functionality
document.getElementById('send-btn').addEventListener('click', function() {
    const userMessage = document.getElementById('user-message').value;

    // Ensure the message isn't empty
    if (!userMessage.trim()) return;

    // Display the user message in the chat window
    const messageElement = document.createElement('div');
    messageElement.textContent = "You: " + userMessage;
    messageElement.classList.add('user-message');
    document.getElementById('messages').appendChild(messageElement);
    
    // Clear the input field after sending the message
    document.getElementById('user-message').value = '';

    // Send the message to the server and get the bot's response
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        // Display the bot's response in the chat window
        const botMessageElement = document.createElement('div');
        botMessageElement.textContent = "Bot: " + data.response;
        botMessageElement.classList.add('bot-message');
        document.getElementById('messages').appendChild(botMessageElement);

        // Scroll to the latest message
        document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
    })
    .catch(error => console.error('Error:', error));
});

// Handle the file upload and display anomalies functionality
document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault();

    // Create FormData object to handle the file upload
    const formData = new FormData();
    const fileInput = document.getElementById('csv-file');
    formData.append('file', fileInput.files[0]);

    // Send the file to the server
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.anomalies) {
            // Display the anomalies in a table format
            const anomaliesTable = document.getElementById('anomalies');
            anomaliesTable.innerHTML = `
                <tr>
                    <th>Transaction ID</th>
                    <th>Amount</th>
                    <th>Anomaly</th>
                    <th>Timestamp</th>
                </tr>
            `;
            data.anomalies.forEach(anomaly => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${anomaly.transaction_id}</td>
                    <td>${anomaly.amount}</td>
                    <td>${anomaly.anomaly}</td>
                    <td>${anomaly.timestamp}</td>
                `;
                anomaliesTable.appendChild(row);
            });

            // Show the anomalies table
            document.getElementById('anomalies-table').style.display = 'block';

            // Optionally, if there's a PDF URL to download the results:
            if (data.pdf_url) {
                // Create a download button dynamically for the PDF
                const downloadBtn = document.createElement("button");
                downloadBtn.innerHTML = "Download Anomalies Report as PDF";
                downloadBtn.onclick = function() {
                    window.location.href = data.pdf_url;
                };
                document.body.appendChild(downloadBtn);
            }
        }
    })
    .catch(error => console.error('Error uploading file:', error));
});
