import { useEffect } from 'react'
import { useChat } from '@/hooks/useChat'
import { ChatHeader } from '../organisms/ChatHeader'
import { MessageList } from '../organisms/MessageList'
import { ChatInput } from '../molecules/ChatInput'
import { SuggestionChips } from '../molecules/SuggestionChips'

export function ChatTemplate() {
  const {
    messages,
    suggestions,
    greeting,
    isLoading,
    error,
    sendMessage,
    clearError,
  } = useChat()

  // Auto-dismiss error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(clearError, 5000)
      return () => clearTimeout(timer)
    }
  }, [error, clearError])

  const handleSuggestionSelect = (suggestion: string) => {
    sendMessage(suggestion)
  }

  const hasMessages = messages.length > 0

  return (
    <div className="flex flex-col h-full w-full max-w-3xl mx-auto bg-background">
      <ChatHeader isLoading={isLoading} isVisible={hasMessages} />

      <MessageList
        messages={messages}
        greeting={greeting}
        isLoading={isLoading}
        error={error}
        onErrorDismiss={clearError}
      />

      <div className="flex-shrink-0 border-t border-border bg-background">
        <SuggestionChips
          suggestions={suggestions}
          onSelect={handleSuggestionSelect}
          disabled={isLoading}
        />

        <ChatInput
          onSend={sendMessage}
          disabled={isLoading}
          placeholder="Ketik pesan..."
        />
      </div>
    </div>
  )
}
