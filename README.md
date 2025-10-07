# GitHub Auto-Uploader 🚀

![GitHub Auto-Uploader Screenshot](https://via.placeholder.com/800x400.png?text=App+Screenshot+Here)

> A sleek web application that allows you to upload a zipped project and instantly create a new GitHub repository, all without touching the command line.

This tool is designed for developers who want a quick and easy way to push new projects to GitHub. With a secure OAuth2 login, real-time progress feedback, and a modern UI, it streamlines the initial setup of a new repository.

---

## ✨ Features

- **Modern, Dark UI:** A beautiful and intuitive interface built with Tailwind CSS.
- **Secure GitHub Login:** Authenticates using the official GitHub OAuth2 flow. Your credentials are never stored or exposed.
- **Real-time Progress:** A live console log shows you the status of your repository creation and file uploads.
- **Smart Uploading:** Automatically respects your project's `.gitignore` file, ensuring only necessary files are uploaded.
- **Customization Options:** Easily specify the repository name, visibility (public/private), target branch, and commit message.
- **Dynamic Landing Page:** A mini-landing page introduces the platform to new users.

## 🛠️ Tech Stack

- **Backend:** Flask, Flask-SocketIO
- **Frontend:** Tailwind CSS, JavaScript
- **Authentication:** GitHub OAuth2
- **Deployment:** Python, Gunicorn (recommended for production)

## ⚙️ Setup and Installation

Follow these steps to get the application running on your local machine.

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Create a GitHub OAuth App

To use the GitHub login, you need to register a new OAuth application.

- Go to **[GitHub Developer Settings](https://github.com/settings/developers)**.
- Click **New OAuth App**.
- Fill in the details:
  - **Application name:** `GitHub Auto-Uploader`
  - **Homepage URL:** `http://127.0.0.1:5000`
  - **Authorization callback URL:** `http://127.0.0.1:5000/github/callback`
- Generate a **new client secret** and copy both the **Client ID** and the **Client Secret**.

### 3. Configure Environment Variables

- In the project root, copy the `.env.example` file to a new file named `.env`.
- Open the `.env` file and paste your GitHub Client ID and Secret.

```
GITHUB_CLIENT_ID=your_client_id_here
GITHUB_CLIENT_SECRET=your_client_secret_here
SECRET_KEY=a_long_random_string_for_flask_sessions
```

### 4. Install Dependencies

Create a virtual environment and install the required packages.

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install packages
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python main.py
```

The application will be available at `http://127.0.0.1:5000`.

##  usage

1.  **Login:** Click the "Login with GitHub" button to authorize the application.
2.  **Fill out the form:** Provide a repository name, select your zipped project file, and set any other options.
3.  **Upload:** Click "Upload to GitHub" and watch the live progress.
4.  **Done:** Once complete, you'll get a success message and a direct link to your new repository.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

&copy; 2025 Ghostscript. All Rights Reserved.
