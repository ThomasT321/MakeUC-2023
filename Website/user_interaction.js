const SubmitRatings = () =>
{
    
    // Collect the form data
    const formData = {
        usr_imp: new FormData(document.querySelector('form#imp')).get("bias"),
        usr_bias: new FormData(document.querySelector('form#bias')).get("bias"),
        usr_opin: new FormData(document.querySelector('form#opin')).get("bias"),
    };

    // Define the URL where you want to send the data
    const endpoint = '/submit_rating';

    // Make an HTTP POST request to send the data
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
    })
    .then(response => {
        if (response.ok) {
            // Handle a successful response here
            console.log('Data sent successfully');
        } else {
            // Handle errors or failed response
            console.error('Failed to send data');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
