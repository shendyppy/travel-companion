"use client";

/**
 * One message.
 *
 * Agent messages are not bubbles. They are a reading column with an avatar
 * beside them, because the content is long-form Markdown with cards and tool
 * status folded into it — wrapping several hundred words and a stack of flight
 * cards in a rounded speech bubble makes both harder to read. The user's own
 * messages are short and do get a bubble, which also gives the thread its
 * left/right rhythm without needing two bubble styles.
 *
 * `parts` renders in order, so a tool called halfway through an answer appears
 * halfway through the answer.
 */

import { Compass } from "lucide-react";
import { cn } from "@/lib/utils";
import { MessageMarkdown } from "@/components/molecules/MessageMarkdown";
import { ToolActivity } from "@/components/molecules/ToolActivity";
import { ToolResult } from "@/components/organisms/ToolResult";
import type { Message } from "@/lib/types";

export function ChatBubble({
  message,
  onAsk,
}: {
  message: Message;
  onAsk?: (message: string) => void;
}) {
  if (message.role === "user") {
    const text = message.parts.map((p) => (p.kind === "text" ? p.text : "")).join("");
    return (
      <div className="animate-rise flex justify-end">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-bubble rounded-br-md bg-accent px-4 py-2.5 text-base text-accent-fg">
          {text}
        </p>
      </div>
    );
  }

  const empty = message.parts.length === 0;

  return (
    <div className="animate-rise flex gap-3">
      <span
        className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-full bg-accent-soft"
        aria-hidden
      >
        <Compass className="size-4 text-accent" />
      </span>

      <div className="min-w-0 flex-1">
        {empty && message.pending && <ThinkingDots />}

        {message.parts.map((part, index) => {
          if (part.kind === "text") {
            const last = index === message.parts.length - 1;
            return (
              <div key={index}>
                <MessageMarkdown>{part.text}</MessageMarkdown>
                {last && message.pending && <Caret />}
              </div>
            );
          }
          return (
            <div key={part.activity.id} className="my-2.5">
              <ToolActivity activity={part.activity} />
              <ToolResult activity={part.activity} onAsk={onAsk} />
            </div>
          );
        })}

        {message.error && (
          <p
            className={cn(
              "mt-2 rounded-lg border border-border bg-error-soft/50 px-3 py-2 text-sm text-fg-muted",
            )}
          >
            {message.error}
          </p>
        )}
      </div>
    </div>
  );
}

/** Shown between sending and the first token. */
function ThinkingDots() {
  return (
    <div className="flex h-6 items-center gap-1" role="status" aria-label="Agent sedang berpikir">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="animate-breathe size-1.5 rounded-full bg-fg-subtle"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  );
}

/** Sits at the end of streaming text. Purely decorative, so hidden from AT. */
function Caret() {
  return (
    <span
      className="animate-caret ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 bg-accent"
      aria-hidden
    />
  );
}
