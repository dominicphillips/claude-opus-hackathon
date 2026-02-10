import { useState } from "react";
import { useQuery } from "@/hooks/useApi";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { Character, Child, Clip, Scenario } from "@/types/api";
import { Sparkles, BookOpen, Trophy, Moon, Lightbulb, Wand2, Play, Clock, Shield, Volume2 } from "lucide-react";

const SCENARIO_ICONS: Record<string, React.ReactNode> = {
  chore_motivation: <Sparkles className="w-5 h-5" />,
  storytelling: <BookOpen className="w-5 h-5" />,
  educational: <Lightbulb className="w-5 h-5" />,
  positive_reinforcement: <Trophy className="w-5 h-5" />,
  bedtime: <Moon className="w-5 h-5" />,
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  generating: "bg-blue-100 text-blue-800",
  safety_review: "bg-purple-100 text-purple-800",
  ready: "bg-green-100 text-green-800",
  approved: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-800",
  safety_failed: "bg-red-100 text-red-800",
};

export default function Dashboard() {
  const { data: characters } = useQuery<Character[]>("/characters");
  const { data: children } = useQuery<Child[]>("/children");
  const { data: scenarios } = useQuery<Scenario[]>("/scenarios");
  const { data: clips, refetch: refetchClips } = useQuery<Clip[]>("/clips");

  const [creating, setCreating] = useState(false);
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [parentNote, setParentNote] = useState("");
  const [generating, setGenerating] = useState(false);

  const child = children?.[0]; // Thomas — our demo child

  async function handleGenerate() {
    if (!child || !selectedCharacter || !selectedScenario) return;
    setGenerating(true);

    try {
      const res = await fetch("/api/clips/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          child_id: child.id,
          character_id: selectedCharacter,
          scenario_type: selectedScenario,
          parent_note: parentNote || null,
        }),
      });
      const clip = await res.json();

      // Poll for completion
      const poll = setInterval(async () => {
        const r = await fetch(`/api/clips/${clip.id}`);
        const updated = await r.json();
        if (["ready", "approved", "failed", "safety_failed"].includes(updated.status)) {
          clearInterval(poll);
          setGenerating(false);
          setCreating(false);
          setSelectedCharacter(null);
          setSelectedScenario(null);
          setParentNote("");
          refetchClips();
        }
      }, 2000);
    } catch (e) {
      setGenerating(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-frog flex items-center justify-center text-white font-bold text-lg">
              S
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">StorySpark</h1>
              <p className="text-xs text-muted-foreground">Character Studio for Parents</p>
            </div>
          </div>
          {child && (
            <div className="flex items-center gap-2 bg-muted rounded-lg px-4 py-2">
              <span className="text-sm text-muted-foreground">Making clips for</span>
              <span className="font-semibold text-foreground">{child.name}</span>
              {child.age && <span className="text-xs text-muted-foreground">age {child.age}</span>}
            </div>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Create New Clip */}
        {!creating ? (
          <Card className="border-dashed border-2 border-primary/30 bg-primary/5 hover:bg-primary/10 transition-colors cursor-pointer" onClick={() => setCreating(true)}>
            <CardContent className="py-12 flex flex-col items-center gap-3">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                <Wand2 className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-lg font-semibold">Create a New Clip</h2>
              <p className="text-muted-foreground text-sm text-center max-w-md">
                Pick a character, choose a scenario, and let AI create a personalized clip for {child?.name || "your child"}
              </p>
            </CardContent>
          </Card>
        ) : (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wand2 className="w-5 h-5 text-primary" />
                Create a Clip for {child?.name}
              </CardTitle>
              <CardDescription>Pick a character and scenario, then add your personal touch</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Step 1: Character */}
              <div>
                <label className="text-sm font-medium mb-3 block">1. Choose a Character</label>
                <div className="grid grid-cols-2 gap-3">
                  {characters?.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => setSelectedCharacter(c.id)}
                      className={`p-4 rounded-xl border-2 text-left transition-all ${
                        selectedCharacter === c.id
                          ? "border-primary bg-primary/5 shadow-md"
                          : "border-border hover:border-primary/30"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white text-xl font-bold ${
                          c.name === "Frog" ? "bg-frog" : "bg-toad"
                        }`}>
                          {c.name[0]}
                        </div>
                        <div>
                          <p className="font-semibold">{c.name}</p>
                          <p className="text-xs text-muted-foreground">{c.show_name}</p>
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{c.personality.slice(0, 100)}...</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Step 2: Scenario */}
              {selectedCharacter && (
                <div className="animate-fade-in">
                  <label className="text-sm font-medium mb-3 block">2. What kind of clip?</label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {scenarios?.map((s) => (
                      <button
                        key={s.id}
                        onClick={() => setSelectedScenario(s.type)}
                        className={`p-4 rounded-xl border-2 text-left transition-all ${
                          selectedScenario === s.type
                            ? "border-primary bg-primary/5 shadow-md"
                            : "border-border hover:border-primary/30"
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          {SCENARIO_ICONS[s.type] || <Sparkles className="w-4 h-4" />}
                          <p className="font-medium text-sm">{s.name}</p>
                        </div>
                        <p className="text-xs text-muted-foreground">{s.description.slice(0, 80)}...</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 3: Parent Note */}
              {selectedScenario && (
                <div className="animate-fade-in">
                  <label className="text-sm font-medium mb-2 block">3. Add context (optional)</label>
                  <textarea
                    value={parentNote}
                    onChange={(e) => setParentNote(e.target.value)}
                    placeholder={`e.g., "Thomas needs to put away his Legos before dinner" or "He was really brave at swimming today"`}
                    className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px] resize-none"
                  />
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center gap-3 pt-2">
                <Button
                  onClick={handleGenerate}
                  disabled={!selectedCharacter || !selectedScenario || generating}
                  size="lg"
                >
                  {generating ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Wand2 className="w-4 h-4 mr-2" />
                      Generate Clip
                    </>
                  )}
                </Button>
                <Button variant="ghost" onClick={() => { setCreating(false); setSelectedCharacter(null); setSelectedScenario(null); }}>
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent Clips */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Recent Clips</h2>
          {!clips?.length ? (
            <p className="text-muted-foreground text-sm">No clips yet. Create your first one above!</p>
          ) : (
            <div className="grid gap-4">
              {clips.map((clip) => (
                <ClipCard key={clip.id} clip={clip} characters={characters || []} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function ClipCard({ clip, characters }: { clip: Clip; characters: Character[] }) {
  const character = characters.find((c) => c.id === clip.character_id);
  const [playing, setPlaying] = useState(false);
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className="animate-fade-in">
      <CardContent className="py-4">
        <div className="flex items-start gap-4">
          {/* Character avatar */}
          <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white text-lg font-bold shrink-0 ${
            character?.name === "Frog" ? "bg-frog" : "bg-toad"
          }`}>
            {character?.name?.[0] || "?"}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold">{character?.name}</span>
              <span className="text-xs text-muted-foreground">{clip.scenario_type.replace(/_/g, " ")}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[clip.status] || "bg-gray-100"}`}>
                {clip.status}
              </span>
            </div>

            {clip.parent_note && (
              <p className="text-sm text-muted-foreground mb-2">"{clip.parent_note}"</p>
            )}

            {clip.generated_script && (
              <button onClick={() => setExpanded(!expanded)} className="text-xs text-primary hover:underline mb-2">
                {expanded ? "Hide script" : "Show script"}
              </button>
            )}
            {expanded && clip.generated_script && (
              <div className="bg-muted rounded-lg p-3 text-sm mb-2 animate-fade-in">
                {clip.generated_script}
              </div>
            )}

            {/* Safety checks */}
            {clip.safety_checks && (
              <div className="flex flex-wrap gap-1 mb-2">
                {Object.entries(clip.safety_checks).map(([key, val]) => (
                  <span key={key} className={`text-xs px-2 py-0.5 rounded-full ${val.pass ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                    <Shield className="w-3 h-3 inline mr-1" />
                    {key.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            )}

            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              {clip.duration_seconds && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {clip.duration_seconds.toFixed(1)}s
                </span>
              )}
              {clip.generation_time_ms && (
                <span className="flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  {(clip.generation_time_ms / 1000).toFixed(1)}s to generate
                </span>
              )}
            </div>
          </div>

          {/* Play button */}
          {clip.audio_url && clip.status === "ready" && (
            <div>
              {!playing ? (
                <Button
                  size="icon"
                  variant="outline"
                  onClick={() => {
                    const audio = new Audio(clip.audio_url!);
                    audio.onended = () => setPlaying(false);
                    audio.play();
                    setPlaying(true);
                  }}
                >
                  <Play className="w-4 h-4" />
                </Button>
              ) : (
                <Button size="icon" variant="outline" className="animate-pulse-soft">
                  <Volume2 className="w-4 h-4 text-primary" />
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
