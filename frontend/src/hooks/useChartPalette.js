import { useEffect, useState } from "react";
import { readChartPalette } from "../utils/charts.js";

export default function useChartPalette() {
  const [palette, setPalette] = useState(null);

  useEffect(() => {
    let frame;
    const root = document.documentElement;
    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => setPalette(readChartPalette(getComputedStyle(root))));
    };
    update();
    // O atributo muda no mesmo clique do controle; o observer redesenha todos os canvas.
    const observer = new MutationObserver(update);
    observer.observe(root, { attributes: true, attributeFilter: ["data-theme"] });
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, []);

  return palette;
}
