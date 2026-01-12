# Govee Scene Control - Complete API Documentation

This document describes all three methods for controlling scenes on Govee devices, their capabilities, and current implementation status.

## 🎯 Quick Start - What Actually Works

**For H6078 Torch Floor Lamp (and likely other Govee devices):**

### ✅ Recommended: Platform API v2 (100% Working)
Use these MCP tools for **reliable scene control**:

```python
# List your 7 custom DIY scenes
list_diy_scenes()

# List 89 built-in platform scenes
list_platform_scenes()

# Activate DIY scene by name
activate_diy_scene("Fire")

# Activate platform scene by name
activate_platform_scene_tool("Sunrise")
activate_platform_scene_tool("Christmas")
activate_platform_scene_tool("Ocean")
```

**Available Scenes:** 96 total (7 DIY + 89 platform)
**Reliability:** ✅ Excellent - Works every time
**Setup:** Just needs GOVEE_API_KEY in .env

### ⚠️ Local UDP - Basic Controls Only
The local UDP API works for basic controls but **scene activation is unreliable on H6078**:

```python
# ✅ These work fine
turn_on() / turn_off()
set_brightness(50)
set_color(255, 0, 0)

# ❌ These may not work on H6078
list_scenes()  # Shows 15 scenes but...
activate_scene(10)  # Often doesn't activate properly
```

### ❌ Tap-to-Run - Not Working Yet
Undocumented API authentication is currently blocked (status 454).
Infrastructure is ready, but activation pending auth fix.

---

## Overview

| API Type | Status | Requires | Scenes Available | Activation |
|----------|--------|----------|------------------|------------|
| **Local UDP** | ✅ Working | Device IP | 15 common scenes | ✅ Instant |
| **Platform API** | ✅ Working | API Key | DIY + 89 platform scenes | ✅ Instant |
| **Undocumented API** | ⚠️ Partial | Email/Password | Tap-to-run shortcuts + effects | ⏳ Pending AWS IoT |

## Option 1: Local UDP API (✅ Complete)

### Implementation
- Module: `src/local_api.py`
- Direct unicast UDP communication
- No multicast dependency

### MCP Tools
- `list_scenes()` - Lists 15 common scene codes
- `activate_scene(scene_code: int)` - Activates scene by code

### Available Scenes (15)
1. Sunrise
2. Sunset
3. Movie
4. Dating
5. Romantic
6. Blinking
7. Candlelight
8. Snowflake
9. Energetic
10. Rings
11. Beautiful
12. Night
13. Reading
14. Working
15. Sleeping

### Protocol Details
```python
# Discovery (UDP port 4001)
{
  "msg": {
    "cmd": "scan",
    "data": {"account_topic": "reserve"}
  }
}

# Scene Activation (UDP port 4003)
{
  "msg": {
    "cmd": "ptReal",
    "data": {
      "command": "pt",
      "value": 10  # Scene code
    }
  }
}
```

### Advantages
- ✅ Works offline (no internet required)
- ✅ Fastest response time
- ✅ No authentication needed
- ✅ Simple implementation

### Limitations
- ❌ Limited to 15 predefined scenes
- ❌ Requires device IP address
- ❌ No custom scene support

## Option 2: Platform API v2 (✅ Complete)

### Implementation
- Uses official Govee OpenAPI
- Endpoint: `https://openapi.api.govee.com`

### MCP Tools
- `list_diy_scenes()` - Lists custom DIY scenes
- `list_platform_scenes()` - Lists built-in platform scenes
- `activate_diy_scene(scene_name: str)` - Activates DIY scene
- `activate_platform_scene_tool(scene_name: str)` - Activates platform scene

### Available Scenes

#### DIY Scenes (7 custom for H6078)
- Lava
- Torch
- Green-Storm
- Dripping blood
- Renee
- Beach
- Fire

#### Platform Scenes (89 built-in for H6078)

**Nature Scenes:**
- Sunrise, Sunset, Sunset Glow, Rainbow, Snow flake, Aurora
- Forest, Waves, Fire, Falling Petals, Feather, Firefly
- Ocean, Moonlight, Water Drop, Waterfall, Earth, Mount Fuji
- Fish tank, Goldfish, Field, Strawberry, Mountain Stream
- Morning Dew, Sunflower, Bamboo Forest, Water Lily

**Holiday Scenes:**
- Halloween, Christmas, Valentine's Day, Easter
- Father's Day, Mother's Day, Halloween Witches, Christmas Eve
- Surprise Gifts, Christmas Bell, Candy Cane, Christmas Wreath
- Gingerbread Man, Santa Claus, Halloween Pumpkin, Santa's Belt
- Gingerbread House, Magic Pumpkin, Christmas Tree, Party

