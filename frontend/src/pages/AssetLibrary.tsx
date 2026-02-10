import { useState } from "react";
import { useQuery } from "@/hooks/useApi";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { ImageAsset } from "@/types/api";
import { Search, ImagePlus, Download, Loader2 } from "lucide-react";

export default function AssetLibrary() {
  const { data: assets, refetch } = useQuery<{ images: ImageAsset[]; count: number }>("/agents/assets/images");
  const [searchQuery, setSearchQuery] = useState("Frog & Toad Apple TV");
  const [searching, setSearching] = useState(false);
  const [generatePrompt, setGeneratePrompt] = useState("");
  const [generating, setGenerating] = useState(false);

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      await fetch("/api/agents/images/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery }),
      });
      refetch();
    } finally {
      setSearching(false);
    }
  }

  async function handleGenerate() {
    if (!generatePrompt.trim()) return;
    setGenerating(true);
    try {
      await fetch("/api/agents/images/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: generatePrompt }),
      });
      refetch();
      setGeneratePrompt("");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <h1 className="text-xl font-bold">Asset Library</h1>
          <p className="text-sm text-muted-foreground">Browse and generate images for your clips</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Search Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5" />
              Find Show Images
            </CardTitle>
            <CardDescription>
              Our AI agent will browse the web for images of characters, scenes, and backgrounds
            </CardDescription>
          </CardHeader>
          <CardContent>
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
          </CardContent>
        </Card>

        {/* Generate Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ImagePlus className="w-5 h-5" />
              Generate Custom Image
            </CardTitle>
            <CardDescription>
              Create original images using Google Nano Banana Pro via Replicate
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3">
              <input
                value={generatePrompt}
                onChange={(e) => setGeneratePrompt(e.target.value)}
                placeholder="e.g., A friendly frog and toad sitting by a pond, children's book illustration style"
                className="flex-1 rounded-lg border border-border bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
              />
              <Button onClick={handleGenerate} disabled={generating} variant="secondary">
                {generating ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating...</>
                ) : (
                  <><ImagePlus className="w-4 h-4 mr-2" /> Generate</>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Image Grid */}
        <div>
          <h2 className="text-lg font-semibold mb-4">
            Image Library {assets?.count ? `(${assets.count} images)` : ""}
          </h2>

          {!assets?.images?.length ? (
            <div className="text-center py-16 text-muted-foreground">
              <ImagePlus className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No images yet. Search for show images or generate custom ones above.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {assets.images.map((img) => (
                <Card key={img.filename} className="overflow-hidden group">
                  <div className="aspect-square bg-muted relative">
                    <img
                      src={img.url}
                      alt={img.title || img.filename}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <Button size="sm" variant="secondary">
                        <Download className="w-3 h-3 mr-1" /> Use
                      </Button>
                    </div>
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
