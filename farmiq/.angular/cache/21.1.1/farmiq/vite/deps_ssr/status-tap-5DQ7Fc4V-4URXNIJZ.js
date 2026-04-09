import { createRequire } from 'module';const require = createRequire(import.meta.url);
import {
  findClosestIonContent,
  scrollToTop
} from "./chunk-4B5JDM4Q.js";
import {
  componentOnReady
} from "./chunk-BXYMEQR3.js";
import {
  readTask,
  writeTask
} from "./chunk-MZZK63CD.js";
import "./chunk-EEKZWN3V.js";

// node_modules/@ionic/core/dist/esm/status-tap-5DQ7Fc4V.js
var startStatusTap = () => {
  const win = window;
  win.addEventListener("statusTap", () => {
    readTask(() => {
      const width = win.innerWidth;
      const height = win.innerHeight;
      const el = document.elementFromPoint(width / 2, height / 2);
      if (!el) {
        return;
      }
      const contentEl = findClosestIonContent(el);
      if (contentEl) {
        new Promise((resolve) => componentOnReady(contentEl, resolve)).then(() => {
          writeTask(async () => {
            contentEl.style.setProperty("--overflow", "hidden");
            await scrollToTop(contentEl, 300);
            contentEl.style.removeProperty("--overflow");
          });
        });
      }
    });
  });
};
export {
  startStatusTap
};
//# sourceMappingURL=status-tap-5DQ7Fc4V-4URXNIJZ.js.map
