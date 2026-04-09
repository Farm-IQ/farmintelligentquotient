import { createRequire } from 'module';const require = createRequire(import.meta.url);

// node_modules/@ionic/core/dist/esm/validity-DJztqcrH.js
var checkInvalidState = (el) => {
  const hasIonTouched = el.classList.contains("ion-touched");
  const hasIonInvalid = el.classList.contains("ion-invalid");
  return hasIonTouched && hasIonInvalid;
};

export {
  checkInvalidState
};
//# sourceMappingURL=chunk-7QQ7GWHT.js.map
