# Recreating the Masters of Interactive Light

**NAME OF BOTH COLLABORATOR(S) HERE:** Giorgi Samushia, Shuning Liu

**THE MASTERWORK YOU DREW FROM THE HAT:** teamLab Borderless (teamLab, 2018): "Light-flowers bloom and scatter on the surfaces you touch and pass."

---

# The Report

## Part 0. Know Your Master

teamLab Borderless is a digital art museum in Tokyo, opened in 2018 by teamLab, a collective of artists, programmers, and engineers. The name refers to the artworks having no frames: they spill out of their rooms and flow into each other. Our card refers to the flower works inside the museum, mainly *Forest of Flowers and People: Lost, Immersed and Reborn*. Flowers are projected onto the walls, the floor, and the visitors themselves, continuously budding, blooming, withering, and fading. None of it is a recording; the imagery is generated live and shaped by the people in the room.

The interaction itself is simple. The field feels alive before you even do anything, and if you stay in one place the flowers bloom more abundantly around you. Touch was the part we had to investigate: teamLab's own description says that touched flowers "wither and die all at once". However, in the videos we watched, the petals scatter around the visitor's hand and drift back while the rest of the field continues. Installations seem to differ, so we recreated what we could actually observe.

When someone comes close, the flowers turn warmer and brighter, as if the field notices them. And even when nobody is there, everything keeps drifting and breathing, like the field is living its own life.

As for who is present, the visitor is never alone with the piece. The flowers land on other people as well, and someone walking through can undo your stillness. Other visitors become inputs into the same system.

The strength of the piece, to us, is that you feel immersed while understanding yourself as a part of it rather than its center. Its weakness is that a single person's effect is easy to miss, and that the immersion depends heavily on a dark room and large-scale projection. We felt this directly: our recreation did not work until the frame was nothing but flowers.

The core interaction someone would recognize it by: the flowers bloom and breathe on every surface, and your presence genuinely moves them, but the field is never about you. You affect it the way we affect nature, and it continues without you.

## Part A. Plan

**Setting:** A dim indoor gallery with a colorful animated flower projection covering a wall.

**Players:** The primary player is a curious gallery visitor exploring the projection. A friend and other visitors are present nearby. They observe the interaction, react to the changing light, and may become interested in participating.

**Activity:** The player explores how distance, touch, and hand gestures affect the projected flowers. The light changes brightness and temperature accordingly, and this leads people to respond further emotionally and physically.

**Goals:** The player wants to discover how the projection responds to his body and gestures.

### Storyboard 1: Proximity

Flowers respond to the visitor's distance: as Alex approaches they glow brighter and warmer, the light gets even brighter as more people come close, and when everyone leaves it fades back to dim, cool colors.

![storyboard 1: proximity](storyboard1.jpg)

### Storyboard 2: Tap

The wall responds to touch: the touched flower highlights and scatters away from the finger, the playful response draws everyone closer, and the flowers return slowly, inviting another touch.

![storyboard 2: tap](storyboard2.jpg)

### Storyboard 3: Swing

Flowers react along the path of a large gesture: those nearest the hand highlight first, the swing scatters them away leaving a moving gap, and they slowly gather back after a while.

![storyboard 3: swing](storyboard3.jpg)

**Feedback on the storyboards:** Most of the concept came from the two of us reading about the piece and watching videos of it, so the storyboards themselves didn't get much outside critique. The useful feedback arrived when we staged the prototype: early takes read as a laptop projecting on part of a wall. The projection didn't cover the frame and it looked a lot less immersive. We reframed the shot with Rati until the frame was nothing but flowers, and that single change is most of why the final video works.

## Part B. Act out the Interaction

Our acting out happened in two rounds: first physically testing the water-bottle idea with a phone and Tinkerbelle, and later rehearsing the scene against the real projection with a friend before recording.

**Are there things that seemed better on paper than when acted out?**

On paper we thought we could use Tinkerbelle as-is: put a water bottle on top of a phone and let it cast light around the room. We couldn't find a space dark and plain enough to make it work. Also, the effects couldn't happen at the point of interaction. The phone + bottle method gave us no accurate spot to display anything, so the light responded somewhere, just never where you touched.

