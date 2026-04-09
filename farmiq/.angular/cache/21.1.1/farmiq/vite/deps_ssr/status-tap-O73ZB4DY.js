import { createRequire } from 'module';const require = createRequire(import.meta.url);
import {
  findClosestIonContent,
  scrollToTop
} from "./chunk-CRESRBVU.js";
import {
  readTask,
  writeTask
} from "./chunk-LMMOMJ6R.js";
import {
  componentOnReady
} from "./chunk-DVD5D6D2.js";
import "./chunk-PDQ2DTDR.js";
import "./chunk-EEKZWN3V.js";

// node_modules/@ionic/core/components/status-tap.js
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
//# sourceMappingURL=status-tap-O73ZB4DY.js.map
