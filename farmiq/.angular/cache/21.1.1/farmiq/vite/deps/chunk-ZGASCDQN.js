import {
  __glob
} from "./chunk-PAXKX5KU.js";

// import("./**/*.entry.js") in node_modules/ionicons/dist/esm/index-Z3yp5Yym.js
var globImport_entry_js = __glob({
  "./ion-icon.entry.js": () => import("./ion-icon.entry-JPSX7HJX.js")
});

// node_modules/ionicons/dist/esm/index-Z3yp5Yym.js
var __defProp = Object.defineProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var getHostRef = (ref) => {
  if (ref.__stencil__getHostRef) {
    return ref.__stencil__getHostRef();
  }
  return void 0;
};
var registerInstance = (lazyInstance, hostRef) => {
  lazyInstance.__stencil__getHostRef = () => hostRef;
  hostRef.$lazyInstance$ = lazyInstance;
};
var consoleError = (e, el) => (0, console.error)(e, el);
var win = typeof window !== "undefined" ? window : {};
var plt = {
  $flags$: 0,
  $resourcesUrl$: "",
  jmp: (h2) => h2(),
  raf: (h2) => requestAnimationFrame(h2),
  ael: (el, eventName, listener, opts) => el.addEventListener(eventName, listener, opts),
  rel: (el, eventName, listener, opts) => el.removeEventListener(eventName, listener, opts),
  ce: (eventName, opts) => new CustomEvent(eventName, opts)
};
var promiseResolve = (v) => Promise.resolve(v);
var supportsConstructableStylesheets = (() => {
  try {
    new CSSStyleSheet();
    return typeof new CSSStyleSheet().replaceSync === "function";
  } catch (e) {
  }
  return false;
})();
var queuePending = false;
var queueDomReads = [];
var queueDomWrites = [];
var queueTask = (queue, write) => (cb) => {
  queue.push(cb);
  if (!queuePending) {
    queuePending = true;
    if (write && plt.$flags$ & 4) {
      nextTick(flush);
    } else {
      plt.raf(flush);
    }
  }
};
var consume = (queue) => {
  for (let i2 = 0; i2 < queue.length; i2++) {
    try {
      queue[i2](performance.now());
    } catch (e) {
      consoleError(e);
    }
  }
  queue.length = 0;
};
var flush = () => {
  consume(queueDomReads);
  {
    consume(queueDomWrites);
    if (queuePending = queueDomReads.length > 0) {
      plt.raf(flush);
    }
  }
};
var nextTick = (cb) => promiseResolve().then(cb);
var writeTask = queueTask(queueDomWrites, true);
var getAssetPath = (path) => {
  const assetUrl = new URL(path, plt.$resourcesUrl$);
  return assetUrl.origin !== win.location.origin ? assetUrl.href : assetUrl.pathname;
};
var setAssetPath = (path) => plt.$resourcesUrl$ = path;
var isComplexType = (o) => {
  o = typeof o;
  return o === "object" || o === "function";
};
var escapeRegExpSpecialCharacters = (text) => {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
};
var result_exports = {};
__export(result_exports, {
  err: () => err,
  map: () => map,
  ok: () => ok,
  unwrap: () => unwrap,
  unwrapErr: () => unwrapErr
});
var ok = (value) => ({
  isOk: true,
  isErr: false,
  value
});
var err = (value) => ({
  isOk: false,
  isErr: true,
  value
});
function map(result, fn) {
  if (result.isOk) {
    const val = fn(result.value);
    if (val instanceof Promise) {
      return val.then((newVal) => ok(newVal));
    } else {
      return ok(val);
    }
  }
  if (result.isErr) {
    const value = result.value;
    return err(value);
  }
  throw "should never get here";
}
var unwrap = (result) => {
  if (result.isOk) {
    return result.value;
  } else {
    throw result.value;
  }
};
var unwrapErr = (result) => {
  if (result.isErr) {
    return result.value;
  } else {
    throw result.value;
  }
};
var h = (nodeName, vnodeData, ...children) => {
  let child = null;
  let key = null;
  let simple = false;
  let lastSimple = false;
  const vNodeChildren = [];
  const walk = (c) => {
    for (let i2 = 0; i2 < c.length; i2++) {
      child = c[i2];
      if (Array.isArray(child)) {
        walk(child);
      } else if (child != null && typeof child !== "boolean") {
        if (simple = typeof nodeName !== "function" && !isComplexType(child)) {
          child = String(child);
        }
        if (simple && lastSimple) {
          vNodeChildren[vNodeChildren.length - 1].$text$ += child;
        } else {
          vNodeChildren.push(simple ? newVNode(null, child) : child);
        }
        lastSimple = simple;
      }
    }
  };
  walk(children);
  if (vnodeData) {
    if (vnodeData.key) {
      key = vnodeData.key;
    }
    {
      const classData = vnodeData.className || vnodeData.class;
      if (classData) {
        vnodeData.class = typeof classData !== "object" ? classData : Object.keys(classData).filter((k) => classData[k]).join(" ");
      }
    }
  }
  const vnode = newVNode(nodeName, null);
  vnode.$attrs$ = vnodeData;
  if (vNodeChildren.length > 0) {
    vnode.$children$ = vNodeChildren;
  }
  {
    vnode.$key$ = key;
  }
  return vnode;
};
var newVNode = (tag, text) => {
  const vnode = {
    $flags$: 0,
    $tag$: tag,
    $text$: text,
    $elm$: null,
    $children$: null
  };
  {
    vnode.$attrs$ = null;
  }
  {
    vnode.$key$ = null;
  }
  return vnode;
};
var Host = {};
var createSupportsRuleRe = (selector) => {
  const safeSelector2 = escapeRegExpSpecialCharacters(selector);
  return new RegExp(
    // First capture group: match any context before the selector that's not inside @supports selector()
    // Using negative lookahead to avoid matching inside @supports selector(...) condition
    `(^|[^@]|@(?!supports\\s+selector\\s*\\([^{]*?${safeSelector2}))(${safeSelector2}\\b)`,
    "g"
  );
};
createSupportsRuleRe("::slotted");
createSupportsRuleRe(":host");
createSupportsRuleRe(":host-context");
var getElement = (ref) => getHostRef(ref).$hostElement$;
var CAPTURE_EVENT_SUFFIX = "Capture";
var CAPTURE_EVENT_REGEX = new RegExp(CAPTURE_EVENT_SUFFIX + "$");

