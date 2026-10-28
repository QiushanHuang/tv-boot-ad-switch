const test = require('node:test');
const assert = require('node:assert/strict');
const { validIp, deviceSelection, resultKind } = require('../ui/state.js');

test('only a usable private IPv4 enables connection', () => {
  assert.equal(validIp('192.168.4.8'), true);
  assert.equal(validIp('10.2.3.4'), true);
  assert.equal(validIp('172.16.0.2'), true);
  for (const value of ['8.8.8.8', '127.0.0.1', '192.168.01.1', '192.168.1.256', 'host;reboot', '']) {
    assert.equal(validIp(value), false);
  }
});

test('a single discovery can be filled automatically but multiple TVs need a choice', () => {
  const one = { ip: '192.168.8.2', name: 'TV one' };
  const two = { ip: '192.168.8.3', name: 'TV two' };
  assert.deepEqual(deviceSelection([]), { mode: 'none', selected: null });
  assert.deepEqual(deviceSelection([one]), { mode: 'single', selected: one });
  assert.deepEqual(deviceSelection([one, two]), { mode: 'multiple', selected: null });
});

test('the UI does not offer a write for unsupported or incomplete results', () => {
  assert.equal(resultKind({ view: { state: 'unsupported', can_disable: false } }), 'unsupported');
  assert.equal(resultKind({ view: { state: 'ready', can_disable: false } }), 'blocked');
  assert.equal(resultKind({ view: { state: 'ready', can_disable: true } }), 'ready');
  assert.equal(resultKind({ view: { state: 'off', can_disable: false } }), 'off');
});
