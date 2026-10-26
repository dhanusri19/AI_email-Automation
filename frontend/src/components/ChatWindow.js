import React, { useState, useRef, useEffect } from "react";
import { api } from "../services/api";
import MicButton from "./MicButton";
export default function ChatWindow() {
  const [msgs, setMsgs] = useState([{ from: "bot", text: "Hi HR! Say 'help' to see what I can do." }]);
  const [text, setText] = useState("");
  const [voice, setVoice] = useState(true);
  const end = useRef(null);
  useEffect(() => { end.current && end.current.scrollIntoView(); }, [msgs]);
  const speak = (t) => {
    if (!voice || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(t.replace(/[-|]/g, " ")));
  };
  const send = async (m) => {
    const msg = (m ?? text).trim();
    if (!msg) return;
    setMsgs((p) => [...p, { from: "user", text: msg }]); setText("");
    try {
      const r = await api.post("/api/chat", { message: msg });
      setMsgs((p) => [...p, { from: "bot", text: r.reply }]); speak(r.reply);
    } catch { setMsgs((p) => [...p, { from: "bot", text: "Cannot reach server." }]); }
  };
  return (
    <div className="card">
      <h3>HR Chatbot</h3>
      <div className="chatbox">{msgs.map((m, i) => <div key={i} className={"msg " + m.from}>{m.text}</div>)}<div ref={end} /></div>
      <div style={{ marginTop: 8 }}>
        <input style={{ width: "60%" }} value={text} placeholder="Type e.g. show reviews today"
          onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} />
        <button className="btn" onClick={() => send()}>Send</button>
        <MicButton onResult={(t) => send(t)} />
        <label><input type="checkbox" checked={voice} onChange={(e) => setVoice(e.target.checked)} /> Voice replies</label>
      </div>
      <div>
        <button className="btn" onClick={() => setText("announce: ")}>announce: </button>
        <button className="btn" onClick={() => send("send email to anyone mail")}>send email to anyone mail</button>
        {["show reviews today", "show pending reviews", "dashboard", "send review emails", "yes", "no"].map((q) =>
          <button key={q} className="btn" onClick={() => send(q)}>{q}</button>)}
      </div>
    </div>
  );
}
