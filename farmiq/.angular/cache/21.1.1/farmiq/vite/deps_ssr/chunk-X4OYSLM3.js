import { createRequire } from 'module';const require = createRequire(import.meta.url);

// node_modules/@ionic/core/dist/esm/dir-C53feagD.js
var isRTL = (hostEl) => {
  if (hostEl) {
    if (hostEl.dir !== "") {
      return hostEl.dir.toLowerCase() === "rtl";
    }
  }
  return (document === null || document === void 0 ? void 0 : document.dir.toLowerCase()) === "rtl";
};

export {
  isRTL
};
//# sourceMappingURL=chunk-X4OYSLM3.js.map
