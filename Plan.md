FridgeMind – Final Project Plan
<div align="left">

Team Members: Xiaocheng Li(XL2222); Haotian Xu(hx332); Xiang Chang (xc529)

Course: Interactive Device Design

Date: November 11, 2025

</div> <hr>

<h2 style="margin-top: 20px;">1. Big Idea</h2>
<p style="line-height: 1.6;"> <strong>FridgeMind</strong> is an AI-powered fridge assistant that helps people track food, reduce waste, and make smarter meal decisions. Mounted on the refrigerator door, the device uses a <strong>camera</strong> for food recognition, a <strong>touchscreen</strong> for quantity confirmation and browsing inventory, a <strong>microphone</strong> for voice-based meal queries, and an <strong>RGB LED strip</strong> for ambient system feedback. <br><br> All recognition and inventory management run <strong>locally on Raspberry Pi</strong>, while an external AI API provides meal suggestions based on real-time inventory. </p> <hr>

<img width="2048" height="1152" alt="6fd32781-0c27-4ede-9918-ad07daec5b2f" src="https://github.com/user-attachments/assets/89041a34-9290-423d-833c-80cc763e3bad" />

<h2 style="margin-top: 20px;">2. Interaction Summary</h2>
<h3>2.1 Visual Input for Food Recognition</h3>
![Uploading 6fd32781-0c27-4ede-9918-ad07daec5b2f.png…]()

Users place food items in front of the device.
The camera automatically identifies the food category using a lightweight ONNX model.

<h3>2.2 Touchscreen Confirmation</h3>

The touchscreen shows the detected item and allows users to confirm or adjust the quantity.
Food logging is based on image input, not voice.

<h3>2.3 Voice for Meal Guidance Only</h3>

Users can ask things like:

“What can I cook today?”

“Show me recipes using eggs.”

“Which foods are expiring soon?”

“What should I use first?”

Voice interaction is used only for meal queries, not for adding/removing items.

<h3>2.4 AI-Generated Recipes</h3>

The system sends inventory to an AI API to generate simple recipes,
helping users cook efficiently and reduce waste.

<h3>2.5 LED Feedback</h3>

🔵 Scanning

🟢 Success

🟡 Expiring soon

🔴 Recognition error

<hr>
<h2 style="margin-top: 20px;">3. Design Concept</h2>
<div style="line-height: 1.6;"> The device is designed as a compact, friendly module that blends into kitchen environments: </div>

Soft, rounded 3D-printed enclosure

Vertical layout: camera → screen → LED

Magnetic mounting

Three-screen UI: Capture / Inventory / Recipes

LED strip for ambient feedback

One-hand, quick interaction workflow

<hr>
<h2 style="margin-top: 20px;">4. Parts Needed (Beyond Class Kit)</h2>

Raspberry Pi 4 / 5

Pi Camera Module v3

6.9–7 inch touchscreen

USB microphone

RGB LED strip (WS2812B)

3D-printed enclosure + magnets

Wires, connectors, power supply

<hr>
<h2 style="margin-top: 20px;">5. Timeline</h2>

🗓 Week 1 — System Architecture & Design Concept (Nov 10–17)
<img width="2048" height="1152" alt="db91fef8-bc7e-4d20-b208-17cdca50d716" src="https://github.com/user-attachments/assets/c9af04fa-44cd-4296-a97e-cfefa48999c6" />

Goal: Define overall structure + interaction

Finalize physical layout (camera, screen, mic, LED)

Early enclosure sketches

UI information architecture

Test ONNX inference on Pi

Basic voice queries

Set up SQLite schema

🗓 Week 2 — 3D Modeling & Functional Integration (Nov 17–24)

Goal: Build enclosure V1 + connect core functionality

Complete CAD model

3D-print enclosure V1

Implement touchscreen UI

Train lightweight recognition model

Connect recognition → logging → inventory UI

🗓 Week 3 — AI Recipe Integration & Refinement (Nov 24–Dec 1)

Goal: Add intelligence + improve design

Refine enclosure V2

Recipe suggestion UI page

AI meal generation (OpenAI / Claude / Gemini)

Voice queries for recipes + expiring foods

LED feedback states

🗓 Week 4 — Integration, Testing & Demo (Dec 1–Dec 7)

Goal: Deliver polished interactive prototype

Stress-test entire pipeline

Apply finishing (sanding, paint, logo)

UI animation + feedback optimization

Record full demo video

Prepare documentation + final slides

<hr>
<h2 style="margin-top: 20px;">6. Fall-Back Plan</h2>

If recognition fails → manual category selection on touchscreen

If voice fails → use on-screen recipe button

If API fails → local rule-based recipes

If enclosure fails → laser-cut or cardboard version

<hr>

<hr>
<h2 style="margin-top: 20px;">7. Documentation Plan</h2>

Sketches & design iterations

CAD & 3D printing files

UI assets + layouts

Full code repository

Wiring & build guide

Demo video

Reflection & process write-up
