log_definitions = {
    "apache": {
        "sep": " ",
        "fields": [
            {"name": "datetime", "pos": slice(0, 5), "type": "datetime"},
            {"name": "status", "pos": 5, "type": int},
            {"name": "message", "pos": slice(6, None), "type": str},
        ],
    },
    "auth": {
        "sep": " ",
        "fields": [
            {"name": "month", "pos": 0, "type": str},
            {"name": "day", "pos": 1, "type": int},
            {"name": "time", "pos": 2, "type": "datetime"},
            {"name": "hostname", "pos": 3, "type": str},
            {"name": "service", "pos": 4, "type": str},
            {"name": "message", "pos": slice(5, None), "type": str},
        ],
    },
    "dns": {
        "sep": " ",
        "fields": [
            {"name": "date", "pos": 0, "type": "datetime"},
            {"name": "time", "pos": 1, "type": "datetime"},
            {"name": "query", "pos": 2, "type": str},
            {"name": "domain", "pos": 3, "type": str},
            {"name": "record_type", "pos": 4, "type": str},
        ],
    },
    "firewall": {
        "sep": " ",
        "fields": [
            {"name": "month", "pos": 0, "type": str},
            {"name": "day", "pos": 1, "type": int},
            {"name": "time", "pos": 2, "type": "datetime"},
            {"name": "host", "pos": 3, "type": str},
            {"name": "kernel", "pos": 4, "type": str},
            {"name": "message", "pos": slice(5, None), "type": str},
        ],
    },
    "linux": {
        "sep": " ",
        "fields": [
            {"name": "datetime", "pos": slice(0, 3), "type": "datetime"},
            {"name": "level", "pos": 3, "type": str},
            {"name": "component", "pos": 4, "type": str},
            {"name": "pid", "pos": 5, "type": str},
            {"name": "Content", "pos": slice(6, None), "type": str},
        ],
    },
    "ssh": {
        "sep": " ",
        "fields": [
            {"name": "datetime", "pos": slice(0, 3), "type": "datetime"},
            {"name": "level", "pos": 3, "type": str},
            {"name": "component", "pos": 4, "type": str},
            {"name": "pid", "pos": 5, "type": str},
            {"name": "Content", "pos": slice(6, None), "type": str},
        ],
    },
    "xferlog": {
        "sep": " ",
        "fields": [
            {"name": "current_time", "pos": slice(0, 5), "type": "datetime"},
            {"name": "transfer_time", "pos": 5, "type": int},
            {"name": "remote_host", "pos": 6, "type": str},
            {"name": "file_size", "pos": 7, "type": int},
            {"name": "filename", "pos": 8, "type": str},
            {"name": "transfer_type", "pos": 9, "type": str},
            {"name": "special_flag", "pos": 10, "type": str},
            {"name": "direction", "pos": 11, "type": "direction"},
            {"name": "access_mode", "pos": 12, "type": str},
            {"name": "username", "pos": 13, "type": str},
            {"name": "service_name", "pos": 14, "type": str},
            {"name": "auth_method", "pos": 15, "type": int},
            {"name": "auth_user_id", "pos": 16, "type": str},
            {"name": "status", "pos": 17, "type": str},
        ],
    },
}
