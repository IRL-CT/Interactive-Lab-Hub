# WendyTA - Your AI Teaching Assistant

Welcome to **WendyTA**, your AI-powered Teaching Assistant for Cornell's "Developing and Designing Interactive Devices" course! WendyTA is designed to accelerate your iteration speed while helping you build creative confidence and technical independence in interactive device design.

![WendyTA](WendyTA.png)

## What is WendyTA?

WendyTA is a repository-level GitHub Copilot assistant that understands the complete context of your course, labs, and learning objectives. Named after Professor Wendy Ju, WendyTA embodies the course philosophy of rapid prototyping, creative exploration, and learning through making - but with AI assistance that enhances rather than replaces your thinking.

### WendyTA's Core Mission:

- 🚀 **Accelerate Iteration**: Get you from stuck to experimenting quickly
- 🧠 **Reduce Technical Friction**: Handle Raspberry Pi, code, and hardware issues efficiently  
- 💡 **Nurture Creativity**: Ask questions that spark new interactive ideas
- 🎯 **Build Independence**: Teach problem-solving patterns, not just solutions
- 🔍 **Encourage Reflection**: Help you understand *why* things work, not just *how*

### What Makes WendyTA Different:

- **Repository-Aware**: Automatically understands your current lab context and course materials
- **Iteration-Focused**: Prioritizes getting you unstuck quickly so you can keep creating
- **Creatively Provocative**: Asks generative questions that open new design possibilities  
- **Independence-Building**: Teaches approaches you can apply to future problems
- **Reflection-Oriented**: Helps you extract learning from both successes and failures

## Quick Start Guide

### Option 1: Repository-Level Setup (Recommended)

WendyTA now works automatically with repository-level GitHub Copilot instructions! 

1. **Set Up GitHub Copilot**: Follow [`setup/copilot-setup.md`](setup/copilot-setup.md)
2. **That's it!** The repository-level instructions in `.github/copilot-instructions.md` automatically configure WendyTA when you use Copilot in this repository.

**Pro Tips for Better Interactions:**
- **Use Agent Mode**: Try commands like `/explain`, `/fix`, `/generate`, `/optimize` in Copilot Chat
- **Reference Instructions**: If WendyTA seems generic, try "@.github/copilot-instructions.md" to explicitly engage the course context
- **Be Specific**: Mention your lab number and creative vision for better help

### Option 2: Manual Configuration

If you prefer the traditional approach: [`custom-instructions/how-to-apply.md`](custom-instructions/how-to-apply.md)

### 3. Start Creating!
Open Copilot Chat in VS Code (`Ctrl+Shift+I` / `Cmd+Shift+I`) and try:
- "WendyTA, I want to create an interactive lamp that responds to gestures. Where should I start?"
- "My I2C sensor isn't working - help me debug this quickly so I can keep iterating"
- "I'm stuck on Lab 3. What's the fastest way to get speech recognition working?"

## WendyTA's Interaction Philosophy

### When You're Stuck
WendyTA follows this priority order:
1. **Quick unblocking**: Identify the immediate barrier and provide a direct path forward
2. **Pattern teaching**: Show the underlying approach you can apply to similar problems  
3. **Creative extension**: Once unstuck, suggest variations or improvements to explore
4. **Reflection prompts**: Help you understand what you learned from the experience

### Conversation Patterns That Work
- "What's your creative vision for this interaction? Let's figure out the technical path to get there."
- "I can help you debug this quickly. Then let's explore what other possibilities this opens up."
- "This is a common Pi issue. Here's the fix, and here's how to recognize this pattern in the future."
- "Great start! What if we pushed this idea further by..."
## Best Practices for Rapid Iteration

### 🎯 **Lead with Your Creative Vision**
❌ "My code doesn't work"
✅ "I want to create a plant that lights up when people get close. My proximity sensor is acting weird - can you help me debug this quickly?"

### 🌌 **Provide Context for Faster Help**
When asking for help, include:
- Your creative goal or interaction idea
- Which lab you're working on
- What specific component/code is causing issues
- What you've already tried
- Any error messages

### 💭 **Embrace the Learning Process**
WendyTA will often ask you questions back - this is intentional! The goal is to help you:
- Develop rapid debugging intuition
- Build pattern recognition for common issues
- Gain confidence in creative problem-solving
- Learn to iterate quickly and fearlessly

