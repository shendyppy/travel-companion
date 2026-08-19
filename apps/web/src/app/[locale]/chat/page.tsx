import type { Metadata } from "next";
import { getMessages } from "@/lib/i18n";
import { ChatClient } from "@/components/templates/ChatClient";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const m = getMessages(locale);

  return {
    title: m.nav.companion,
    description: m.meta.description,
    // The conversation is the product here, not something to index.
    robots: { index: false, follow: true },
  };
}

export default function ChatPage() {
  return <ChatClient />;
}
