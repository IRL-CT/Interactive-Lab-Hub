# WendyTA - Your AI Teaching Assistant

Welcome to **WendyTA**, your AI-powered Teaching Assistant for the Interactive Lab Hub course! WendyTA is designed to help you succeed in your physical computing and Raspberry Pi projects by providing personalized guidance, debugging assistance, and learning support.
![WendyTA Logo](custom-instructions/WendyTA.png)

## What is WendyTA?

WendyTA is a customized version of GitHub Copilot that acts as your personal teaching assistant. Named after Professor Wendy, WendyTA has been specifically trained to understand the context of your course and provide helpful, educational guidance rather than just giving you answers.

### What WendyTA Can Help With:

- 🔧 **Hardware Debugging**: Troubleshoot Raspberry Pi, sensor, and circuit issues
- 💻 **Code Review**: Help improve your Python, JavaScript, and other code
- 🧠 **Concept Explanation**: Break down complex topics in physical computing
- 🎯 **Design Guidance**: Provide feedback on your interactive projects
- 🔍 **Problem Solving**: Guide you through systematic debugging approaches
- 📚 **Learning Support**: Explain programming concepts and best practices

### What Makes WendyTA Special:

- **Educational Focus**: Asks guiding questions to help you learn, rather than just providing answers
- **Course Context**: Understands your lab assignments and course objectives
- **Systematic Approach**: Teaches you debugging and problem-solving methodologies
- **Safety Conscious**: Always considers electrical safety and proper component handling
- **Progress Tracking**: Logs interactions to help instructors improve the course (with your consent)

## Quick Start Guide

### 1. Set Up GitHub Copilot
Follow the comprehensive setup guide: [`setup/copilot-setup.md`](setup/copilot-setup.md)

This includes:
- Getting your free GitHub Student license
- Installing GitHub Copilot in VS Code
- Configuring the extension

### 2. Apply WendyTA Instructions
Configure Copilot to act as WendyTA: [`custom-instructions/how-to-apply.md`](custom-instructions/how-to-apply.md)

### 3. Start Asking Questions!
Open Copilot Chat in VS Code (`Ctrl+Shift+I` / `Cmd+Shift+I`) and try:
- "Hi WendyTA, I'm working on Lab 2 and my OLED display isn't working"
- "Can you help me understand I2C communication?"
- "My servo motor is acting strange, where should I start debugging?"

## How to Interact with WendyTA

### Best Practices for Getting Help

#### 🎯 **Be Specific About Context**
❌ Bad: "My code doesn't work"
✅ Good: "I'm working on Lab 3, trying to set up MQTT communication, but getting a connection timeout error"

#### 📋 **Provide Relevant Details**
When asking for help, include:
- Which lab assignment you're working on
- What hardware components you're using
- What error messages you're seeing
- What you've already tried

#### 🤔 **Embrace the Learning Process**
WendyTA will often ask you questions back - this is intentional! The goal is to help you:
- Develop systematic debugging skills
- Understand underlying concepts
- Build confidence in problem-solving

#### 🔄 **Follow Up and Iterate**
Don't hesitate to:
- Ask follow-up questions
- Request clarification
- Share what you tried based on WendyTA's suggestions

### Example Conversation Flow

```
You: "Hi WendyTA, my proximity sensor isn't giving consistent readings"

WendyTA: "Let's debug this systematically! First, can you tell me:
1. Which proximity sensor model are you using?
2. How is it wired to your Raspberry Pi?
3. What kind of inconsistencies are you seeing?
4. Are you seeing this in all conditions or specific situations?"

You: "I'm using the VL53L0X, wired via I2C. Sometimes it reads 50mm when nothing is there, other times it's accurate"

WendyTA: "Interesting! Intermittent I2C sensor issues often relate to a few common causes:
- Power supply stability
- I2C address conflicts
- Environmental interference

Let's start with the basics: Can you run `i2cdetect -y 1` and tell me what addresses show up? Also, are you using a breadboard or more permanent connections?"

[Conversation continues with guided troubleshooting...]
```

## Course Integration

### Lab-Specific Help

WendyTA is familiar with all course labs:

- **Lab 1**: Raspberry Pi setup, basic GPIO, getting started
- **Lab 2**: Displays (OLED, LCD), buttons, I2C communication, sensors
- **Lab 3**: Networking, speech processing, web interfaces, Flask apps
- **Lab 4**: Advanced sensors, actuators, servo motors, cameras
- **Lab 5**: Computer vision, machine learning, TensorFlow Lite
- **Lab 6**: Distributed systems, MQTT, IoT communication

### Design Project Support

