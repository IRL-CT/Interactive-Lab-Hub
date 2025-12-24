# Final Project  

Collaborators: Kyle Li (kl2296), Angela Bi (ab3348)

<details>
Requirements:
1. Project plan: Big idea, timeline, parts needed, fall-back plan. (Can be same as previous turn-in, but updated if you changed your plan)
2. Functioning project: The finished project should be a device, system, interface, etc. that people can interact with.
3. Documentation of design process
4. Archive of all code, design patterns, etc. used in the final design. (As with labs, the standard should be that the documentation would allow you to recreate your project if you woke up with amnesia.)
5. Video of someone using your project
</details>

## Project plan  
<img width="1007" height="564" alt="Screenshot 2025-12-11 at 1 07 05 PM" src="https://github.com/user-attachments/assets/5fc27aab-237c-43e0-9be7-f6c8cebca19f" />  
<img width="1000" height="560" alt="Screenshot 2025-12-11 at 1 07 19 PM" src="https://github.com/user-attachments/assets/d84d8b19-5ef3-48bd-82b9-8c68a4b9802f" />

Big idea: Our big idea was to make an interactive installation resembling the New York City skyline. Given a QR code of a song, the system would play the song over its speakers, project the album cover onto a building, and sample its dominant colors to create synchronized LED light pulses that illuminate the building interiors.

Timeline: Our initial plan was highlighted in the screenshot. However, as we were planning out the components needed, our plan changed a bit. Here was our revised breakdown:

