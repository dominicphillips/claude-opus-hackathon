# AGENTS.md — StorySpark AI Agent Architecture

StorySpark uses a multi-agent system powered by Claude to transform parent input into magical, character-faithful clips that delight children. Each agent has a specialized role in the clip creation pipeline.

## Agent Overview

```
Parent Input (character + scenario + child name + context)
        │
        ▼
┌─────────────────────┐
│  Orchestrator Agent  │ ← Coordinates the full pipeline
└────────┬────────────┘
         │
    ┌────┴────┬──────────────┬─────────────┐
    ▼         ▼              ▼             ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Script │ │ Character│ │ Safety   │ │ Scene    │
│ Writer │ │ Voice    │ │ Guardian │ │ Director │
│ Agent  │ │ Agent    │ │ Agent    │ │ Agent    │
└────────┘ └──────────┘ └──────────┘ └──────────┘
    │            │             │            │
    ▼            ▼             ▼            ▼
  Script    Voice params   Safety OK    Scene desc
    │            │                         │
    └────────────┴─────────────────────────┘
                      │
                      ▼
              ┌──────────────┐
              │  TTS Service │
              └──────┬───────┘
                     │
                     ▼
                Audio Clip → Stored & Playable
```

---

## Agent Definitions

### 1. Orchestrator Agent

**Role:** Central coordinator that manages the clip creation pipeline.

**Responsibilities:**
- Receives parent's clip request (character, scenario type, child details, custom message)
- Dispatches work to specialized agents
- Manages the pipeline: Script → Safety Check → Voice Generation
- Handles errors and retries
- Returns final clip to parent for preview/approval

**Input:** `ClipRequest` from parent via API
**Output:** `GeneratedClip` with audio, script, and metadata

**Tools Available:**
- Call Script Writer Agent
- Call Safety Guardian Agent
- Call Scene Director Agent
- Invoke TTS API
- Store clip to database

---

### 2. Script Writer Agent

**Role:** Generates scripts that are faithful to each character's personality, speech patterns, and the show's tone.

**System Prompt Core:**
```
You are a children's TV script writer specializing in creating short,
personalized messages from beloved characters. You write scripts that:

1. Are PERFECTLY faithful to the character's voice, vocabulary, and personality
2. Address the child by name naturally (not forced)
3. Match the show's tone and themes
4. Are age-appropriate and warm
5. Accomplish the parent's goal (motivation, education, storytelling)
6. Are 30-90 seconds when spoken aloud
```

**Character Profiles (Frog & Toad):**

| Character | Personality | Speech Pattern | Themes |
|-----------|------------|----------------|--------|
| Frog | Optimistic, adventurous, encouraging, gentle leader | Warm, enthusiastic, uses nature metaphors, asks questions | Friendship, bravery, trying new things |
| Toad | Cautious, loyal, endearing worrier, ultimately brave | Hesitant then determined, self-deprecating humor, heartfelt | Overcoming fear, friendship, comfort |

**Scenario Templates:**

```python
SCENARIOS = {
    "chore_motivation": {
        "description": "Character encourages child to do a specific chore",
        "structure": [
            "Greeting (character-authentic)",
            "Relate to chore through show-relevant anecdote",
            "Encourage the child specifically",
            "Promise of satisfaction / tie back to friendship theme"
        ],
        "example_prompt": "Frog motivates Thomas to clean his room"
    },
    "storytelling_prompt": {
        "description": "Character starts a story and invites child to continue",
        "structure": [
            "Character sets the scene",
            "Introduces a gentle problem or adventure",
            "Pauses and asks child: 'What do you think happens next?'",
            "Encourages child's imagination"
        ]
    },
    "educational": {
        "description": "Character teaches a concept through show-relevant framing",
        "structure": [
            "Character notices something in their world",
            "Explains concept naturally through their experience",
            "Connects to child's world",
            "Asks engaging question"
        ]
    },
    "positive_reinforcement": {
        "description": "Character celebrates child's achievement",
        "structure": [
            "Excited greeting",
            "Specifically names what child did well",
            "Relates to character's own experience with effort",
            "Expression of pride and warmth"
        ]
    },
    "bedtime": {
        "description": "Character says goodnight with warmth",
        "structure": [
            "Gentle greeting",
            "Reflect on the day positively",
            "Cozy imagery from the show's world",
            "Warm goodnight"
        ]
    }
}
```

**Input:** Character, scenario type, child name, custom parent notes
**Output:** Script text with stage directions and emotion markers

---

### 3. Safety Guardian Agent

**Role:** Reviews all generated content to ensure it is safe, appropriate, and positive for children.

**Checks:**
- **Age appropriateness** — Language, concepts, and tone suitable for target age (2-8)
- **Emotional safety** — No fear-inducing content, guilt-tripping, or manipulation
- **Character fidelity** — Characters stay in-character and don't say anything the real character wouldn't
- **Positive framing** — Motivation through encouragement, never shame or punishment
- **No commercial content** — No brand mentions or purchasing encouragement
- **Cultural sensitivity** — Inclusive and respectful language

**Input:** Generated script + character profile + scenario context
**Output:** `SafetyResult` — approved, or rejected with specific feedback for revision

**Guardrails:**
```python
SAFETY_RULES = [
    "Never use negative reinforcement or guilt",
    "Never threaten consequences",
    "Never compare child unfavorably to others",
    "Always maintain character's canonical personality",
    "Never introduce scary or anxiety-inducing elements",
    "Never mention real-world violence or conflict",
    "Never use conditional love ('I'll like you if...')",
    "Always end on a positive, warm note",
    "Limit clip to age-appropriate vocabulary",
    "Never collect or reference personal data beyond first name"
]
```

