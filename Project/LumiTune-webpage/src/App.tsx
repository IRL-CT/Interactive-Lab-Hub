import React, { useEffect, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
import { Send } from 'lucide-react';
import mqtt, { MqttClient } from 'mqtt';

const GENRES = [
  { id: 'chill', label: 'Chill', color: '#A8C5E5' },
  { id: 'energetic', label: 'Energetic', color: '#9FD8A8' },
  { id: 'warm', label: 'Warm', color: '#F4DFA5' },
  { id: 'party', label: 'Party', color: '#E7A6A1' },
];

const config = (window as any).MUSICBOX_CONFIG;

const MQTT_URL = `ws://${config.PI_IP}:${config.WS_PORT}`;
const MQTT_TOPIC = "musicbox/genre/request";

export default function App() {
  const [name, setName] = useState('');
  const [decade, setDecade] = useState('2020');      // stored as "1950", "1960", ...
  const [genre, setGenre] = useState('chill');       // must match GENRES in mqtt_musicbox.py
  const [volume, setVolume] = useState(0.7);
  const [lastSent, setLastSent] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [mqttError, setMqttError] = useState<string | null>(null);

  const clientRef = useRef<MqttClient | null>(null);

  // ---- MQTT connection setup ----
  useEffect(() => {
    const client = mqtt.connect(MQTT_URL);
    clientRef.current = client;

    client.on('connect', () => {
      console.log('[MQTT] Connected');
      setIsConnected(true);
      setMqttError(null);
    });

    client.on('error', (err) => {
      console.error('[MQTT] Error', err);
      setMqttError('MQTT connection error');
      setIsConnected(false);
    });

    client.on('close', () => {
      console.log('[MQTT] Disconnected');
      setIsConnected(false);
    });

    return () => {
      client.end(true);
    };
  }, []);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!clientRef.current || !isConnected) {
      setLastSent('Not connected to music box (MQTT broker).');
      return;
    }

    const yearInt = parseInt(decade, 10);

    const payload = {
      type: 'genre_request',
      client_id: name || 'web_client',
      genre,                      // already lowercase: "chill", "energetic", "warm", "party"
      year: yearInt,              // must match YEAR_GROUPS in mqtt_musicbox.py
      volume,                     // 0.0 – 1.0
      timestamp: Math.floor(Date.now() / 1000),
    };

    const clientMessage = `Sent: year=${yearInt}, ${genre}, volume=${volume.toFixed(
      2,
    )}${name ? `, from ${name}` : ''}`;

    setIsSending(true);

    clientRef.current.publish(
      MQTT_TOPIC,
      JSON.stringify(payload),
      {},
      (err) => {
        if (err) {
          console.error('[MQTT] Publish error', err);
          setLastSent('Failed to send to music box via MQTT.');
        } else {
          console.log('[MQTT] Published payload', payload);
          setLastSent(clientMessage);
        }
        setIsSending(false);
      },
    );
  };

  return (
    <div className="min-h-screen bg-[#F9F8F6]">
      {/* Main content */}
      <div className="min-h-screen flex flex-col items-center justify-center px-4 py-8 md:py-12">
        {/* Hero Section */}
        <div className="text-center mb-8 md:mb-12 space-y-3 md:space-y-4">
          {/* Main title */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl text-[#5A4A3A]">
            LumiTune Controller
          </h1>

          {/* Subtitle */}
          <p className="text-base md:text-lg text-[#8B7B6B] max-w-2xl mx-auto px-4">
            Choose a decade, let the light pick the mood, and control music with gesture.
          </p>

          {/* Small MQTT status */}
          <div className="text-xs md:text-sm text-[#A39383]">
            MQTT: {isConnected ? 'Connected ✅' : 'Disconnected ❌'}
            {mqttError && <span className="ml-2">({mqttError})</span>}
          </div>
        </div>

        {/* Central Panel */}
        <div className="w-full max-w-[720px] mx-auto">
          <form onSubmit={handleSubmit}>
            <div className="panel p-6 md:p-8 lg:p-10 space-y-6 md:space-y-8">
              {/* Your Name */}
              <div className="form-field">
                <label htmlFor="name" className="form-label">
                  Your Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="form-input"
                  placeholder="Enter your name..."
                />
              </div>

              {/* Choose Decade */}
              <div className="form-field">
                <label htmlFor="decade" className="form-label">
                  Choose Decade
                </label>
                <select
                  id="decade"
                  value={decade}
                  onChange={(e) => setDecade(e.target.value)}
                  className="form-select"
                >
                  <option value="1950">1950s</option>
                  <option value="1960">1960s</option>
                  <option value="1970">1970s</option>
                  <option value="1980">1980s</option>
                  <option value="1990">1990s</option>
                  <option value="2000">2000s</option>
                  <option value="2010">2010s</option>
                  <option value="2020">2020s</option>
                </select>
              </div>

              {/* Choose Genre - Button Grid */}
              <div className="form-field">
                <label className="form-label">
                  Choose Genre
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
                  {GENRES.map((g) => (
                    <button
                      key={g.id}
                      type="button"
                      onClick={() => setGenre(g.id)}
                      className={`genre-button ${genre === g.id ? 'active' : ''}`}
                      style={
                        {
                          '--genre-color': g.color,
                        } as CSSProperties
                      }
                    >
                      {g.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Volume Slider */}
              <div className="form-field">
                <label htmlFor="volume" className="form-label">
                  Volume (0–1)
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    id="volume"
                    min="0"
                    max="1"
                    step="0.01"
                    value={volume}
                    onChange={(e) => setVolume(parseFloat(e.target.value))}
                    className="flex-1 slider"
                  />
                  <div className="volume-display">
                    {volume.toFixed(2)}
                  </div>
                </div>
              </div>

              {/* Submit Section */}
              <div className="space-y-4">
                <button
                  type="submit"
                  className="submit-button group disabled:opacity-60 disabled:cursor-not-allowed"
                  disabled={isSending || !isConnected}
                >
                  <Send className="w-5 h-5 transition-transform group-hover:translate-x-1" />
                  <span>
                    {isSending
                      ? 'Sending…'
                      : !isConnected
                      ? 'Not connected'
                      : 'Send to Music Box'}
                  </span>
                </button>

                {/* Status Message */}
                {lastSent && (
                  <div className="status-message">
                    {lastSent}
                  </div>
                )}
              </div>
            </div>
          </form>
        </div>

        {/* Footer hint */}
        <div className="mt-8 text-center text-[#A39383] text-sm">
          Designed with care ✨
        </div>
      </div>
    </div>
  );
}