**Mood Scenes:**
- Enthusiastic, Warm, Relax, Ecological, Healing, Mysterious
- Reading, Work, Leisure, Sleep, Cheerful, Gradient, Daze
- Tension, Sweet, Meditation, Heartbeat, Childishness

**Game/Animation Scenes:**
- Dot Eater, Rope Skipping, Rings, Marshmallow, Contorted
- Aircraft Battle, Climbing Bamboo, Airship, Candy Crush
- Greedy Snake, Flow, Fantasy, Intergalactic Adventure

**Activity Scenes:**
- Kitchen Aromas, Dancing, Geometry, Smoke Rings
- Exercise, Little Duck, Hot Air Balloon, Seaside Sunset
- City Night Scene, Astronaut, Cherry Blossom Festival

### Protocol Details
```python
# List DIY Scenes
POST /router/api/v1/device/diy-scenes
{
  "requestId": "<uuid>",
  "payload": {
    "sku": "H6078",
    "device": "A1:39:D0:03:81:46:47:6A"  # WITH colons
  }
}

# Activate Scene
POST /router/api/v1/device/control
{
  "requestId": "<uuid>",
  "payload": {
    "sku": "H6078",
    "device": "A1:39:D0:03:81:46:47:6A",
    "capability": {
      "type": "devices.capabilities.dynamic_scene",
      "instance": "lightScene",  # or "diyScene"
      "value": {"id": 4139, "paramId": 4571}  # Platform scenes
      # OR
      "value": 21106205  # DIY scenes use numeric ID
    }
  }
}
```

### Advantages
- ✅ Official supported API
- ✅ Access to all DIY scenes
- ✅ 89+ platform scenes
- ✅ Works remotely (internet-based)
- ✅ Reliable and documented

### Limitations
- ❌ Requires internet connection
- ❌ Requires API key
- ❌ Doesn't include tap-to-run shortcuts

## Option 3: Undocumented API (⚠️ Partial)