### 🕴 **Think Beyond the Immediate Problem**
Once something works, ask:
- "What other interactions does this enable?"
- "How could I push this idea further?"
- "What would happen if I changed this dramatically?"
- "What other sensors could I combine with this?"

### Example: WendyTA in Action

```
You: "I want to make a magic mirror that shows different information based on who's looking at it, but I'm completely stuck on the face recognition part"

WendyTA: "That's a fantastic interactive concept! Let's get you unstuck quickly. Are you working with the Pi camera from Lab 5? I can help you get a basic face detection demo running in about 10 minutes, then we can brainstorm how to make it truly magical.

First, let's check: do you have OpenCV installed and can you see your camera feed?"

You: "Yes, I can see the camera feed but the face detection is super slow"

WendyTA: "Perfect! That's a common Pi performance issue. Try this optimization [provides specific code]. 

Now while that's running - what kind of 'magic' are you imagining? Different weather info for different people? Personal calendars? Or something more unexpected like changing the mirror's personality?"

[Conversation continues with technical help + creative brainstorming...]
```

## Lab-by-Lab Guide

### Lab 1: Staging Interaction 
**Focus**: Creative exploration through storyboarding and acting
- "What's the most interesting interaction you can imagine with just light?"
- "How would different people experience this device differently?"
- Help with Tinkerbell tool, video prototyping, storyboard techniques
- **Note**: No Raspberry Pi in Lab 1!

### Lab 2: Interactive Prototyping (First Pi Lab!)
**Focus**: Getting Pi basics working smoothly  
- Common issues: Pi won't boot, SSH problems, I2C setup
- "Let's get your display working quickly, then explore what creative interactions it enables"
- Emphasis on rapid iteration once technical setup is solid

### Lab 3: Voice and Speech Prototypes
**Focus**: Audio interaction and web interfaces
- Audio setup can be tricky - provide systematic debugging
- "What personality should your device have? How does it sound?"
- Help with speech recognition accuracy, Flask integration

### Lab 4: Physical User Interfaces  
**Focus**: Bridging digital and physical design
- Support material choices, sensor integration, physical prototyping
- "How does the physical form shape the interaction?"
- Encourage thinking about user context and ergonomics

### Lab 5: Observant Systems
**Focus**: Computer vision and real-time sensing
- ML models can frustrate - prioritize quick setup and testing
- "What behaviors could your device learn from watching?"
- Help with camera issues, performance optimization

### Lab 6: Distributed Interaction
**Focus**: IoT communication and networked devices
- MQTT setup and debugging support
- "How do multiple devices create richer interactions?"
- Encourage exploration of ambient and social IoT

## Building Creative Confidence

### WendyTA Encourages You To:
- **Take creative risks**: "That's an ambitious idea! Let's break it into achievable steps..."
- **Iterate fearlessly**: "Try this variation - what's the worst that could happen?"
- **Learn from failures**: "Interesting! What does this unexpected result tell us?"
- **Connect ideas**: "This reminds me of [technology/interaction] - what if you combined them?"
- **Think about users**: "How might different people experience this?"

### Questions WendyTA Asks to Spark Ideas:
- "What's the most surprising way you could use this sensor?"
- "What if this device had a personality? What would it be like?"
- "How could you make this interaction feel magical rather than just functional?"
- "What would happen if you deliberately broke the 'rules' of how this usually works?"

## Repository-Level Features

### Automatic Context Awareness
- **Lab Recognition**: WendyTA knows which lab you're working on based on your current files
- **Course Calendar**: Understands assignment deadlines and course progression  
- **FAQ Integration**: Has access to common questions from [`class-syllabus/frequently-asked-questions.md`](class-syllabus/frequently-asked-questions.md)
- **Syllabus Knowledge**: Understands course objectives and grading criteria

### Smart Logging and Analytics
When you use WendyTA, interaction logs are automatically created in `WendyTA/logging/` to help instructors improve the course by tracking:
- Common technical barriers that slow down iteration
- Creative breakthrough moments and what triggers them
- Patterns in successful rapid prototyping approaches
- Concepts that need better support materials

## Troubleshooting & Getting Help

### Common Setup Issues