For your final projects, WendyTA can help with:
- **Concept Development**: Brainstorming interactive ideas
- **Technical Feasibility**: Assessing if your ideas are achievable
- **Component Selection**: Choosing the right sensors and actuators
- **System Architecture**: Planning your hardware and software design
- **Implementation Strategy**: Breaking down complex projects into manageable steps

## Privacy and Logging

### Optional Interaction Logging

To help improve the course, you can opt-in to having your WendyTA interactions logged:

- **What's Logged**: Course-related questions and WendyTA's responses
- **What's NOT Logged**: Personal information or non-course conversations
- **Access**: Only instructors and TAs can review logs
- **Purpose**: Identify common learning challenges and improve course content
- **Control**: You can opt-out or request log deletion at any time

See [`logging/setup-logging.md`](logging/setup-logging.md) for details.

### Data Privacy

- All interactions stay within your GitHub repository
- No data is sent to external services beyond GitHub Copilot
- You maintain control over your learning data
- Instructors only access logs to improve the course

## Troubleshooting

### Common Issues and Solutions

#### WendyTA Doesn't Respond as Expected
- Make sure you've applied the custom instructions correctly
- Try starting a new chat session
- Clear your chat history and re-apply the context

#### GitHub Copilot Not Working
- Verify your student license is active
- Check that you're signed in to GitHub in VS Code
- Restart VS Code after installation
- Ensure you have an internet connection

#### Getting Generic Responses
- Be more specific about your course context
- Mention the lab you're working on
- Include details about your hardware setup

### Getting Additional Help

If WendyTA can't solve your problem:

1. **Search Course Resources**: Check lab documentation and examples
2. **Ask Classmates**: Use the course discussion forum
3. **Office Hours**: Visit instructor or TA office hours
4. **Human Review**: Sometimes you need human expertise!

Remember: WendyTA is a powerful learning tool, but it's not a replacement for human instructors and peer collaboration.

## Advanced Usage

### Code Review and Optimization

WendyTA can help you:
- Review your code for best practices
- Suggest performance improvements
- Identify potential bugs or edge cases
- Explain complex programming concepts

### Research and Exploration

Ask WendyTA about:
- Alternative approaches to problems
- Related technologies and concepts
- Integration possibilities between different components
- Industry applications of what you're learning

### Project Planning

For larger projects:
- Break down complex ideas into manageable tasks
- Identify potential technical challenges early
- Plan your development timeline
- Consider user experience and interaction design

## Contributing to WendyTA's Improvement

Your interactions help make WendyTA better for future students:

- **Provide Feedback**: Let instructors know what works well and what doesn't
- **Report Issues**: If WendyTA gives incorrect or unhelpful advice, report it
- **Suggest Improvements**: Ideas for better responses or new capabilities
- **Share Success Stories**: Help us understand what makes interactions effective

## Files and Resources

```
WendyTA/
├── README.md                           # This file
├── setup/
│   └── copilot-setup.md               # GitHub Copilot installation guide
├── custom-instructions/
│   ├── wendyta-instructions.md        # The full WendyTA personality and instructions
│   └── how-to-apply.md               # How to configure Copilot with WendyTA
└── logging/
    ├── setup-logging.md              # Interaction logging system
    ├── templates/
    │   └── session-template.md       # Template for manual logging
    └── analyze-interactions.py       # Analysis script for instructors
```

## Frequently Asked Questions

### Is WendyTA always available?
Yes! As long as you have internet access and GitHub Copilot is working, WendyTA is available 24/7.

### Can WendyTA do my homework for me?
No, and it won't! WendyTA is designed to help you learn by guiding you through problems, not by providing complete solutions.

### What if WendyTA doesn't know something?
WendyTA will tell you when it's not sure and suggest alternative resources or recommend asking human instructors.

### Can I use WendyTA for other courses?
The custom instructions are specific to this course, but you can modify them or use regular GitHub Copilot for other programming tasks.

### How accurate is WendyTA's advice?
WendyTA is quite knowledgeable, but always verify important information and test solutions thoroughly. When in doubt, consult human instructors.

---

## Get Started Today!

Ready to begin your journey with WendyTA? 

1. 📖 **Read the setup guide**: [`setup/copilot-setup.md`](setup/copilot-setup.md)
2. ⚙️ **Configure WendyTA**: [`custom-instructions/how-to-apply.md`](custom-instructions/how-to-apply.md)
3. 💬 **Start chatting**: Open Copilot Chat in VS Code and say hello!

Welcome to a new way of learning with AI assistance! WendyTA is here to support your journey in physical computing and interactive design.

**Happy building! 🚀🤖**

---

*Questions about WendyTA? Ask in the course discussion forum or visit office hours.*