**Did new ideas about the piece surface once you were on your feet?**

**Giorgi:** Not during the staging. The new idea came from watching the video we had staged. Seeing the field keep living after I walk out of frame gave me a new perspective on the interaction: nature is unchangeable and keeps being without us, even though we might affect it in significant ways for a while. Until then I had read the piece mostly through its immersive quality; this reframed it as being about our relationship with something that outlasts us.

**Shuning:** Yes, new ideas came up during the staging process. In our first test, we tried projecting the light directly from a computer, but it was too dim to create the effect we wanted, so we decided to borrow a projector. Staging also pushed us to think more specifically about the interaction—whether to use abstract light or flowers, and how the flowers should react when someone approaches, touches them, or moves a hand across the wall. Planning the sequence of the video helped turn our initial idea into a clearer interaction with distinct responses to different human actions.

**Are there key moments in the interaction where things could go in a different direction?**

At every point the visitor could just watch and not interact at all, or deliberately observe without disturbing the scene. And their interaction is not fully theirs: someone else entering the space can affect it, ripple through their patch, or flick a flower they were watching. Our video follows one path (approach, tap, flick, leave), but the piece holds all of these at once.

## Part C. Prototype the Light

We projected the Tinkerbelle light page onto the wall with a projector connected to the laptop, so the flowers appear at room scale on the surface the visitor touches. The wizard drives the light from the same laptop's keyboard, out of frame.

Out of the box, Tinkerbelle just turns the whole screen one flat colour that you pick from a colour picker. That could not read as Borderless, which is why the app in our video looks different. We changed the code quite a bit, and our fork is in the [`tinkerbelle`](tinkerbelle/) folder. We fixed a bug where fades finished almost instantly instead of taking their set time, and made colour fades travel through the in-between hues instead of through grey. Then we added a new mode for the light page that draws a field of about 300 flowers instead of a flat colour. Each flower takes its own shade of whatever colour the wizard picks, they all breathe and drift on their own, colour changes spread outward from the centre of the wall, and gesture keys make them ripple away from a tap or send one flying across the field. The wizard has keys for colours and keys for what the visitor's hand is doing:

| Key | What the light does | Meaning |
|---|---|---|
| L | 5 s fade to a dim violet-blue, flowers moving on their own | the resting field, nobody close |
| 1 | 6 s fade to emerald | idle drift, so the field visibly lives |
| A | 4 s fade to a warm rose, a little brighter | someone **walks up** to the flowers |
| Space | a ripple spreads out from the touch point: flowers are pushed outward, brighten, and drift back | visitor **taps** the wall |
| Enter | the flower nearest the touch point is sent flying across the wall, shoving the flowers it passes; everything drifts back | visitor **flicks** a flower |
| 0 | fade to black | off, end of the take |

The wizard watches the actor's hand and presses the matching key as the gesture happens; the flowers always drift back to where they were, so the field heals after every touch.

## Part D. Wizard the Device

Giorgi acted at the projected wall while our friend Rati sat at the laptop out of frame, watching Giorgi's hand directly and pressing the matching keys (approach, tap, flick, leave) as each gesture happened. In our first recording the projection covered only part of the frame, the browser's buttons were visible in the corner of the projection, and cables crossed the wall. For the final take we fullscreened the page, cleared the cables, and tightened the framing until only flowers were visible. The wizarding only read as real because Rati was keying off Giorgi's hand, not a script: the closer the light's response landed to the moment of the gesture, the more alive the wall felt.

https://github.com/user-attachments/assets/475a56d0-ebfa-43fa-aba7-ae19f038d57f

## Part E. (optional) Costume the Device

## Part F. Record

https://github.com/user-attachments/assets/bbcf7629-c265-4380-bcd7-726544ff1939

