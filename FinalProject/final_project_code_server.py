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
    print("Laptop Listener Active! Waiting for Pi...")
    app.run(host='0.0.0.0', port=5001)
