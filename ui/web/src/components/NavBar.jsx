import React from "react";
import { Link } from "react-router-dom";

export default function NavBar() {
  return (
    <div className="w-full bg-primary text-white p-4 flex justify-between px-8">
      <div className="font-bold text-xl tracking-wide">AutoTARA-RAG UI</div>

      <div className="flex gap-6">
        <Link to="/" className="hover:text-accent">Dashboard</Link>
        <Link to="/stage1" className="hover:text-accent">Stage 1</Link>
        <Link to="/stage2" className="hover:text-accent">Stage 2</Link>
        <Link to="/stage3" className="hover:text-accent">Stage 3</Link>
        <Link to="/stage4" className="hover:text-accent">Stage 4</Link>
        <Link to="/stage5" className="hover:text-accent">Stage 5</Link>
        <Link to="/stage6" className="hover:text-accent">Stage 6</Link>
        <Link to="/stage7" className="hover:text-accent">Stage 7</Link>
      </div>
    </div>
  );
}
