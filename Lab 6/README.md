# Distributed Interaction

**Sean Hardesty Lewis**

---

## Prep

Done!

## Part A: MQTT Messaging

Done!

Here is a picture of it working:
<img width="956" height="366" alt="image" src="https://github.com/user-attachments/assets/2c382d5b-17ae-4479-8239-b23e901227b9" />

**💡 My 5 ideas for messaging between devices**

1.) The first idea I had was an **LLM telephone game**, where one RPI tells the next RPI something but we either a.) mask b.) translate c.) add noise/permute etc. and see what the end message becomes. (Update 11/05/2025: Hauke presented this idea in class, so it is very low-hanging fruit and obvious!)

2.) Another idea I had was **3 pt reconstruction of a scene**. We know that one-shot / multi-view NeRF has come a long way, but I think having three RPIs with different angles of the same area then reconstructing that might be interesting. Obviously this has been done time and time again (not with RPIs, but generally).

3.) Another idea that piggybacks on the aforementioned one is using the sensors of the RPI instead of just camera. For example, we could have one RPI with a depth sensor, and one RPI with a VLM that are both running in real-time for a **semantic depth interpretation of the scene**. Could we get a decent translation of our environment, and a sense of depth? (There is really no reason to have multiple RPIs for this besides just splitting the computational demand of potential running a depth sensor and VLM at same time).

4.) Another idea I had was another extremely low-hanging fruit of you clicking a button on one RPI and it makes the other RPIs light turn on and vice versa. This has been time and time again with **"long distance relationship touch lamps"** which are pretty much the same concept.

5.) Another idea was using the RPI as a **visual transformation game** that uses the camera of your RPI (faced towards your opponent with another RPI and exact same setup). The RPI will then detect using object detection or VLM your opponent and anything else in the scene. It then transforms the scene (with filters, replacement, or slow image generation) on your RPI display with a fantastical version of your opponent in the game (think regular human in work clothes -> medieval knight with greatsword). It would play out like a normal Pokemon battle or 1v1 game, just with this "Ready Player One" interpretation of your opponent. The person you see in front of you is completely different from what you see on the RPI screen, and vice versa for them. You could have the RPIs connect and synthesize a concurrent theme, local game states of attack/defend, and really sell the entire transformation.

Here are some sketches of my ideas:

<img width="1132" height="845" alt="image" src="https://github.com/user-attachments/assets/c658dcc4-641d-43f6-8a7f-b50c087290fc" />
<img width="1055" height="726" alt="image" src="https://github.com/user-attachments/assets/a5233cd0-941f-48fc-bc8a-c326ab892d1f" />


---

## Part B: Collaborative Pixel Grid

Done!

**📸 Below is a creenshot of grid + photo of my Pi setup**

My streamed color is the blue one on bottom left, detected by putting the sensor near the servo motor!
<p align="center">
  <img src="https://github.com/user-attachments/assets/39846d86-3b41-4014-9023-a5ed2fb1e490" height="250">
  <img src="https://github.com/user-attachments/assets/941ee7e8-c4a5-4c6d-a17b-9521092dbed0" height="250">
</p>

---

## Part C: Make Your Own

**1. Project Description**

