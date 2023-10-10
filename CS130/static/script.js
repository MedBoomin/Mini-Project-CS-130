// Function to update the table with data
function updateTable() {
    fetch('/log') // Fetch data from the /log endpoint
        .then((response) => response.json()) // Parse response as JSON
        .then((data) => {
            const tableBody = document.querySelector('#data-table tbody');
            tableBody.innerHTML = ''; // Clear the existing table rows

            data.forEach((entry) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${entry.input}</td>
                    <td>${entry.result}</td>
                    <td>${entry.timestamp}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch((error) => {
            console.error('Error fetching data:', error);
        });
}

// Wait for the DOM to be ready
document.addEventListener("DOMContentLoaded", function () {
    // Call the updateTable function immediately to load data when the page loads
    updateTable();

    // Handle manual enqueuing when the enqueue button is clicked
    const enqueueButton = document.querySelector('#enqueue-button');
    enqueueButton.addEventListener('click', () => {
        const inputField = document.querySelector('#integer');
        const inputValue = inputField.value.trim();

        if (inputValue !== '') {
            // Send the input value to the server via POST request
            fetch('/hook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ integer: parseInt(inputValue) }),
            })
            .then((response) => {
                if (response.status === 200) {
                    // If the POST request is successful, update the table
                    updateTable();
                } else {
                    console.error('Failed to enqueue:', response.status);
                }
            })
            .catch((error) => {
                console.error('Error sending POST request:', error);
            });

            // Clear the input field
            inputField.value = '';
        } else {
            console.error('Invalid input. Please enter a valid integer.');
        }
    });

    // Update the table periodically (every 3 seconds in this example)
    setInterval(updateTable, 3000);
});
