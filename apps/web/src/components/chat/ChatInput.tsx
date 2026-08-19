"use client";

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { ArrowUp, Square } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMessages } from "@/components/i18n/MessagesProvider";

const MAX_HEIGHT = 160;

/**
 * Multiline input that grows with its content.
 *
 * Enter sends, Shift+Enter breaks a line. The growth is capped rather than
 * unbounded — past about six lines the input starts eating the conversation it
 * belongs to, and scrolling within the field is the lesser problem.
 */
export function ChatInput({
  onSend,
  onStop,
  busy,
  placeholder,
  autoFocus,
  className,
}: {
  onSend: (message: string) => void;
  onStop?: () => void;
  busy?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
  className?: string;
}) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const { m } = useMessages();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
  }, [value]);

  const submit = () => {
    const text = value.trim();
    if (!text || busy) return;
    onSend(text);
    setValue("");
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <div
      className={cn(
        "flex items-end gap-2 rounded-panel border border-border bg-surface p-2 pl-4",
        "transition-[border-color,box-shadow] focus-within:border-border-strong focus-within:shadow-raised",
        className,
      )}
    >
      <textarea
        ref={ref}
        rows={1}
        value={value}
        autoFocus={autoFocus}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder={placeholder ?? m.tool.inputPlaceholder}
        aria-label="Pesan untuk agent"
        className="flex-1 resize-none bg-transparent py-2 text-base outline-none placeholder:text-fg-subtle"
      />

      {busy && onStop ? (
        <button
          type="button"
          onClick={onStop}
          aria-label="Hentikan"
          className="grid size-9 shrink-0 place-items-center rounded-lg border border-border text-fg-muted hover:bg-surface-2"
        >
          <Square className="size-3.5 fill-current" />
        </button>
      ) : (
        <button
          type="button"
          onClick={submit}
          disabled={!value.trim() || busy}
          aria-label="Kirim"
          className="grid size-9 shrink-0 place-items-center rounded-lg bg-accent text-accent-fg transition-opacity disabled:opacity-40"
        >
          <ArrowUp className="size-4" />
        </button>
      )}
    </div>
  );
}
