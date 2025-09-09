# GitHub Copilot Setup for Students

Welcome to the Interactive Lab Hub! This guide will help you set up GitHub Copilot in Visual Studio Code to work with **WendyTA**, your AI teaching assistant.

## What is GitHub Copilot?

GitHub Copilot is an AI-powered code completion tool that helps you write code faster and learn programming concepts. For this class, we've configured it to act as **WendyTA**, your virtual teaching assistant who can:

- Answer questions about lab assignments
- Help debug your code
- Explain programming concepts
- Provide guidance on design tasks
- Assist with hardware integration problems

## Prerequisites

1. **GitHub Account**: You need a GitHub account (you should already have this for the class)
2. **Visual Studio Code**: Download and install VS Code from [code.visualstudio.com](https://code.visualstudio.com/)
3. **Student License**: You need to verify your student status to get free access

## Step 1: Get Your GitHub Student License

GitHub Copilot is normally a paid service, but it's **FREE for verified students**!

### Apply for GitHub Student Developer Pack:

1. Go to [education.github.com](https://education.github.com/)
2. Click "Get benefits" or "Apply for Student Developer Pack"
3. Sign in with your GitHub account
4. Fill out the application form:
   - Use your **school email address** (.edu domain)
   - Upload proof of enrollment (student ID, transcript, or enrollment verification)
   - Provide your school name and graduation date

### Verification Process:
- **Automatic approval**: If you use a .edu email, you might get instant approval
- **Manual review**: If not automatic, GitHub will review your application (usually takes 1-7 days)
- **Check status**: Go to [education.github.com/discount](https://education.github.com/discount) to check your application status

## Step 2: Install GitHub Copilot in VS Code

Once your student status is verified:

### Install the Extension:

1. Open Visual Studio Code
2. Click on the Extensions icon in the sidebar (or press `Ctrl+Shift+X` / `Cmd+Shift+X`)
3. Search for "GitHub Copilot"
4. Install the **GitHub Copilot** extension by GitHub
5. Also install **GitHub Copilot Chat** extension for enhanced interaction

### Sign In to GitHub:

1. After installation, VS Code will prompt you to sign in
2. Click "Sign in to GitHub"
3. Authorize VS Code to access your GitHub account
4. VS Code should automatically detect your student license

### Verify Installation:

1. Open any code file (like a `.py` or `.js` file)
2. Start typing some code - you should see Copilot suggestions in gray text
3. Press `Tab` to accept suggestions
4. Open Copilot Chat by pressing `Ctrl+Shift+I` / `Cmd+Shift+I`

## Step 3: Configure WendyTA

### Apply Custom Instructions:

1. In VS Code, open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Type "Copilot: Configure Custom Instructions"
3. Copy and paste the WendyTA instructions from `../custom-instructions/wendyta-instructions.md`
4. Save the configuration

### Test Your Setup:

Open Copilot Chat and try asking:
- "Hello WendyTA, what lab are we working on today?"
- "Can you help me understand the assignment requirements?"
- "I'm having trouble with my Raspberry Pi setup"

## Step 4: Enable Logging (Optional)

To help instructors improve the course, you can enable interaction logging:

1. Follow the instructions in `../logging/setup-logging.md`
2. This will create logs of your WendyTA interactions in your branch
3. **Privacy Note**: Only your course-related questions and WendyTA's responses are logged

## Troubleshooting

### Student License Issues:
- **Not a student?** You'll need to purchase a Copilot license
- **License not recognized?** Wait 24 hours after approval, then restart VS Code
- **Still having issues?** Contact GitHub Education support

### Extension Problems:
- **Copilot not working?** Check if you're signed in: Look for GitHub icon in VS Code status bar
- **No suggestions appearing?** Make sure Copilot is enabled in VS Code settings
- **Chat not working?** Ensure both Copilot and Copilot Chat extensions are installed

### Common Solutions:
1. **Restart VS Code** after installation
2. **Check internet connection** - Copilot requires internet access
3. **Update extensions** to the latest version
4. **Sign out and sign back in** to GitHub

## Getting Help

If you're still having trouble:

1. **Check the GitHub Copilot documentation**: [docs.github.com/copilot](https://docs.github.com/en/copilot)
2. **Ask in class discussion forum**
3. **Contact your TA or instructor**
4. **Visit office hours**

## What's Next?

Once you have Copilot set up with WendyTA:

1. Read the main WendyTA documentation (`../README.md`)
2. Learn how to interact effectively with your AI TA
3. Start using WendyTA for your lab assignments!

Remember: WendyTA is here to help you learn, not to do your work for you. Use it as a learning tool to understand concepts and debug problems.

---

**Happy coding with WendyTA! 🚀**