![IMG_923AACFAA2C0-1](https://github.com/user-attachments/assets/37fa3141-f17e-4506-949a-5f0e54afe011)

For each component, we came up with a breakdown of what we needed to do:
- Buildings
  - Design buildings
  - Cut buildings
- Base
  - Design base
  - Cut base
- QR scanner
  - Write code for webcam -> recognizing song
- Song-related code
  - Write code that gets album from song
  - Write code to detect colors in album
- Lights 
  - Installation of lights
  - Write code to change colors of the lights
- Display and speaker
  - Screen that shows song, write code that displays song on screen
  - Write code that plays song

This is how we broke it down into a timeline:
| DATE   | TO DO                                                                                                                                                                                                                                                                          |
|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Nov 17 | By Nov 17: Implement webcam input to detect song QR code. From the spotify link, use spotify API to get metadata like album cover. Design building cut patterns. <br> During Nov 17: Given the song, play the corresponding track. Start cutting buildings |
| Nov 19 | By Nov 19: Display song on screen. Connect lights with Pi. Extract dominant colors from album art. Get lights to work <br> During Nov 19: Finish designing and printing buildings and base. |
| Nov 24 | By Nov 24: Play song on speakers, get lights to work                                                                                                                                                                                                                                        |
| Dec 1  | Protype showcase deadline; get prototype be functional (e.g. scan song -> plays songs and gets album cover)                                                                                                                                                                                                            |
| Dec 5  | Finalize prototype. Conduct tests with users to ensure the experience is intuitive, engaging, and safe.                                                                                                                                                                                                   |
| Dec 14 | Compile design process, source code, reflections, project documentation, demo video, and group work questionnaire.                                                                                                                                                                     |

## Documentation of design process

### Buildings and Base

We used makeabox.io to create the designs for the base and buildings, which we exported to Illustrator and used Trotec to cut out acrylic and wood. This took a lot of trial and error---sometimes, makeabox.io made a box that didn't fit together, and sometimes we added the wrong material/thickness so it didn't completely cut out the designs. [Video of laser cutting](https://drive.google.com/file/d/1b2aTOYd5n_8dTt5-nXg4UEktvBCX7vKe/view?usp=sharing)

In addition to being able to assemble individual buildings and the base, the design also had to involve fitting the acrylic buildings onto the wooden base. This also took some trial and error, because we had to modify the width of the holes cut in the base so that we were able to fit the acrylic buildings on top of the base. [Video of earlier prototype](https://drive.google.com/file/d/1vNrLCEC3M1uJeTkorbxCvN4FkjzVsQPe/view?usp=drive_link)

<img width="50%" alt="Screenshot 2025-12-14 at 7 12 24 PM" src="https://github.com/user-attachments/assets/1eb12ff2-1ec3-4fd4-ac80-60897180363f" />
<img width="50%" alt="Screenshot 2025-12-14 at 7 12 57 PM" src="https://github.com/user-attachments/assets/b3a38701-0c07-4492-9d0e-f933d6c35906" />
<img width="50%" alt="Screenshot 2025-12-14 at 7 13 12 PM" src="https://github.com/user-attachments/assets/1bf3c92e-9957-40a6-a98e-11295e53323e" />


### Overview: Input (QR code) -> song information -> outputs (pi display, speakers, LED lights)

This is how we broke down the process of input (QR code) to outputs (pi screen, speaker, lights):

![IMG_96BF61FF06B5-1](https://github.com/user-attachments/assets/90b052b8-19c9-41c8-974e-5ecf68c43348)

### QR code -> song link, album cover

We used `CV2` to get song information from a user scanning a song's QR code with the webcam. We initially thought that we could use spotify because they have a developer API so we could get its metadata like the album, etc.

```
def find_spotify_qr():
   """
   Opens webcam, scans for QR codes, and returns the FIRST valid Spotify track URL found.
   """
   print("Scanning for Spotify QR codes... (press 'q' to quit)")


   cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
   if not cap.isOpened():
       print("Failed to open")
   else:
       print("Opened!")


   try:
       while True:
           ret, frame = cap.read()
           if not ret:
               continue


           qr_codes = decode(frame)
           for code in qr_codes:
               link = code.data.decode('utf-8')


               # Only accept Spotify track links
               if "open.spotify.com/track/" in link:
                   print(f"Found Spotify Track: {link}")
                   cap.release()
                   cv2.destroyAllWindows()
                   return link


           cv2.imshow('QR Scanner', frame)
           if cv2.waitKey(1) & 0xFF == ord('q'):
               break


   finally:
       cap.release()
       cv2.destroyAllWindows()


   return None
```

After getting the song, we realized that in order to play the song, the process to do so through spotify would involve many steps (involving signing into the spotify developer account after the link is opened). We changed our code to take in a QR code for a youtube link, which would both allow us to get a png of the album cover for the pi and LEDs, and play the song over the speaker without additional hurdles. 

Below is the relevant snippet in our `___main___` function"
```
print("Starting Webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Webcam not found.")
        return

    print("Scanner Running. Waiting for QR codes...")
    
    # Flash blue to show it's ready
    show_status_color(0, 0, 255)
    time.sleep(0.5)
    show_status_color(0, 0, 0) # Clear to black

    last_played_link = None
    last_seen_time = 0

    try:
        while True:
            # Read frame
            ret, frame = cap.read()
            if not ret:
                break

            qr_codes = decode(frame)

            # Reset logic: If no code seen for RESET_TIME, allow rescanning
            if not qr_codes:
                if last_played_link is not None and (time.time() - last_seen_time > RESET_TIME):
                    print("Resetting... Ready for new code.")
                    last_played_link = None
                    show_status_color(0, 0, 0) # Clear screen to black when reset

            for code in qr_codes:
                link = code.data.decode('utf-8')
                last_seen_time = time.time()

                if link != last_played_link:
                    print("-" * 30)
                    print(f"Found: {link}")
```

### Song -> play song on speaker

After getting the song url, we sent a request to a laptop connected to the same server, and to play the song, we connected our speaker to laptop over bluetooth. 

Below is the relevant snippet in our `___main___` function:
```
# 2. Send to Laptop
    try:
        requests.get(f"http://{LAPTOP_IP}:{LAPTOP_PORT}/play", params={'url': link}, timeout=1)
        print("Sent to laptop.")
    except:
        print("Could not connect to laptop.")
```
This code makes it so that once a song is found, the youtube link opens in the laptop. On the server/computer side, the user must run the code:

```
from flask import Flask, request
import webbrowser
import os

app = Flask(__name__)

@app.route('/play', methods=['GET'])
def play():
    # Get the link sent from the Pi
    link = request.args.get('url')

    if link:
        print(f"Received command to play: {link}")
        # Open the link in your default browser (Chrome/Safari/Edge)
        webbrowser.open(link)
        return "Command Received: Playing!"
    else:
        return "Error: No URL provided."

if __name__ == '__main__':
    # '0.0.0.0' allows other devices (like the Pi) to talk to this laptop
    print("🔊 Laptop Listener Active! Waiting for Pi...")
    app.run(host='0.0.0.0', port=5001)
```

This makes it so that when the pi sends the request with the Youtube URL, the computer connected to the server can play it. In order to play the song out loud, we connected the computer with a bluetooth speaker and put it inside of our prototype.

### Song -> pi screen 

After getting the song url, we were also able to convert the Youtube thumbnail into a PIL Image, which we displayed in the pi screen.

Below is the relevant snippet in the helper function `get_youtube_thumbnail`:
```
def get_youtube_thumbnail(url):
    """
    Downloads YouTube thumbnail and converts it to a PIL Image 
    that fits the ST7789 screen.
    """
    video_id = ""
    if "v=" in url:
        try:
            video_id = url.split("v=")[1].split("&")[0]
        except: pass
    elif "youtu.be/" in url:
        try:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        except: pass

    if not video_id:
        return None

    # Download High Quality Thumb
    thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    print(f"Downloading art: {thumb_url}")
    
    try:
        resp = requests.get(thumb_url, timeout=2)
        if resp.status_code == 200:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(resp.content))
            
            # Resize and Crop to fit the screen dimensions
            image = ImageOps.fit(image, (display.width, display.height), method=Image.LANCZOS)
            return image
    except Exception as e:
        print(f"Image download failed: {e}")
    
    return None
```

Below is the relevant snippet in our `___main___` function, where we called `get_youtube_thumbnail` to get the PIL image and displayed it on the pi screen:
```
# 3. Get Album Art
art_image = get_youtube_thumbnail(link)

# 4. Display Art
if art_image:
    display.image(art_image)
```

By the showcase deadline of December 1, we had everything working except the LED lights. [Here is a video we recorded of it working.](https://drive.google.com/file/d/1paV4NpYWIWsTyBRG5n4qti43AxIXps6V/view)

### Song album cover -> LED lights 

The hardest part of the whole process was getting the LED lights to display the dominant colors of the album. This was the initial code we used to extract the dominant colors from the album art:

```
def extract_primary_colors(image, num_colors=3):
    """
    Given a PIL Image, returns `num_colors` dominant colors as RGB tuples.
    Uses k-means clustering on all pixels.
    """
    # Convert image to numpy array
    img = image.convert("RGB")
    img_np = np.array(img)

    # Flatten pixel array into (num_pixels, 3)
    pixels = img_np.reshape(-1, 3)

    # KMeans clustering
    kmeans = KMeans(n_clusters=num_colors, n_init="auto")
    kmeans.fit(pixels)

    # Cluster centers are the dominant colors
    colors = kmeans.cluster_centers_.astype(int)

    # Convert to list of (R, G, B)
    return [tuple(color) for color in colors]
```

When we tried to get the LED lights to work, our combined lack of electrical engineering experience resulted in all of our Raspberry Pis being nonfunctional or partially broken. Nophar managed to get a Raspberry Pi 4, which she reprogrammed to make it work and connect successfully with the LED lights. [Video of LED lights working for the first time!](https://drive.google.com/file/d/1jKgiAGw1eiiBCnUjCLtnjzUOQv13hL-a/view?usp=drive_link)

After we were able to get the LED lights to work, we were able to generate code that made the LED lights turn colors. In our updated set of functions, `set_leds_from_image` creates the top three dominant colors, and `set_led_colors` and `show_status_color` change the LEDs according to those colors.

```
 def set_led_colors(color_list):
     """Updates the global target for the animation thread"""
     global target_colors
     target_colors = color_list
 def show_status_color(r, g, b):
     # 1. Update Screen
     display.fill(color565(r, g, b))
     # 2. Update LEDs (Set as single static color)
     set_led_colors([(r, g, b)])
 def set_leds_from_image(image):
     try:
         # 1. Resize to a small thumbnail (faster processing)
         thumb = image.resize((50, 50))
         # 2. Reduce colors to a palette of 10 dominant shades
         quantized = thumb.quantize(colors=10, method=2)
         palette = quantized.getpalette()
         # 3. Find the TOP 3 most "colorful" (saturated) colors
         scored_colors = []
         # Check the first 8 dominant colors
         for i in range(8):
             if len(palette) < i*3+3: break
             r = palette[i*3]
             g = palette[i*3+1]
             b = palette[i*3+2]
             # Skip if too dark (black) or too bright (white)
             brightness = r + g + b
             if brightness < 40 or brightness > 700:
                 continue
             # Calculate saturation (difference between highest and lowest channel)
             sat = max(r,g,b) - min(r,g,b)
             scored_colors.append((sat, (r,g,b)))
         # Sort by saturation (most vibrant first)
         scored_colors.sort(key=lambda x: x[0], reverse=True)
         # Pick top 3
         top_colors = [c[1] for c in scored_colors[:3]]
         # Fallback if image is B&W or we couldn't find good colors
         if not top_colors:
             top_colors = [(palette[0], palette[1], palette[2])]
         print(f"Cycling between: {top_colors}")
         # Update the animation thread
         set_led_colors(top_colors)
     except Exception as e:
         print(f"Could not calculate colors: {e}")
```

--- 

## Final Functioning project + Archive of all code, design patterns, etc. used in the final design.

<img src="https://github.com/user-attachments/assets/c9beec79-c5bb-48a3-968d-c724e2cb226e" width="50%" />

Final code for the raspberry pi (4) is under the file `final_project_code_pi.py`. 

Final code for the computer is under the file `final_project_code_server.py`.

Designs used are in [this shared google drive](https://drive.google.com/drive/folders/1y_ihyC7CYjQWi6quVmSAh8PM_WfXcZeX?usp=sharing). QR code card designs are [here](https://drive.google.com/file/d/1zqDnjq1lMP1CET62hn4BgXigs2bKYedH/view?usp=drive_link). 

### Video of someone using our project + Feedback and future directions

Videos of the Skyline Speaker in action: [this shared google drive](https://drive.google.com/drive/folders/1owq4bvrL6NGnxdHZzq-smcAHwIi2oI_W?usp=drive_link)
We tested and got feedback about our prototype with multiple people. 

When we first demoed our project to Wendy, Albert and Hauke, we got the following feedback:
- Make the prototype closer to eye level so that people have an easier time scanning the QR code
- Make QR code flashcards that you can hand to people to make the demonstration easier
- Have some way of indicating to the user that the camera is recording, has recognized the QR code, etc.

We also tested our prototype with Philip, a M.Eng CS student. Here is the [video](https://drive.google.com/file/d/1-6Gw8yGcm1vT1X375p9KZTV2dBWQM-Bf/view?usp=drive_link) 

During demo day, we were able to let many people test our prototype. Here is some feedback we got:
- We laser printed QR code cards, but the engravings ended up being too light for `cv2` to recognize. In the future, we would make it so that the engravings are dark enough or find alternate ways to make QR code cards!
-  Sometimes, it would take a long time for the QR codes to be recognized by the camera and `cv2`. This might have been because of the orientation, positioning, distance from the camera, lighting, etc. but there was no way for us to know why the QR code wasn't being read and how we could adjust the QR code or environment. In the future, we might incorporate ways for the system to give feedback to the user, telling them when the QR code isn't being read, and how they might adjust it.
-  Some album colors involving pink and blue displayed a lot better on the LED lights than other colors such as green. In the future, we would troubleshoot both the algorithm used to generate the dominant colors sent to the LEDs, and the LEDs themselves to figure out how to display colors better.
