import os
import glob
import logging
import requests
from typing import List, Dict, Tuple, Optional, Any

logger = logging.getLogger(__name__)

TECHGIUM_API_BASE = "https://techgium-backend.reddesert-11b07dc0.centralindia.azurecontainerapps.io/api"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin": "https://ltts.techgium.com",
    "Referer": "https://ltts.techgium.com/",
    "Content-Type": "application/json"
}

# Optional cached active token loaded via environment variable
CACHED_ACTIVE_TOKEN = os.getenv("TECHGIUM_TOKEN", "")

def _snappy_decompress(data: bytes) -> bytes:
    """Lightweight pure-python Snappy block decompressor for LevelDB."""
    pos = 0
    uncompressed_len = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        uncompressed_len |= (b & 0x7f) << shift
        if not (b & 0x80):
            break
        shift += 7

    out = bytearray()
    while pos < len(data):
        tag = data[pos]
        pos += 1
        elem_type = tag & 0x03
        if elem_type == 0:  # Literal
            length = tag >> 2
            if length < 60:
                length += 1
            elif length == 60:
                length = data[pos] + 1
                pos += 1
            elif length == 61:
                length = int.from_bytes(data[pos:pos+2], 'little') + 1
                pos += 2
            elif length == 62:
                length = int.from_bytes(data[pos:pos+3], 'little') + 1
                pos += 3
            elif length == 63:
                length = int.from_bytes(data[pos:pos+4], 'little') + 1
                pos += 4
            out.extend(data[pos:pos+length])
            pos += length
        elif elem_type == 1:  # Copy 1-byte offset
            length = ((tag >> 2) & 0x07) + 4
            offset = ((tag & 0xe0) << 3) | data[pos]
            pos += 1
            for _ in range(length):
                out.append(out[-offset])
        elif elem_type == 2:  # Copy 2-byte offset
            length = (tag >> 2) + 1
            offset = int.from_bytes(data[pos:pos+2], 'little')
            pos += 2
            for _ in range(length):
                out.append(out[-offset])
        elif elem_type == 3:  # Copy 4-byte offset
            length = (tag >> 2) + 1
            offset = int.from_bytes(data[pos:pos+4], 'little')
            pos += 4
            for _ in range(length):
                out.append(out[-offset])
    return bytes(out)

def _read_varint(data: bytes, pos: int) -> Tuple[int, int]:
    val = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        val |= (b & 0x7f) << shift
        if not (b & 0x80):
            break
        shift += 7
    return val, pos

def extract_token_from_brave() -> Optional[str]:
    """
    Extracts the authenticated Techgium JWT token directly from Brave browser LevelDB storage.
    """
    brave_leveldb_dir = os.path.expandvars(
        r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Local Storage\leveldb"
    )
    if not os.path.exists(brave_leveldb_dir):
        return None

    ldb_files = glob.glob(os.path.join(brave_leveldb_dir, "*.ldb"))
    for filepath in sorted(ldb_files, key=os.path.getmtime, reverse=True):
        try:
            with open(filepath, 'rb') as f:
                content = f.read()

            if len(content) < 48:
                continue

            footer = content[-48:]
            pos = 0
            meta_offset, pos = _read_varint(footer, pos)
            meta_size, pos = _read_varint(footer, pos)
            index_offset, pos = _read_varint(footer, pos)
            index_size, pos = _read_varint(footer, pos)

            idx_raw = content[index_offset:index_offset+index_size]
            idx_type = content[index_offset+index_size]
            idx_block = _snappy_decompress(idx_raw) if idx_type == 1 else idx_raw

            restarts_offset = len(idx_block) - 4 * int.from_bytes(idx_block[-4:], 'little') - 4
            pos = 0
            prev_key = b""
            while pos < restarts_offset:
                shared, pos = _read_varint(idx_block, pos)
                unshared, pos = _read_varint(idx_block, pos)
                val_len, pos = _read_varint(idx_block, pos)
                key = prev_key[:shared] + idx_block[pos:pos+unshared]
                pos += unshared
                val = idx_block[pos:pos+val_len]
                pos += val_len
                prev_key = key

                b_pos = 0
                b_offset, b_pos = _read_varint(val, b_pos)
                b_size, b_pos = _read_varint(val, b_pos)

                b_raw = content[b_offset:b_offset+b_size]
                b_type = content[b_offset+b_size]
                try:
                    data = _snappy_decompress(b_raw) if b_type == 1 else b_raw
                    if b'token":"eyJ' in data:
                        idx = data.find(b'token":"eyJ') + len('token":"')
                        end_idx = data.find(b'"', idx)
                        if end_idx != -1:
                            token_candidate = data[idx:end_idx].decode('ascii', errors='ignore')
                            if token_candidate.startswith("eyJ") and len(token_candidate) > 50:
                                return token_candidate
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Error reading ldb {filepath}: {e}")

    return None

