import { useEffect, useRef } from 'react'
import type { ChatMessage } from '@/types'
import { ChatBubble } from '../molecules/ChatBubble'
import { TypingIndicator } from '../molecules/TypingIndicator'
import { ErrorToast } from '../molecules/ErrorToast'
import { WelcomeScreen } from './WelcomeScreen'
import { ScrollArea } from '@/components/ui'

interface MessageListProps {
  messages: ChatMessage[]
  greeting?: string
  isLoading?: boolean
  error?: string | null
  onErrorDismiss?: () => void
}

export function MessageList({
  messages,
  greeting,
  isLoading,
  error,
  onErrorDismiss,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Don't show typing indicator if the last message is still streaming
  const lastMessage = messages[messages.length - 1]
  const showTypingIndicator = isLoading && !lastMessage?.isStreaming

  return (
    <ScrollArea className="flex-1 overflow-y-auto">
      <div className="px-4 py-4 space-y-4">
        {messages.length === 0 && <WelcomeScreen greeting={greeting} />}

        {messages.map((message) => (
          <ChatBubble key={message.id} message={message} />
        ))}

        {showTypingIndicator && <TypingIndicator />}

        {error && onErrorDismiss && (
          <ErrorToast message={error} onDismiss={onErrorDismiss} />
        )}

        <div ref={messagesEndRef} />
      </div>
    </ScrollArea>
  )
}
