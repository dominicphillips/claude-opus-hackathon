import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "@/pages/Dashboard";
import AssetLibrary from "@/pages/AssetLibrary";
import { Wand2, Image } from "lucide-react";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background">
        {/* Bottom nav for quick switching */}
        <nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border z-50">
          <div className="max-w-6xl mx-auto flex">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `flex-1 flex flex-col items-center py-3 text-xs font-medium transition-colors ${
                  isActive ? "text-primary" : "text-muted-foreground hover:text-foreground"
                }`
              }
            >
              <Wand2 className="w-5 h-5 mb-1" />
              Clip Studio
            </NavLink>
            <NavLink
              to="/assets"
              className={({ isActive }) =>
                `flex-1 flex flex-col items-center py-3 text-xs font-medium transition-colors ${
                  isActive ? "text-primary" : "text-muted-foreground hover:text-foreground"
                }`
              }
            >
              <Image className="w-5 h-5 mb-1" />
              Asset Library
            </NavLink>
          </div>
        </nav>

        {/* Main content with bottom padding for nav */}
        <div className="pb-20">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/assets" element={<AssetLibrary />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