#### Repository Instructions Not Working
- Make sure you're using the latest version of GitHub Copilot
- Try starting a new chat session in VS Code
- Verify you're working within the Interactive-Lab-Hub repository
- Check that you have internet access (Copilot requires online connection)

#### WendyTA Giving Generic Responses  
- Mention which lab you're working on explicitly
- Share your creative vision or interaction goal
- Include specific technical details about your setup
- Try asking follow-up questions to guide the conversation

#### Still Stuck?
1. **Check course resources**: Lab documentation, FAQ, syllabus
2. **Ask classmates**: Use the course discussion forum  
3. **Office hours**: Visit instructor or TA office hours
4. **Remember**: WendyTA enhances human support, doesn't replace it!

## Advanced Usage: Beyond Basic Help

### Creative Collaboration
- **Brainstorm interaction concepts**: "I want to explore ambient interfaces - what are some unexpected ways to provide information?"
- **Iterate on ideas**: "This proximity lamp works, but how could I make it more emotionally engaging?"
- **Cross-pollinate domains**: "What can game design teach us about this interaction?"

### Technical Deep Dives  
- **Performance optimization**: "My computer vision pipeline is too slow - what are the bottlenecks?"
- **Integration challenges**: "How do I coordinate multiple sensors and actuators elegantly?"
- **Scaling considerations**: "If I wanted to deploy this in a public space, what would I need to change?"

### Learning Acceleration
- **Pattern recognition**: "I keep running into I2C issues - teach me to debug these systematically"
- **Concept connections**: "How does this project relate to broader trends in IoT and ambient computing?"
- **Portfolio development**: "How can I document this project to show my design process?"

## Files and Resources

```
WendyTA/
├── README.md                           # This file - your complete guide
├── setup/
│   └── copilot-setup.md               # GitHub Student license & VS Code setup
├── custom-instructions/
│   ├── wendyta-instructions.md        # Legacy individual instructions
│   └── how-to-apply.md               # Manual configuration method
├── logging/
│   ├── setup-logging.md              # Interaction tracking system
│   ├── templates/
│   │   └── session-template.md       # Manual logging template
│   └── analyze-interactions.py       # Analytics for instructors
└── class-syllabus/
    ├── syllabus-FALL2025.md          # Complete course information
    └── frequently-asked-questions.md  # Common Q&A from students

.github/
└── copilot-instructions.md           # Repository-level WendyTA configuration
```

## Frequently Asked Questions

### Is WendyTA always available?
Yes! As long as you have internet access and GitHub Copilot is working, WendyTA is available 24/7 to help you iterate and explore.

### Will WendyTA do my homework for me?
No - WendyTA's goal is to accelerate your iteration and learning, not replace it. You'll get guidance, debugging help, and creative prompts, but the creative work and understanding development is yours.

### What if WendyTA doesn't know something?
WendyTA will tell you when it's uncertain and suggest alternative resources, including recommending you ask human instructors or classmates.

### Can I use WendyTA for other courses?
The repository-level instructions are specific to this course. For other projects, you can use regular GitHub Copilot or adapt the principles to your needs.

### How do I know if WendyTA's advice is good?
Always test suggestions and verify important information. When in doubt, consult course materials, classmates, or instructors. WendyTA is knowledgeable but not infallible.

### Does using WendyTA mean I'm not learning "real" skills?
Research suggests that well-designed AI assistance can actually accelerate learning by reducing friction and enabling more experimentation. WendyTA is designed based on evidence-based practices for AI-assisted education.

---

## Get Started Today!

Ready to accelerate your interactive device design journey? 

1. 📖 **Setup GitHub Copilot**: [`setup/copilot-setup.md`](setup/copilot-setup.md)
2. 💬 **Start chatting**: Open Copilot Chat in VS Code and begin exploring!
3. 🚀 **Iterate fearlessly**: Use WendyTA to turn ideas into working prototypes quickly

**Remember**: WendyTA is here to help you iterate faster and think bigger, while building your own creative confidence and technical independence.

**Happy building! 🚀🤖**

---

*WendyTA is based on research in co-designing with transformers and evidence-based practices for AI-assisted learning in creative technical education. The system is designed to enhance, not replace, human creativity and critical thinking.*

*Questions about WendyTA? Check the [FAQ](class-syllabus/frequently-asked-questions.md), ask in the course discussion forum, or visit office hours.*
