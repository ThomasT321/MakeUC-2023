function sendfile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response=>response.json())
        .then(data=>{ 
            document.getElementById("textDisplay").innerText = data.Description;
        })
        .catch(error => {
            console.error('Error:', error);
        });
    } else {
        console.log('No file selected.');
    }
}