import pytest
import os
from tempfile import NamedTemporaryFile
from src.data.parser import parse_zeek_log

def create_temp_log(content: str) -> str:
    """Helper to create a temporary log file for testing."""
    temp_file = NamedTemporaryFile(delete=False, mode='w')
    temp_file.write(content)
    temp_file.close()
    return temp_file.name

def test_valid_conn_log():
    content = """#fields\tts\tuid\tid.orig_h\tid.orig_p\tid.resp_h\tid.resp_p\tproto\tservice
1592398284.456	C123	192.168.1.5	12345	10.0.0.8	80	tcp	http
"""
    filepath = create_temp_log(content)
    try:
        logs = parse_zeek_log(filepath)
        assert len(logs) == 1
        assert logs[0]["timestamp"] == "1592398284.456"
        assert logs[0]["src_ip"] == "192.168.1.5"
        assert logs[0]["dst_ip"] == "10.0.0.8"
        assert logs[0]["protocol"] == "tcp"
        assert logs[0]["payload_snippet"] == ""
        assert logs[0]["ground_truth_technique_id"] is None
    finally:
        os.remove(filepath)

def test_missing_fields_graceful():
    # Only ts and id.orig_h are present in #fields, simulating a very stripped log
    content = """#fields\tts\tid.orig_h
1592398284.456	192.168.1.5
"""
    filepath = create_temp_log(content)
    try:
        logs = parse_zeek_log(filepath)
        assert len(logs) == 1
        assert logs[0]["timestamp"] == "1592398284.456"
        assert logs[0]["src_ip"] == "192.168.1.5"
        assert logs[0]["dst_ip"] == "" # Default from get()
        assert logs[0]["protocol"] == "" # Default from get()
        assert logs[0]["ground_truth_technique_id"] is None
    finally:
        os.remove(filepath)

def test_malformed_line_skips():
    # 3 headers, but only 2 fields provided on the data line
    content = """#fields\tts\tid.orig_h\tproto
1592398284.456	192.168.1.5
"""
    filepath = create_temp_log(content)
    try:
        logs = parse_zeek_log(filepath)
        assert len(logs) == 0 # Malformed line should be skipped silently
    finally:
        os.remove(filepath)

def test_dns_log_parsing():
    content = """#fields\tts\tuid\tid.orig_h\tid.orig_p\tid.resp_h\tid.resp_p\tproto\ttrans_id\tquery
1592398284.456	C123	192.168.1.5	12345	8.8.8.8	53	udp	1234	evil.com
"""
    filepath = create_temp_log(content)
    try:
        logs = parse_zeek_log(filepath)
        assert len(logs) == 1
        assert logs[0]["protocol"] == "udp"
        assert logs[0]["payload_snippet"] == "evil.com" # Should map 'query' to 'payload_snippet'
    finally:
        os.remove(filepath)
