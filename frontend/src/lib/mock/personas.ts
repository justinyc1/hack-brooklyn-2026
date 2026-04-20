import type { InterviewerPersonaConfig, BehavioralPersonaConfig } from '../types'

export const personas: InterviewerPersonaConfig[] = [
  {
    id: 'friendly',
    name: 'Rachel',
    description: 'Warm, encouraging — puts you at ease while still probing for depth',
    traits: ['Encouraging', 'Patient', 'Supportive follow-ups'],
    sampleIntro: "Hi! Great to meet you. Let's work through this together — feel free to think out loud.",
  },
  {
    id: 'neutral',
    name: 'George',
    description: 'Professional and balanced — mirrors a real FAANG screen',
    traits: ['Balanced', 'Professional', 'Fair follow-ups'],
    sampleIntro: "Good morning. We have 45 minutes today. I'll walk you through the problem and we'll go from there.",
  },
  {
    id: 'intense',
    name: 'Adam',
    description: 'High-pressure, time-boxing — expects sharp, concise answers fast',
    traits: ['Time-boxing', 'Demanding', 'Rapid follow-ups'],
    sampleIntro: "Let's not waste time. You have 2 minutes to explain your approach before you start coding.",
  },
  {
    id: 'skeptical',
    name: 'Callum',
    description: 'Challenges every assumption — pushes hard on edge cases and tradeoffs',
    traits: ['Challenging', 'Skeptical', 'Deep-dive probing'],
    sampleIntro: "Interesting approach. But what if I told you that won't scale? Walk me through your assumptions.",
  },
]

export const behavioralPersonas: BehavioralPersonaConfig[] = [
  {
    id: 'supportive',
    name: 'Sarah',
    description: 'Warm, encouraging — prompts deeper storytelling and personal impact',
    traits: ['Encouraging', 'Depth-focused', 'Reflective'],
  },
  {
    id: 'corporate',
    name: 'Daniel',
    description: 'Formal, structured — strictly enforces STAR format throughout',
    traits: ['Structured', 'STAR-strict', 'Professional'],
  },
  {
    id: 'pressure',
    name: 'Fin',
    description: 'Fast-paced, direct — cuts off rambling, demands conciseness',
    traits: ['Time-boxing', 'Direct', 'Concise'],
  },
  {
    id: 'probing',
    name: 'Clyde',
    description: 'Skeptical, detail-oriented — questions every claim and motive',
    traits: ['Evidence-seeking', 'Skeptical', 'Deep-dive'],
  },
]
