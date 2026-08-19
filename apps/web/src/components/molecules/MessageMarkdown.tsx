import Markdown from "react-markdown";

/**
 * Markdown for agent answers.
 *
 * Agent replies are frequently several hundred words with headings, bold, lists
 * and the occasional table, so this is a reading surface rather than a chat
 * bubble with some formatting. The rhythm comes from the type scale in
 * globals.css — 15px body with a 25px line height — and the job here is mostly
 * to keep vertical spacing consistent as text streams in.
 */
export function MessageMarkdown({ children }: { children: string }) {
  return (
    <div className="text-base leading-relaxed [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
      <Markdown
        components={{
          p: ({ children }) => <p className="my-2.5">{children}</p>,
          strong: ({ children }) => <strong className="font-semibold text-fg">{children}</strong>,
          ul: ({ children }) => <ul className="my-2.5 list-disc space-y-1 pl-5">{children}</ul>,
          ol: ({ children }) => <ol className="my-2.5 list-decimal space-y-1 pl-5">{children}</ol>,
          li: ({ children }) => <li className="pl-0.5">{children}</li>,
          h1: ({ children }) => <h1 className="mb-2 mt-4 text-lg font-semibold">{children}</h1>,
          h2: ({ children }) => <h2 className="mb-2 mt-4 text-base font-semibold">{children}</h2>,
          h3: ({ children }) => <h3 className="mb-1.5 mt-3 text-base font-semibold">{children}</h3>,
          hr: () => <hr className="my-4 border-border" />,
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent underline underline-offset-2"
            >
              {children}
            </a>
          ),
          code: ({ children }) => (
            <code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-sm">{children}</code>
          ),
          blockquote: ({ children }) => (
            <blockquote className="my-3 border-l-2 border-accent bg-accent-soft/40 py-1 pl-3 text-fg-muted">
              {children}
            </blockquote>
          ),
          // Tables carry cost breakdowns and comparisons. They must scroll in
          // their own container — the page body never scrolls sideways.
          table: ({ children }) => (
            <div className="my-3 overflow-x-auto">
              <table className="w-full border-collapse text-sm">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border-b border-border px-2.5 py-1.5 text-left font-medium">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="tabular border-b border-border px-2.5 py-1.5">{children}</td>
          ),
        }}
      >
        {children}
      </Markdown>
    </div>
  );
}
