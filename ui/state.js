(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.TVBootState = api;
})(globalThis, function () {
  'use strict';

  function validIp(value) {
    if (typeof value !== 'string') return false;
    const parts = value.trim().split('.');
    if (parts.length !== 4 || parts.some(part => !/^(0|[1-9]\d{0,2})$/.test(part) || Number(part) > 255)) return false;
    const [a, b] = parts.map(Number);
    return a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168);
  }

  function deviceSelection(devices) {
    if (devices.length === 1) return { mode: 'single', selected: devices[0] };
    if (devices.length > 1) return { mode: 'multiple', selected: null };
    return { mode: 'none', selected: null };
  }

  function resultKind(result) {
    const view = result && result.view;
    if (!view || view.state === 'unsupported') return 'unsupported';
    if (view.state === 'off') return 'off';
    return view.can_disable ? 'ready' : 'blocked';
  }

  return { validIp, deviceSelection, resultKind };
});