To illustrate the non-sequential side of the interaction, the take strings together different kinds of input rather than one repeated action: approaching, tapping, flicking, and just standing back. Between gestures the field keeps moving on its own, so the viewer can see that nothing forces the next step; the visitor could stop at any beat, do them in another order, or never touch the wall at all, and the flowers would go on either way.

## Reflections

Tinkerbelle out of the box can only turn a screen one flat colour, and a flat colour could not carry this piece. We ended up extending it a lot: fixing its fade timing, drawing a field of flowers on a canvas, and adding keys for what the visitor's hand is doing. It ate time the assignment maybe didn't ask for, but it forced us to decide which part of the interaction actually mattered, and that decision is the recreation.

**Giorgi:** My understanding of the piece also changed by making it. Going in, I had read Borderless mostly through its immersive quality. Watching our own staged footage, where the field keeps living after I walk out of frame, made the point land differently: we affect nature in significant ways for a bit, but it keeps being without us. I would not have gotten there by reading about it.

**Shuning:** Creating the storyboards was more difficult than I expected because I had to communicate a complete scene through a limited number of panels. I realized that it was not enough to show only how the interaction worked. The changes in the surrounding environment and the players’ reactions were also important parts of the interaction and needed to be visible in the drawings. This required me to think about the experience more broadly and organize each storyboard carefully. During staging, I also learned that recreating the piece was not simply about copying teamLab’s exact visual effect. We had to consider the technology and tools available to us, identify the core experience, and decide how to reproduce different interactions within those limitations.

**Collaborators and credits:** Shuning Liu nailed down the core interaction from the research and videos, wrote the Part A plan, drew the storyboards, and brainstormed the recreation with Giorgi. Giorgi Samushia built the modified Tinkerbelle prototype, staged and acted the video, and put together this writeup. Rati Mukhuradze (friend) lent us the projector, helped stage the shot, and hand-wizarded the final take. Giorgi's roommate and family reacted to early ideas. Tinkerbelle tool by the IRL-CT lab. Research from teamLab's artwork page (teamlab.art/ew/flowerforest) and their official video of the work. Claude was used to help research the artwork and to debug and extend the Tinkerbelle code.

---

---

# Part 2 — ReMastering the light

*This describes the second week's work for this lab activity.*

## Prep (before the next lab)

Find three other groups. (How? Maybe Slack?) Visit their Lab Hub pages, watch their
videos, and give them reactions and feedback: tell them what you saw happening,
guess the masterwork and the goals of the characters, and ask about anything that
wasn't clear.

**Who were the other groups you kibitzed with? Add links to their project pages here.**

We exchanged feedback with three other groups over Slack:

