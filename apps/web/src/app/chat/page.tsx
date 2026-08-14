import type { Metadata } from "next";
import { ChatClient } from "./ChatClient";

export const metadata: Metadata = {
  title: "Companion",
  description: "Ngobrol sama travel companion kamu — destinasi, penerbangan, itinerary.",
  // The conversation is the product here, not something to index.
  robots: { index: false, follow: true },
};

export default function ChatPage() {
  return <ChatClient />;
}
