import { createRequire } from 'module';const require = createRequire(import.meta.url);
import {
  createColorClasses
} from "./chunk-N72R6IQI.js";
import {
  getIonMode
} from "./chunk-AKSLLNZ7.js";
import {
  Host,
  h,
  registerInstance
} from "./chunk-MZZK63CD.js";
import "./chunk-EEKZWN3V.js";

// node_modules/@ionic/core/dist/esm/ion-text.entry.js
var textCss = ":host(.ion-color){color:var(--ion-color-base)}";
var Text = class {
  constructor(hostRef) {
    registerInstance(this, hostRef);
  }
  render() {
    const mode = getIonMode(this);
    return h(Host, { key: "361035eae7b92dc109794348d39bad2f596eb6be", class: createColorClasses(this.color, {
      [mode]: true
    }) }, h("slot", { key: "c7b8835cf485ba9ecd73298f0529276ce1ea0852" }));
  }
};
Text.style = textCss;
export {
  Text as ion_text
};
//# sourceMappingURL=ion-text.entry-U7RHB7FU.js.map