I decided to do my idea (#5 above) of a **visual transformation game** since I found out that SDXL Turbo could generate 1 image every 0.3s on my PC. So, I could have 3fps videos essentially as long as I had some kind of prompt. I believe this would be interesting since as image generation improves and gets faster, we could get live filters for what we see around us. We could have a VLM that identifies the basics of actors, environments, actions within a scene. Then, we could keep that caption the same or use an LLM to transform it with some theme we choose. Then, we can generate a plausible real-time image (or low-fps video) with the caption. The user experience I propose would be a game of sorts where two players both have RPIs with screens and cameras. The cameras are faced towards the other player, and the screens are what each player is looking at. With a background prompt, we can transform what the VLM sees of the other player to "an alien world" or to "a medieval scene" and the player will be able to see the other player as an alien or a knight almost instantaneously. This will make interaction fun especially for children who may always be reading fiction, getting to see the real world transformed into their favorite fiction universes through just a screen and camera, and in near real-time.

**2. Architecture Diagram**

```
[Camera] → [FastVLM] → (caption)
│
▼ HTTPS (CF)
[SDXL API] — PC
│
base64 JPEG frames
▼
[MQTT Broker] — TCP :1883 (local)
▲
WS :9001 (local) → Cloudflare → WSS URL
▼
[RPi App + PiTFT] subscribe sdxl/frames/<VIDEO_UID>
```

Effectively, each RPI captions an image it takes with its webcam, then optionally sends that to local Ollama for style transformation, then sends the caption to the SDXL API on the PC. The PC reads the caption and uses SDXL Turbo to generate JPEG frames which the base64s are published on the MQTT server under a video uid. Each RPI can read from a different video uid that is unique to them and will receive base64 images which they can display on their own screens.

**3. Build Documentation**

<p align=center>
<img width="400" src="https://github.com/user-attachments/assets/4ff7f9fa-bedb-46e6-b6df-bafd0576d7aa" />
<img width="400" src="https://github.com/user-attachments/assets/8a7d48af-c1e1-48a2-889c-b502ee844a8a" />
</p>

Each player in the game is comprised up of their RPI itself, the webcam attached to their device, and their PiTFT screen. The webcam is the only sensor we are using to get pictures of the world, actors, and actions happening within it. The RPI and remote server PC are able to interpret this world from the camera and transform it into a newly generated image which appears on the screen. These images appear at about a rate of 2 frames per second with 2 users, and less as more users join in on the game.

In my game, MQTT is mostly used as a way to distribute the streams of generated jpegs. Each RPI can subscribe to a unique stream of generated 512x512 jpegs from the PC and effectively get a 3fps "video". 

Here is the code that we use to receive and display the image from the MQTT stream. We read the base64 from the decoded MQTT subscription, use pillow to convert it from base64 bytes to RGB and render it to the RPI display. All of this happens multiple times per second since the PC churns generating images with the prompt, puts the base64 on the MQTT server, which the subscribed RPIs read and can immediately display on their screens.
```
def on_message(client, userdata, msg):
        global last_frame_ts
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            b = base64.b64decode(data["b64"])
            im = Image.open(io.BytesIO(b)).convert("RGB")
            _render_to_buf(im)
            if DISP_OK:
                disp.image(image_buf, rotation)
            last_frame_ts = time.time()
        except Exception as e:
            log(f"MQTT frame error: {e}")
```

Here is an example of our setup SDXL Turbo API which runs at 3fps, we caption it and get ~3 512x512 generated images per second.

https://github.com/user-attachments/assets/4fbcb262-8078-405a-9c5a-9665f5281116

**4. User Testing**

I tested the system with two people outside my team using the full pipeline (webcam → caption → optional style transform → SDXL Turbo → MQTT → PiTFT display). Both players stood across from each other with the RPIs facing them. Before trying the game, both testers assumed it would feel like a "Snapchat filter but slower." Neither expected that the scene would be fully regenerated rather than layered with filters. He thought it would probably just tint the colors or put a cartoon overlay and was surprised when I explained it was actually re-rendering the whole frame with a caption.

What surprised them most was how quickly the world transformed. Even at ~2–3 fps, the SDXL video felt alive. He laughed immediately when he appeared as a Cyberpunk 2047 Keanu Reeves style character. There were erratic but funny hallucinations. Objects would spontaneously morph such as chairs became thrones, a cup became glowing for no reason, etc. The experience was just in seeing each other differently. Both said the fact that each person sees a different transformed version of the other made it feel like sort of a VR without the headset. They also loved experimenting with poses or holding items to see how the VLM would reinterpret them. He found he could intentionally trick it into making cooler images by raising his arms or leaning into the frame.

Some fixes they suggested were:
* Faster style transformation. The Ollama step running on-device added noticeable lag (~10s). They said that when the style transform froze for a few seconds, it broke immersion, even with the constant running stream from the previous caption.
* Higher loyalty to original actors/scene. The model often changed the character or scene between frames. They wanted it to be more consistent so the generated characters / scenes stayed coherent somewhat with the real world.
* Reducing the camera zoom. They had trouble framing themselves without backing far away from the camera since the automatic zoom levels are pretty zoomed in.

Here is the demo for the interaction without any style transformation (default VLM caption used for SDXL):

https://github.com/user-attachments/assets/a47ded81-4669-4587-90b7-32182afd6ca3

Here is the demo for the interaction with style transformation (VLM caption is passed to local RPI Ollama with stylistic transformation prompt which then gets passed to SDXL):

https://github.com/user-attachments/assets/bf5acedc-26b1-424d-ad25-540dff906d64

**5. Reflection**

The best part off the experience (what worked well) is definitely the initial reaction when the players realize that the world around them is being transformed into something that the computer is generating. A person in view becomes a medieval knight or a cyborg, a dog becomes a hippogriff, etc.
Once players catch on to what is happening, the experience becomes a light-hearted "Who can get the AI to generate something crazier?" with different objects, poses, etc. to try to get the VLM (and for style transforms, the LLM) to describe a scene that would convert to a great generated image/video.

The biggest challenges with distributed interaction was definitely the server load. One RPI could subscribe to an image generation feed and the PC could reliably pump out 3fps. However, as soon as there are two image generation feeds, it might only be 1.5fps as the server has to generate 2 different captioned image as fast as it can.
This meant that as more players join the game, the experience deteriorates for everyone. This is no fault of MQTT, but of using one centralized server for image generation capabilities. We could improve this by doing image generation on the RPIs, but 0.3s on a 3090 converts to roughly 1-3 minutes on the RPI. Here is someone who managed to get it working in one minute on the RPI on [Medium](https://medium.com/data-science/generating-images-with-stable-diffusion-and-onnxstream-on-the-raspberry-pi-f126636b6c0c). For my game, one minute to generate a single frame defeats the entire experience when the purpose is to try to get it as near real-time as possible. 

Another area that sacrifices quite a bit of time is the LLM caption style transfer being done locally via Ollama on the RPI. This can often take 10-15 seconds for something that if offloaded to the PC would take < 1s. Decidely, this is not as bad as FastVLM which can freeze up the entire RPIs resources for around 30s while it runs.
For the purposes of my experiment, I am using the following servers and locations (PC vs RPI) for each. I could optimize the game further by moving everything off of the RPI and only using them as edge nodes, but I felt I still wanted to use the computational power of the RPI somehow. Bolded is my setup.
* FastVLM Server for Captioning Images **(PC, ~0.5s)** vs (RPI, ~30s)
* SDXL Server for Generating Images **(PC, ~0.3s)** vs (RPI, 1-3mins)
* Ollama QWEN2.5 0.5b Instruct LLM for Optional Style Transfer of Caption (PC, 0.2s) vs **(RPI, ~15s)**

Sensor events worked well for the most part. The webcams are zoomed in by default which is a bit tricky when a user is standing extremely close to their webcam as it does not comprehend any scene. The MQTT server with seperate streams for each RPI webcam captioning flow was extremely useful and made it possible for different users to get unique streams of images that pertained to their own camera, even with a centralized image generation server.

For improvements, the first thing I would definitely fix would be the style transfer in two ways. One, I would move it to the server PC to be much faster. Second, I would modify the Ollama style transform prompts to stay more loyal to the original caption. I noticed that the style transformations that the LLM did often reduced the caption to meaningless scenes or actors that weren't that relevant to what the original caption had.

In terms of other improvements, I would definitely compress SDXL Turbo to generate maybe 100x100 images or even smaller. I noticed that the PiTFT screens couldn't even render the full 512x512 image, so I was wasting image quality as well as time in generating them for such a small screen. I could get faster image generation for all players, as well as better end-to-end latency by compressing the sizes of images being generated. I would also switch out my bespoke server to the official StreamDiffusion server which is optimized to render at nearly 100fps, dwarfing this server.

## Code Files

**Server files:**
- `fastvlm_server_pc.py` - FastVLM Captioning Server for PC
- `sdxl_turbo_server_mqtt.py` - SDXL Turbo Image Gen Server for PC, publishes to MQTT at localhost:1833
- `viewer.py` - SDXL Turbo Image Gen Viewer for PC

**Pi files:**
- `fastvlm_server.mjs` - FastVLM Captioning Server for RPI
- `rpi5_fastvlm_to_sdxl.py` - RPI Pipeline for capturing camera frame, querying FastVLM, transforming caption with Ollama, calling SDXL API, reading MQTT base64 frames and displaying to screen

**Misc:**
- `wss_sub_test.py` - Testing local + cloudflare MQTT stream

I acknowledge the use of Copilot to create these scripts as well as helpful guidance from ChatGPT, especially with the RPI Pipeline script where I mishmashed several disparate components I had. The FastVLM server is converted from their [template](https://github.com/apple/ml-fastvlm) for querying, and also has some unused endpoints (ex. /caption_batch that I use in other offline applications). The SDXL Turbo server was heavily inspired from [StreamDiffusion](https://github.com/cumulo-autumn/StreamDiffusion), although my implementation is a bit heavier and not quite as robust as theirs.

I used Cloudflared tunneling to make my localhost servers from PC available to the RPI to use. I also used it (with its websocket support) to let the RPI subscribe to the MQTT websockets server.