---

### 4. Scene Director Agent

**Role:** Creates scene descriptions and visual/audio context for clips.

**Responsibilities:**
- Selects appropriate background setting from show's world
- Defines character emotion/expression states
- Adds ambient sound suggestions (birds, rain, cozy fire)
- Creates visual scene description for potential future video generation

**Input:** Script + scenario type + character
**Output:** `SceneDescription` with setting, mood, ambient audio tags

---

### 5. Character Voice Agent

**Role:** Translates scripts into voice generation parameters.

**Responsibilities:**
- Maps character personality to TTS voice parameters
- Adds emotion markers (warm, excited, gentle, sleepy)
- Controls pacing, pauses, and emphasis
- Ensures voice output matches character's canonical sound

**Voice Profiles:**
```python
VOICE_PROFILES = {
    "frog": {
        "base_voice": "warm_male_young",
        "pitch": "medium",
        "speed": "moderate",
        "warmth": "high",
        "enthusiasm": "medium-high",
        "personality_notes": "Gentle optimism, slight uplift at end of sentences"
    },
    "toad": {
        "base_voice": "warm_male_mature",
        "pitch": "slightly_lower",
        "speed": "slightly_slower",
        "warmth": "high",
        "enthusiasm": "medium",
        "personality_notes": "Endearing worry that resolves into warmth, thoughtful pauses"
    }
}
```

**Input:** Script with emotion markers + character voice profile
**Output:** TTS API parameters + processed script segments

---

## Pipeline Flow (Detailed)

```
1. PARENT CREATES CLIP REQUEST
   ├── Selects character: "Frog"
   ├── Selects scenario: "chore_motivation"
   ├── Enters child name: "Thomas"
   ├── Custom note: "He needs to put away his Legos"
   └── Submits request

2. ORCHESTRATOR receives request
   ├── Loads character profile for Frog
   ├── Loads scenario template for chore_motivation
   └── Dispatches to Script Writer

3. SCRIPT WRITER generates script
   └── Output: "Oh hello there, Thomas! It's me, Frog.
        You know, Toad and I had the most wonderful day today,
        but first we had to tidy up our garden. At first, Toad
        said 'Oh this is too much work, Frog!' But you know what?
        We made it into a game! I bet you could do the same with
        those Legos. What if you sorted them by color? I think
        you'd be amazed at what you can build tomorrow with a
        nice tidy set of Legos. Toad and I believe in you, Thomas!"

4. SAFETY GUARDIAN reviews script
   ├── ✅ Age appropriate
   ├── ✅ Positive framing (no guilt)
   ├── ✅ Character-faithful
   ├── ✅ Emotionally safe
   └── Output: APPROVED

5. CHARACTER VOICE AGENT processes for TTS
   ├── Applies Frog's voice profile
   ├── Marks emotion: warm_greeting → enthusiastic → encouraging
   └── Sets pacing and pauses

6. SCENE DIRECTOR creates context
   ├── Setting: Frog's garden, sunny afternoon
   ├── Mood: Cheerful, encouraging
   └── Ambient: Birds chirping, gentle breeze

7. TTS SERVICE generates audio
   └── Output: audio_clip.mp3

8. ORCHESTRATOR stores clip
   ├── Saves to database
   ├── Associates with child profile
   └── Returns clip for parent preview

9. PARENT PREVIEWS & APPROVES
   └── Clip is ready for Thomas! 🎉
```

---

## Technical Implementation

### Agent SDK Integration

```python
# Example: Script Writer Agent definition
from anthropic import Agent, tool

script_writer = Agent(
    name="ScriptWriter",
    model="claude-sonnet-4-5-20250929",
    system_prompt=SCRIPT_WRITER_SYSTEM_PROMPT,
    tools=[
        get_character_profile,
        get_scenario_template,
        get_show_context,
    ]
)

safety_guardian = Agent(
    name="SafetyGuardian",
    model="claude-sonnet-4-5-20250929",
    system_prompt=SAFETY_GUARDIAN_SYSTEM_PROMPT,
    tools=[
        check_vocabulary_level,
        check_emotional_safety,
        check_character_fidelity,
    ]
)

orchestrator = Agent(
    name="Orchestrator",
    model="claude-sonnet-4-5-20250929",
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    tools=[
        generate_script,      # calls script_writer
        review_safety,        # calls safety_guardian
        direct_scene,         # calls scene_director
        prepare_voice,        # calls character_voice
        generate_audio,       # calls TTS API
        store_clip,           # saves to DB
    ]
)
```

### API Endpoints

```
POST   /api/clips/generate     — Start clip generation pipeline
GET    /api/clips/{id}         — Get clip details + audio
GET    /api/clips              — List all clips for a child
POST   /api/clips/{id}/approve — Parent approves clip
DELETE /api/clips/{id}         — Delete a clip

GET    /api/characters         — List available characters
GET    /api/characters/{id}    — Character details + profile

GET    /api/scenarios          — List scenario templates
GET    /api/scenarios/{type}   — Scenario details

POST   /api/children           — Add a child profile
GET    /api/children/{id}      — Get child profile
```

---

## Design Principles

1. **Character Fidelity First** — Every word must sound like it came from the real character
2. **Safety is Non-Negotiable** — Every clip passes through safety review before reaching a child
3. **Parent Control** — Parents always preview and approve before a child sees/hears anything
4. **Warmth Over Efficiency** — We optimize for emotional warmth, not clip throughput
5. **Privacy by Design** — Minimal data collection, no child data sent to third parties beyond first name
