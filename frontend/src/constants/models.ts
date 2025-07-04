export interface Model {
  id: string;
  name: string;
  description?: string;
}

export const AVAILABLE_MODELS: Model[] = [
  { id: 'gpt-4', name: 'GPT-4', description: 'Most capable GPT model' },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'Fast and efficient' },
  { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus', description: 'Most capable Claude model' },
  { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', description: 'Balanced performance' },
  { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku', description: 'Fast and economical' }
];