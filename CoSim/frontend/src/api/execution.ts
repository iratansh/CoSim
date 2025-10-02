import axios from 'axios';
import { authorizedClient } from './client';

export interface CodeExecutionRequest {
  session_id: string;
  language: 'python' | 'cpp';
  code: string;
  file_path: string;
  args?: string[];
  stdin?: string;
}

export interface CodeExecutionResponse {
  execution_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  stdout?: string;
  stderr?: string;
  exit_code?: number;
  execution_time_ms?: number;
}

export interface BuildRequest {
  session_id: string;
  source_files: string[];
  output_binary: string;
  compiler: 'gcc' | 'g++' | 'clang' | 'clang++';
  flags?: string[];
}

export interface BuildResponse {
  build_id: string;
  status: 'success' | 'failed';
  stdout: string;
  stderr: string;
  artifacts?: string[];
}

export interface FileOperation {
  session_id: string;
  path: string;
  content?: string;
  operation: 'read' | 'write' | 'delete' | 'create' | 'list';
}

export interface FileResponse {
  path: string;
  content?: string;
  exists: boolean;
  is_directory?: boolean;
  files?: string[];
}

/**
 * Execute Python code in the session environment
 */
export const executePython = async (
  token: string,
  sessionId: string,
  code: string,
  filePath: string = '/tmp/script.py',
  args: string[] = []
): Promise<CodeExecutionResponse> => {
  const { data } = await authorizedClient(token).post<CodeExecutionResponse>(
    '/api/v1/sessions/execute/python',
    {
      session_id: sessionId,
      language: 'python',
      code,
      file_path: filePath,
      args
    }
  );
  return data;
};

/**
 * Build C++ code with specified compiler
 */
export const buildCpp = async (
  token: string,
  sessionId: string,
  sourceFiles: string[],
  outputBinary: string = 'a.out',
  compiler: 'g++' | 'clang++' = 'g++',
  flags: string[] = ['-std=c++17', '-O2']
): Promise<BuildResponse> => {
  const { data } = await authorizedClient(token).post<BuildResponse>(
    '/api/v1/sessions/build/cpp',
    {
      session_id: sessionId,
      source_files: sourceFiles,
      output_binary: outputBinary,
      compiler,
      flags
    }
  );
  return data;
};

/**
 * Execute compiled C++ binary
 */
export const executeBinary = async (
  token: string,
  sessionId: string,
  binaryPath: string,
  args: string[] = []
): Promise<CodeExecutionResponse> => {
  const { data } = await authorizedClient(token).post<CodeExecutionResponse>(
    '/api/v1/sessions/execute/binary',
    {
      session_id: sessionId,
      binary_path: binaryPath,
      args
    }
  );
  return data;
};

/**
 * Save file to session workspace
 */
export const saveFile = async (
  token: string,
  sessionId: string,
  path: string,
  content: string
): Promise<FileResponse> => {
  const { data } = await authorizedClient(token).post<FileResponse>(
    '/api/v1/sessions/files/write',
    {
      session_id: sessionId,
      path,
      content,
      operation: 'write'
    }
  );
  return data;
};

/**
 * Read file from session workspace
 */
export const readFile = async (
  token: string,
  sessionId: string,
  path: string
): Promise<FileResponse> => {
  const { data } = await authorizedClient(token).post<FileResponse>(
    '/api/v1/sessions/files/read',
    {
      session_id: sessionId,
      path,
      operation: 'read'
    }
  );
  return data;
};

/**
 * List files in directory
 */
export const listFiles = async (
  token: string,
  sessionId: string,
  path: string = '/'
): Promise<FileResponse> => {
  const { data } = await authorizedClient(token).post<FileResponse>(
    '/api/v1/sessions/files/list',
    {
      session_id: sessionId,
      path,
      operation: 'list'
    }
  );
  return data;
};

/**
 * Create WebSocket connection for terminal
 */
export const createTerminalWebSocket = (
  token: string,
  sessionId: string
): WebSocket => {
  const wsUrl = import.meta.env.VITE_API_BASE_URL?.replace('http', 'ws') || 'ws://localhost:8080';
  const ws = new WebSocket(`${wsUrl}/v1/sessions/${sessionId}/terminal?token=${token}`);
  return ws;
};

/**
 * Get execution status
 */
export const getExecutionStatus = async (
  token: string,
  executionId: string
): Promise<CodeExecutionResponse> => {
  const { data } = await authorizedClient(token).get<CodeExecutionResponse>(
    `/api/v1/sessions/executions/${executionId}`
  );
  return data;
};
