import React, { useState } from "react";
export default function MicButton({ onResult }) {
  const [on, setOn] = useState(false);
  const start = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return alert("Speech recognition not supported. Use Chrome or Edge.");
    const rec = new SR();
    rec.lang = "en-US"; rec.interimResults = false;
    rec.onstart = () => setOn(true);
    rec.onend = () => setOn(false);
    rec.onerror = () => setOn(false);
    rec.onresult = (e) => onResult(e.results[0][0].transcript);
    rec.start();
  };
  return <button className={"btn" + (on ? " red" : "")} onClick={start}>{on ? "Listening..." : "🎤 Speak"}</button>;
}
