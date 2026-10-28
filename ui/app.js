(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const { validIp, deviceSelection, resultKind } = window.TVBootState;
  const form = $('connect-form');
  const ip = $('tv-ip');
  const discoverButton = $('discover');
  const connectButton = $('connect');
  const disableButton = $('disable');
  const restoreButton = $('restore');
  const recheckButton = $('recheck');
  const backButton = $('back');
  const deviceChoice = $('device-choice');
  const selectedDevice = $('selected-device');
  const deviceList = $('tv-list');
  const connectMessage = $('connect-message');
  const resultMessage = $('result-message');
  const restoreDialog = $('restore-dialog');
  let ready = false;
  let busy = false;
  let connectedHost = '';
  let currentResult = null;

  function message(element, value, informative = false) {
    element.textContent = value || '';
    element.hidden = !value;
    element.classList.toggle('info', informative);
  }

  function updateControls() {
    discoverButton.disabled = !ready || busy;
    connectButton.disabled = !ready || busy || !validIp(ip.value);
    ip.disabled = busy;
    deviceList.disabled = busy;
    disableButton.disabled = busy;
    restoreButton.disabled = busy;
    recheckButton.disabled = busy;
    backButton.disabled = busy;
  }

  async function perform(action, button, pendingText) {
    if (!ready || busy) return null;
    busy = true;
    const labelNode = button.querySelector('span') || button;
    const label = labelNode.textContent;
    labelNode.textContent = pendingText;
    updateControls();
    try {
      return await action();
    } catch (_) {
      return { ok: false, error: '连接未完成，请重试。' };
    } finally {
      busy = false;
      labelNode.textContent = label;
      updateControls();
    }
  }

  function selectDevice(device) {
    ip.value = device.ip;
    selectedDevice.textContent = device.name;
    selectedDevice.hidden = !device.name;
    message(connectMessage, '');
    updateControls();
  }

  discoverButton.addEventListener('click', async () => {
    message(connectMessage, '');
    const result = await perform(() => window.pywebview.api.discover(), discoverButton, '搜索中…');
    if (!result) return;
    if (!result.ok) return message(connectMessage, result.error);
    const selection = deviceSelection(result.devices || []);
    deviceChoice.hidden = selection.mode !== 'multiple';
    selectedDevice.hidden = true;
    if (selection.mode === 'single') {
      selectDevice(selection.selected);
      connectButton.focus();
    } else if (selection.mode === 'multiple') {
      ip.value = '';
      deviceList.replaceChildren(new Option('请选择电视', ''));
      for (const device of result.devices) deviceList.add(new Option(device.name, device.ip));
      updateControls();
      deviceList.focus();
    } else {
      message(connectMessage, '未找到电视，可输入电视 IP。', true);
      ip.focus();
    }
  });

  deviceList.addEventListener('change', () => {
    ip.value = deviceList.value;
    selectedDevice.hidden = true;
    message(connectMessage, '');
    updateControls();
  });

  ip.addEventListener('input', () => {
    selectedDevice.hidden = true;
    deviceChoice.hidden = true;
    message(connectMessage, '');
    updateControls();
  });

  function showResult(result, notice = '') {
    currentResult = result;
    const kind = resultKind(result);
    const view = result.view;
    $('connect-screen').hidden = true;
    $('result-screen').hidden = false;
    const device = result.device || {};
    $('device-meta').textContent = [device.model, device.firmware || device.display].filter(Boolean).join(' · ');
    $('state-icon').src = kind === 'unsupported' || kind === 'blocked' ? 'icons/circle-alert.svg' : 'icons/circle-check.svg';
    $('state-heading').textContent = kind === 'ready' ? '可以关闭' : kind === 'off' ? '开关已关闭' : view.heading;
    const detail = kind === 'off' ? '重启电视后确认效果。' :
      kind === 'ready' && view.evidence && view.evidence.includes('社区') ? '社区报告，尚未经本项目实机验证。' :
      kind === 'blocked' || kind === 'unsupported' ? view.detail : '';
    $('state-detail').textContent = detail;
    $('state-detail').hidden = !detail;
    disableButton.hidden = !view.can_disable;
    restoreButton.hidden = !view.can_restore;
    message(resultMessage, notice, true);
    $('result-title').focus();
    updateControls();
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    const host = ip.value.trim();
    if (!validIp(host)) return message(connectMessage, '请输入有效的局域网 IP。');
    message(connectMessage, '');
    const result = await perform(() => window.pywebview.api.connect(host), connectButton, '连接中…');
    if (!result) return;
    if (!result.ok) return message(connectMessage, result.error);
    connectedHost = host;
    showResult(result);
  });

  backButton.addEventListener('click', () => {
    $('result-screen').hidden = true;
    $('connect-screen').hidden = false;
    currentResult = null;
    connectedHost = '';
    message(resultMessage, '');
    $('connect-title').focus();
    updateControls();
  });

  disableButton.addEventListener('click', async () => {
    message(resultMessage, '');
    const result = await perform(() => window.pywebview.api.disable(connectedHost), disableButton, '处理中…');
    if (!result) return;
    if (!result.ok) return message(resultMessage, result.error);
    showResult(result);
  });

  recheckButton.addEventListener('click', async () => {
    message(resultMessage, '');
    const result = await perform(() => window.pywebview.api.connect(connectedHost), recheckButton, '检测中…');
    if (!result) return;
    if (!result.ok) return message(resultMessage, result.error);
    showResult(result);
  });

  restoreButton.addEventListener('click', () => {
    restoreDialog.showModal();
    $('cancel-restore').focus();
  });
  $('cancel-restore').addEventListener('click', () => restoreDialog.close());
  $('confirm-restore').addEventListener('click', async () => {
    restoreDialog.close();
    message(resultMessage, '');
    const result = await perform(() => window.pywebview.api.restore(connectedHost), restoreButton, '恢复中…');
    if (!result) return;
    if (!result.ok) return message(resultMessage, result.error);
    showResult(result, '已恢复原设置。');
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && $('help').open) $('help').open = false;
  });
  window.addEventListener('pywebviewready', () => { ready = true; updateControls(); });
  if (window.pywebview && window.pywebview.api) ready = true;
  updateControls();
})();