- [Group 1](https://github.com/JindiChai/Interactive-Lab-Hub/tree/Fall2026/Lab%201)
- [Group 2](https://github.com/davidzhanggg/Interactive-Lab-Hub/tree/Fall2026/Lab%201)
- [Group 3](https://github.com/Alexyen04/Alex-Yen-Interactive-Lab-Hub/tree/Fall2026/Lab%201)

**Summarize the feedback you got from your partners here.**

Feedback received:

* Jindi Chai: I was very surprised after seeing your demo video. It looks really cool visually. I can understand the main functional interactions and visual changes you described in the previous storyboards from the demo video. For instance, when someone approaches the scene, the flowers' color turns warm, and the interaction effect between the hand and the flowers is also very clear. If you want to go further, you could add sounds or more interactive actions on the current foundation. Since this project now feels more like a piece of art, adding some emotional or practical functions could make it more interesting and unique.

* David Zhang: Your masterwork can be clearly understood just by looking at the video and storyboards, where the projected flowers respond to the visitor's presence and gestures. The modifications made to the Tinkerbelle tool are amazing! They really make the experience super immersive and almost comparable to the real museum in Tokyo!

   The different interactions were also easy to distinguish, specially the 'swing', where the flowers scatter away from the user's hand. It was visually satisfying to see. However, I wonder whether a visitor who is unfamiliar with the installation would immediately know that they can approach, tap, or swing the flowers. Maybe the flowers could provide some subtle visual cue that encourages the user to experiment with different gestures.

   Another thing that would be interesting to explore is having multiple people interact with the projection at the same time. What would happen if two people touched of flicked the flowers in different places simultaneously? Would they affect each other?
I was also wondering how the installation decides exactly where the user's hand is. If you were to implement the interaction without a wizard, how would you detect the position and gestures of the user's hand?

   I also found the idea of the flowers continuing to move even when the user is not interacting really thoughtful. It shows that the environment exists independently from the user and makes the installation feel more alive

* Alex Yen: The story board very clearly illustrates the interaction between the user and masterwork. The colors and panels show very vividly that when a user interacts with the flowers on display, they light up brightly. Both storyboard and video are very good representation of the masterwork and how it interacts with the user.

***summary***

All three groups were able to understand the concept and the main interactions from the demo video and storyboards alone.  The approach response (flowers turning warm) and the hand-to-flower effects read clearly, and the swing was singled out as the most satisfying moment to watch. The Tinkerbelle modifications were called out as what makes the projection feel close to the real museum, and one group specifically liked that the field keeps moving when nobody is interacting, because it makes the environment feel like it exists on its own.

We also received several questions and suggestions that revealed directions for further development. First, would visitors who are unfamiliar with the installation naturally realize that they can approach, tap, or swing at the flowers? Subtle visual or sound cues could encourage them to explore these interactions. Second, we could consider multi-user interaction. For example, if two people touch or flick the flowers in different places at the same time, their effects might influence each other or create new patterns. In addition, without a wizard controlling the system, the installation would need a reliable way to detect the position of the user’s hand and distinguish between gestures such as tapping and swinging.

The feedback also suggested adding sound or more interactive actions. Since the project currently feels primarily like an artistic experience, giving it a clearer emotional expression or practical purpose could make it more distinctive. Based on these suggestions, our next iteration could focus on making the interactions easier to discover, exploring multi-user behavior, and using visual and sound feedback to create a clearer emotional experience.

## Remix, Update, or Critique the Master

Now that you understand your masterwork from the inside, respond to it. Do the
recreation again, but this time make it your own — pick one of these moves (or
combine them):

1. **Remix the modality.** Your recreation no longer has to (just) use light. Use
   vibration, sound, motion, heat — whatever best carries the interaction. Feel
   free to fork and modify the Tinkerbelle code. (Add your updates to this lab's folder!)
2. **Update it.** Redesign the piece for today's context, or for a setting its
   creators never imagined (the piece with roommates in the room, with children
   present, on a phone, in a car).
3. **Fix its weaknesses.** You identified this master's strengths and weaknesses
   in Part 0 — now address a weakness, or push a strength further.

We will grade this second pass with an emphasis on **creativity** and on how well
your response engages with what your master was really doing.

**Document everything here — especially the storyboard and video. Photos of the
prototype are great too.**

### Our remix

We combined two of the three moves: we remixed the modality by adding sound, and we fixed a weakness we saw in our own Part 1 build, that touching the flowers changed nothing.

Sound came first because the original has it. Borderless is not silent, and in Part 1 our wall was. Sound is also the cheapest way to pull a visitor further in, and it gave us an answer to one of the peer questions: with each gesture playing a note, two people touching the wall at once make a chord instead of two separate events.

The second change came from looking at our own Part 1 build. Our flowers rippled when touched and drifted back home, and nothing about the field was different after someone left. That is not what the original does. In Borderless, touching a flower scatters it. So we made touch take the flower apart: the petals fly off and the spot stays empty. We first planned for a different flower to grow back in the empty spot. Shuning's storyboard had the petals gathering back into the same flower instead, and we built to the storyboard. The field still outlasts us, which is what Part 1 was about for us. Now it also shows that we were there.

The peer questions about two people and about a visitor knowing they can interact both fed in. Two touch points, petal collisions and the flare wave are the two-people answer. The local approach, flowers gathering and twinkling near the person, is our answer to discoverability, and it is a change from Part 1, where approaching turned the whole wall warm.

Now a touch takes the flower apart. When the visitor taps, swings a hand across the wall, or flicks, the flowers under the hand burst into their own petals and the petals drift and tumble across the field. After a while each petal flies back on its own and the same flower reassembles as its petals land. The field heals, but petal by petal, so a touch stays visible for a while. Two people can touch the wall at once: petals from different hands collide, bounce apart, and flash where they meet, and a flying petal that crosses a living flower makes it flare, with the flare passing to its neighbours, weaker each time, until it dies out. Approach is local now too. When someone walks up, only the flowers near them drift toward the spot, twinkle, and warm, and when they leave those flowers relax back.

Every gesture also plays a sound: a tap, swing, or flick plucks a harp chord in a pentatonic scale, with its root chosen by where the hand is across the wall, low on the left and high on the right, and the notes ring long enough that two people at two places sound as a chord. Underneath sits an ambient bed. The field has a life of its own as well. Each flower buds, blooms, withers, and is replaced by a new flower in the same place, so the wall keeps changing when nobody is there, and there are three seasons, cherry, summer, and autumn, each with its own palette; a season change sweeps across the wall from one point. Two things from the feedback we did not address: the hand is still located by a person at the keyboard, and the piece still reads as art rather than gaining an emotional or practical function.

Credits for this part: the ambient track is "Uplifting Pad Texture" by samuelfjohanns, from Pixabay, used under the Pixabay Content License. The petal and centre artwork was drawn in Claude Design. The code changes to the Tinkerbelle fork were made with Claude Code.

### Storyboards

<img width="984" height="1024" alt="touch" src="https://github.com/user-attachments/assets/fd103697-133e-4668-a5d4-580aa64b0d13" />

Single touch and two touches. Drawn by Shuning.


<img width="980" height="1024" alt="swing" src="https://github.com/user-attachments/assets/a3f75a31-50fa-48e8-b056-807feed050e2" />

Single swing and two swings. Drawn by Shuning.

### Video

https://youtu.be/GmXsl4PS20c

We lost access to the projector after Part 1, so Part 2 is documented with a scripted screen recording with captions; the Part 1 video above shows the staging on the wall.

### Photos

![two touches at once, petals colliding](images/take-lights-0m59-1x.png)

Two touches at once: the two clouds of petals meet in the middle (the take at 0:59).

![two swings toward the centre](images/take-lights-2m24-1x.png)

Two swings toward the centre, in summer (the take at 2:24).

![the field in the autumn season](images/season-autumn-1x.png)

The field in the autumn season, nobody interacting.

## Reflection

The second round made us realize that we spent most of Part 1 trying to make the project look like teamLab. In Part 2, we started thinking more about what we personally wanted to change. The feedback from other groups helped because they asked questions we had not really considered, especially what could happen if two people interacted at the same time and how visitors would know what they could do. Even though our responses were still pre-programmed and manually triggered, thinking through these questions helped us imagine the project as a shared interaction instead of only a visual effect.

We also learned that it is easy to keep adding features once an idea starts working. We added sound, seasons, flower life cycles, petal collisions, and several types of gestures. Some of these made the demonstration feel more alive, but together they also made the prototype harder to control and explain. If we worked on it again, we would probably focus on fewer interactions and develop them more fully. Most importantly, we would connect the visual effects to a camera or sensor so that the system could detect a visitor’s position and gestures instead of relying on a person at the keyboard or a scripted recording.

The biggest thing we could not test was how the remix would feel as a real installation. Since we no longer had the projector, we had to document it through a scripted screen recording. The video shows our idea for how the flowers could respond, but it does not prove that someone standing in front of the wall would notice the responses or understand that they could interact. Our next step would be to add real-time tracking, project it at full scale, and let people try it without instructions. That would help us see which parts of the interaction are actually clear and which ones only seem clear because we already know how the system is supposed to work.

---



*Assignment lineage: this lab merges "Staging Interaction" (Interactive Lab Hub)
with "Recreating the Masters" (Interaction Design Studio, Profs. Scott Minneman &
Wendy Ju). Massive list of interactive light masterworks generated by Claude.ai.*
