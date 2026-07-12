# Agent Notes & Guidelines for ha-stiga-ble

These are critical architectural and technical rules that must be followed when working on this repository.

## 1. BLE Protocol & Protobuf Usage
Stiga does **not** send simple fixed-position hex structures over BLE. The payloads are serialized using **Protocol Buffers (Protobuf)** without keys. 
- Do not use index-based byte access (e.g., `data[4]`) unless verifying a header. 
- Use the generic Protobuf decoder (currently implemented in `coordinator.py:extract_protobuf_fields`) that handles `Varint` and `Little-Endian 32-bit float` decoding.
- **Key Characteristics**:
  - `General Status Characteristic` (Handler 48 / UUID `ed2abe7b...`): Status enum in Field 3 (Varint).
  - `Battery Status Characteristic` (Handler 43 / UUID `00002a19...`): Contains Capacity (Field 1, Varint), SOC (Field 2, Varint), Voltage (Field 7, Float), Cycles (Field 8, Varint), and Remaining Time (Field 9, Float).

## 2. Home Assistant Timeout Gotcha (DataUpdateCoordinator)
When initializing BLE integrations via `async_config_entry_first_refresh()` in Home Assistant, HA enforces a **strict 10-second default setup timeout** around the `_async_update_data` method.
- **Never use fixed sleep times** (e.g., `await asyncio.sleep(5)`) while waiting for notifications. Establishing the BLE connection often takes 5-7 seconds. If you blindly wait an additional 5 seconds, the total duration will exceed 10 seconds, causing `asyncio.exceptions.CancelledError` and a failed integration setup.
- **Solution**: Always use an `asyncio.Event()` that gets `.set()` immediately when the necessary notifications (e.g., status and battery) have arrived. Await this event via `asyncio.wait_for(...)` so the setup completes instantly once data is received, avoiding HA's timeout cancellation.
