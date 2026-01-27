// Type definitions for all the data types used on the frontend

// ============================================================================
// Core Data Models
// ============================================================================

export interface User {
    user_id: number;
    name: string;
    email: string;
    phone?: string;
    address?: string;
    city?: string;
    state?: string;
    risk_score: number; // 0.0 to 1.0
  }
  
  export interface Account {
    account_id: number;
    user_id: number;
    balance: number;
    type: "checking" | "savings";
  }
  
  export interface Transaction {
    transaction_id: number;
    account_id: number;
    amount: number; // Negative for spending, positive for deposits
    category: string;
    merchant?: string;
    timestamp: string; // ISO date string
    description?: string;
  }
  
  // ============================================================================
  // Chat & AI Agent Types
  // ============================================================================
  
  export type ChatEventType = 
    | "thinking" 
    | "tool_call" 
    | "tool_execution" 
    | "response" 
    | "done" 
    | "error";
  
  export interface ChatEvent {
    type: ChatEventType;
    content?: string;
    tools?: string[]; // Tool names being called
    metadata?: ToolMetadata[]; // SQL queries, RAG results, etc.
    status?: string;
  }
  
  export interface ToolMetadata {
    tool_name: string;
    tool_args: Record<string, any>;
    sql_params?: Record<string, any>; // For SQL analytics tool
    rag_results?: RAGSearchResult[]; // Top 3 RAG search results
  }
  
  export interface RAGSearchResult {
    id: number;
    title: string;
    content: string;
    metadata?: Record<string, any>;
    similarity_distance?: number;
  }
  
  export interface ChatMessage {
    id: string; // Unique message ID
    role: "user" | "assistant";
    content: string;
    timestamp: string;
    toolDetails?: ToolMetadata[]; // Expandable tool execution details
  }
  
  export interface ChatRequest {
    query: string;
    user_id: number;
    thread_id?: string;
  }
  
  // ============================================================================
  // Balance & Spending Analytics Types
  // ============================================================================
  
  export interface BalanceRequest {
    user_id: number;
    account_id?: number;
    account_type?: "checking" | "savings";
  }
  
  export interface BalanceResponse {
    user_id: number;
    filters: {
      account_id?: number;
      account_type?: string;
    };
    results: Account[];
  }
  
  export interface SpendingRequest {
    user_id: number;
    category?: string;
    start_date?: string; // ISO date string
    end_date?: string; // ISO date string
    group_by?: "category" | "merchant" | "month" | "account";
    account_id?: number;
    account_type?: "checking" | "savings";
  }
  
  export interface SpendingResult {
    group_value?: string; // Category name, merchant name, etc.
    month?: string; // ISO date string
    account_id?: number;
    account_type?: string;
    transaction_count: number;
    total_spending: number;
  }
  
  export interface SpendingResponse {
    user_id: number;
    start_date: string;
    end_date: string;
    filters: {
      account_id?: number;
      account_type?: string;
      category?: string;
    };
    group_by: string;
    summary: {
      total_transactions: number;
      total_spending: number;
    };
    results: SpendingResult[];
  }
  
  // ============================================================================
  // Admin Dashboard Types
  // ============================================================================
  
  export interface AdminStats {
    total_users: number;
    total_accounts: number;
    total_transactions: number;
    total_balance: number;
  }
  
  export interface PaginationInfo {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  }
  
  export interface UsersResponse {
    users: User[];
    pagination: PaginationInfo;
  }
  
  export interface UserDetails {
    user: User;
    accounts: Account[];
    transaction_summary: {
      total_transactions: number;
      total_spending: number;
      first_transaction: string | null;
      last_transaction: string | null;
    };
  }
  
  export interface TrendDataPoint {
    period: string; // ISO date string
    transaction_count: number;
    total_spending: number;
    unique_users: number;
  }
  
  export interface TrendsResponse {
    start_date: string;
    end_date: string;
    group_by: "day" | "week" | "month";
    trends: TrendDataPoint[];
  }
  
  export interface GeographicDistribution {
    state: string;
    user_count: number;
    avg_risk_score: number;
  }
  
  export interface GeographicResponse {
    distribution: GeographicDistribution[];
    total_states: number;
  }
  
  export interface RiskScoreStatistics {
    min_risk: number;
    max_risk: number;
    avg_risk: number;
    median_risk: number;
    low_risk_count: number; // risk_score < 0.3
    medium_risk_count: number; // 0.3 <= risk_score < 0.7
    high_risk_count: number; // risk_score >= 0.7
  }
  
  export interface RiskScoresResponse {
    statistics: RiskScoreStatistics;
    high_risk_users: User[]; // Top 10 highest risk users
  }
  
  // ============================================================================
  // API Error Types
  // ============================================================================
  
  export interface ApiError {
    detail: string;
    status_code?: number;
  }
  
  // ============================================================================
  // Utility Types
  // ============================================================================
  
  export type LoadingState = "idle" | "loading" | "success" | "error";
  
  export interface ApiResponse<T> {
    data?: T;
    error?: ApiError;
    loading: boolean;
  }