const $ = id => document.getElementById(id);
const moods = {normal: 'Feeling cozy', happy: 'Happy little heart', needs_care: 'A little care, please'};
const captions = {normal: 'Small acts of kindness make a happy home.', happy: 'All this love is making my heart glow.', needs_care: 'Could we spend a little time together?'};
async function refresh() {
  try {
    const response = await fetch('/api/state', {cache: 'no-store'});
    if (!response.ok) throw new Error('Server unavailable');
    const {state:s, connected, fresh} = await response.json();
    $('connection').textContent = !connected ? '● MQTT disconnected · reconnecting' : !fresh ? '● MQTT connected · waiting for engine' : '● MQTT connected · in sync';
    $('connection').classList.toggle('online', connected && fresh);
    if (!s) return;
    for (const key of ['fullness', 'happiness', 'energy']) {
      $(key).value = s[key];
      $(key + '-value').replaceChildren(document.createTextNode(s[key] + ' '));
      const small = document.createElement('small'); small.textContent = '/ 100'; $(key + '-value').append(small);
    }
    const won = s.status === 'won';
    document.body.classList.toggle('won', won);
    $('pet').setAttribute('class', s.mood);
    $('mood').textContent = !fresh ? 'Last known state' : won ? 'We did it! ♡' : moods[s.mood];
    $('pet-caption').textContent = won ? 'Three friends. One very loved Longan.' : captions[s.mood];
    const elapsed = Number(s.cooperation_seconds) || 0;
    $('cooperation').value = elapsed;
    $('countdown').textContent = `${elapsed.toFixed(1)} / 10s`;
    $('goal-title').textContent = won ? 'Together, we did it!' : 'Better, together';
    $('goal-copy').textContent = won ? 'Round complete. Start a new game when everyone is ready.' : 'Bring every bar to 70, then keep them there for 10 seconds.';
    for (const role of ['feed', 'play', 'rest']) $('role-' + role).classList.toggle('contributed', (s.contributors || []).includes(role));
    $('last-action').textContent = s.last_action ? `${s.last_device} shared a little ${s.last_action === 'feed' ? 'snack' : s.last_action === 'play' ? 'playtime' : 'rest'}${s.last_simulated ? ' · simulated' : ''}.` : 'Waiting for the first moment of care…';
    $('round-label').textContent = 'ROUND ' + s.round_id.slice(0, 6).toUpperCase();
  } catch (error) {
    $('connection').textContent = '● Dashboard unavailable · retrying';
    $('connection').classList.remove('online');
  } finally { setTimeout(refresh, 700); }
}
for (const button of document.querySelectorAll('[data-action]')) {
  button.addEventListener('click', async () => {
    button.disabled = true;
    try {
      const response = await fetch('/api/action/' + button.dataset.action, {method:'POST', headers:{'X-Pet-Token':document.querySelector('meta[name="pet-token"]').content}});
      const body = await response.json();
      $('control-status').textContent = body.error || body.message;
    } catch (_) { $('control-status').textContent = 'Dashboard unavailable. Check its terminal.'; }
    setTimeout(() => {button.disabled = false;}, 3000);
  });
}
refresh();
