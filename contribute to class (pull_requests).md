
## How to Create a Pull Request on GitHub (Using GitHub.com Interface)

If you find an issue in the course content or have suggestions for improvement, you can contribute by creating a pull request (PR) to the main repository. Follow the steps below:

### 1. **Fork the Repository**
- Navigate to the main repository on GitHub.
- Click on the "Fork" button in the top-right corner. This will create a copy of the repository in your GitHub account.

### 2. **Edit Files in Your Forked Repository**
- In your forked repository, navigate to the file you want to edit.
- Click on the pencil icon (Edit this file) in the top-right corner of the file viewer.
- Make the necessary changes to the file.
- Scroll down and describe your changes in the "Commit changes" section. Provide a short title in the "Commit changes" box and an optional detailed description below it.
- Choose to commit the changes directly to the `main` branch (or the default branch of the repository).

### 3. **Create a Pull Request**
- After committing your changes, go to the main page of your forked repository.
- Click on the "Pull request" tab, then click the "New pull request" button.
- <img width="294" alt="Screenshot 2023-09-06 185503" src="https://github.com/FAR-Lab/Interactive-Lab-Hub/assets/90477986/af7d7b6d-9474-4c54-932f-51a23484648f">
- Ensure that the base fork points to the main repository and the head fork points to your forked repository.
- Review your changes and click on the "Create pull request" button.
- Add a descriptive title and explain the changes you made in the description box.
- <img width="427" alt="Screenshot 2023-09-06 185512" src="https://github.com/FAR-Lab/Interactive-Lab-Hub/assets/90477986/ba2f40f5-55c5-4072-9016-ed0ce9eb906d">
- Click "Create pull request" again.

### 4. **Wait for Review**
- The repository maintainers will review your pull request.
- They might ask for changes or improvements. Make sure to keep an eye on the pull request for any comments or requests.
- <img width="423" alt="Screenshot 2023-09-06 185629" src="https://github.com/FAR-Lab/Interactive-Lab-Hub/assets/90477986/c33b726c-a756-4a88-8dc8-670112c82439">


## How to Create a Pull Request on GitHub when working in a local repository

If you find an issue in the course content or have suggestions for improvement, you can contribute by creating a pull request (PR) to the main repository. Follow the steps below to create a pull request:

### 1. **Fork the Repository**
- Navigate to the main repository on GitHub.
- Click on the "Fork" button in the top-right corner. This will create a copy of the repository in your GitHub account.

### 2. **Clone the Forked Repository**
- Go to your forked repository.
- Click on the "Code" button and copy the URL.
- Open a terminal or command prompt and run: 
  ```
  git clone [URL]
  ```
  Replace `[URL]` with the URL you just copied.

### 3. **Make Your Changes**
- Navigate to the directory where you cloned the repository.
- Make the necessary changes to the files.

### 4. **Commit and Push Your Changes**
- In your terminal or command prompt, navigate to the cloned repository directory.
- Run the following commands:
  ```
  git add .
  git commit -m "Describe your changes here"
  git push origin main
  ```
  Replace `main` with the default branch name if it's different.

### 5. **Create a Pull Request**
- Go back to your forked repository on GitHub.
- Click on the "New pull request" button.
- Ensure that the base fork points to the main repository and the head fork points to your forked repository.
- Review your changes and click on the "Create pull request" button.
- Add a descriptive title and explain the changes you made in the description box.
- Click "Create pull request" again.

### 6. **Wait for Review**
- The repository maintainers will review your pull request.
- They might ask for changes or improvements. Make sure to keep an eye on the pull request for any comments or requests.
