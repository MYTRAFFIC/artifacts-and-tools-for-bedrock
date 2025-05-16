export enum OutboundEventType {
  HEARTBEAT = "HEARTBEAT",
  CONVERSE = "CONVERSE",
  INTERRUPT = "INTERRUPT",
}

export enum InboundEventType {
  HEARTBEAT = "HEARTBEAT",
  ERROR = "ERROR",
  LOOP = "LOOP",
  TEXT_CHUNK = "TEXT_CHUNK",
  TOOL_USE = "TOOL_USE",
}

export enum ToolStatus {
  RUNNING = "running",
  SUCCESS = "success",
  ERROR = "error",
}

export interface InboundFrame {
  frame_id: string;
  num_frames: number;
  frame_idx: number;
  last: boolean;
  data: string;
}

export type InboundPayload =
  | InboundPayloadHeartbeat
  | InboundPayloadError
  | InboundPayloadLoop
  | InboundPayloadTextChunk
  | InboundPayloadToolUse;

export interface InboundPayloadHeartbeat {
  event_type: InboundEventType.HEARTBEAT;
  sequence_idx: number;
  payload: unknown;
}

export interface InboundPayloadError {
  event_type: InboundEventType.ERROR;
  sequence_idx: number;
  error: string;
}

export interface InboundPayloadLoop {
  event_type: InboundEventType.LOOP;
  sequence_idx: number;
  finish: boolean;
}

export interface InboundPayloadTextChunk {
  event_type: InboundEventType.TEXT_CHUNK;
  sequence_idx: number;
  text: string;
}

export interface InboundPayloadToolUse {
  event_type: InboundEventType.TOOL_USE;
  sequence_idx: number;
  tool_use_id: string;
  tool_name: string;
  status: ToolStatus;
  extra: {
    request_text?: string;
    response_text?: string;
    response_html?: string;
    output_files?: {
      file_id: string;
      file_name: string;
    }[];
  };
}
