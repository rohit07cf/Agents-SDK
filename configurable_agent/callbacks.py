# callbacks.py

class StreamingCallback:
    """Simple callback to stream every intermediate token/step."""

    def on_step(self, text: str):
        print(f"📤 STREAM: {text}", end="", flush=True)

    def on_final(self, text: str):
        print(f"\n🏁 FINAL OUTPUT: {text}")
