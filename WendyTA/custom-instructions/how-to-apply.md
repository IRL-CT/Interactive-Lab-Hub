# How to Apply WendyTA Custom Instructions

## Method 1: GitHub Copilot Custom Instructions (Recommended)

This is the official way to customize GitHub Copilot as mentioned in the GitHub documentation.

### Steps:

1. **Open VS Code**
2. **Access Command Palette**: Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
3. **Find Custom Instructions**: Type "Copilot: Edit Custom Instructions"
4. **Open Instructions File**: This will open a file where you can paste custom instructions
5. **Copy WendyTA Instructions**: Copy the entire content from `wendyta-instructions.md`
6. **Paste and Save**: Paste the instructions and save the file
7. **Restart Copilot**: Reload VS Code or restart the Copilot extension

### Verification:

Open Copilot Chat and ask: "Hi, what's your name and role?"
WendyTA should respond identifying itself as a Teaching Assistant for the Interactive Lab Hub course.

## Method 2: Chat Context Setting

If Method 1 doesn't work in your VS Code version:

### Steps:

1. **Open Copilot Chat**: Press `Ctrl+Shift+I` / `Cmd+Shift+I`
2. **Start New Session**: Click the "New Chat" button if there's an existing conversation
3. **Provide Context**: Copy and paste the WendyTA instructions as your first message
4. **Add Prefix**: Start with "Please act according to these instructions:"
5. **Begin Interaction**: After Copilot acknowledges, start asking your course-related questions

### Note:
This method requires you to provide the context at the beginning of each new chat session.

## Method 3: Workspace Configuration

Create a workspace-specific configuration:

### Steps:

1. **Create .vscode folder** in your lab directory (if it doesn't exist)
2. **Create settings.json** file in the .vscode folder
3. **Add Configuration**:
```json
{
    "github.copilot.chat.welcomeMessage": "Hi! I'm WendyTA, your AI Teaching Assistant for the Interactive Lab Hub course. I'm here to help you with Raspberry Pi programming, hardware integration, and design questions. What are you working on today?",
    "github.copilot.enable": {
        "*": true,
        "yaml": true,
        "plaintext": true,
        "markdown": true
    }
}
```

## Testing Your Setup

Once you've applied the custom instructions, test with these questions:

### Basic Identity Test:
"Hi WendyTA, who are you and what do you help with?"

### Course-Specific Test:
"I'm working on Lab 2 and having trouble with my OLED display. Can you help?"

### Teaching Style Test:
"Can you just write the code for my proximity sensor?"
(WendyTA should offer to guide you through it rather than just providing code)

## Troubleshooting

### Custom Instructions Not Working:
- Make sure you're using the latest version of the GitHub Copilot extension
- Try Method 2 (Chat Context Setting) as a fallback
- Restart VS Code completely
- Check that your GitHub Copilot subscription is active

### WendyTA Not Responding as Expected:
- Clear your chat history and start fresh
- Re-apply the custom instructions
- Make sure you copied the complete instructions file

### Alternative: Manual Context
If automated methods don't work, simply start each Copilot Chat session by saying:
"Please act as WendyTA, my teaching assistant for an Interactive Lab Hub course focused on Raspberry Pi and physical computing. Help me learn by asking guiding questions rather than giving direct answers."

## Need Help?

If you're having trouble with setup:
1. Check the troubleshooting section in `../setup/copilot-setup.md`
2. Ask in the class discussion forum
3. Visit office hours
4. Try the alternative methods above

Remember: The goal is to have an AI assistant that helps you learn, not one that does the work for you!
