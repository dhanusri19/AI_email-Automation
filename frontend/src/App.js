import React, { useState } from "react";
import UploadPanel from "./components/UploadPanel";
import ChatWindow from "./components/ChatWindow";
import Dashboard from "./components/Dashboard";
import EmailStatus from "./components/EmailStatus";
import FeedbackForm from "./components/FeedbackForm";
const tabs = { Upload: UploadPanel, Chat: ChatWindow, Dashboard, Emails: EmailStatus, Feedback: FeedbackForm };
export default function App() {
  const [tab, setTab] = useState("Upload");
  const Page = tabs[tab];
  return (
    <div>
      <div className="nav">{Object.keys(tabs).map((t) => <button key={t} className={t === tab ? "active" : ""} onClick={() => setTab(t)}>{t}</button>)}</div>
      <div className="page"><Page key={tab} /></div>
    </div>
  );
}