def get_active_session_token() -> Optional[str]:
    """
    Returns an active authenticated Techgium session token by checking:
    1. Brave browser storage
    2. Cached known token
    Validates token against the challenges endpoint before returning.
    """
    candidates = []
    brave_token = extract_token_from_brave()
    if brave_token:
        candidates.append(brave_token)
    if CACHED_ACTIVE_TOKEN and CACHED_ACTIVE_TOKEN not in candidates:
        candidates.append(CACHED_ACTIVE_TOKEN)

    for tok in candidates:
        try:
            url = f"{TECHGIUM_API_BASE}/challenges/getChallenges"
            headers = {**DEFAULT_HEADERS, "Authorization": f"Bearer {tok}"}
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200 and isinstance(res.json(), list):
                logger.info(f"Verified active Techgium session token ({len(res.json())} challenges available).")
                return tok
        except Exception as e:
            logger.debug(f"Token validation failed: {e}")

    return None

def login_techgium(email: str, password: str) -> Tuple[bool, str, Optional[str], bool]:
    """
    Initiates login to Techgium backend.
    Returns: (success: bool, message: str, token: Optional[str], requires_otp: bool)
    """
    url = f"{TECHGIUM_API_BASE}/users/login"
    payload = {
        "email": email.strip(),
        "password": password.strip()
    }
    
    try:
        logger.info(f"Attempting Techgium login for: {email}")
        response = requests.post(url, json=payload, headers=DEFAULT_HEADERS, timeout=15)
        data = response.json()
        
        if response.status_code == 200 and not data.get("error"):
            token = data.get("token")
            if not token and isinstance(data.get("user"), dict):
                token = data["user"].get("token")
            
            msg = data.get("message", "Login successful!")
            # Techgium sends OTP for 2FA verification
            if "otp" in msg.lower() or not token:
                logger.info("Techgium sent OTP to user email.")
                return True, msg or "OTP has been sent to your email address.", None, True

            return True, msg, token, False
        else:
            err_msg = data.get("message") or "Authentication failed. Please check your credentials."
            return False, err_msg, None, False
            
    except Exception as e:
        logger.error(f"Techgium login exception: {e}")
        return False, f"Connection to Techgium login API failed: {str(e)}", None, False

def verify_techgium_otp(email: str, otp: str) -> Tuple[bool, str, Optional[str]]:
    """
    Verifies 6-digit OTP sent to the user's email.
    Returns: (success: bool, message: str, token: Optional[str])
    """
    url = f"{TECHGIUM_API_BASE}/users/verify-otp"
    payload = {
        "email": email.strip(),
        "otp": otp.strip()
    }
    
    try:
        logger.info(f"Submitting OTP verification for: {email}")
        response = requests.post(url, json=payload, headers=DEFAULT_HEADERS, timeout=15)
        data = response.json()
        
        if response.status_code == 200 and not data.get("error"):
            token = data.get("token")
            if not token and isinstance(data.get("user"), dict):
                token = data["user"].get("token")
            return True, data.get("message", "OTP verified successfully!"), token
        else:
            msg = data.get("message", "Invalid or expired OTP.")
            return False, msg, None
            
    except Exception as e:
        logger.error(f"OTP verification exception: {e}")
        return False, f"Failed to verify OTP: {str(e)}", None

def fetch_techgium_challenges(token: str) -> Tuple[bool, str, List[Dict]]:
    """
    Fetches all official problem statements / challenges using a Bearer token.
    Returns: (success: bool, message: str, challenges: List[Dict])
    """
    url = f"{TECHGIUM_API_BASE}/challenges/getChallenges"
    headers = {
        **DEFAULT_HEADERS,
        "Authorization": f"Bearer {token.strip()}"
    }
    
    try:
        logger.info("Fetching challenges from Techgium API...")
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Filter for published challenges if status field exists
                published = [c for c in data if c.get("status") in ["publish", "active", None]]
                challenges = published if published else data
                logger.info(f"Successfully retrieved {len(challenges)} Techgium challenges.")
                return True, f"Found {len(challenges)} official challenges.", challenges
            elif isinstance(data, dict) and data.get("error"):
                return False, data.get("message", "Failed to retrieve challenges."), []
            else:
                return False, "Unexpected response format from challenges endpoint.", []
        elif response.status_code == 401:
            return False, "Session token expired or access denied (401). Please re-enter your credentials or OTP.", []
        else:
            return False, f"Techgium API returned HTTP {response.status_code}", []
            
    except Exception as e:
        logger.error(f"Error fetching Techgium challenges: {e}")
        return False, f"Failed to connect to challenges endpoint: {str(e)}", []
