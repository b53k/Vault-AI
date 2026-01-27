/**
 * API Client for Chat Streaming
 * This handles Server-Sent Events (SSE) for real-time chat
 * 
 * @param request - Chat request with query, user_id, and optional thread_id
 * @param onEvent - Callback function called for each event received from the server
 * @param onError - Optional error handler
 * @return AbortController for canceling the stream
 */

import type { ChatRequest, ChatEvent } from '@/lib/types';

const AGENT_SERVICE_URL = process.env.NEXT_PUBLIC_AGENT_SERVICE_URL || 'http://localhost:8000';


export async function streamChat(
  request: ChatRequest,
  onEvent: (event: ChatEvent) => void,
  onError?: (error: Error) => void
): Promise<AbortController> {
  // Create an AbortController so we can cancel the request if needed
  const abortController = new AbortController();

  try {
    // Make a POST request to the streaming endpoint
    const response = await fetch(`${AGENT_SERVICE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      signal: abortController.signal, // Allow cancellation
    });

    // Check if the response is ok
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Check if the response is actually a stream
    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('text/event-stream')) {
      throw new Error('Expected Server-Sent Events stream');
    }

    // Get the reader from the response body
    // This allows us to read the stream chunk by chunk
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    // Create a TextDecoder to convert bytes to text
    const decoder = new TextDecoder();

    // Buffer to accumulate partial messages
    let buffer = '';

    // Read the stream asynchronously
    const readStream = async () => {
      try {
        while (true) {
          // Read a chunk from the stream
          const { done, value } = await reader.read();

          // If the stream is done, break the loop
          if (done) {
            // Send a final "done" event
            onEvent({ type: 'done' });
            break;
          }

          // Decode the chunk (convert bytes to text)
          buffer += decoder.decode(value, { stream: true });

          // SSE format: "data: {json}\n\n"
          // We need to split by double newlines to get complete events
          const lines = buffer.split('\n\n');
          
          // Keep the last incomplete line in the buffer
          buffer = lines.pop() || '';

          // Process each complete event
          for (const line of lines) {
            // Skip empty lines
            if (!line.trim()) continue;

            // SSE events start with "data: "
            if (line.startsWith('data: ')) {
              try {
                // Extract the JSON part (everything after "data: ")
                const jsonStr = line.slice(6); // Remove "data: " prefix
                
                // Parse the JSON into a ChatEvent
                const event: ChatEvent = JSON.parse(jsonStr);
                
                // Call the callback with the event
                onEvent(event);
              } catch (parseError) {
                console.error('Failed to parse SSE event:', parseError);
                // Continue processing other events even if one fails
              }
            }
          }
        }
      } catch (error) {
        // Handle errors during streaming
        if (error instanceof Error && error.name === 'AbortError') {
          // Request was cancelled - this is expected, don't treat as error
          return;
        }
        
        // Call the error handler if provided
        if (onError) {
          onError(error instanceof Error ? error : new Error(String(error)));
        } else {
          console.error('Error reading stream:', error);
        }
      }
    };

    // Start reading the stream (don't await - let it run in background)
    readStream();

    // Return the abort controller so the caller can cancel if needed
    return abortController;
  } catch (error) {
    // Handle initial connection errors
    if (onError) {
      onError(error instanceof Error ? error : new Error(String(error)));
    } else {
      console.error('Error starting chat stream:', error);
    }
    
    // Return abort controller anyway (even though request failed)
    return abortController;
  }
}

/**
 * Helper function to check if the agent service is healthy
 */
export async function checkAgentHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${AGENT_SERVICE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}