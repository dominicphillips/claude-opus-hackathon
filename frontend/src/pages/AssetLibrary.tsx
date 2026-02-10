import { useState, useRef } from "react";
import { useQuery } from "@/hooks/useApi";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { ImageAsset } from "@/types/api";
import { Search, Paintbrush, Loader2, Check, AlertCircle, Image as ImageIcon, X, ChevronRight, UserPlus } from "lucide-react";

interface StreamEvent {
  step: string;
  status: string;
  detail: string;
  progress?: number;
  result_url?: string;
  images?: ImageAsset[];
  count?: number;
}

export default function AssetLibrary() {
  const { data: assets, refetch } = useQuery<{ images: ImageAsset[]; count: number }>("/agents/assets/images");
  const [searchQuery, setSearchQuery] = useState("Frog & Toad Apple TV show");
  const [searching, setSearching] = useState(false);
  const [searchEvents, setSearchEvents] = useState<StreamEvent[]>([]);

  // Character creator
  const [childProfile, setChildProfile] = useState({
    name: "Thomas",
    gender: "boy",
    hair_color: "brown",
    hair_style: "short and curly",
    eye_color: "blue",
    skin_tone: "light",
    height: "small",
    age: 4,
    outfit: "red t-shirt and blue shorts",
    extra: "happy and smiling",
  });

  // Customization state
  const [selectedImage, setSelectedImage] = useState<ImageAsset | null>(null);
  const [customizing, setCustomizing] = useState(false);
  const [customizeEvents, setCustomizeEvents] = useState<StreamEvent[]>([]);
  const [customizeResult, setCustomizeResult] = useState<string | null>(null);
  const [maskPosition, setMaskPosition] = useState("center");

  // ---- Streaming Image Search ----
  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setSearchEvents([]);

    const eventSource = new EventSource(
      `/api/agents/images/search/stream?query=${encodeURIComponent(searchQuery)}`
    );

    eventSource.addEventListener("status", (e) => {
      const data: StreamEvent = JSON.parse(e.data);
      setSearchEvents((prev) => [...prev, data]);
    });

    eventSource.addEventListener("result", (e) => {
      const data = JSON.parse(e.data);
      setSearchEvents((prev) => [...prev, { step: "complete", status: "done", detail: `Found ${data.count} images!` }]);
      eventSource.close();
      setSearching(false);
      refetch();
    });

    eventSource.addEventListener("error", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        setSearchEvents((prev) => [...prev, { step: "error", status: "error", detail: data.detail }]);
      } catch {
        setSearchEvents((prev) => [...prev, { step: "error", status: "error", detail: "Connection lost" }]);
      }
      eventSource.close();
      setSearching(false);
    });

    eventSource.onerror = () => {
      eventSource.close();
      setSearching(false);
      refetch();
    };
  }

  // ---- Image Customization ----
  async function handleCustomize() {
    if (!selectedImage) return;
    setCustomizing(true);
    setCustomizeEvents([]);
    setCustomizeResult(null);

    const formData = new FormData();
    formData.append("scene_image_url", selectedImage.url);
    formData.append("name", childProfile.name);
    formData.append("gender", childProfile.gender);
    formData.append("hair_color", childProfile.hair_color);
    formData.append("hair_style", childProfile.hair_style);
    formData.append("eye_color", childProfile.eye_color);
    formData.append("skin_tone", childProfile.skin_tone);
    formData.append("height", childProfile.height);
    formData.append("age", String(childProfile.age));
    formData.append("outfit", childProfile.outfit);
    formData.append("extra", childProfile.extra);
    formData.append("mask_position", maskPosition);

    try {
      const response = await fetch("/api/agents/images/customize/stream", {
        method: "POST",
        body: formData,
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data: StreamEvent = JSON.parse(line.slice(6));
                setCustomizeEvents((prev) => [...prev, data]);
                if (data.result_url) {
                  setCustomizeResult(data.result_url);
                }
              } catch {}
            }
          }
        }
      }
    } catch (e) {
      setCustomizeEvents((prev) => [...prev, { step: "error", status: "error", detail: String(e) }]);
    } finally {
      setCustomizing(false);
      refetch();
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <h1 className="text-xl font-bold">Asset Library</h1>
          <p className="text-sm text-muted-foreground">Find show images and add your child to scenes</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">

        {/* === Create Character === */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="w-5 h-5" />
              Create Character
            </CardTitle>
            <CardDescription>
              Build a character based on your child. This character will be drawn into show scenes in the matching art style.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">Name</label>
                <input value={childProfile.name} onChange={(e) => setChildProfile((p) => ({ ...p, name: e.target.value }))} className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">Gender</label>
                <select value={childProfile.gender} onChange={(e) => setChildProfile((p) => ({ ...p, gender: e.target.value }))} className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm">
                  <option value="boy">Boy</option>
                  <option value="girl">Girl</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">Age</label>
                <input type="number" value={childProfile.age} onChange={(e) => setChildProfile((p) => ({ ...p, age: parseInt(e.target.value) || 4 }))} min={1} max={12} className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">Height</label>
                <select value={childProfile.height} onChange={(e) => setChildProfile((p) => ({ ...p, height: e.target.value }))} className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm">
                  <option value="small">Small</option>
                  <option value="average">Average</option>
                  <option value="tall for their age">Tall</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">Hair Color</label>
                <select value={childProfile.hair_color} onChange={(e) => setChildProfile((p) => ({ ...p, hair_color: e.target.value }))} className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm">
                  <option>brown</option><option>blonde</option><option>black</option><option>red</option><option>auburn</option><option>light brown</option><option>dark brown</option><option>strawberry blonde</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">Hair Style</label>
                <select value={childProfile.hair_style} onChange={(e) => setChildProfile((p) => ({ ...p, hair_style: e.target.value }))} className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm">
                  <option>short and curly</option><option>short and straight</option><option>medium length wavy</option><option>long and straight</option><option>long and curly</option><option>short spiky</option><option>in a ponytail</option><option>in pigtails</option><option>with bangs</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">Eye Color</label>
                <select value={childProfile.eye_color} onChange={(e) => setChildProfile((p) => ({ ...p, eye_color: e.target.value }))} className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm">
                  <option>blue</option><option>brown</option><option>green</option><option>hazel</option><option>dark brown</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">Skin Tone</label>
                <select value={childProfile.skin_tone} onChange={(e) => setChildProfile((p) => ({ ...p, skin_tone: e.target.value }))} className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm">
                  <option>light</option><option>fair</option><option>medium</option><option>olive</option><option>tan</option><option>brown</option><option>dark</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className="text-xs font-medium text-muted-foreground mb-1 block">Outfit</label>
                <input value={childProfile.outfit} onChange={(e) => setChildProfile((p) => ({ ...p, outfit: e.target.value }))} placeholder="e.g., red t-shirt and blue shorts, favorite dinosaur hoodie" className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm" />
              </div>
              <div className="col-span-2">
                <label className="text-xs font-medium text-muted-foreground mb-1 block">Anything else?</label>
                <input value={childProfile.extra} onChange={(e) => setChildProfile((p) => ({ ...p, extra: e.target.value }))} placeholder="e.g., always carries a toy frog, wears glasses, has freckles" className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="mt-4 p-3 bg-muted rounded-lg text-sm text-muted-foreground">
              <span className="font-medium text-foreground">{childProfile.name}</span> — {childProfile.age}-year-old {childProfile.gender} with {childProfile.hair_style} {childProfile.hair_color} hair, {childProfile.eye_color} eyes, {childProfile.skin_tone} skin, wearing {childProfile.outfit}{childProfile.extra ? `. ${childProfile.extra}` : ""}
            </div>
          </CardContent>
        </Card>

        {/* === Image Search with Streaming === */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5" />
              Find Show Images
            </CardTitle>
            <CardDescription>
              Claude Agent browses the web for images — watch the progress live
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3">
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="e.g., Frog & Toad, Bluey, Daniel Tiger..."
                className="flex-1 rounded-lg border border-border bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              />
              <Button onClick={handleSearch} disabled={searching}>
                {searching ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Searching...</>
                ) : (
                  <><Search className="w-4 h-4 mr-2" /> Search</>
                )}
              </Button>
            </div>

            {/* Streaming status feed */}
            {searchEvents.length > 0 && (
              <div className="bg-muted rounded-lg p-3 space-y-2 animate-fade-in">
                {searchEvents.map((evt, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    {evt.status === "error" ? (
                      <AlertCircle className="w-4 h-4 text-destructive mt-0.5 shrink-0" />
                    ) : evt.step === "complete" ? (
                      <Check className="w-4 h-4 text-green-600 mt-0.5 shrink-0" />
                    ) : (
                      <Loader2 className="w-4 h-4 text-primary mt-0.5 shrink-0 animate-spin" />
                    )}
                    <span className={evt.status === "error" ? "text-destructive" : "text-foreground"}>
                      {evt.detail}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* === Image Customization Panel (when image selected) === */}
        {selectedImage && (
          <Card className="border-primary/30 animate-fade-in">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Paintbrush className="w-5 h-5 text-primary" />
                  Add {childProfile.name} to This Scene
                </CardTitle>
                <Button variant="ghost" size="icon" onClick={() => { setSelectedImage(null); setCustomizeResult(null); setCustomizeEvents([]); }}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-6">
                {/* Source image */}
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-2">Original Scene</p>
                  <img src={selectedImage.url} alt="Scene" className="rounded-lg w-full" />
                </div>

                {/* Result or placeholder */}
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-2">
                    {customizeResult ? "Result" : "Preview"}
                  </p>
                  {customizeResult ? (
                    <img src={customizeResult} alt="Customized" className="rounded-lg w-full" />
                  ) : (
                    <div className="aspect-video rounded-lg bg-muted flex items-center justify-center">
                      <p className="text-sm text-muted-foreground">{childProfile.name} will appear here</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Position picker */}
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-2 block">Character Position</label>
                <div className="flex gap-2">
                  {["left", "center", "right", "small_center"].map((pos) => (
                    <button
                      key={pos}
                      onClick={() => setMaskPosition(pos)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                        maskPosition === pos
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border hover:border-primary/30"
                      }`}
                    >
                      {pos.replace("_", " ")}
                    </button>
                  ))}
                </div>
              </div>

              {/* Progress events */}
              {customizeEvents.length > 0 && (
                <div className="bg-muted rounded-lg p-3 space-y-2">
                  {customizeEvents.map((evt, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      {evt.status === "done" ? (
                        <Check className="w-4 h-4 text-green-600 mt-0.5 shrink-0" />
                      ) : evt.status === "error" ? (
                        <AlertCircle className="w-4 h-4 text-destructive mt-0.5 shrink-0" />
                      ) : (
                        <Loader2 className="w-4 h-4 text-primary mt-0.5 shrink-0 animate-spin" />
                      )}
                      <div>
                        <span className="font-medium">{evt.step.replace("_", " ")}</span>
                        <span className="text-muted-foreground"> — {evt.detail}</span>
                      </div>
                    </div>
                  ))}
                  {/* Progress bar */}
                  {customizing && customizeEvents.length > 0 && (
                    <div className="w-full bg-border rounded-full h-1.5 mt-2">
                      <div
                        className="bg-primary h-1.5 rounded-full transition-all duration-500"
                        style={{ width: `${(customizeEvents[customizeEvents.length - 1]?.progress || 0) * 100}%` }}
                      />
                    </div>
                  )}
                </div>
              )}

              <Button onClick={handleCustomize} disabled={customizing} size="lg">
                {customizing ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Adding {childProfile.name} to the scene...</>
                ) : (
                  <><Paintbrush className="w-4 h-4 mr-2" /> Add {childProfile.name} to Scene</>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* === Image Grid === */}
        <div>
          <h2 className="text-lg font-semibold mb-4">
            Image Library {assets?.count ? `(${assets.count} images)` : ""}
          </h2>

          {!assets?.images?.length ? (
            <div className="text-center py-16 text-muted-foreground">
              <ImageIcon className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No images yet. Search for show images above.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {assets.images.map((img) => (
                <Card
                  key={img.filename}
                  className={`overflow-hidden group cursor-pointer transition-all ${
                    selectedImage?.filename === img.filename
                      ? "ring-2 ring-primary shadow-md"
                      : "hover:shadow-md"
                  }`}
                  onClick={() => setSelectedImage(img)}
                >
                  <div className="aspect-square bg-muted relative">
                    <img
                      src={img.url}
                      alt={img.title || img.filename}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <div className="bg-white/90 rounded-lg px-3 py-1.5 flex items-center gap-1 text-sm font-medium">
                        <Paintbrush className="w-3 h-3" /> Customize
                      </div>
                    </div>
                    {img.category === "customized" && (
                      <div className="absolute top-2 right-2 bg-primary text-white text-xs px-2 py-0.5 rounded-full">
                        Customized
                      </div>
                    )}
                  </div>
                  <CardContent className="p-3">
                    <p className="text-xs font-medium truncate">{img.title || img.filename}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-muted-foreground">{img.category}</span>
                      {img.relevance && (
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          img.relevance === "high" ? "bg-green-100 text-green-700" :
                          img.relevance === "medium" ? "bg-yellow-100 text-yellow-700" :
                          "bg-gray-100 text-gray-700"
                        }`}>
                          {img.relevance}
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
