document.addEventListener('DOMContentLoaded', () => {
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    const form = document.getElementById('upload-form');
    const submitBtn = document.getElementById('submit-btn');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const logOutput = document.getElementById('log-output');
    const resultContainer = document.getElementById('result-container');
    const resultMessage = document.getElementById('result-message');
    const repoUrl = document.getElementById('repo-url');

    if (form) {
        form.addEventListener('submit', (event) => {
            event.preventDefault();

            // Get form data
            const repoName = document.getElementById('repo-name').value;
            const zipFile = document.getElementById('zip-file').files[0];
            const branch = document.getElementById('branch').value;
            const visibility = document.getElementById('visibility').value;
            const commitMessage = document.getElementById('commit-message').value;

            if (!zipFile) {
                alert('Please select a .zip file.');
                return;
            }

            // Disable form and show progress
            form.classList.add('d-none');
            progressContainer.classList.remove('d-none');
            resultContainer.classList.add('d-none'); // Hide result container
            logOutput.textContent = '';
            progressBar.style.width = '0%';
            progressBar.classList.remove('bg-success', 'bg-danger');

            // Read file as Base64
            const reader = new FileReader();
            reader.onload = (e) => {
                const fileData = e.target.result.split(',')[1];
                
                // Emit data to server via WebSocket
                socket.emit('upload_project', {
                    repo_name: repoName,
                    file: fileData,
                    branch: branch,
                    visibility: visibility,
                    commit_message: commitMessage
                });
            };
            reader.readAsDataURL(zipFile);
        });
    }

    const startOverBtn = document.getElementById('start-over-btn');
    if(startOverBtn) {
        startOverBtn.addEventListener('click', () => {
            resultContainer.classList.add('d-none');
            form.classList.remove('d-none');
        });
    }

    // --- Socket.IO Event Listeners ---
    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('progress', (msg) => {
        logOutput.textContent += msg.data + '\n';
        logOutput.scrollTop = logOutput.scrollHeight;
        if (msg.progress) {
            progressBar.style.width = msg.progress + '%';
        }
    });

    socket.on('success', (msg) => {
        progressBar.style.width = '100%';
        progressBar.classList.add('bg-success');
        logOutput.textContent += msg.data + '\n';
        logOutput.scrollTop = logOutput.scrollHeight;

        resultMessage.textContent = msg.data;
        repoUrl.href = msg.repo_url;
        resultContainer.classList.remove('d-none');
        progressContainer.classList.add('d-none'); // Hide progress container
    });

    socket.on('error', (msg) => {
        progressBar.style.width = '100%';
        progressBar.classList.add('bg-danger');
        logOutput.textContent += 'ERROR: ' + msg.data + '\n';
        logOutput.scrollTop = logOutput.scrollHeight;

        resultMessage.textContent = 'ERROR: ' + msg.data;
        repoUrl.href = '#';
        resultContainer.classList.remove('d-none');
        progressContainer.classList.add('d-none'); // Hide progress container
    });
});