// node_modules/ionicons/dist/esm/index-RzboMlQJ.js
var CACHED_MAP;
var getIconMap = () => {
  if (typeof window === "undefined") {
    return /* @__PURE__ */ new Map();
  } else {
    if (!CACHED_MAP) {
      const win2 = window;
      win2.Ionicons = win2.Ionicons || {};
      CACHED_MAP = win2.Ionicons.map = win2.Ionicons.map || /* @__PURE__ */ new Map();
    }
    return CACHED_MAP;
  }
};
var addIcons = (icons) => {
  Object.keys(icons).forEach((name) => {
    addToIconMap(name, icons[name]);
    const toKebabCase = name.replace(/([a-z0-9]|(?=[A-Z]))([A-Z0-9])/g, "$1-$2").toLowerCase();
    if (name !== toKebabCase) {
      addToIconMap(toKebabCase, icons[name]);
    }
  });
};
var addToIconMap = (name, data) => {
  const map2 = getIconMap();
  const existingIcon = map2.get(name);
  if (existingIcon === void 0) {
    map2.set(name, data);
  } else if (existingIcon !== data) {
    console.warn(`[Ionicons Warning]: Multiple icons were mapped to name "${name}". Ensure that multiple icons are not mapped to the same icon name.`);
  }
};
var getUrl = (i) => {
  let url = getSrc(i.src);
  if (url) {
    return url;
  }
  url = getName(i.name, i.icon, i.mode, i.ios, i.md);
  if (url) {
    return getNamedUrl(url, i);
  }
  if (i.icon) {
    url = getSrc(i.icon);
    if (url) {
      return url;
    }
    url = getSrc(i.icon[i.mode]);
    if (url) {
      return url;
    }
  }
  return null;
};
var getNamedUrl = (iconName, iconEl) => {
  const url = getIconMap().get(iconName);
  if (url) {
    return url;
  }
  try {
    return getAssetPath(`svg/${iconName}.svg`);
  } catch (e) {
    console.log("e", e);
    console.warn(`[Ionicons Warning]: Could not load icon with name "${iconName}". Ensure that the icon is registered using addIcons or that the icon SVG data is passed directly to the icon component.`, iconEl);
  }
};
var getName = (iconName, icon, mode, ios, md) => {
  mode = (mode && toLower(mode)) === "ios" ? "ios" : "md";
  if (ios && mode === "ios") {
    iconName = toLower(ios);
  } else if (md && mode === "md") {
    iconName = toLower(md);
  } else {
    if (!iconName && icon && !isSrc(icon)) {
      iconName = icon;
    }
    if (isStr(iconName)) {
      iconName = toLower(iconName);
    }
  }
  if (!isStr(iconName) || iconName.trim() === "") {
    return null;
  }
  const invalidChars = iconName.replace(/[a-z]|-|\d/gi, "");
  if (invalidChars !== "") {
    return null;
  }
  return iconName;
};
var getSrc = (src) => {
  if (isStr(src)) {
    src = src.trim();
    if (isSrc(src)) {
      return src;
    }
  }
  return null;
};
var isSrc = (str) => str.length > 0 && /(\/|\.)/.test(str);
var isStr = (val) => typeof val === "string";
var toLower = (val) => val.toLowerCase();
var inheritAttributes = (el, attributes = []) => {
  const attributeObject = {};
  attributes.forEach((attr) => {
    if (el.hasAttribute(attr)) {
      const value = el.getAttribute(attr);
      if (value !== null) {
        attributeObject[attr] = el.getAttribute(attr);
      }
      el.removeAttribute(attr);
    }
  });
  return attributeObject;
};
var isRTL = (hostEl) => {
  if (hostEl) {
    if (hostEl.dir !== "") {
      return hostEl.dir.toLowerCase() === "rtl";
    }
  }
  return (document === null || document === void 0 ? void 0 : document.dir.toLowerCase()) === "rtl";
};

export {
  addIcons,
  getUrl,
  getName,
  isStr,
  inheritAttributes,
  isRTL,
  registerInstance,
  setAssetPath,
  h,
  Host,
  getElement
};
//# sourceMappingURL=chunk-ZGASCDQN.js.map