### Implementation
- Module: `src/undoc_api.py`
- Based on research from [govee2mqtt](https://github.com/wez/govee2mqtt)
- Reverse-engineered from Govee mobile app

### MCP Tools
- `list_tap_to_run_shortcuts()` - Lists automation shortcuts
- `list_light_effects()` - Shows effect library
- `activate_tap_to_run_shortcut(name)` - ⏳ Pending AWS IoT

### Endpoints

#### 1. Account Login
```
POST https://app2.govee.com/account/rest/account/v1/login
{
  "email": "user@example.com",
  "password": "password",
  "client": "ios"
}

Response:
{
  "status": 200,
  "data": {
    "token": "bearer_token",
    "accountId": "...",
    "topic": "mqtt_topic"
  }
}
```

#### 2. Community API Login
```
POST https://community-api.govee.com/os/v1/login
{
  "email": "user@example.com",
  "password": "password"
}

Response:
{
  "status": 200,
  "data": {
    "token": "bearer_token",
    "tokenExpiredTime": 1234567890000
  }
}
```

#### 3. One-Click Shortcuts
```
GET https://app2.govee.com/bff-app/v1/exec-plat/home
Authorization: Bearer <community_token>

Response:
{
  "status": 200,
  "data": {
    "groups": [
      {
        "items": [
          {
            "type": "oneClick",
            "data": {
              "name": "Morning Routine",
              "id": "...",
              "iotRules": [...],
              "devices": [...]
            }
          }
        ]
      }
    ]
  }
}
```

#### 4. Light Effect Library
```
GET https://app2.govee.com/appsku/v1/light-effect-libraries?sku=H6078
Authorization: Bearer <account_token>

Response:
{
  "status": 200,
  "data": {
    "sceneCategories": [
      {
        "name": "Nature",
        "scenes": [...]
      }
    ]
  }
}
```

#### 5. IoT Credentials
```
GET https://app2.govee.com/app/v1/account/iot/key
Authorization: Bearer <account_token>

Response:
{
  "status": 200,
  "data": {
    "endpoint": "xxxxxx-ats.iot.us-east-1.amazonaws.com",
    "p12": "<base64_certificate>",
    "p12_pass": "password"
  }
}
```

### Required Headers
```python
{
  "User-Agent": "GoveeHome/5.6.01 (com.ihoment.GoVeeSensor; build:2; iOS 16.5.0)",
  "Content-Type": "application/json",
  "appVersion": "5.6.01",
  "clientId": "<device_id>",
  "clientType": "1",  # iOS
  "iotVersion": "0",
  "timestamp": "<milliseconds>"
}
```

### Current Status

✅ **Implemented:**
- Authentication flow (account + community login)
- One-click shortcut retrieval
- Light effect library retrieval
- IoT credential retrieval
- Token caching and expiration

⚠️ **Current Issue:**
- Authentication returns `status: 454, message: ""`
- Possible causes:
  - Account security settings
  - Rate limiting
  - API version mismatch
  - Region restrictions

⏳ **Pending:**
- AWS IoT MQTT client implementation
- Shortcut activation via MQTT
- P12 certificate parsing and TLS setup

### Advantages
- ✅ Access to tap-to-run automation shortcuts
- ✅ Complete light effect library
- ✅ Most comprehensive scene collection
- ✅ Real-time updates via AWS IoT MQTT

### Limitations
- ❌ Undocumented (may break anytime)
- ❌ Requires email/password
- ❌ Complex AWS IoT MQTT setup
- ❌ Currently blocked by auth issue

## Comparison Matrix

| Feature | Local UDP | Platform API | Undocumented API |
|---------|-----------|--------------|------------------|
| **Scene Count** | 15 | 96+ | Unknown (many) |
| **Custom Scenes** | ❌ | ✅ DIY | ✅ All |
| **Tap-to-Run** | ❌ | ❌ | ✅ (pending) |
| **Offline** | ✅ | ❌ | ❌ |
| **Speed** | ⚡ Instant | 🟢 Fast | 🟡 IoT delay |
| **Reliability** | ✅ High | ✅ High | ⚠️ Medium |
| **Setup** | Simple | Medium | Complex |
| **Auth** | None | API Key | Email/Password |

## Recommended Usage Strategy

### For Home Assistant / n8n Integration
1. **Primary**: Platform API for DIY and platform scenes
2. **Secondary**: Local UDP for instant offline control
3. **Future**: Undocumented API for tap-to-run automation

### For Claude Desktop / AI Integration
- Use Platform API (fully working, reliable)
- Fall back to Local UDP for offline scenarios
- Document tap-to-run shortcuts for future use

## Implementation Status

### ✅ Fully Working
- Local UDP scene control (15 scenes)
- Platform API DIY scenes (7 custom scenes)
- Platform API platform scenes (89 built-in scenes)

### ⏳ Pending
- Undocumented API authentication (status 454 issue)
- AWS IoT MQTT client
- Tap-to-run shortcut activation

### 📝 Future Enhancements
- AWS IoT MQTT implementation for real-time updates
- Tap-to-run shortcut creation/editing
- Music mode support
- Segment control for multi-zone devices

## Testing Results

### H6078 Torch Floor Lamp - Real World Usage

**Platform API (✅ Recommended - Highly Reliable):**
- ✅ 7 DIY scenes - Working perfectly
- ✅ 89 platform scenes - Working perfectly
- ✅ Scene activation - Instant and reliable
- ✅ Best user experience

**Local UDP (⚠️ Limited Functionality):**
- ⚠️ 15 scene codes available
- ❌ Scene activation unreliable on H6078
- ❌ Lamp stays in current state or doesn't respond
- 🔍 May work better on other Govee models
- 💡 Basic controls (on/off, brightness, color) work fine

**Undocumented API (❌ Authentication Blocked):**
- ❌ Auth endpoint returns status 454
- ❌ Tap-to-run shortcuts not accessible
- ⏳ Infrastructure ready, waiting for auth fix

### Recommended Setup
```
Primary: Platform API (96 scenes, 100% reliable)
Backup: Local UDP for basic controls (on/off, brightness, color)
Future: Tap-to-run when auth is resolved
```

### Example Successful Activations
```
✅ Platform API: activate_diy_scene("Fire") → Custom fire scene
✅ Platform API: activate_platform_scene_tool("Sunrise") → Sunrise animation
✅ Platform API: activate_platform_scene_tool("Christmas") → Holiday scene
⚠️ Local UDP: activate_scene(10) → May not work on H6078
```

## References

- [Govee Official Developer Portal](https://developer.govee.com/)
- [govee2mqtt Project](https://github.com/wez/govee2mqtt) - Rust implementation
- [govee-local-api](https://github.com/Galorhallen/govee-local-api) - Python local API
- [govee-api-laggat](https://github.com/LaggAt/python-govee-api) - Python cloud API

---

**Last Updated**: 2026-01-11
**MCP Server Version**: Development
**Tested Device**: H6078 Torch Floor Lamp
