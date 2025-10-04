
        user_text = listen_and_transcribe()
        print(f"You said: {user_text}")

        if "goodbye" in user_text or "bye" in user_text:
            speak("Goodbye, I am going back to photosynthesizing.")
            asleep = True
            disp.image(asleep_image, rotation)

        elif "how are you" in user_text:
            speak("I'm leafy and thriving, thank you for asking!")

        elif "water" in user_text:
            speak("Ahh, yes, water! My favorite drink!")

        elif "sun" in user_text:
            speak("I love the sun. I could lowkey use a bit more sunshine on my leaves.")
        else:
            # Ask Ollama for a personality-driven response
            plant_response = ask_specialized_ollama(user_text, "You are a green houseplant. Be funny and practical.")
            speak(plant_response)

if __name__ == "__main__":
    main()
