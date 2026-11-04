Drop sound files here. The light page looks for these names at load (any of mp3, ogg, wav, m4a):

  ambient.mp3   looping background pad, a minute or more, seamless loop
  tap.mp3       short effect for a tap, under half a second
  swipe.mp3     short effect for a swipe, under half a second

Any missing one is synthesized with Web Audio instead. The wizard's B key flips between
file and synth so the two can be compared live. Reload the light page after adding a file;
no server restart needed.
